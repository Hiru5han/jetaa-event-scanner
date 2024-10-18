import logging
import pprint
import re

import requests
from bs4 import BeautifulSoup

from utils.SlackManager import SlackManager

logger = logging.getLogger(__name__)


class JapanFoundationEventFetcher:
    def __init__(self):
        self.base_url = "https://www.jpf.org.uk"
        self.whatson_url = f"{self.base_url}/whatson.php"
        self.slack_manager = SlackManager()

    def _fetch_webpage_content(self):
        response = requests.get(self.whatson_url)
        response.raise_for_status()  # Ensure we raise an error for bad responses
        return response.text

    @staticmethod
    def _extract_date_info(text):
        pattern = r"\d{1,2}\s+[A-Za-z]+\s+\d{4}"
        dates = re.findall(pattern, text)
        return " - ".join(dates) if dates else "Date Info Not Found"

    def combine_and_return_events(self):
        webpage_content = self._fetch_webpage_content()
        soup = BeautifulSoup(webpage_content, "html.parser")
        events = []

        try:
            for event_block in soup.find_all("div", style="border: solid 1px #666666;"):
                title_tag = event_block.find("font", color="#FFFFFF")
                title = (
                    title_tag.get_text(strip=True) if title_tag else "Title Not Found"
                )

                date_info_tag = event_block.find("td", width="100%")
                date_info = (
                    self._extract_date_info(date_info_tag.get_text(strip=True))
                    if date_info_tag
                    else "Date Info Not Found"
                )

                venue = "Venue Not Found"
                for td in event_block.find_all("td"):
                    if "Venue:" in td.get_text():
                        venue = td.find_next_sibling("td").get_text(strip=True)
                        break

                # Find the correct image URL by looking for images with alt=""
                image_url = "Image Not Found"
                for img_tag in event_block.find_all("img"):
                    if "alt" in img_tag.attrs and img_tag["alt"] == "":
                        if img_tag["src"].startswith("http"):
                            image_url = img_tag["src"]
                        else:
                            image_url = (
                                f"{self.base_url}/{img_tag['src'].lstrip('../')}"
                            )
                        break

                anchor_tag = event_block.find_previous("a", id=True)
                event_id = (
                    anchor_tag["id"]
                    if anchor_tag and "id" in anchor_tag.attrs
                    else None
                )

                event_url = (
                    f"{self.whatson_url}#{event_id}"
                    if event_id
                    else "URL Not Available"
                )

                output_item = {
                    "event_source": "japan_foundation",
                    "event_name": title,
                    "event_location": venue,
                    "event_date": date_info,
                    "event_time": "Not available",
                    "event_price": "Not available",
                    "event_description": "Not available",
                    "event_image_url": image_url,
                    "event_url": event_url,
                }

                events.append(output_item)
        except Exception as page_check_error:
            logger.debug(f"Error in Japan Foundation event fetcher: {page_check_error}")
            return []

        if not events:
            self.slack_manager.send_error_message(
                "Issue with Japan Foundation event fetcher, no events found"
            )
        return events


if __name__ == "__main__":
    scraper = JapanFoundationEventFetcher()
    events = scraper.combine_and_return_events()
    pprint.pprint(events)
