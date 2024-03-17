import json
import requests
from bs4 import BeautifulSoup


class JapanHouseEventFetcher:
    def __init__(self):
        self.url = "https://www.japanhouselondon.uk/whats-on/"
        self.events_data = None
        self.categories = ["posts"]
        self.event_source = "japan_house"

    def fetch_page_content(self):
        response = requests.get(self.url)
        if response.status_code == 200:
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
            posts = self.events_data.get(category, [])
            for post in posts:
                event_dict = {
                    "event_source": self.event_source,
                    "event_name": post.get("title"),
                    "event_location": post.get("event_location"),
                    "event_date": post.get("date_range"),
                    "event_time": "Not available",
                    "event_price": "Not available",
                    "event_url": post.get("url"),
                }
                extracted_events.append(event_dict)

        return extracted_events

    def combine_and_return_events(self):
        events_collected = []
        html_content = self.fetch_page_content()
        self.parse_html_for_json(html_content)
        website_events = self.extract_events()
        combined_events = events_collected + website_events
        return combined_events
