import json
import logging
import os
from datetime import datetime

from fetchers.DaiwaFoundationEventFetcher import DaiwaFoundationEventFetcher
from fetchers.JapanFoundationEventFetcher import JapanFoundationEventFetcher
from fetchers.JapanHouseEventFetcher import JapanHouseEventFetcher
from fetchers.JapanSocietyEventFetcher import JapanSocietyEventFetcher
from fetchers.JETAAEventFetcher import JETAAEventFetcher
from utils.Comparator import Comparator
from utils.GoogleChatManager import GoogleChatManager
from utils.S3Manager import S3Manager

# Logger setup
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Check if there are any handlers already (to avoid duplicates)
if not logger.hasHandlers():
    # Console handler for terminal output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Formatter for console output
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


# Group events by source
def group_events_by_source(events):
    grouped_events = {
        "JAPAN_HOUSE": [],
        "JAPAN_SOCIETY": [],
        "JAPAN_FOUNDATION": [],
        "JETAA": [],
        "DAIWA_FOUNDATION": [],
    }

    for event in events:
        event_source = event.get("event_source")

        if event_source == "japan_house":
            grouped_events["JAPAN_HOUSE"].append(event)
        elif event_source == "japan_society":
            grouped_events["JAPAN_SOCIETY"].append(event)
        elif event_source == "japan_foundation":
            grouped_events["JAPAN_FOUNDATION"].append(event)
        elif event_source == "jetaa":
            grouped_events["JETAA"].append(event)
        elif event_source == "daiwa_foundation":
            grouped_events["DAIWA_FOUNDATION"].append(event)
        else:
            logger.warning(f"Unknown event source: {event_source}")

    return grouped_events


def lambda_handler(event, context):
    bucket_name = "jetaa-events"
    prefix = "as-json"
    weekly_prefix = "weekly"
    year = 2025
    s3_manager = S3Manager()
    jetaa_calendar_events_processor = JETAAEventFetcher(year)
    japan_house_scanner = JapanHouseEventFetcher()
    japan_society_scanner = JapanSocietyEventFetcher()
    japan_foundation = JapanFoundationEventFetcher()
    daiwa_foundation = DaiwaFoundationEventFetcher()
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

    fresh_scan_events["DAIWA_FOUNDATION"] = daiwa_foundation.combine_and_return_events()

    new_events = comparator.find_new_events(fresh_scan_events)
    logger.debug(new_events)

    grouped_new_events = group_events_by_source(new_events)
    logger.debug(grouped_new_events)

    # Initialise GoogleChatManager
    chat_manager = GoogleChatManager()

    # Flatten the grouped events into a single list for sending
    events_to_notify = []
    for event_list in grouped_new_events.values():
        events_to_notify.extend(event_list)

    # Send events to Google Chat
    chat_manager.notify_events(events_to_notify)
    logger.info("Google Chat notified")

    file_name = f"{prefix}/events_{datetime.now().strftime('%Y-%m-%d-%H:%M:%S')}.json"

    s3_manager.upload_json_to_s3(fresh_scan_events, bucket_name, file_name)
    logger.info("Uploaded to S3")

    # Weekly processing
    day = os.environ.get("DAY_NUMBER", 6)
    today = datetime.now()
    if today.weekday() == int(day):  # 6 means Sunday
        logger.info("Today is Sunday. Performing weekly scan.")
        weekly_file_name = (
            f"{prefix}/{weekly_prefix}/events_{today.strftime('%Y-%m-%d')}.json"
        )

        if s3_manager.file_exists(bucket_name, weekly_file_name):
            logger.info(
                f"Weekly file already exists: {weekly_file_name}. Skipping scan."
            )
        else:
            logger.info("Weekly file not found. Running weekly scan.")

            # Find new events for the week
            weekly_new_events = comparator.compare_with_week_old_events(
                fresh_scan_events
            )
            weekly_grouped_events = group_events_by_source(weekly_new_events)
            logger.debug(f"Weekly new events: {weekly_new_events}")

            # Save weekly events JSON to S3
            s3_manager.upload_json_to_s3(
                weekly_grouped_events, bucket_name, weekly_file_name
            )
            logger.info(f"Uploaded weekly events to S3: {weekly_file_name}")

    return {
        "statusCode": 200,
        "body": json.dumps("Event processing completed successfully."),
    }


if __name__ == "__main__":
    lambda_handler(None, None)
