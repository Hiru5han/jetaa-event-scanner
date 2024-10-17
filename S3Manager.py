import csv
import io
import json
import logging
import sys
from datetime import datetime, timedelta, timezone

import boto3
from botocore.exceptions import NoCredentialsError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class S3Manager:
    def __init__(self):
        self.s3_resource = boto3.resource("s3")

    def get_latest_json_file_resource(self, bucket_name, prefix):
        """Returns the content of the latest JSON file from an S3 bucket using boto3 resource, optionally filtered by a prefix."""
        bucket = self.s3_resource.Bucket(bucket_name)
        try:
            json_files = [
                obj
                for obj in bucket.objects.filter(Prefix=prefix)
                if obj.key.endswith(".json") and "weekly" not in obj.key
            ]
            if not json_files:
                return "No JSON files found with the specified prefix."

            latest_file = max(json_files, key=lambda x: x.last_modified)

            json_object = json.load(bucket.Object(latest_file.key).get()["Body"])
            logger.debug(f"JSON object: {json_object}")
            logger.debug(f"JSON object type: {type(json_object)}")
        except NoCredentialsError:
            logger.debug("No AWS credentials found. Please configure them to proceed.")
            return False
        except Exception as latest_json_get_error:
            logger.debug(f"An error occurred: {latest_json_get_error}")
            return False

        return json_object

    def get_json_file_from_week_ago(self, bucket_name, prefix):
        """Returns the JSON file from S3 that was modified a week ago."""
        bucket = self.s3_resource.Bucket(bucket_name)
        try:
            # Make the current datetime timezone-aware
            one_week_ago = datetime.now(timezone.utc) - timedelta(weeks=1)
            json_files = [
                obj
                for obj in bucket.objects.filter(Prefix=prefix)
                if obj.key.endswith(".json")
            ]
            if not json_files:
                return "No JSON files found with the specified prefix."

            # Find the file closest to one week ago
            week_old_file = min(
                json_files,
                key=lambda x: abs((x.last_modified - one_week_ago).total_seconds()),
            )

            json_object = json.load(bucket.Object(week_old_file.key).get()["Body"])
            logger.debug(f"JSON object from a week ago: {json_object}")
        except NoCredentialsError:
            logger.debug("No AWS credentials found. Please configure them to proceed.")
            return False
        except Exception as e:
            logger.debug(f"An error occurred while fetching week-old JSON: {e}")
            return False

        return json_object

    def _csv_formatter(self, events_collected):
        logger.debug("Formatting csv before putting to S3")
        try:
            with io.StringIO() as csv_file:
                writer = csv.writer(
                    csv_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL
                )
                writer.writerow(
                    [
                        "Event Host",
                        "Event Name",
                        "Event Location",
                        "Event Date",
                        "Event Time",
                        "Event Price",
                        "Event url",
                    ]
                )
                writer.writerows(events_collected)

                csv_content = csv_file.getvalue()

            encoded_csv_content = csv_content.encode("utf-8")
        except Exception as formatting_error:
            logger.error(f"Error with formatting: {formatting_error}")
            return None

        return encoded_csv_content

    def upload_csv_to_s3(self, events_collected, bucket_name, file_name):
        encoded_csv_content = self._csv_formatter(events_collected)

        if not encoded_csv_content:
            logger.debug("Formatter returned None, exiting")
            sys.exit(1)

        try:
            logger.debug("Putting to S3 bucket")
            self.s3_resource.Object(bucket_name, file_name).put(
                Body=encoded_csv_content, ContentType="text/csv"
            )
            logger.debug(f"Uploaded {file_name} to S3 bucket {bucket_name}")
        except Exception as upload_error:
            logger.error(
                f"Failed to upload {file_name} to S3 bucket {bucket_name}: {upload_error}"
            )
            return False
        return True

    def upload_json_to_s3(self, dictionary, bucket_name, file_name):
        json_data = json.dumps(dictionary, indent=4)

        try:
            logger.debug("Putting to S3 bucket")
            self.s3_resource.Object(bucket_name, file_name).put(
                Body=json_data, ContentType="application/json"
            )
            logger.debug(f"Uploaded {file_name} to S3 bucket {bucket_name}")
        except Exception as upload_error:
            logger.error(
                f"Failed to upload {file_name} to S3 bucket {bucket_name}: {upload_error}"
            )
            return False

        return True

    def file_exists(self, bucket_name, file_name):
        """Checks if a file exists in the specified S3 bucket."""
        try:
            # Use HeadObject to check for the file without downloading it
            self.s3_resource.Object(bucket_name, file_name).load()
            logger.debug(f"File {file_name} exists in bucket {bucket_name}")
            return True
        except self.s3_resource.meta.client.exceptions.NoSuchKey:
            # This is the specific exception for missing objects
            logger.debug(f"File {file_name} does not exist in bucket {bucket_name}")
            return False
        except self.s3_resource.meta.client.exceptions.ClientError as e:
            # Handle any ClientError that isn't NoSuchKey
            if e.response["Error"]["Code"] == "404":
                logger.debug(f"File {file_name} does not exist in bucket {bucket_name}")
                return False
            else:
                logger.error(f"Error checking file existence: {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error checking file existence: {e}")
            return False


# if __name__ == "__main__":
#     s3_manager = S3Manager()
#     print(
#         s3_manager.get_json_file_from_week_ago(
#             bucket_name="jetaa-events", prefix="as-json"
#         )
#     )
