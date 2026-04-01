"""Fetch messages from a Discord channel via HTTP API.

Uses a bot token for authentication but does NOT run a persistent bot process.
This is a simple HTTP client that fetches message history on demand.
"""
import requests
from datetime import date, datetime

DISCORD_API_BASE = "https://discord.com/api/v10"


def fetch_messages(channel_id: str, bot_token: str, limit: int = 100) -> list[dict]:
    url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
    headers = {"Authorization": f"Bot {bot_token}"}
    params = {"limit": min(limit, 100)}

    resp = requests.get(url, headers=headers, params=params, timeout=10)

    if resp.status_code != 200:
        raise RuntimeError(
            f"Discord API error {resp.status_code}: {resp.json().get('message', 'Unknown error')}"
        )

    return resp.json()


def filter_by_author_and_date(messages: list[dict], user_id: str, target_date: date) -> list[dict]:
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
