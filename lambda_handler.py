import json
from datetime import datetime
from JETAAEventFetcher import JETAAEventFetcher
from JapanHouseEventFetcher import JapanHouseEventFetcher
from JapanSocietyEventFetcher import JapanSocietyEventFetcher
from EmbassyEventFetcher import EmbassyEventFetcher
from S3Manager import S3Manager
from SlackManager import SlackManager
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):
    bucket_name = "jetaa-events"
    prefix = "as-csv"
    year = 2024
    s3_manager = S3Manager()
    slack_manager = SlackManager()
    jetaa_calendar_events_processor = JETAAEventFetcher(year)
    japan_house_scanner = JapanHouseEventFetcher()
    japan_society_scanner = JapanSocietyEventFetcher()
    embassy_calendar_scanner = EmbassyEventFetcher(year)

    jetaa_events_collected = jetaa_calendar_events_processor.jetaa_calendar_events_processor()
    logger.debug(f"Events collected: {jetaa_events_collected}")
    japan_house_events_appended = japan_house_scanner.combine_and_return_events(jetaa_events_collected)
    logger.debug(f"Japan House Events: {japan_house_events_appended}")
    japan_society_events_appended = japan_society_scanner.combine_and_return_events(japan_house_events_appended)
    logger.debug(f"Japan Society Events: {japan_society_events_appended}")
    embassy_events_appended = embassy_calendar_scanner.combine_and_return_events(japan_society_events_appended)
    logger.debug(f"Embassy Events: {embassy_events_appended}")

    if embassy_events_appended:
        slack_manager.slack_notifier(embassy_events_appended, bucket_name, prefix)

        file_name = (
            f"{prefix}/events_{datetime.now().strftime('%Y-%m-%d-%H:%M:%S')}.csv"
        )
        s3_manager.upload_csv_to_s3(embassy_events_appended, bucket_name, file_name)

        slack_manager.send_to_hiru()

        return {
            "statusCode": 200,
            "body": json.dumps("Event processing completed successfully."),
        }
    else:
        logger.debug("Error processing events.")
        return {"statusCode": 500, "body": json.dumps("Error processing events.")}
