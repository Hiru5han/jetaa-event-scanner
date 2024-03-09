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
            raise Exception(f"Failed to fetch the webpage content. Status code: {response.status_code}")

    def parse_html_for_json(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        component_loader_tag = soup.find('component-loader', {'name': 'ArchiveWhatsOn'})
        json_string = component_loader_tag['v-bind']
        self.events_data = json.loads(json_string)

    def extract_events(self):
        if self.events_data is None:
            raise ValueError("Events data is not initialized. Make sure to parse HTML content first.")
        extracted_events = []
        for category in self.categories:
            posts = self.events_data.get(category, [])
            for post in posts:
                event = (
                    self.event_source,
                    post.get("title"),
                    post.get("event_location"),
                    post.get("date_range"),
                    "Not available",
                    "Not available",
                    post.get("url"),
                )
                extracted_events.append(event)
        return extracted_events

    def combine_and_return_events(self, events_collected):
        # Ensure HTML content is fetched and parsed before extracting events
        html_content = self.fetch_page_content()
        self.parse_html_for_json(html_content)
        website_events = self.extract_events()
        combined_events = events_collected + website_events
        return combined_events
