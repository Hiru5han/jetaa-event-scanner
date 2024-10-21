import os
import pytest
from unittest.mock import patch


# Shared fixture to mock all necessary environment variables
@pytest.fixture(autouse=True)
def mock_env_vars():
    env_vars = {
        "SLACK_CALENDAR_IMAGE": "https://cdn.iconscout.com/icon/free/png-512/free-calendar-766-267585.png?f=webp&w=512",
        "SLACK_POST_API": "https://mock-slack-api.com/api/chat.postMessage",
        "SLACK_CHANNEL_ID": "C06UL744QER",
        "SLACK_TOKEN": "mock-token",  # Insert a mock token
        "DEVELOPER_CHANNEL_SLACK_ID": "C06UL744QER",
    }

    # Patch os.environ with the required environment variables
    with patch.dict(os.environ, env_vars):
        yield
