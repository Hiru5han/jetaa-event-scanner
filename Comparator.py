import logging
from S3Manager import S3Manager

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Comparator:
    def __init__(self):
        self.bucket_name = "jetaa-events"
        self.prefix = "as-json"
        self.s3_manager = S3Manager()

    def load_old_events(self):
        old_scan_events = self.s3_manager.get_latest_json_file_resource(
            self.bucket_name, self.prefix
        )
        logger.debug(old_scan_events)
        return old_scan_events

    def find_new_events(self, fresh_scan_events):
        """Compares fresh scan events to old scan events to find new events."""
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
                    logger.debug(fresh_scan_event)
                    new_events.append(fresh_scan_event)
        return new_events
