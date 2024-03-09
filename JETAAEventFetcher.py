import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class JETAAEventFetcher:
    def __init__(self, year, month):
        self.BASE_URL = "https://www.jetaa.org.uk/"
        self.EVENTS_PREFIX = "events/events-calendar/"
        self.year = year
        self.month = month
        self.url = f"{self.BASE_URL}{self.EVENTS_PREFIX}{self.year}/{self.month}/"
        self.events = []
        self.event_source = "jetaa"

    def fetch_events(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()  # Raises HTTPError for bad responses
            self.parse_events(response.text)
        except requests.HTTPError as e:
            logger.debug(f"Failed to retrieve webpage: {e}")

    def parse_events(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        current_month_year = soup.find("h2", class_="currentmonth").text.strip()
        logger.debug(f"Processing events for: {current_month_year}")
        events = soup.find_all("td", class_="containsevent")

        for event in events:
            self.process_event(event, current_month_year)

    def process_event(self, event, current_month_year):
        day = event.find("h4").text.strip() if event.find("h4") else "Unknown day"
        event_details = event.find("div", class_="popup")

        if event_details:
            event_name = event_details.find("h3").text.strip()
            event_date = f"{day} {current_month_year}"
            event_time_price = event_details.find("p").text.strip()
            # Check if the string contains '//'
            if "//" in event_time_price:
                event_time, event_price = event_time_price.split("//", 1)
                event_time = event_time.strip()
                event_price = event_price.strip().strip("<strong>").strip("</strong>")
            else:
                event_time = "Unknown time"
                event_price = "Unknown price"

            # Fetch the event URL
            event_url_element = event.find("a")
            if event_url_element and "href" in event_url_element.attrs:
                event_url = event_url_element["href"]
                # If necessary, adjust the URL to be absolute if it's relative
                if not event_url.startswith("http"):
                    event_url = self.BASE_URL + event_url.lstrip("/")
            else:
                event_url = "URL not found"

            event_location = "Not Available"

            logger.debug(f"Event host: {self.event_source}")
            logger.debug(f"Event name: {event_name}")
            logger.debug(f"Event location: {event_location}")
            logger.debug(f"Event date: {event_date}")
            logger.debug(f"Event time: {event_time}")
            logger.debug(f"Event price: {event_price}")
            logger.debug(f"Event URL: {event_url}")

            self.events.append(
                (self.event_source, event_name, event_location, event_date, event_time, event_price, event_url)
            )
