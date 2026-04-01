# Content Engine Pipeline (Phase 0-2) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a pipeline that converts Tao's daily Discord posts into formatted Twitter threads, and pre-market audio into daily briefs — so his existing private content reaches the public.

**Architecture:** Python scripts in `pipeline/content/` using Discord HTTP API (no bot process) and Claude API (`anthropic` SDK). Manual trigger in Phase 1 (`python -m pipeline.content.discord_to_thread`). Phase 2 adds audio transcription via OpenAI Whisper API. Same infrastructure pattern as the existing `pipeline/screeners/` orchestrator.

**Tech Stack:** Python 3.11, `anthropic` SDK, `requests` (Discord HTTP API), `openai` SDK (Whisper transcription), `pytest`

**Design doc:** `~/.gstack/projects/zhuandy531-art-fluxus-dashboard/taolezhu-main-design-20260322-office-hours-content-engine.md`

---

### Task 1: Project scaffolding + dependencies

**Files:**
- Create: `pipeline/content/__init__.py`
- Create: `pipeline/content/prompts/__init__.py`
- Modify: `pipeline/requirements.txt`
- Create: `pipeline/content/.env.example`

**Step 1: Create directory structure**

```bash
mkdir -p pipeline/content/prompts
touch pipeline/content/__init__.py
touch pipeline/content/prompts/__init__.py
```

**Step 2: Add dependencies to requirements.txt**

Add these lines to `pipeline/requirements.txt`:

```
anthropic>=0.40.0
openai>=1.50.0
```

Note: `requests>=2.31` is already listed. No new dependency needed for Discord HTTP API.

**Step 3: Create .env.example**

Create `pipeline/content/.env.example`:

```
# Discord — create at https://discord.com/developers/applications
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_CHANNEL_ID=your_channel_id_here
DISCORD_USER_ID=your_discord_user_id_here

# Anthropic — https://console.anthropic.com/
ANTHROPIC_API_KEY=your_key_here

# OpenAI (for Whisper transcription) — https://platform.openai.com/
OPENAI_API_KEY=your_key_here
```

**Step 4: Install new dependencies**

Run: `pip install -r pipeline/requirements.txt`

**Step 5: Commit**

```bash
git add pipeline/content/ pipeline/requirements.txt
git commit -m "feat(content): scaffold content pipeline + add anthropic/openai deps"
```

---

### Task 2: Fluxus voice prompt template

**Files:**
- Create: `pipeline/content/prompts/fluxus_voice.py`
- Create: `pipeline/tests/test_content_prompts.py`

**Step 1: Write the failing test**

Create `pipeline/tests/test_content_prompts.py`:

```python
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
        assert "emoji" in prompt  # must mention emoji restriction
        assert "hype" in prompt   # must mention no hype

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
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest pipeline/tests/test_content_prompts.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.content.prompts.fluxus_voice'`

**Step 3: Write the prompt module**

Create `pipeline/content/prompts/fluxus_voice.py`:

```python
"""Fluxus voice prompt templates.

The style prompt is the brand guardrail — it ensures AI output
sounds like Tao's market reads, not generic financial commentary.

Composable: SYSTEM_PROMPT (base voice) + format-specific user prompts.
"""


SYSTEM_PROMPT = """You are a content formatter for Fluxus Capital, a systematic swing trading community.

VOICE — The Fluxus Way:
- You are a coach, not a guru. Teach the system, don't sell hype.
- Written tone: Bloomberg terminal meets thoughtful teacher.
- Concise. Every sentence earns its place. No filler.
- Use precise trading language (relative strength, breakout, consolidation, risk/reward).
- Reference the Fluxus Method pillars when relevant: Select (find strong stocks in strong themes), Read (interpret market signals in real time), Size (position sizing + risk management).

ANTI-DOPAMINE RULES (non-negotiable):
- NEVER use emoji. Not even one.
- NEVER use hype language: "incredible," "amazing," "huge," "insane," "fire," "LFG," "to the moon."
- NEVER use gain percentages as headlines or hooks.
- NEVER imply guaranteed returns or easy money.
- NEVER use exclamation marks for emphasis. Period is always fine.
- DO use specific numbers: prices, levels, R-multiples, percentages in context.
- DO acknowledge uncertainty: "watching for," "if X holds," "risk is defined at."
- DO show the process, not just the outcome.

ENGLISH POLISH:
- The author's first language is not English. Clean up grammar and phrasing naturally.
- Preserve the author's directness and technical precision.
- Do not make it sound academic or overly formal. Keep it conversational but sharp.
- Never add disclaimers like "not financial advice" — the content speaks for itself.
"""


def twitter_thread_prompt(messages: list[str]) -> str:
    """Build user prompt for Discord messages → Twitter thread.

    Args:
        messages: List of Discord message texts from a single trading day.

    Returns:
        User prompt string for Claude API.

    Raises:
        ValueError: If messages list is empty.
    """
    if not messages:
        raise ValueError("No messages provided")

    joined = "\\n---\\n".join(messages)

    return f\"\"\"Convert these Discord trading posts from today into a Twitter thread.

RULES:
- Each tweet MUST be 280 characters or fewer.
- Thread should be 3-8 tweets. Consolidate if the source has many small posts.
- First tweet is the hook — the single most interesting observation from today.
- Last tweet is forward-looking: "Watching X tomorrow" or "Key level to hold is Y."
- Number each tweet: 1/, 2/, 3/ etc.
- No hashtags. No cashtags ($NVDA). Just the ticker symbol (NVDA).
- Preserve specific prices, levels, and ticker symbols exactly.

TODAY'S DISCORD POSTS:
{joined}

Output ONLY the numbered tweets, nothing else.\"\"\"


def daily_brief_prompt(transcript: str) -> str:
    """Build user prompt for audio transcript → daily brief JSON.

    Args:
        transcript: Full text transcript of pre-market talk.

    Returns:
        User prompt string for Claude API.

    Raises:
        ValueError: If transcript is empty.
    """
    if not transcript.strip():
        raise ValueError("No transcript provided")

    return f\"\"\"Summarize this pre-market talk transcript into a daily brief.

Output EXACTLY this JSON structure (no markdown, no code fences):
{{
  "date": "YYYY-MM-DD",
  "title": "Short headline (max 60 chars) — the key theme or observation",
  "summary": "2-4 sentences capturing the main market read, key levels, and positioning. Be specific with numbers.",
  "watchlist": ["TICKER1", "TICKER2", "TICKER3"]
}}

RULES:
- Title should be lowercase-style, like a Bloomberg headline.
- Summary preserves the author's market interpretation, not generic commentary.
- Watchlist: only tickers explicitly mentioned as actionable. Max 5.
- Date: extract from context or use today's date.

TRANSCRIPT:
{transcript}\"\"\"
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest pipeline/tests/test_content_prompts.py -v`
Expected: All 11 tests PASS

**Step 5: Commit**

```bash
git add pipeline/content/prompts/fluxus_voice.py pipeline/tests/test_content_prompts.py
git commit -m "feat(content): add Fluxus voice prompt templates with tests"
```

---

### Task 3: Discord message fetcher

**Files:**
- Create: `pipeline/content/discord_fetch.py`
- Create: `pipeline/tests/test_discord_fetch.py`

**Step 1: Write the failing test**

Create `pipeline/tests/test_discord_fetch.py`:

```python
"""Tests for Discord message fetcher."""
import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import date

from pipeline.content.discord_fetch import fetch_messages, filter_by_author_and_date


# Sample Discord API response (simplified)
SAMPLE_MESSAGES = [
    {
        "id": "111",
        "author": {"id": "USER_1"},
        "content": "NVDA breaking out above 248 with volume",
        "timestamp": "2026-03-21T14:30:00.000000+00:00",
        "type": 0,
    },
    {
        "id": "222",
        "author": {"id": "USER_2"},
        "content": "What do you think about AMD?",
        "timestamp": "2026-03-21T14:35:00.000000+00:00",
        "type": 0,
    },
    {
        "id": "333",
        "author": {"id": "USER_1"},
        "content": "SMH showing relative strength. Watching for close above 250.",
        "timestamp": "2026-03-21T15:00:00.000000+00:00",
        "type": 0,
    },
    {
        "id": "444",
        "author": {"id": "USER_1"},
        "content": "End of day update: took partial on NVDA at 252. Trailing stop at 245.",
        "timestamp": "2026-03-21T19:55:00.000000+00:00",
        "type": 0,
    },
    {
        "id": "555",
        "author": {"id": "USER_1"},
        "content": "Yesterday's note — reviewing weekly chart",
        "timestamp": "2026-03-20T20:00:00.000000+00:00",
        "type": 0,
    },
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
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest pipeline/tests/test_discord_fetch.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write the Discord fetcher**

Create `pipeline/content/discord_fetch.py`:

```python
"""Fetch messages from a Discord channel via HTTP API.

Uses a bot token for authentication but does NOT run a persistent bot process.
This is a simple HTTP client that fetches message history on demand.

Usage:
    messages = fetch_messages(channel_id, bot_token)
    filtered = filter_by_author_and_date(messages, user_id, target_date)
"""
import requests
from datetime import date, datetime, timezone

DISCORD_API_BASE = "https://discord.com/api/v10"


def fetch_messages(
    channel_id: str,
    bot_token: str,
    limit: int = 100,
) -> list[dict]:
    """Fetch recent messages from a Discord channel.

    Args:
        channel_id: The Discord channel ID.
        bot_token: Bot token for authentication.
        limit: Max messages to fetch (Discord max is 100 per request).

    Returns:
        List of message dicts from Discord API.

    Raises:
        RuntimeError: If the API returns a non-200 status.
    """
    url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
    headers = {"Authorization": f"Bot {bot_token}"}
    params = {"limit": min(limit, 100)}

    resp = requests.get(url, headers=headers, params=params, timeout=10)

    if resp.status_code != 200:
        raise RuntimeError(
            f"Discord API error {resp.status_code}: {resp.json().get('message', 'Unknown error')}"
        )

    return resp.json()


def filter_by_author_and_date(
    messages: list[dict],
    user_id: str,
    target_date: date,
) -> list[dict]:
    """Filter messages by author and date.

    Args:
        messages: Raw messages from Discord API.
        user_id: Discord user ID to filter by (Tao's ID).
        target_date: Only include messages from this date (UTC).

    Returns:
        Filtered list of message dicts, chronologically ordered.
    """
    filtered = []
    for msg in messages:
        if msg["author"]["id"] != user_id:
            continue
        msg_date = datetime.fromisoformat(msg["timestamp"]).date()
        if msg_date != target_date:
            continue
        filtered.append(msg)

    # Discord returns newest first — reverse to chronological
    filtered.reverse()
    return filtered
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest pipeline/tests/test_discord_fetch.py -v`
Expected: All 9 tests PASS

**Step 5: Commit**

```bash
git add pipeline/content/discord_fetch.py pipeline/tests/test_discord_fetch.py
git commit -m "feat(content): add Discord message fetcher with tests"
```

---

### Task 4: Claude API content processor

**Files:**
- Create: `pipeline/content/processor.py`
- Create: `pipeline/tests/test_content_processor.py`

**Step 1: Write the failing test**

Create `pipeline/tests/test_content_processor.py`:

```python
"""Tests for Claude API content processor."""
import json
import pytest
from unittest.mock import patch, MagicMock

from pipeline.content.processor import (
    process_to_thread,
    process_to_brief,
    split_thread,
)


SAMPLE_THREAD_OUTPUT = \"\"\"1/ NVDA broke above 248 with volume today. When the biggest name in semis moves with conviction, pay attention to the sector — SMH confirming at the same time.

2/ Took partial profits at 252. Not because the trade was done, but because the system says: secure 1R, let the rest run. Trailing stop at 245.

3/ Watching tomorrow: can NVDA hold 248 on a pullback? If yes, adding back the partial. If no, stop does its job. The process matters more than the outcome.\"\"\"


class TestSplitThread:
    def test_splits_numbered_tweets(self):
        tweets = split_thread(SAMPLE_THREAD_OUTPUT)
        assert len(tweets) == 3
        assert tweets[0].startswith("1/")

    def test_each_tweet_under_280(self):
        tweets = split_thread(SAMPLE_THREAD_OUTPUT)
        for i, tweet in enumerate(tweets):
            assert len(tweet) <= 280, f"Tweet {i+1} is {len(tweet)} chars: {tweet[:50]}..."

    def test_empty_input(self):
        tweets = split_thread("")
        assert tweets == []

    def test_single_tweet(self):
        tweets = split_thread("1/ Just one observation today.")
        assert len(tweets) == 1


class TestProcessToThread:
    @patch("pipeline.content.processor.anthropic.Anthropic")
    def test_returns_list_of_tweets(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=SAMPLE_THREAD_OUTPUT)]
        mock_client.messages.create.return_value = mock_msg
        mock_anthropic_cls.return_value = mock_client

        tweets = process_to_thread(["NVDA broke out", "Took partial at 252"])
        assert isinstance(tweets, list)
        assert len(tweets) > 0

    @patch("pipeline.content.processor.anthropic.Anthropic")
    def test_calls_claude_with_system_prompt(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="1/ Test tweet")]
        mock_client.messages.create.return_value = mock_msg
        mock_anthropic_cls.return_value = mock_client

        process_to_thread(["test"])

        call_kwargs = mock_client.messages.create.call_args[1]
        assert "coach" in call_kwargs["system"].lower()
        assert call_kwargs["model"].startswith("claude-")


class TestProcessToBrief:
    @patch("pipeline.content.processor.anthropic.Anthropic")
    def test_returns_valid_brief_dict(self, mock_anthropic_cls):
        mock_client = MagicMock()
        brief_json = json.dumps({
            "date": "2026-03-21",
            "title": "Semis leading again",
            "summary": "NVDA broke above 248. Watching for continuation.",
            "watchlist": ["NVDA", "SMH"]
        })
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=brief_json)]
        mock_client.messages.create.return_value = mock_msg
        mock_anthropic_cls.return_value = mock_client

        brief = process_to_brief("SPY is flat. NVDA looks strong.")
        assert "date" in brief
        assert "title" in brief
        assert "summary" in brief
        assert "watchlist" in brief
        assert isinstance(brief["watchlist"], list)

    @patch("pipeline.content.processor.anthropic.Anthropic")
    def test_handles_json_in_code_fence(self, mock_anthropic_cls):
        mock_client = MagicMock()
        brief_json = '```json\\n{"date":"2026-03-21","title":"Test","summary":"Test summary","watchlist":["SPY"]}\\n```'
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=brief_json)]
        mock_client.messages.create.return_value = mock_msg
        mock_anthropic_cls.return_value = mock_client

        brief = process_to_brief("test transcript")
        assert brief["title"] == "Test"


class TestSplitThreadEdgeCases:
    def test_tweet_over_280_chars_is_preserved(self):
        long_tweet = "1/ " + "A" * 300
        tweets = split_thread(long_tweet)
        assert len(tweets) == 1
        assert len(tweets[0]) > 280

    def test_thread_with_no_numbers(self):
        tweets = split_thread("Just a single observation about NVDA today.")
        assert len(tweets) == 1

    def test_thread_with_mixed_spacing(self):
        raw = "1/ First tweet\\n\\n2/ Second tweet\\n\\n\\n3/ Third tweet"
        tweets = split_thread(raw)
        assert len(tweets) == 3

    def test_thread_preserves_ticker_symbols(self):
        raw = "1/ NVDA at 248. SMH confirming.\\n\\n2/ Watching PLTR for breakout."
        tweets = split_thread(raw)
        assert "NVDA" in tweets[0]
        assert "PLTR" in tweets[1]
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest pipeline/tests/test_content_processor.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write the processor**

Create `pipeline/content/processor.py`:

```python
"""Claude API content processor.

Takes raw text (Discord messages or audio transcripts) and produces
formatted output (Twitter threads or daily briefs) using the Fluxus voice.

                ┌──────────────┐
  raw text ──▶  │  Claude API  │  ──▶  formatted output
                │  + Fluxus    │       (thread or brief)
                │    voice     │
                └──────────────┘
"""
import json
import re

import anthropic

from pipeline.content.prompts.fluxus_voice import (
    SYSTEM_PROMPT,
    twitter_thread_prompt,
    daily_brief_prompt,
)

MODEL = "claude-sonnet-4-20250514"


def process_to_thread(
    messages: list[str],
    api_key: str | None = None,
) -> list[str]:
    """Convert Discord messages into a formatted Twitter thread.

    Args:
        messages: List of message text strings from Discord.
        api_key: Anthropic API key. If None, uses ANTHROPIC_API_KEY env var.

    Returns:
        List of tweet strings, each ≤280 characters.
    """
    client = anthropic.Anthropic(api_key=api_key)

    user_prompt = twitter_thread_prompt(messages)

    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_output = response.content[0].text
    return split_thread(raw_output)


def process_to_brief(
    transcript: str,
    api_key: str | None = None,
) -> dict:
    """Convert an audio transcript into a daily brief JSON object.

    Args:
        transcript: Full text transcript of pre-market talk.
        api_key: Anthropic API key. If None, uses ANTHROPIC_API_KEY env var.

    Returns:
        Dict matching briefs.json schema: {date, title, summary, watchlist}.
    """
    client = anthropic.Anthropic(api_key=api_key)

    user_prompt = daily_brief_prompt(transcript)

    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_output = response.content[0].text
    return _parse_brief_json(raw_output)


def split_thread(raw_output: str) -> list[str]:
    """Split Claude's raw thread output into individual tweets.

    Handles numbered format: "1/ ...\\n\\n2/ ...\\n\\n3/ ..."

    Args:
        raw_output: Raw text from Claude containing numbered tweets.

    Returns:
        List of tweet strings. Empty list if input is empty.
    """
    if not raw_output.strip():
        return []

    # Split on tweet numbers: "1/ ", "2/ ", etc.
    tweets = re.split(r"\\n\\n(?=\\d+/\\s)", raw_output.strip())
    return [t.strip() for t in tweets if t.strip()]


def _parse_brief_json(raw_output: str) -> dict:
    """Parse JSON from Claude's response, handling code fences.

    Args:
        raw_output: Raw text that should contain a JSON object.

    Returns:
        Parsed dict.

    Raises:
        ValueError: If no valid JSON found in output.
    """
    # Strip markdown code fences if present
    cleaned = re.sub(r"```json\\s*", "", raw_output)
    cleaned = re.sub(r"```\\s*", "", cleaned)
    cleaned = cleaned.strip()

    # Find the JSON object
    match = re.search(r"\\{[\\s\\S]*\\}", cleaned)
    if not match:
        raise ValueError(f"No valid JSON found in Claude response: {raw_output[:200]}")

    brief = json.loads(match.group(0))

    # Validate required fields
    required = {"date", "title", "summary", "watchlist"}
    missing = required - set(brief.keys())
    if missing:
        raise ValueError(f"Brief JSON missing required fields: {missing}")

    return brief
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest pipeline/tests/test_content_processor.py -v`
Expected: All 11 tests PASS

**Step 5: Commit**

```bash
git add pipeline/content/processor.py pipeline/tests/test_content_processor.py
git commit -m "feat(content): add Claude API content processor with tests"
```

---

### Task 5: Discord-to-thread CLI script

**Files:**
- Create: `pipeline/content/discord_to_thread.py`

**Step 1: Write the CLI script**

Create `pipeline/content/discord_to_thread.py`:

```python
"""Discord → Twitter thread pipeline.

Manual trigger: converts today's Discord posts into a formatted Twitter thread.

Usage:
    python -m pipeline.content.discord_to_thread
    python -m pipeline.content.discord_to_thread --date 2026-03-21
    python -m pipeline.content.discord_to_thread --date 2026-03-21 --output thread.txt

Environment variables required:
    DISCORD_BOT_TOKEN   — Discord bot token
    DISCORD_CHANNEL_ID  — Channel ID to read from
    DISCORD_USER_ID     — Tao's Discord user ID (filter messages)
    ANTHROPIC_API_KEY   — Claude API key
"""
import argparse
import os
import sys
from datetime import date, datetime
from pathlib import Path

from pipeline.content.discord_fetch import fetch_messages, filter_by_author_and_date
from pipeline.content.processor import process_to_thread


def main():
    parser = argparse.ArgumentParser(
        description="Convert Discord posts into a Twitter thread"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Date to fetch posts for (YYYY-MM-DD). Default: today.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path. Default: print to stdout.",
    )
    args = parser.parse_args()

    # Resolve date
    target_date = (
        date.fromisoformat(args.date) if args.date else date.today()
    )

    # Load env vars
    bot_token = os.environ.get("DISCORD_BOT_TOKEN")
    channel_id = os.environ.get("DISCORD_CHANNEL_ID")
    user_id = os.environ.get("DISCORD_USER_ID")

    if not all([bot_token, channel_id, user_id]):
        print("Error: Missing required environment variables.", file=sys.stderr)
        print("Set: DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID, DISCORD_USER_ID", file=sys.stderr)
        sys.exit(1)

    # Fetch and filter
    print(f"Fetching messages from Discord for {target_date}...")
    raw_messages = fetch_messages(channel_id, bot_token)
    filtered = filter_by_author_and_date(raw_messages, user_id, target_date)

    if not filtered:
        print(f"No messages found for {target_date}. Nothing to process.")
        sys.exit(0)

    print(f"Found {len(filtered)} messages. Processing with Claude...")

    # Extract text content
    message_texts = [m["content"] for m in filtered if m["content"].strip()]

    # Process to thread
    tweets = process_to_thread(message_texts)

    # Output
    thread_text = "\\n\\n".join(tweets)

    if args.output:
        Path(args.output).write_text(thread_text)
        print(f"Thread saved to {args.output}")
    else:
        print("\\n" + "=" * 60)
        print("TWITTER THREAD")
        print("=" * 60)
        print()
        print(thread_text)
        print()
        print("=" * 60)
        print(f"{len(tweets)} tweets | Copy, review, and post to Twitter/X")


if __name__ == "__main__":
    main()
```

**Step 2: Test manually (dry run)**

Run: `python -m pipeline.content.discord_to_thread --help`
Expected: Help text with `--date` and `--output` options

**Step 3: Commit**

```bash
git add pipeline/content/discord_to_thread.py
git commit -m "feat(content): add discord-to-thread CLI script"
```

---

### Task 6: Audio-to-brief CLI script

**Files:**
- Create: `pipeline/content/audio_to_brief.py`

**Step 1: Write the CLI script**

Create `pipeline/content/audio_to_brief.py`:

```python
"""Audio → Daily brief pipeline.

Transcribes a pre-market talk recording and produces a daily brief
in the same JSON format as briefs.json.

Usage:
    python -m pipeline.content.audio_to_brief --file premarket-2026-03-21.mp3
    python -m pipeline.content.audio_to_brief --file talk.m4a --append

Environment variables required:
    OPENAI_API_KEY     — For Whisper transcription
    ANTHROPIC_API_KEY  — For Claude brief generation
"""
import argparse
import json
import os
import sys
from pathlib import Path

from openai import OpenAI

from pipeline.content.processor import process_to_brief

BRIEFS_PATH = Path("data/output/briefs.json")
MAX_FILE_SIZE_MB = 25


def transcribe_audio(file_path: str, api_key: str | None = None) -> str:
    """Transcribe audio file using OpenAI Whisper API.

    Args:
        file_path: Path to audio file (.mp3, .m4a, .wav, etc.)
        api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.

    Returns:
        Transcript text.

    Raises:
        FileNotFoundError: If audio file doesn't exist.
        ValueError: If file exceeds 25MB Whisper limit.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(
            f"Audio file is {size_mb:.1f}MB — exceeds Whisper's {MAX_FILE_SIZE_MB}MB limit. "
            f"Split the file first: ffmpeg -i {file_path} -t 1200 -c copy part1.mp3"
        )

    client = OpenAI(api_key=api_key)

    with open(path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="text",
        )

    return transcript


def main():
    parser = argparse.ArgumentParser(
        description="Convert pre-market talk audio into a daily brief"
    )
    parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Path to audio file (.mp3, .m4a, .wav)",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help=f"Append the new brief to {BRIEFS_PATH}",
    )
    args = parser.parse_args()

    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        print("Error: OPENAI_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    # Transcribe
    print(f"Transcribing {args.file}...")
    transcript = transcribe_audio(args.file, api_key=openai_key)
    print(f"Transcript: {len(transcript)} characters")

    # Generate brief
    print("Generating daily brief with Claude...")
    brief = process_to_brief(transcript)

    # Output
    print("\\n" + json.dumps(brief, indent=2))

    if args.append:
        briefs = []
        if BRIEFS_PATH.exists():
            briefs = json.loads(BRIEFS_PATH.read_text())

        # Insert at beginning (newest first)
        briefs.insert(0, brief)

        # Keep last 30 briefs
        briefs = briefs[:30]

        BRIEFS_PATH.write_text(json.dumps(briefs, indent=2) + "\\n")
        print(f"\\nAppended to {BRIEFS_PATH} ({len(briefs)} total briefs)")


if __name__ == "__main__":
    main()
```

**Step 2: Test manually (dry run)**

Run: `python -m pipeline.content.audio_to_brief --help`
Expected: Help text with `--file` and `--append` options

**Step 3: Commit**

```bash
git add pipeline/content/audio_to_brief.py
git commit -m "feat(content): add audio-to-brief CLI script"
```

---

### Task 7: Audio transcription tests

**Files:**
- Create: `pipeline/tests/test_audio_to_brief.py`

**Step 1: Write tests**

Create `pipeline/tests/test_audio_to_brief.py`:

```python
"""Tests for audio transcription and brief generation."""
import json
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from pipeline.content.audio_to_brief import transcribe_audio, BRIEFS_PATH


class TestTranscribeAudio:
    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError, match="not found"):
            transcribe_audio("/nonexistent/file.mp3")

    @patch("pipeline.content.audio_to_brief.Path")
    def test_file_too_large(self, mock_path_cls):
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.stat.return_value = MagicMock(st_size=30 * 1024 * 1024)  # 30MB
        mock_path_cls.return_value = mock_path

        with pytest.raises(ValueError, match="exceeds Whisper"):
            transcribe_audio("too_large.mp3")

    @patch("pipeline.content.audio_to_brief.OpenAI")
    @patch("pipeline.content.audio_to_brief.Path")
    @patch("builtins.open", mock_open(read_data=b"fake audio"))
    def test_successful_transcription(self, mock_path_cls, mock_openai_cls):
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.stat.return_value = MagicMock(st_size=5 * 1024 * 1024)  # 5MB
        mock_path_cls.return_value = mock_path

        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = "SPY is testing the 50 day."
        mock_openai_cls.return_value = mock_client

        result = transcribe_audio("premarket.mp3", api_key="test-key")
        assert "SPY" in result
```

**Step 2: Run tests**

Run: `python -m pytest pipeline/tests/test_audio_to_brief.py -v`
Expected: All 3 tests PASS

**Step 3: Commit**

```bash
git add pipeline/tests/test_audio_to_brief.py
git commit -m "test(content): add audio transcription tests"
```

---

### Task 8: Run full test suite + final verification

**Step 1: Run entire content pipeline test suite**

Run:
```bash
python -m pytest pipeline/tests/test_content_prompts.py pipeline/tests/test_discord_fetch.py pipeline/tests/test_content_processor.py pipeline/tests/test_audio_to_brief.py -v
```

Expected: All ~24 tests PASS

**Step 2: Verify CLI scripts show help**

Run:
```bash
python -m pipeline.content.discord_to_thread --help
python -m pipeline.content.audio_to_brief --help
```

Expected: Both show usage information without errors.

**Step 3: Final commit if any files were adjusted**

```bash
git add -A pipeline/content/ pipeline/tests/
git diff --staged --quiet || git commit -m "chore(content): final cleanup after full test pass"
```

---

## File manifest

```
pipeline/
├── content/
│   ├── __init__.py                  (Task 1)
│   ├── .env.example                 (Task 1)
│   ├── prompts/
│   │   ├── __init__.py              (Task 1)
│   │   └── fluxus_voice.py          (Task 2)
│   ├── discord_fetch.py             (Task 3)
│   ├── processor.py                 (Task 4)
│   ├── discord_to_thread.py         (Task 5)
│   └── audio_to_brief.py            (Task 6)
├── tests/
│   ├── test_content_prompts.py      (Task 2)
│   ├── test_discord_fetch.py        (Task 3)
│   ├── test_content_processor.py    (Task 4)
│   └── test_audio_to_brief.py       (Task 7)
└── requirements.txt                 (Task 1 — modified)
```

Total: 8 new files created, 1 file modified, ~24 tests.
