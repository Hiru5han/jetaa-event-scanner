import json
from datetime import datetime
from EventFetcher import EventFetcher
from S3Manager import S3Manager
from SlackManager import SlackManager
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def monthly_events_processor():
    events_collected = []
    try:
        for month in range(1, 13):
            logger.debug(f"\nProcessing month: {month}")
            event_fetcher = EventFetcher(2024, month)
            event_fetcher.fetch_events()
            events_collected.extend(event_fetcher.events)
    except Exception as monthly_processor_error:
        logger.debug(f"Error: {monthly_processor_error}")
        return []
    return events_collected


def lambda_handler(event, context):
    bucket_name = "jetaa-events"
    prefix = "as-csv"
    events_collected = monthly_events_processor()
    s3_manager = S3Manager()
    slack_manager = SlackManager()

    if events_collected:
        slack_manager.slack_notifier(s3_manager, events_collected, bucket_name, prefix)

        file_name = (
            f"{prefix}/events_{datetime.now().strftime('%Y-%m-%d-%H:%M:%S')}.csv"
        )
        s3_manager.upload_csv_to_s3(events_collected, bucket_name, file_name)

        slack_manager.send_to_hiru()

        return {
            "statusCode": 200,
            "body": json.dumps("Event processing completed successfully."),
        }
    else:
        logger.debug("Error processing events.")
        return {"statusCode": 500, "body": json.dumps("Error processing events.")}
