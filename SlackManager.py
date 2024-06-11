import logging
import os
import requests


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SlackManager:
    def __init__(self):
        self.slack_calendar_image = os.environ["SLACK_CALENDAR_IMAGE"]
        self.slack_post_api = os.environ["SLACK_POST_API"]
        self.pubilc_channel_id = os.environ["SLACK_CHANNEL_ID"]
        self.token = os.environ["SLACK_TOKEN"]
        self.developer_channel_slack_id = os.environ["DEVELOPER_CHANNEL_SLACK_ID"]

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
                f"Error generating message header: {
                    message_header_generator_error}"
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
            "japan_foundation": {
                "Event Name": event_name,
                "Date": event_date,
            },
        }

        try:
            event_details = event_details_config.get(event_source, {})

            event_details_text = "\n".join(
                f"*{key}:* {value}" for key, value in event_details.items()
            )

        except Exception as text_generator_error:
            logger.error(f"Error generating text: {text_generator_error}")
            self.send_error_message(f"Error generating text: {
                                    text_generator_error}")

        return event_details_text

    def _fetch_event_source_metadata(self, event_source):
        source = None

        if event_source == "jetaa":
            source = "JETAA Calendar"
            logo_url = self.slack_calendar_image
        if event_source == "japan_house":
            source = "Japan House"
            logo_url = "https://scontent-man2-1.xx.fbcdn.net/v/t1.18169-9/17903458_753329014834327_7911341844049710436_n.jpg?_nc_cat=101&ccb=1-7&_nc_sid=5f2048&_nc_ohc=Gp3rZOKlB4cAX9cy4ho&_nc_ht=scontent-man2-1.xx&oh=00_AfCohk6fxfk549Uo_CF1CaM3N9hl1UV5Julc_IRD4gNc_w&oe=66224822"
        if event_source == "japan_society":
            source = "Japan Society"
            logo_url = "https://scontent-man2-1.xx.fbcdn.net/v/t39.30808-6/376906703_710744664427573_2474862616829504513_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=5f2048&_nc_ohc=mbHME51bF3wAX8SEMdM&_nc_ht=scontent-man2-1.xx&oh=00_AfCWWt91kW6bHyCUbXHxTNyNn41UYZDyvloxmK3PojQo7w&oe=6600647E"
        if event_source == "embassy":
            source = "Embassy"
            logo_url = "https://www.uk.emb-japan.go.jp/JAPANUKEvent/assets/images/Logo2022/JPNUKECLogo125x72.png"
        if event_source == "japan_foundation":
            source = "Japan Foundation"
            logo_url = "https://scontent-man2-1.xx.fbcdn.net/v/t39.30808-6/326585033_897223148096653_606147465752039503_n.jpg?_nc_cat=106&ccb=1-7&_nc_sid=5f2048&_nc_ohc=bWQAsrNzoVsAX_Di8c_&_nc_ht=scontent-man2-1.xx&oh=00_AfBTHE7cQ6EVL2ARGrPWEE8zvn2-nBh_Igonom7yVID0AQ&oe=66001E2C"

        return source, logo_url

    def _message_data_generator(
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
        logger.debug("Generating message data")
        event_details_text = self._message_text_generator(
            event_source,
            event_name,
            event_location,
            event_date,
            event_time,
            event_price,
        )

        source, logo_url = self._fetch_event_source_metadata(event_source)

        try:
            data = {
                "channel": self.pubilc_channel_id,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"✨ New Event Found at {source}!",
                            "emoji": True,
                        },
                    },
                    {
                        "type": "image",
                        "title": {
                            "type": "plain_text",
                            "text": "Event Image",
                            "emoji": True,
                        },
                        "image_url": event_image_url,
                        "alt_text": "Event Image",
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": event_details_text},
                        # "accessory": {
                        #     "type": "image",
                        #     "image_url": logo_url,
                        #     "alt_text": "calendar",
                        # },
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
                f"Error generating message data: {
                    message_data_generator_error}"
            )
            self.send_error_message(
                f"Error generating message data: {
                    message_data_generator_error}"
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
        event_image_url,
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
            event_image_url,
        )

        try:
            logger.debug("Posting slack message")
            response = requests.post(
                self.slack_post_api, headers=headers, json=data)
            logger.debug("Message sent successfully!")
            logger.debug(f"Response: {response}")
        except Exception as post_error:
            logger.error(f"Error posting message to slack {post_error}")
            self.send_error_message(
                f"Error posting message to slack {post_error}")
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
            event_image_url = event["event_image_url"]

            self._send_to_slack(
                event_source,
                event_name,
                event_location,
                event_date,
                event_time,
                event_price,
                event_url,
                event_image_url,
            )

    def send_to_dev(self):
        logger.debug("Sending to slack")
        headers = self._message_header_generator()
        data = {
            "channel": self.developer_channel_slack_id,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "The event scanner function has successfully run.",
                        "emoji": True,
                    },
                }
            ],
        }
        try:
            logger.debug("Posting slack message")
            response = requests.post(
                self.slack_post_api, headers=headers, json=data)
            logger.debug("Message sent successfully!")
            logger.debug(f"Response: {response}")
        except Exception as post_error:
            logger.error(
                f"Error posting successful run message to slack {post_error}")
            return False

        return True

    def send_error_message(self, message):
        logger.debug("Sending error message to slack")
        headers = self._message_header_generator()

        data = {
            "channel": self.developer_channel_slack_id,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": message,
                        "emoji": True,
                    },
                }
            ],
        }
        try:
            logger.debug("Posting slack message")
            response = requests.post(
                self.slack_post_api, headers=headers, json=data)
            logger.debug("Message sent successfully!")
            logger.debug(f"Response: {response}")
        except Exception as post_error:
            logger.error(f"Error posting message to slack {post_error}")
            return False

        return True
