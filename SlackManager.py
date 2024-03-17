import logging
import os
import requests


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SlackManager:
    def __init__(self):
        self.slack_calendar_image = os.environ["SLACK_CALENDAR_IMAGE"]
        self.slack_post_api = os.environ["SLACK_POST_API"]
        self.channel_id = os.environ["SLACK_CHANNEL_ID"]
        self.token = os.environ["SLACK_TOKEN"]

    def _message_header_generator(self):
        logger.debug("Generating message header")

        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
            logger.debug("Message header generated")
        except Exception as message_header_generator_error:
            logger.error(
                f"Error generating message header: {message_header_generator_error}"
            )

        return headers

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
        logger.debug("Generating message text")

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
        }

        try:
            event_details = event_details_config.get(event_source, {})

            event_details_text = "\n".join(
                f"*{key}:* {value}" for key, value in event_details.items()
            )

        except Exception as text_generator_error:
            logger.error(f"Error generating text: {text_generator_error}")

        return event_details_text

    def _header_generator(self, event_source):
        source = None

        if event_source == "jetaa":
            source = "JETAA Calendar"
        if event_source == "japan_house":
            source = "Japan House website"
        if event_source == "japan_society":
            source = "Japan Society website"
        if event_source == "embassy":
            source = "Embassy website"

        return source

    def _message_data_generator(
        self,
        event_source,
        event_name,
        event_location,
        event_date,
        event_time,
        event_price,
        event_url,
    ):
        logger.debug("Generating message data")
        event_details_text = self._message_text_generator(
            event_source,
            event_name,
            event_location,
            event_date,
            event_time,
            event_price,
        )

        source = self._header_generator(event_source)

        try:
            data = {
                "channel": self.channel_id,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"✨ New Event Found on {source}!",
                            "emoji": True,
                        },
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": event_details_text},
                        "accessory": {
                            "type": "image",
                            "image_url": self.slack_calendar_image,
                            "alt_text": "calendar",
                        },
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "View online",
                                    "emoji": True,
                                },
                                "value": "click_me_123",
                                "url": event_url,
                                "action_id": "actionId-0",
                            }
                        ],
                    },
                    {"type": "divider"},
                ],
            }

            logger.debug("Message data generated")
        except Exception as message_data_generator_error:
            logger.error(
                f"Error generating message data: {message_data_generator_error}"
            )

        return data

    def _send_to_slack(
        self,
        event_source,
        event_name,
        event_location,
        event_date,
        event_time,
        event_price,
        event_url,
    ):
        logger.debug("Sending to slack")
        headers = self._message_header_generator()
        data = self._message_data_generator(
            event_source,
            event_name,
            event_location,
            event_date,
            event_time,
            event_price,
            event_url,
        )

        try:
            logger.debug("Posting slack message")
            response = requests.post(self.slack_post_api, headers=headers, json=data)
            logger.debug("Message sent successfully!")
            logger.debug(f"Response: {response}")
        except Exception as post_error:
            logger.error(f"Error posting message to slack {post_error}")
            return False

        return True

    def slack_notifier(self, new_events):
        logger.debug("New events:")

        for event in new_events:
            logger.debug(event)
            event_source = event["event_source"]
            event_name = event["event_name"]
            event_location = event["event_location"]
            event_date = event["event_date"]
            event_time = event["event_time"]
            event_price = event["event_price"]
            event_url = event["event_url"]

            self._send_to_slack(
                event_source,
                event_name,
                event_location,
                event_date,
                event_time,
                event_price,
                event_url,
            )

    def send_to_hiru(self):
        logger.debug("Sending to slack")
        headers = self._message_header_generator()
        data = {
            "channel": self.channel_id,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "The event scanner function has successfully run. CSV is updated in S3.",
                        "emoji": True,
                    },
                }
            ],
        }
        try:
            logger.debug("Posting slack message")
            response = requests.post(self.slack_post_api, headers=headers, json=data)
            logger.debug("Message sent successfully!")
            logger.debug(f"Response: {response}")
        except Exception as post_error:
            logger.error(f"Error posting message to slack {post_error}")
            return False

        return True
