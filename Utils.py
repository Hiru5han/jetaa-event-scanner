import logging
from SlackManager import SlackManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Utils:
    def __init__(self):
        self.slack_manager = SlackManager()

    def error_handler(self, message):
        logger.error(message)
        self.slack_manager.send_error_message(message)
        return False