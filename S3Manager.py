import csv
import io
import sys
import boto3
import logging
from botocore.exceptions import NoCredentialsError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class S3Manager:
    def __init__(self):
        self.s3_resource = boto3.resource("s3")

    def get_latest_csv_file_content(self, bucket_name, prefix):
        logger.debug("Fetching the latest CSV file")
        try:
            bucket = self.s3_resource.Bucket(bucket_name)

            csv_files = []
            logger.debug(f"CSV files before appending: {csv_files}")
            # Include the prefix in the objects filter
            for obj in bucket.objects.filter(Prefix=prefix):
                if obj.key.endswith(".csv"):
                    csv_files.append(
                        {"Key": obj.key, "LastModified": obj.last_modified}
                    )
            logger.debug(f"CSV files after appending: {csv_files}")
            if not csv_files:
                logger.debug("No CSV files found within the specified prefix.")

            logger.debug("Retreiving latest CSV file")
            # Find the latest CSV file
            latest_csv_file = sorted(
                csv_files, key=lambda x: x["LastModified"], reverse=True
            )[0]["Key"]

            # Get the object for the latest CSV file
            csv_object = bucket.Object(latest_csv_file).get()
            logger.debug(f"CSV object: {csv_object}")

            # Get the body of the object
            csv_content = csv_object["Body"].read().decode("utf-8")
            logger.debug(f"CSV content: {csv_content}")

            csv_lines = csv_content.split("\n")
            reader = csv.reader(csv_lines)
            next(reader)  # Skip header
            csv2_data = [tuple(row) for row in reader]

        except NoCredentialsError:
            logger.error("Error: AWS credentials not found.")
        except Exception as file_fetch_error:
            logger.error(f"Error: {file_fetch_error}")

        return csv2_data

    def _csv_formatter(self, events_collected):
        logger.debug("Formatting csv before puttting to S3")
        # To handle event titles with commas in CSVs
        try:
            # Use StringIO to create CSV content in memory
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

                # Move the cursor to the beginning of the
                # StringIO object to read its content
                csv_content = csv_file.getvalue()

            # Ensure content is encoded in 'utf-8'
            encoded_csv_content = csv_content.encode("utf-8")
        except Exception as formatting_error:
            logger.error(f"Error with formatting: {formatting_error}")
            return None

        return encoded_csv_content

    def upload_csv_to_s3(self, events_collected, bucket_name, file_name):
        encoded_csv_content = self._csv_formatter(events_collected)

        if not encoded_csv_content:
            logger.debug("Formatter returned None, exitting")
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
