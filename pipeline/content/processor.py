"""Claude API content processor.

Takes raw text (Discord messages or audio transcripts) and produces
formatted output (Twitter threads or daily briefs) using the Fluxus voice.
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


def process_to_thread(messages: list[str], api_key: str | None = None) -> list[str]:
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


def process_to_brief(transcript: str, api_key: str | None = None) -> dict:
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
    if not raw_output.strip():
        return []
    tweets = re.split(r"\n\n(?=\d+/\s)", raw_output.strip())
    return [t.strip() for t in tweets if t.strip()]


def _parse_brief_json(raw_output: str) -> dict:
    cleaned = re.sub(r"```json\s*", "", raw_output)
    cleaned = re.sub(r"```\s*", "", cleaned)
    cleaned = cleaned.strip()
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if not match:
        raise ValueError(f"No valid JSON found in Claude response: {raw_output[:200]}")
    brief = json.loads(match.group(0))
    required = {"date", "title", "summary", "watchlist"}
    missing = required - set(brief.keys())
    if missing:
        raise ValueError(f"Brief JSON missing required fields: {missing}")
    return brief
