"""Tests for Fluxus voice prompt templates."""
import pytest
from pipeline.content.prompts.fluxus_voice import (
    SYSTEM_PROMPT,
    twitter_thread_prompt,
    daily_brief_prompt,
)


class TestSystemPrompt:
    def test_system_prompt_is_string(self):
        assert isinstance(SYSTEM_PROMPT, str)
        assert len(SYSTEM_PROMPT) > 100

    def test_system_prompt_contains_anti_dopamine_rules(self):
        prompt = SYSTEM_PROMPT.lower()
        assert "emoji" in prompt
        assert "hype" in prompt

    def test_system_prompt_mentions_coach_not_guru(self):
        prompt = SYSTEM_PROMPT.lower()
        assert "coach" in prompt


class TestTwitterThreadPrompt:
    def test_returns_string(self):
        result = twitter_thread_prompt(["Post 1", "Post 2"])
        assert isinstance(result, str)

    def test_includes_messages(self):
        messages = ["NVDA breaking out above 248", "SMH showing relative strength"]
        result = twitter_thread_prompt(messages)
        assert "NVDA" in result
        assert "SMH" in result

    def test_specifies_280_char_limit(self):
        result = twitter_thread_prompt(["test"])
        assert "280" in result

    def test_empty_messages_raises(self):
        with pytest.raises(ValueError, match="No messages"):
            twitter_thread_prompt([])


class TestDailyBriefPrompt:
    def test_returns_string(self):
        result = daily_brief_prompt("Full transcript of today's pre-market talk...")
        assert isinstance(result, str)

    def test_includes_transcript(self):
        text = "SPY is testing the 50-day moving average"
        result = daily_brief_prompt(text)
        assert "SPY" in result

    def test_specifies_json_schema(self):
        result = daily_brief_prompt("test")
        assert "title" in result
        assert "summary" in result
        assert "watchlist" in result

    def test_empty_transcript_raises(self):
        with pytest.raises(ValueError, match="No transcript"):
            daily_brief_prompt("")
