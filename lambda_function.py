import json
import logging
from datetime import datetime

from Comparator import Comparator

# from EmbassyEventFetcher import EmbassyEventFetcher
from JapanFoundationEventFetcher import JapanFoundationEventFetcher
from JapanHouseEventFetcher import JapanHouseEventFetcher
from JapanSocietyEventFetcher import JapanSocietyEventFetcher
from JETAAEventFetcher import JETAAEventFetcher
from S3Manager import S3Manager
from SlackManager import SlackManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):
    bucket_name = "jetaa-events"
    prefix = "as-json"
    year = 2024
    s3_manager = S3Manager()
    slack_manager = SlackManager()
    jetaa_calendar_events_processor = JETAAEventFetcher(year)
    japan_house_scanner = JapanHouseEventFetcher()
    japan_society_scanner = JapanSocietyEventFetcher()
    # embassy_calendar_scanner = EmbassyEventFetcher(year)
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
    # fresh_scan_events["JAPAN_EMBASSY"] = (
    #     embassy_calendar_scanner.combine_and_return_events()
    # )
    fresh_scan_events["JAPAN_FOUNDATION"] = japan_foundation.combine_and_return_events()

    new_events = comparator.find_new_events(fresh_scan_events)

    logger.debug(new_events)

    slack_manager.slack_notifier(new_events)
    logger.info("Slack notified")

    file_name = f"{prefix}/events_{datetime.now().strftime('%Y-%m-%d-%H:%M:%S')}.json"

    s3_manager.upload_json_to_s3(fresh_scan_events, bucket_name, file_name)
    logger.info("Uploaded to S3")

    # slack_manager.send_to_dev()

    return {
        "statusCode": 200,
        "body": json.dumps("Event processing completed successfully."),
    }


if __name__ == "__main__":
    lambda_handler(None, None)
