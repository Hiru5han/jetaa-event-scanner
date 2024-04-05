import csv
import io
import json
import sys
import boto3
import logging
from botocore.exceptions import NoCredentialsError

from SlackManager import SlackManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class S3Manager:
    def __init__(self):
        self.s3_resource = boto3.resource("s3")
        self.slack_manager = SlackManager()

    def get_latest_json_file_resource(self, bucket_name, prefix):
        """Returns the content of the latest JSON file from an S3 bucket using boto3 resource, optionally filtered by a prefix."""
        bucket = self.s3_resource.Bucket(bucket_name)
        try:
            json_files = [
                obj
                for obj in bucket.objects.filter(Prefix=prefix)
                if obj.key.endswith(".json")
            ]
            if not json_files:
                return "No JSON files found with the specified prefix."

            latest_file = max(json_files, key=lambda x: x.last_modified)

            json_object = json.load(bucket.Object(latest_file.key).get()["Body"])
            logger.debug(f"JSON object: {json_object}")
            logger.debug(f"JSON object type: {type(json_object)}")
        except NoCredentialsError:
            logger.debug("No AWS credentials found. Please configure them to proceed.")
            self.slack_manager.send_error_message(
                "No AWS credentials found. Please configure them to proceed."
            )
            return False
        except Exception as latest_json_get_error:
            logger.debug(f"An error occurred: {latest_json_get_error}")
            self.slack_manager.send_error_message(
                f"An error occurred: {latest_json_get_error}"
            )
            return False

        return json_object

    def _csv_formatter(self, events_collected):
        logger.debug("Formatting csv before puttting to S3")
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
            self.slack_manager.send_error_message(
                f"Error with formatting: {formatting_error}"
            )
            return None

        return encoded_csv_content

    def upload_csv_to_s3(self, events_collected, bucket_name, file_name):
        encoded_csv_content = self._csv_formatter(events_collected)

        if not encoded_csv_content:
            logger.debug("Formatter returned None, exitting")
            self.slack_manager.send_error_message("Formatter returned None, exitting")
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
            self.slack_manager.send_error_message(
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
            self.slack_manager.send_error_message(
                f"Failed to upload {file_name} to S3 bucket {bucket_name}: {upload_error}"
            )
            return False

        return True
