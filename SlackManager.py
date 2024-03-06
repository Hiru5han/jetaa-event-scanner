import logging
import os
import requests

from CSVComparator import CSVComparator

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

    def _message_text_generator(self, event_name, event_date, event_time, event_price):
        logger.debug("Generating message text")

        try:
            event_details_text = (
                f"*Event Name:* {event_name}\n"
                f"*Date:* {event_date}\n"
                f"*Time:* {event_time}\n"
                f"*Price:* £{event_price}\n"
            )
        except Exception as text_generator_error:
            logger.error(f"Error generating text: {text_generator_error}")

        return event_details_text

    def _message_data_generator(
        self, event_name, event_date, event_time, event_price, event_url
    ):
        logger.debug("Generating message data")
        event_details_text = self._message_text_generator(
            event_name, event_date, event_time, event_price
        )
        try:
            data = {
                "channel": self.channel_id,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "✨ New Event Found on Calendar!",
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
                    {"type": "divider"},
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "View on JETAA Calendar",
                                    "emoji": True,
                                },
                                "value": "click_me_123",
                                "url": event_url,
                                "action_id": "actionId-0",
                            }
                        ],
                    },
                ],
            }

            logger.debug("Message data generated")
        except Exception as message_data_generator_error:
            logger.error(
                f"Error generating message data: {message_data_generator_error}"
            )

        return data

    def _send_to_slack(
        self, event_name, event_date, event_time, event_price, event_url
    ):
        logger.debug("Sending to slack")
        headers = self._message_header_generator()
        data = self._message_data_generator(
            event_name, event_date, event_time, event_price, event_url
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

    def slack_notifier(self, s3_manager, events_collected, bucket_name, prefix):
        previous_csv = s3_manager.get_latest_csv_file_content(bucket_name, prefix)
        comparator = CSVComparator(events_collected, previous_csv)
        differences = comparator.compare()

        logger.debug("New events:")

        for diff in differences["in_first_not_in_second"]:
            logger.debug(diff)
            event_name, event_date, event_time, event_price, event_url = eval(diff)
            self._send_to_slack(
                event_name, event_date, event_time, event_price, event_url
            )

        logger.debug("Events that were removed:")
        for diff in differences["in_second_not_in_first"]:
            logger.debug(diff)

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
                        "text": "Just scanned the calendar, I've put the CSV in S3.",
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
