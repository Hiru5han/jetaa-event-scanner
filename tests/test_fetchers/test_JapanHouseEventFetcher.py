from unittest.mock import patch

import pytest
import requests

from fetchers.JapanHouseEventFetcher import JapanHouseEventFetcher

# Mock response for successful event fetch
mock_html_content = """
<archive-whats-on v-bind='{"posts": [{"title": "Japan House Event 1", "event_location": "London", "date_range": "2024-10-20", "url": "https://japanhouselondon.uk/event-1", "image": {"url": "https://japanhouselondon.uk/image-100x100.jpg"}}]}'></archive-whats-on>
"""

# Mock response for an empty event fetch
mock_empty_html_content = """
<archive-whats-on v-bind='{"posts": []}'></archive-whats-on>
"""


# Mock SlackManager send_error_message method
@patch("utils.SlackManager.SlackManager.send_error_message")
@patch("requests.get")
def test_fetch_events_success(mock_get, mock_slack):
    # Mock a successful response from the event fetch API
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = mock_html_content

    fetcher = JapanHouseEventFetcher()
    events = fetcher.combine_and_return_events()

    # Assertions to check event fetching works as expected
    assert len(events) == 1
    assert events[0]["event_name"] == "Japan House Event 1"
    assert events[0]["event_location"] == "London"
    assert events[0]["event_date"] == "2024-10-20"

    # Ensure that no error message was sent to Slack
    mock_slack.assert_not_called()


# Test for an empty event response
@patch("utils.SlackManager.SlackManager.send_error_message")
@patch("requests.get")
def test_fetch_events_empty(mock_get, mock_slack):
    # Mock a successful response but with no events
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = mock_empty_html_content

    fetcher = JapanHouseEventFetcher()
    events = fetcher.combine_and_return_events()

    # Assert that no events were fetched
    assert len(events) == 0

    # Ensure that an error message was sent to Slack
    mock_slack.assert_called_once_with(
        "Issue with Japan House event fetcher, no events found"
    )


@patch("utils.SlackManager.SlackManager.send_error_message")
@patch("requests.get")
def test_fetch_events_network_error(mock_get, mock_slack):
    # Simulate a network exception during the fetch
    mock_get.side_effect = requests.exceptions.RequestException

    fetcher = JapanHouseEventFetcher()

    # Expect the fetch to handle the exception gracefully
    events = fetcher.combine_and_return_events()

    # Assert no events are returned
    assert len(events) == 0

    # Ensure that the correct error message was sent to Slack
    mock_slack.assert_called_once_with("Network error fetching japan_house events")


@patch("utils.SlackManager.SlackManager.send_error_message")
@patch("requests.get")
def test_fetch_events_non_200_status(mock_get, mock_slack):
    # Mock a non-200 status code
    mock_get.return_value.status_code = 500
    fetcher = JapanHouseEventFetcher()
    events = fetcher.combine_and_return_events()

    assert len(events) == 0
    mock_slack.assert_called_once_with(
        "Failed to fetch japan_house webpage. Status code: 500"
    )


@patch("utils.SlackManager.SlackManager.send_error_message")
@patch("requests.get")
def test_parse_events_invalid_json(mock_get, mock_slack):
    # Mock invalid JSON in v-bind
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = (
        "<archive-whats-on v-bind='invalid-json'></archive-whats-on>"
    )

    fetcher = JapanHouseEventFetcher()
    events = fetcher.combine_and_return_events()

    assert len(events) == 0
    mock_slack.assert_called_once_with("Error decoding JSON from v-bind")


@patch("utils.SlackManager.SlackManager.send_error_message")
@patch("requests.get")
def test_fetch_events_no_posts_key(mock_get, mock_slack):
    # Mock a response without 'posts' key
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = (
        "<archive-whats-on v-bind='{\"no_posts\": []}'></archive-whats-on>"
    )

    fetcher = JapanHouseEventFetcher()
    events = fetcher.combine_and_return_events()

    assert len(events) == 0
    mock_slack.assert_called_once_with(
        "Issue with Japan House event fetcher, no events found"
    )


@patch("utils.SlackManager.SlackManager.send_error_message")
@patch("requests.get")
def test_fetch_events_no_html_content(mock_get, mock_slack):
    # Mock a scenario where no content is fetched
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = None

    fetcher = JapanHouseEventFetcher()
    events = fetcher.combine_and_return_events()

    assert len(events) == 0
    mock_slack.assert_called_once_with(
        "Issue with Japan House event fetcher, no events found"
    )
