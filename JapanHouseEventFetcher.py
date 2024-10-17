import json
import logging
import re

import requests
from bs4 import BeautifulSoup

from SlackManager import SlackManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class JapanHouseEventFetcher:
    def __init__(self):
        self.url = "https://www.japanhouselondon.uk/whats-on/"
        self.event_source = "japan_house"
        self.slack_manager = SlackManager()
        self.events_data = []

    def _fetch_page_content(self):
        response = requests.get(self.url)
        logger.debug(f"URL: {self.url}")
        logger.debug(f"Status code: {response.status_code}")

        if response.status_code == 200:
            logger.debug("Successfully fetched the webpage content.")
            return response.text
        else:
            logger.error(
                f"Failed to fetch the {self.event_source} webpage content. Status code: {response.status_code}"
            )
            return None

    def _parse_events_from_vbind(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")

        # Find the archive-whats-on component and its v-bind attribute
        archive_whats_on = soup.find("archive-whats-on")
        if archive_whats_on and "v-bind" in archive_whats_on.attrs:
            vbind_content = archive_whats_on["v-bind"]
            # Replace HTML entities with actual quotes
            vbind_content = vbind_content.replace("&quot;", '"')
            try:
                event_data_json = json.loads(vbind_content)
                logger.debug(f"Extracted JSON: {event_data_json}")
                return event_data_json
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from v-bind: {e}")
                return None
        else:
            logger.error("Could not find the 'v-bind' attribute in 'archive-whats-on'.")
            return None

    def _extract_event_details(self, event_json):
        extracted_events = []

        if "posts" in event_json:
            for post in event_json["posts"]:
                # Extract image URL and clean it from size suffixes if present
                image_url = post.get("image", {}).get("url", "")
                if image_url:
                    # Remove any size suffixes from the image URL
                    image_url = re.sub(r"-\d+x\d+(?=\.\w{3,4}$)", "", image_url)

                # Construct the event_dict with the original keys
                event_dict = {
                    "event_source": self.event_source,
                    "event_name": post.get("title"),
                    "event_location": post.get("event_location"),
                    "event_date": post.get("date_range"),
                    "event_time": "Not available",
                    "event_price": "Not available",
                    "event_url": post.get("url"),
                    "event_image_url": image_url,
                }

                logger.debug(f"Extracted event: {event_dict}")
                extracted_events.append(event_dict)
        else:
            logger.error("No 'posts' data found in JSON.")
        return extracted_events

    def combine_and_return_events(self):
        html_content = self._fetch_page_content()
        if not html_content:
            logger.error("No HTML content to parse.")
            return []

        # Parse the v-bind JSON from the archive-whats-on component
        event_json = self._parse_events_from_vbind(html_content)
        if event_json is None:
            logger.error("Failed to parse events from JSON.")
            return []

        # Extract event details from the parsed JSON
        self.events_data = self._extract_event_details(event_json)

        if not self.events_data:
            logger.error("Issue with Japan House event fetcher, no events found")
            self.slack_manager.send_error_message(
                "Issue with Japan House event fetcher, no events found"
            )

        return self.events_data


if __name__ == "__main__":
    scraper = JapanHouseEventFetcher()
    events = scraper.combine_and_return_events()
    for event in events:
        print(event)
