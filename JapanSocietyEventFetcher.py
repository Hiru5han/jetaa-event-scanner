import json
import logging

import requests
from bs4 import BeautifulSoup

from SlackManager import SlackManager

logger = logging.getLogger(__name__)


class JapanSocietyEventFetcher:
    def __init__(self):
        self.base_url = "https://www.japansociety.org.uk/events"
        self.session = requests.Session()
        self.slack_manager = SlackManager()

    def _scrape_events_from_url(self, url, existing_events):
        try:
            response = self.session.get(url)
            response.raise_for_status()
            logger.debug(f"Successfully fetched the webpage content from URL: {url}")

            soup = BeautifulSoup(response.text, "html.parser")

            event_cards = soup.find_all("div", class_="card")
            logger.debug(f"Number of event cards: {len(event_cards)}")

            for card in event_cards:
                event_details = self._extract_event_details(card)
                if event_details:
                    existing_events.append(event_details)
                    logger.debug(f"Event details added: {event_details}")
        except Exception as scrape_error:
            logger.error(f"Error fetching events from URL: {url}")
            logger.error(f"Error: {scrape_error}")

    def _extract_event_details(self, card):
        event_details = {
            "event_source": "japan_society",
            "event_location": "Not Available",
            "event_time": "Not Available",
            "event_price": "Not Available",
            "event_url": "URL not found",
            "event_date": "Date not found",
            "event_name": "Title not found",
            "event_image_url": "Image URL not found",  # New key for image URL
        }

        base_url = "https://www.japansociety.org.uk/"

        # Extract event URL
        url_container = card.find("div", class_="js-news-image mb-3")
        if url_container:
            event_link = url_container.find("a", href=True)
            if event_link:
                event_details["event_url"] = event_link["href"]

        # Extract event date
        event_date_span = card.find("span", class_="js-event-date")
        if event_date_span:
            event_details["event_date"] = event_date_span.text.strip()

        # Extract event name
        event_name_span = card.find("span", class_="card-text")
        if event_name_span:
            event_details["event_name"] = event_name_span.text.strip()

        # Extract event description
        event_description = card.find("div", class_="js-listing-intro")
        if event_description:
            event_details["event_description"] = event_description.text.strip()

        # # Extract event image["event_image_url"] = base_url + img_tag["src"]

        # Fetch additional details from the event URL
        if event_details["event_url"] != "URL not found":
            event_page = requests.get(event_details["event_url"])
            if event_page.status_code == 200:
                event_soup = BeautifulSoup(event_page.content, "html.parser")
                # Extract event image URL matching the event name
                img_tag = event_soup.find("img", alt=event_details["event_name"])
                if img_tag and "src" in img_tag.attrs:
                    event_details["event_image_url"] = base_url + img_tag["src"]

        # Check if essential details were found
        if (
            event_details["event_name"] == "Title not found"
            and event_details["event_date"] == "Date not found"
            and event_details["event_url"] == "URL not found"
        ):
            return None
        else:
            return event_details

    def _get_pagination_urls(self, soup):
        pagination_links = soup.find_all("a", class_="page-link")
        page_urls = [
            link.get("href")
            for link in pagination_links
            if link.get("href") and link.get("href") != "#"
        ]
        return page_urls

    def combine_and_return_events(self):
        existing_events = []
        self._scrape_events_from_url(self.base_url, existing_events)

        initial_response = self.session.get(self.base_url)
        initial_response.raise_for_status()
        initial_soup = BeautifulSoup(initial_response.text, "html.parser")
        page_urls = self._get_pagination_urls(initial_soup)

        unique_page_urls = sorted(set(page_urls), key=page_urls.index)
        for page_url in unique_page_urls:
            if not page_url.startswith("http"):
                page_url = self.base_url + page_url
            self._scrape_events_from_url(page_url, existing_events)

        if existing_events == []:
            self.slack_manager.send_error_message(
                "Issue with Japan Society event fetcher, no events found"
            )
        logger.error(f"Existing_events: {existing_events}")
        return existing_events


if __name__ == "__main__":
    japansocietyeventfetcher = JapanSocietyEventFetcher()
    logger.info(
        json.dumps(japansocietyeventfetcher.combine_and_return_events(), indent=4)
    )
