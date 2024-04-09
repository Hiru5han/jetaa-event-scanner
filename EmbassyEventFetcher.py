import logging
import requests
from bs4 import BeautifulSoup

from SlackManager import SlackManager
from Utils import Utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class EmbassyEventFetcher:
    def __init__(self, year):
        self.base_url = "https://www.uk.emb-japan.go.jp/JAPANUKEvent/event/"
        self.year = year
        self.short_year = str(year)[2:]
        self.slack_manager = SlackManager()
        self.utils = Utils()

    def combine_and_return_events(self):
        events = []
        for month in range(1, 13):
            logger.debug(f"Fetching events for {month}/{self.year}")
            month_str = str(month).zfill(2)
            url = f"{self.base_url}eve-list{self.short_year}-{month_str}.html"
            logger.debug(f"URL: {url}")
            headers = {"User-Agent": "Mozilla/5.0"}
            try:
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    response.encoding = (
                        "utf-8"
                        if response.encoding is None
                        or response.encoding == "ISO-8859-1"
                        else response.encoding
                    )
                    soup = BeautifulSoup(response.text, "html.parser")
                    event_blocks = soup.findAll("div", class_="card-wrapper")
                    for block in event_blocks:
                        event_info = self._extract_event_info(block)
                        events.append(event_info)
                else:
                    logger.error(
                        f"Failed to retrieve the webpage for {month_str}/{self.year}. Status code: {response.status_code}"
                    )
            except Exception as e:
                logger.error(
                    f"An error occurred while fetching the events for {month_str}/{self.year}: {e}"
                )
                return []
            
        if events == []:
            logger.error("Issue with Japan Society event fetcher, no events found")
            self.slack_manager.send_error_message("Issue with Japan Society event fetcher, no events found")

        return events

    def _extract_event_info(self, block):
        try:
            event_url_suffix = block.find("a")["href"]
            event_url = self.base_url + event_url_suffix
            event_name = block.find("h4", class_="card-title").text.strip()
            date_location_str = (
                block.find("p", class_="mbr-text").text.strip().split("\r\n")
            )
            event_date = date_location_str[0].strip()
            event_location = (
                date_location_str[1].strip()
                if len(date_location_str) > 1
                else "Not Available"
            )
            event_time = "Not Available"
            event_price = "Not Available"
        except Exception as extraction_error:
            logger.error(f"Error extracting event info from block: {extraction_error}")
            return False

        event_details = {
            "event_source": "embassy",
            "event_location": event_location,
            "event_time": event_time,
            "event_price": event_price,
            "event_url": event_url,
            "event_date": event_date,
            "event_name": event_name,
        }
        logger.debug(f"Event details: {event_details}")

        return event_details
