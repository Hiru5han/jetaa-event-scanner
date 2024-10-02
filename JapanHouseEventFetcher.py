import json
import logging
import pprint
import re

import requests
from bs4 import BeautifulSoup

from SlackManager import SlackManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class JapanHouseEventFetcher:
    def __init__(self):
        self.url = "https://www.japanhouselondon.uk/whats-on/"
        self.events_data = None
        self.categories = ["posts"]
        self.event_source = "japan_house"
        self.slack_manager = SlackManager()

    def _fetch_page_content(self):
        response = requests.get(self.url)
        logger.debug(f"URL: {self.url}")
        logger.debug(f"Status code: {response.status_code}")
        logger.debug(f"Response text: {response.text}")

        if response.status_code == 200:
            logger.debug("Successfully fetched the webpage content.")
            return response.text
        else:
            logger.error(
                f"Failed to fetch the {self.event_source} webpage content. Status code: {response.status_code}"
            )
            return False

    def _parse_html_for_json(self, html_content):
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            logger.debug(f"Japan House Soup: {soup}")
            component_loader_tag = soup.find(
                "component-loader", {"name": "ArchiveWhatsOn"}
            )
            if component_loader_tag and "v-bind" in component_loader_tag.attrs:
                json_string = component_loader_tag["v-bind"]
                # Replace HTML entities with actual quotes
                json_string = json_string.replace("&quot;", '"')
                self.events_data = json.loads(json_string)
            else:
                logger.error(
                    "Component loader tag not found or does not contain 'v-bind' attribute."
                )
                self.events_data = []
        except Exception as parsing_error:
            logger.error(
                f"Error parsing HTML content for {self.event_source}: {parsing_error}"
            )
            self.events_data = []

    def _extract_events(self):
        if self.events_data is None:
            logger.error(
                "Events data is not initialized. Make sure to parse HTML content first."
            )
            return []

        try:
            extracted_events = []
            for category in self.categories:
                logger.debug(f"Extracting events for category: {self.categories}")
                logger.debug(f"Category: {category}")
                posts = self.events_data.get(category, [])
                logger.debug(f"Number of posts: {len(posts)}")
                logger.debug(f"Posts: {posts}")

                for post in posts:
                    logger.debug(f"Posts: {posts}")
                    logger.debug(f"Extracting event info for post: {post}")

                    image_url = post.get("image", {}).get("url")
                    if image_url:
                        # Remove any size suffixes from the image URL
                        image_url = re.sub(r"-\d+x\d+(?=\.\w{3,4}$)", "", image_url)

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
                    logger.debug(f"Event details: {event_dict}")
                    extracted_events.append(event_dict)
                    logger.debug(f"Extracted events: {extracted_events}")
        except Exception as extract_events_error:
            logger.error(
                f"Error extracting events from {self.event_source}: {extract_events_error}"
            )
            return []
        return extracted_events

    def combine_and_return_events(self):
        events_collected = []
        html_content = self._fetch_page_content()
        if not html_content:
            return []

        logger.debug(f"HTML content: {html_content}")
        self._parse_html_for_json(html_content)

        website_events = self._extract_events()
        logger.debug(f"Website events: {website_events}")

        combined_events = events_collected + website_events
        logger.debug(f"Combined events: {combined_events}")

        if combined_events == []:
            logger.error("Issue with Japan House event fetcher, no events found")
            self.slack_manager.send_error_message(
                "Issue with Japan House event fetcher, no events found"
            )

        return combined_events


if __name__ == "__main__":
    scraper = JapanHouseEventFetcher()
    events = scraper.combine_and_return_events()
    pprint.pprint(events)
