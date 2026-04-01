"""Tests for Discord message fetcher."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date
from pipeline.content.discord_fetch import fetch_messages, filter_by_author_and_date

SAMPLE_MESSAGES = [
    {"id": "555", "author": {"id": "USER_1"}, "content": "Yesterday's note — reviewing weekly chart", "timestamp": "2026-03-20T20:00:00.000000+00:00", "type": 0},
    {"id": "444", "author": {"id": "USER_1"}, "content": "End of day update: took partial on NVDA at 252. Trailing stop at 245.", "timestamp": "2026-03-21T19:55:00.000000+00:00", "type": 0},
    {"id": "333", "author": {"id": "USER_1"}, "content": "SMH showing relative strength. Watching for close above 250.", "timestamp": "2026-03-21T15:00:00.000000+00:00", "type": 0},
    {"id": "222", "author": {"id": "USER_2"}, "content": "What do you think about AMD?", "timestamp": "2026-03-21T14:35:00.000000+00:00", "type": 0},
    {"id": "111", "author": {"id": "USER_1"}, "content": "NVDA breaking out above 248 with volume", "timestamp": "2026-03-21T14:30:00.000000+00:00", "type": 0},
]


class TestFilterByAuthorAndDate:
    def test_filters_by_author(self):
        result = filter_by_author_and_date(SAMPLE_MESSAGES, "USER_1", date(2026, 3, 21))
        assert len(result) == 3
        assert all(m["author"]["id"] == "USER_1" for m in result)

    def test_filters_by_date(self):
        result = filter_by_author_and_date(SAMPLE_MESSAGES, "USER_1", date(2026, 3, 21))
        assert len(result) == 3

    def test_returns_content_strings(self):
        result = filter_by_author_and_date(SAMPLE_MESSAGES, "USER_1", date(2026, 3, 21))
        assert result[0]["content"] == "NVDA breaking out above 248 with volume"

    def test_no_messages_returns_empty(self):
        result = filter_by_author_and_date(SAMPLE_MESSAGES, "NOBODY", date(2026, 3, 21))
        assert result == []

    def test_different_date_returns_different_messages(self):
        result = filter_by_author_and_date(SAMPLE_MESSAGES, "USER_1", date(2026, 3, 20))
        assert len(result) == 1
        assert "weekly chart" in result[0]["content"]


class TestFetchMessages:
    @patch("pipeline.content.discord_fetch.requests.get")
    def test_successful_fetch(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = SAMPLE_MESSAGES
        mock_get.return_value = mock_resp
        result = fetch_messages("CHANNEL_123", "TOKEN_ABC")
        assert len(result) == 5
        mock_get.assert_called_once()

    @patch("pipeline.content.discord_fetch.requests.get")
    def test_invalid_token_raises(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.json.return_value = {"message": "401: Unauthorized"}
        mock_get.return_value = mock_resp
        with pytest.raises(RuntimeError, match="Discord API error 401"):
            fetch_messages("CHANNEL_123", "BAD_TOKEN")

    @patch("pipeline.content.discord_fetch.requests.get")
    def test_channel_not_found_raises(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.json.return_value = {"message": "Unknown Channel"}
        mock_get.return_value = mock_resp
        with pytest.raises(RuntimeError, match="Discord API error 404"):
            fetch_messages("BAD_CHANNEL", "TOKEN_ABC")

    @patch("pipeline.content.discord_fetch.requests.get")
    def test_rate_limit_raises(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.json.return_value = {"message": "You are being rate limited", "retry_after": 5}
        mock_get.return_value = mock_resp
        with pytest.raises(RuntimeError, match="Discord API error 429"):
            fetch_messages("CHANNEL_123", "TOKEN_ABC")
