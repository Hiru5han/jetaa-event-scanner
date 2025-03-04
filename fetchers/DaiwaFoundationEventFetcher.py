import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class DaiwaFoundationEventFetcher:
    def __init__(self):
        self.base_url = "https://dajf.org.uk/events"
        self.event_source = "daiwa_foundation"
        self.events_data = []

    def _fetch_page_content(self, url):
        logger.info(f"Attempting to fetch page content from {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            logger.info(
                f"Successfully fetched content from {url} with status code {response.status_code}"
            )
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching page content from {url}: {e}")
            return None

    def _extract_event_links(self, html_content):
        logger.info("Extracting event links from the main page...")
        soup = BeautifulSoup(html_content, "html.parser")
        event_links = []
        # Find all event links on the main page
        for event in soup.select("article.event_listing h2.listing_title a"):
            event_links.append(event["href"])
        logger.info(f"Found {len(event_links)} event links.")
        return event_links

    def _extract_event_details(self, event_page_content, event_url):
        logger.info(f"Extracting details from event page: {event_url}")
        soup = BeautifulSoup(event_page_content, "html.parser")
        try:
            # Extract event name
            event_name_tag = soup.find("h1", id="no_rule")
            event_name = (
                event_name_tag.get_text(strip=True)
                if event_name_tag
                else "No title available"
            )

            # Extract event date and time
            event_date_tag = soup.find("p", id="head_date")
            event_date_time = (
                event_date_tag.get_text(strip=True)
                if event_date_tag
                else "No date available"
            )

            # Extract event location
            event_location_tag = soup.select_one("header p.head_txt")
            event_location = (
                event_location_tag.get_text(strip=True)
                if event_location_tag
                else "No location available"
            )

            # Extract event image URL
            event_image_tag = soup.find("img")
            event_image_url = (
                event_image_tag["src"] if event_image_tag else "No image available"
            )

            # You may also want to split the date and time if needed
            event_date, event_time = (
                event_date_time.split(" ", 1)
                if " " in event_date_time
                else (event_date_time, "Not available")
            )

            event_details = {
                "event_source": self.event_source,
                "event_name": event_name,
                "event_location": event_location,
                "event_date": event_date,
                "event_time": event_time,
                "event_price": "Not available",  # Placeholder if price is not found
                "event_url": event_url,
                "event_image_url": event_image_url,
            }
            logger.info(f"Successfully extracted event: {event_name}")
            return event_details
        except AttributeError as e:
            logger.error(f"Error extracting event details from {event_url}: {e}")
            return None

    def combine_and_return_events(self):
        logger.info(f"Starting event scraping for {self.event_source}...")
        html_content = self._fetch_page_content(self.base_url)
        if not html_content:
            logger.error("No HTML content to parse.")
            return []

        event_links = self._extract_event_links(html_content)
        if not event_links:
            logger.warning("No event links found on the main page.")

        for event_link in event_links:
            logger.info(f"Fetching event details from {event_link}")
            event_page_content = self._fetch_page_content(event_link)
            if event_page_content:
                event_details = self._extract_event_details(
                    event_page_content, event_link
                )
                if event_details:
                    self.events_data.append(event_details)

        if not self.events_data:
            logger.error(f"No events found for {self.event_source}.")
            return []

        logger.info(f"Scraping complete. Found {len(self.events_data)} events.")
        return self.events_data


# Example usage:
if __name__ == "__main__":
    scraper = DaiwaFoundationEventFetcher()
    events = scraper.combine_and_return_events()
    for event in events:
        print(event)
