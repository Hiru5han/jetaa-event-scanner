import logging

from S3Manager import S3Manager
from SlackManager import SlackManager


logger = logging.getLogger(__name__)


class Comparator:
    def __init__(self):
        self.bucket_name = "jetaa-events"
        self.prefix = "as-json"
        self.s3_manager = S3Manager()
        self.slack_manager = SlackManager()

    def load_old_events(self):
        logger.debug("Loading previous state")
        old_scan_events = self.s3_manager.get_latest_json_file_resource(
            self.bucket_name, self.prefix
        )
        logger.debug(f"Loaded old events: {old_scan_events}")
        return old_scan_events

    def find_new_events(self, fresh_scan_events):
        old_scan_events = self.load_old_events()
        logger.debug(f"Old scan events: {old_scan_events}")
        old_scan_event_source_ids = {}
        for old_scan_source, old_scan_events in old_scan_events.items():
            old_scan_event_set = set()
            for old_scan_event in old_scan_events:
                old_scan_event_id = (
                    old_scan_event["event_source"],
                    old_scan_event["event_name"],
                    old_scan_event["event_location"],
                    old_scan_event["event_date"],
                    old_scan_event["event_time"],
                    old_scan_event["event_price"],
                    old_scan_event["event_url"],
                )
                old_scan_event_set.add(old_scan_event_id)
            old_scan_event_source_ids[old_scan_source] = old_scan_event_set

        new_events = []
        logger.debug("Checking for new events")

        try:
            for fresh_scan_source, fresh_scan_events in fresh_scan_events.items():
                for fresh_scan_event in fresh_scan_events:
                    fresh_scan_event_id = (
                        fresh_scan_event["event_source"],
                        fresh_scan_event["event_name"],
                        fresh_scan_event["event_location"],
                        fresh_scan_event["event_date"],
                        fresh_scan_event["event_time"],
                        fresh_scan_event["event_price"],
                        fresh_scan_event["event_url"],
                    )
                    if (
                        fresh_scan_source in old_scan_event_source_ids
                        and fresh_scan_event_id
                        not in old_scan_event_source_ids[fresh_scan_source]
                    ):
                        try:
                            logger.debug(f"New event found: {fresh_scan_event}")
                            new_events.append(fresh_scan_event)
                        except Exception as event_error:
                            logger.error(f"Error parsing new event: {event_error}")
                            self.slack_manager.send_error_message(
                                f"Error parsing new event: {event_error}"
                            )
        except Exception as event_compare_error:
            logger.error(f"Error comparing old events to new: {event_compare_error}")
            self.slack_manager.send_error_message(
                f"Error comparing old events to new: {event_compare_error}"
            )
        return new_events

    def load_week_old_events(self):
        """Load events from a week ago."""
        logger.debug("Loading week-old events")
        week_old_events = self.s3_manager.get_json_file_from_week_ago(
            self.bucket_name, self.prefix
        )
        logger.debug(f"Loaded week-old events: {week_old_events}")
        return week_old_events

    def compare_with_week_old_events(self, fresh_scan_events):
        """Compare fresh scan with week-old scan to find new events."""
        old_scan_events = self.load_week_old_events()
        new_events = []
        logger.debug("Comparing fresh scan with week-old events")

        if not old_scan_events:
            logger.error("No old events found to compare.")
            return new_events

        old_event_ids = {
            (
                e["event_source"],
                e["event_name"],
                e["event_location"],
                e["event_date"],
                e["event_time"],
                e["event_price"],
                e["event_url"],
            )
            for events in old_scan_events.values()
            for e in events
        }

        for source, events in fresh_scan_events.items():
            for event in events:
                event_id = (
                    event["event_source"],
                    event["event_name"],
                    event["event_location"],
                    event["event_date"],
                    event["event_time"],
                    event["event_price"],
                    event["event_url"],
                )
                if event_id not in old_event_ids:
                    logger.debug(f"New event found: {event}")
                    new_events.append(event)

        return new_events
