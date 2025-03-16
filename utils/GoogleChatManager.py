import logging
import os
import requests
from urllib.parse import quote

logger = logging.getLogger(__name__)


class GoogleChatManager:
    def __init__(self):
        self.webhook_url = os.environ["GOOGLE_CHAT_WEBHOOK_URL"]

    def _price_formatter(self, event_price):
        event_price_str = str(event_price)

        if event_price == 0 or event_price_str == "0":
            return "Free"
        elif "£" not in event_price_str:
            return "£" + event_price_str
        return event_price_str

    def _message_text_generator(
        self,
        event_source,
        event_name,
        event_location,
        event_date,
        event_time,
        event_price,
    ):
        formatted_price = self._price_formatter(event_price)

        event_details_config = {
            "jetaa": {
                "Event Name": event_name,
                "Date": event_date,
                "Time": event_time,
                "Price": formatted_price,
            },
            "japan_house": {
                "Event Name": event_name,
                "Location": event_location,
                "Date": event_date,
            },
            "japan_society": {
                "Event Name": event_name,
                "Date": event_date,
            },
            "embassy": {
                "Event Name": event_name,
                "Date": event_date,
                "Location": event_location,
            },
            "japan_foundation": {
                "Event Name": event_name,
                "Date": event_date,
            },
            "daiwa_foundation": {
                "Event Name": event_name,
                "Date": event_date,
                "Time": event_time,
                "Location": event_location,
            },
        }

        event_details = event_details_config.get(event_source, {})

        event_details_text = "\n".join(
            f"**{key}:** {value}" for key, value in event_details.items()
        )

        return event_details_text

    def _fetch_event_source_metadata(self, event_source):
        source = None
        logo_url = ""

        if event_source == "jetaa":
            source = "JETAA Calendar"
            logo_url = "https://cdn.iconscout.com/icon/free/png-512/free-calendar-766-267585.png?f=webp&w=512"
        elif event_source == "japan_house":
            source = "Japan House"
            logo_url = (
                "https://event-source-logos.s3.eu-west-2.amazonaws.com/japan_house.png"
            )
        elif event_source == "japan_society":
            source = "Japan Society"
            logo_url = "https://event-source-logos.s3.eu-west-2.amazonaws.com/japan_society.jpeg"
        elif event_source == "embassy":
            source = "Embassy"
            logo_url = "https://event-source-logos.s3.eu-west-2.amazonaws.com/japan_embassy.png"
        elif event_source == "japan_foundation":
            source = "Japan Foundation"
            logo_url = "https://event-source-logos.s3.eu-west-2.amazonaws.com/japan_foundation.jpeg"
        elif event_source == "daiwa_foundation":
            source = "Daiwa Foundation"
            logo_url = "https://event-source-logos.s3.eu-west-2.amazonaws.com/daiwa_foundation_logo.png"

        return source, logo_url

    def send_event_message(
        self,
        event_source,
        event_name,
        event_location,
        event_date,
        event_time,
        event_price,
        event_url,
        event_image_url,
    ):

        _, logo_url = self._fetch_event_source_metadata(event_source)

        message_card = {
            "cardsV2": [
                {
                    "cardId": event_name,
                    "card": {
                        "header": {
                            "title": f"✨ New Event Found!",
                            "subtitle": event_name,
                            "imageUrl": logo_url,
                            "imageType": "SQUARE",
                        },
                        "sections": [
                            {
                                "widgets": [
                                    {
                                        "image": {
                                            "imageUrl": event_image_url,
                                            "altText": "Event Image",
                                        }
                                    },
                                    {
                                        "decoratedText": {
                                            "startIcon": {"knownIcon": "INVITE"},
                                            "text": event_date,
                                        }
                                    },
                                    {
                                        "decoratedText": {
                                            "startIcon": {"knownIcon": "CLOCK"},
                                            "text": event_time,
                                        }
                                    },
                                    {
                                        "decoratedText": {
                                            "startIcon": {"knownIcon": "MAP_PIN"},
                                            "text": event_location,
                                        }
                                    },
                                    {
                                        "decoratedText": {
                                            "startIcon": {"knownIcon": "DOLLAR"},
                                            "text": event_price,
                                        }
                                    },
                                    {
                                        "buttonList": {
                                            "buttons": [
                                                {
                                                    "text": "🌐 View Event",
                                                    "onClick": {
                                                        "openLink": {"url": event_url}
                                                    },
                                                }
                                            ]
                                        }
                                    },
                                ]
                            }
                        ],
                    },
                }
            ]
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=message_card,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            logger.debug("Message sent successfully to Google Chat")
        except requests.RequestException as e:
            logger.error(f"Failed to send message to Google Chat: {e}")

    def notify_events(self, events):
        for event in events:
            self.send_event_message(
                event["event_source"],
                event["event_name"],
                event["event_location"],
                event["event_date"],
                event["event_time"],
                event["event_price"],
                event["event_url"],
                event["event_image_url"],
            )
