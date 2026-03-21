"""Discord -> Twitter thread pipeline.

Usage:
    python -m pipeline.content.discord_to_thread
    python -m pipeline.content.discord_to_thread --date 2026-03-21
    python -m pipeline.content.discord_to_thread --date 2026-03-21 --output thread.txt

Environment variables required:
    DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID, DISCORD_USER_ID, ANTHROPIC_API_KEY
"""
import argparse
import os
import sys
from datetime import date
from pathlib import Path

from pipeline.content.discord_fetch import fetch_messages, filter_by_author_and_date
from pipeline.content.processor import process_to_thread


def main():
    parser = argparse.ArgumentParser(description="Convert Discord posts into a Twitter thread")
    parser.add_argument("--date", type=str, default=None, help="Date to fetch posts for (YYYY-MM-DD). Default: today.")
    parser.add_argument("--output", type=str, default=None, help="Output file path. Default: print to stdout.")
    args = parser.parse_args()

    target_date = date.fromisoformat(args.date) if args.date else date.today()

    bot_token = os.environ.get("DISCORD_BOT_TOKEN")
    channel_id = os.environ.get("DISCORD_CHANNEL_ID")
    user_id = os.environ.get("DISCORD_USER_ID")

    if not all([bot_token, channel_id, user_id]):
        print("Error: Missing required environment variables.", file=sys.stderr)
        print("Set: DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID, DISCORD_USER_ID", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching messages from Discord for {target_date}...")
    raw_messages = fetch_messages(channel_id, bot_token)
    filtered = filter_by_author_and_date(raw_messages, user_id, target_date)

    if not filtered:
        print(f"No messages found for {target_date}. Nothing to process.")
        sys.exit(0)

    print(f"Found {len(filtered)} messages. Processing with Claude...")
    message_texts = [m["content"] for m in filtered if m["content"].strip()]
    tweets = process_to_thread(message_texts)
    thread_text = "\n\n".join(tweets)

    if args.output:
        Path(args.output).write_text(thread_text)
        print(f"Thread saved to {args.output}")
    else:
        print("\n" + "=" * 60)
        print("TWITTER THREAD")
        print("=" * 60 + "\n")
        print(thread_text)
        print("\n" + "=" * 60)
        print(f"{len(tweets)} tweets | Copy, review, and post to Twitter/X")


if __name__ == "__main__":
    main()
