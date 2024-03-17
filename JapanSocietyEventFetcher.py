import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class JapanSocietyEventFetcher:
    def __init__(self):
        self.base_url = "https://www.japansociety.org.uk/events"
        self.session = requests.Session()

    def scrape_events_from_url(self, url, existing_events):
        response = self.session.get(url)
        logger.debug(f"URL: {url}")
        logger.debug(f"Response text: {response.text}")
        response.raise_for_status()
        logger.debug("Successfully fetched the webpage content.")

        soup = BeautifulSoup(response.text, "html.parser")

        event_cards = soup.find_all("div", class_="card")
        logger.debug(f"Number of event cards: {len(event_cards)}")
        logger.debug(f"Event cards: {event_cards}")

        for card in event_cards:
            event_details = self.extract_event_details(card)
            logger.debug(f"Event details: {event_details}")
            if event_details:
                existing_events.append(event_details)
                logger.debug(f"Existing events: {existing_events}")

    def extract_event_details(self, card):
        event_details = {
            "event_source": "japan_society",
            "event_location": "Not Available",
            "event_time": "Not Available",
            "event_price": "Not Available",
            "event_url": "URL not found",
            "event_date": "Date not found",
            "event_name": "Title not found",
        }

        url_container = card.find("div", class_="border-top")
        event_link = url_container.find("a", href=True) if url_container else None
        event_details["event_url"] = (
            event_link["href"] if event_link else event_details["event_url"]
        )

        event_date_span = card.find("span", class_="js-event-date")
        event_details["event_date"] = (
            event_date_span.text.strip()
            if event_date_span
            else event_details["event_date"]
        )

        event_name_span = card.find("span", class_="card-text")
        event_details["event_name"] = (
            event_name_span.text.strip()
            if event_name_span
            else event_details["event_name"]
        )

        if (
            event_details["event_name"] == "Title not found"
            and event_details["event_date"] == "Date not found"
            and event_details["event_url"] == "URL not found"
        ):
            return None
        else:
            return event_details

    def get_pagination_urls(self, soup):
        pagination_links = soup.find_all("a", class_="page-link")
        page_urls = [
            link.get("href")
            for link in pagination_links
            if link.get("href") and link.get("href") != "#"
        ]
        return page_urls

    def combine_and_return_events(self):
        existing_events = []
        self.scrape_events_from_url(self.base_url, existing_events)
        logger.debug(f"Existing events: {existing_events}")

        initial_response = self.session.get(self.base_url)
        initial_response.raise_for_status()
        initial_soup = BeautifulSoup(initial_response.text, "html.parser")
        page_urls = self.get_pagination_urls(initial_soup)

        unique_page_urls = sorted(set(page_urls), key=page_urls.index)
        for page_url in unique_page_urls:
            logger.debug(f"Page URL: {page_url}")
            if not page_url.startswith("http"):
                page_url = self.base_url + page_url
            self.scrape_events_from_url(page_url, existing_events)

        return existing_events
