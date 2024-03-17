import json
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class JapanHouseEventFetcher:
    def __init__(self):
        self.url = "https://www.japanhouselondon.uk/whats-on/"
        self.events_data = None
        self.categories = ["posts"]
        self.event_source = "japan_house"

    def fetch_page_content(self):
        response = requests.get(self.url)
        logger.debug(f"URL: {self.url}")
        logger.debug(f"Status code: {response.status_code}")
        logger.debug(f"Response text: {response.text}")
        if response.status_code == 200:
            logger.debug("Successfully fetched the webpage content.")
            return response.text
        else:
            raise Exception(
                f"Failed to fetch the webpage content. Status code: {response.status_code}"
            )

    def parse_html_for_json(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        component_loader_tag = soup.find("component-loader", {"name": "ArchiveWhatsOn"})
        json_string = component_loader_tag["v-bind"]
        self.events_data = json.loads(json_string)

    def extract_events(self):
        if self.events_data is None:
            raise ValueError(
                "Events data is not initialized. Make sure to parse HTML content first."
            )
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
                event_dict = {
                    "event_source": self.event_source,
                    "event_name": post.get("title"),
                    "event_location": post.get("event_location"),
                    "event_date": post.get("date_range"),
                    "event_time": "Not available",
                    "event_price": "Not available",
                    "event_url": post.get("url"),
                }
                logger.debug(f"Event details: {event_dict}")
                extracted_events.append(event_dict)
                logger.debug(f"Extracted events: {extracted_events}")

        return extracted_events

    def combine_and_return_events(self):
        events_collected = []
        html_content = self.fetch_page_content()
        logger.debug(f"HTML content: {html_content}")
        self.parse_html_for_json(html_content)
        website_events = self.extract_events()
        logger.debug(f"Website events: {website_events}")
        combined_events = events_collected + website_events
        logger.debug(f"Combined events: {combined_events}")
        return combined_events
