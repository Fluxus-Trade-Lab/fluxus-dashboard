"""Content processor using Claude Code CLI.

Takes raw text (Discord messages or audio transcripts) and produces
formatted output (Twitter threads or daily briefs) using the Fluxus voice.

Uses `claude -p` (Claude Code CLI) instead of the Anthropic API,
so it runs on your Max subscription — no separate API credits needed.
"""
import json
import re
import subprocess

from pipeline.content.prompts.fluxus_voice import (
    SYSTEM_PROMPT,
    twitter_thread_prompt,
    daily_brief_prompt,
)


def _claude(prompt: str, system: str) -> str:
    """Call Claude Code CLI with a prompt and system instruction."""
    full_prompt = f"<system>\n{system}\n</system>\n\n{prompt}"
    result = subprocess.run(
        ["claude", "-p", full_prompt],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI error: {result.stderr.strip()}")
    return result.stdout.strip()


def process_to_thread(messages: list[str], style_examples: str = "") -> list[str]:
    user_prompt = twitter_thread_prompt(messages)
    system = SYSTEM_PROMPT
    if style_examples:
        system = system + "\n\n" + style_examples
    raw_output = _claude(user_prompt, system)
    return split_thread(raw_output)


def process_to_brief(transcript: str) -> dict:
    user_prompt = daily_brief_prompt(transcript)
    raw_output = _claude(user_prompt, SYSTEM_PROMPT)
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
