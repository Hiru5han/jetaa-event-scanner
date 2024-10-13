import json
import logging
from datetime import datetime

from Comparator import Comparator
from JapanFoundationEventFetcher import JapanFoundationEventFetcher
from JapanHouseEventFetcher import JapanHouseEventFetcher
from JapanSocietyEventFetcher import JapanSocietyEventFetcher
from JETAAEventFetcher import JETAAEventFetcher
from S3Manager import S3Manager
from SlackManager import SlackManager

# Configure the root logger
logger = logging.getLogger()  # root logger
logger.setLevel(logging.DEBUG)

# Set up file and console handlers
log_file_name = f"lambda_logs_{datetime.now().strftime('%Y-%m-%d-%H:%M:%S')}.txt"
file_handler = logging.FileHandler(log_file_name)
console_handler = logging.StreamHandler()

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


def lambda_handler(event, context):
    bucket_name = "jetaa-events"
    prefix = "as-json"
    weekly_prefix = "weekly"
    year = 2024
    s3_manager = S3Manager()
    slack_manager = SlackManager()
    jetaa_calendar_events_processor = JETAAEventFetcher(year)
    japan_house_scanner = JapanHouseEventFetcher()
    japan_society_scanner = JapanSocietyEventFetcher()
    japan_foundation = JapanFoundationEventFetcher()
    comparator = Comparator()
    fresh_scan_events = {}

    fresh_scan_events["JETAA"] = (
        jetaa_calendar_events_processor.jetaa_calendar_events_processor()
    )
    fresh_scan_events["JAPAN_HOUSE"] = japan_house_scanner.combine_and_return_events()
    fresh_scan_events["JAPAN_SOCIETY"] = (
        japan_society_scanner.combine_and_return_events()
    )
    fresh_scan_events["JAPAN_FOUNDATION"] = japan_foundation.combine_and_return_events()

    new_events = comparator.find_new_events(fresh_scan_events)

    logger.debug(new_events)

    slack_manager.slack_notifier(new_events)
    logger.info("Slack notified")

    file_name = f"{prefix}/events_{datetime.now().strftime('%Y-%m-%d-%H:%M:%S')}.json"

    s3_manager.upload_json_to_s3(fresh_scan_events, bucket_name, file_name)
    logger.info("Uploaded to S3")

    # Check if today is Sunday
    today = datetime.now()
    if today.weekday() == 6:  # 6 means Sunday in Python's weekday() function
        logger.info("Today is Sunday. Performing weekly scan.")

        # Find new events for the week
        weekly_new_events = comparator.compare_with_week_old_events(fresh_scan_events)

        logger.debug(f"Weekly new events: {weekly_new_events}")

        # Save weekly events JSON to S3
        weekly_file_name = (
            f"{prefix}/{weekly_prefix}/events_{today.strftime('%Y-%m-%d')}.json"
        )
        s3_manager.upload_json_to_s3(weekly_new_events, bucket_name, weekly_file_name)
        logger.info(f"Uploaded weekly events to S3: {weekly_file_name}")

    # slack_manager.send_to_dev()

    return {
        "statusCode": 200,
        "body": json.dumps("Event processing completed successfully."),
    }


if __name__ == "__main__":
    lambda_handler(None, None)
