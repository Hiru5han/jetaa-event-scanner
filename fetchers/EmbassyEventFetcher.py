import logging
from random import choice
from time import sleep

import requests
from bs4 import BeautifulSoup

# from utils.SlackManager import SlackManager

logger = logging.getLogger(__name__)


class EmbassyEventFetcher:
    def __init__(self, year):
        self.base_url = "https://www.uk.emb-japan.go.jp/JAPANUKEvent/event/"
        self.year = year
        self.short_year = str(year)[2:]
        # self.slack_manager = SlackManager()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
        ]
        self.session = requests.Session()

    def combine_and_return_events(self):
        events = []
        for month in range(1, 13):
            logger.debug(f"Fetching events for {month}/{self.year}")
            month_str = str(month).zfill(2)
            url = f"{self.base_url}eve-list{self.short_year}-{month_str}.html"
            logger.debug(f"URL: {url}")
            headers = {
                "User-Agent": choice(self.user_agents),
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.uk.emb-japan.go.jp/JAPANUKEvent/index.html",  # More appropriate referrer
                "Connection": "keep-alive",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Cache-Control": "max-age=0",
            }
            proxies = {
                "http": "http://4.158.175.186:8080",  # Replace with actual proxy details
                "https": "http://85.210.203.188:8080",  # Replace with actual proxy details
            }
            cookies = {
                "CookieName1": "CookieValue1",
                "CookieName2": "CookieValue2",
            }

            try:
                response = self.session.get(
                    url, headers=headers, proxies=proxies, cookies=cookies
                )
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
                        if event_info:
                            events.append(event_info)
                else:
                    logger.error(
                        f"Failed to retrieve the webpage for {month_str}/{self.year}. Status code: {response.status_code}"
                    )
            except requests.exceptions.RequestException as e:
                logger.error(
                    f"An error occurred while fetching the events for {month_str}/{self.year}: {e}"
                )
                continue
            sleep(choice(range(2, 6)))  # Random sleep between 1 to 3 seconds

        # if not events:
        #     logger.error("Issue with Embassy event fetcher, no events found")
        #     self.slack_manager.send_error_message(
        #         "Issue with Embassy event fetcher, no events found"
        #     )

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


if __name__ == "__main__":
    embassyeventfetcher = EmbassyEventFetcher(2024)
    print(embassyeventfetcher.combine_and_return_events())
