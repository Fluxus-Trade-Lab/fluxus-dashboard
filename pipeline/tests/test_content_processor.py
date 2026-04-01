"""Tests for Claude API content processor."""
import json
import pytest
from unittest.mock import patch, MagicMock
from pipeline.content.processor import process_to_thread, process_to_brief, split_thread

SAMPLE_THREAD_OUTPUT = """1/ NVDA broke above 248 with volume today. When the biggest name in semis moves with conviction, pay attention to the sector.

2/ Took partial profits at 252. The system says: secure 1R, let the rest run. Trailing stop at 245.

3/ Watching tomorrow: can NVDA hold 248 on a pullback? If yes, adding back. If no, stop does its job."""


class TestSplitThread:
    def test_splits_numbered_tweets(self):
        tweets = split_thread(SAMPLE_THREAD_OUTPUT)
        assert len(tweets) == 3
        assert tweets[0].startswith("1/")

    def test_each_tweet_under_280(self):
        tweets = split_thread(SAMPLE_THREAD_OUTPUT)
        for i, tweet in enumerate(tweets):
            assert len(tweet) <= 280, f"Tweet {i+1} is {len(tweet)} chars"

    def test_empty_input(self):
        assert split_thread("") == []

    def test_single_tweet(self):
        tweets = split_thread("1/ Just one observation today.")
        assert len(tweets) == 1


class TestProcessToThread:
    @patch("pipeline.content.processor.anthropic.Anthropic")
    def test_returns_list_of_tweets(self, mock_cls):
        mock_client = MagicMock()
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=SAMPLE_THREAD_OUTPUT)]
        mock_client.messages.create.return_value = mock_msg
        mock_cls.return_value = mock_client
        tweets = process_to_thread(["NVDA broke out", "Took partial at 252"])
        assert isinstance(tweets, list)
        assert len(tweets) > 0

    @patch("pipeline.content.processor.anthropic.Anthropic")
    def test_calls_claude_with_system_prompt(self, mock_cls):
        mock_client = MagicMock()
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="1/ Test tweet")]
        mock_client.messages.create.return_value = mock_msg
        mock_cls.return_value = mock_client
        process_to_thread(["test"])
        call_kwargs = mock_client.messages.create.call_args[1]
        assert "coach" in call_kwargs["system"].lower()
        assert call_kwargs["model"].startswith("claude-")


class TestProcessToBrief:
    @patch("pipeline.content.processor.anthropic.Anthropic")
    def test_returns_valid_brief_dict(self, mock_cls):
        mock_client = MagicMock()
        brief_json = json.dumps({"date": "2026-03-21", "title": "Semis leading", "summary": "NVDA broke above 248.", "watchlist": ["NVDA", "SMH"]})
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=brief_json)]
        mock_client.messages.create.return_value = mock_msg
        mock_cls.return_value = mock_client
        brief = process_to_brief("SPY is flat. NVDA looks strong.")
        assert "date" in brief
        assert "title" in brief
        assert "summary" in brief
        assert isinstance(brief["watchlist"], list)

    @patch("pipeline.content.processor.anthropic.Anthropic")
    def test_handles_json_in_code_fence(self, mock_cls):
        mock_client = MagicMock()
        brief_json = '```json\n{"date":"2026-03-21","title":"Test","summary":"Test summary","watchlist":["SPY"]}\n```'
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=brief_json)]
        mock_client.messages.create.return_value = mock_msg
        mock_cls.return_value = mock_client
        brief = process_to_brief("test transcript")
        assert brief["title"] == "Test"


class TestSplitThreadEdgeCases:
    def test_tweet_over_280_preserved(self):
        long_tweet = "1/ " + "A" * 300
        tweets = split_thread(long_tweet)
        assert len(tweets) == 1
        assert len(tweets[0]) > 280

    def test_no_numbers(self):
        tweets = split_thread("Just a single observation about NVDA today.")
        assert len(tweets) == 1

    def test_mixed_spacing(self):
        raw = "1/ First tweet\n\n2/ Second tweet\n\n\n3/ Third tweet"
        tweets = split_thread(raw)
        assert len(tweets) == 3

    def test_preserves_tickers(self):
        raw = "1/ NVDA at 248. SMH confirming.\n\n2/ Watching PLTR for breakout."
        tweets = split_thread(raw)
        assert "NVDA" in tweets[0]
        assert "PLTR" in tweets[1]
