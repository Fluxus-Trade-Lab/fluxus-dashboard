"""Discord -> Twitter thread pipeline.

Usage:
    python -m pipeline.content.discord_to_thread
    python -m pipeline.content.discord_to_thread --date 2026-03-21

Output is saved to data/output/threads/{date}/draft.txt automatically.
After revision, the final version is saved as final.txt in the same folder.

Environment variables required:
    DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID, DISCORD_USER_ID
"""
import argparse
import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from pipeline.content.discord_fetch import fetch_messages, filter_by_author_and_date
from pipeline.content.processor import process_to_thread
from pipeline.content.revision import load_style_examples

# Base output directory
THREADS_DIR = Path(__file__).parent.parent.parent / "data" / "output" / "threads"


def main():
    # Load .env from pipeline/content/ (override=True in case vars are set but empty)
    load_dotenv(Path(__file__).parent / ".env", override=True)
    parser = argparse.ArgumentParser(description="Convert Discord posts into a Twitter thread")
    parser.add_argument("--date", type=str, default=None, help="Date to fetch posts for (YYYY-MM-DD). Default: today.")
    args = parser.parse_args()

    target_date = date.fromisoformat(args.date) if args.date else date.today()

    bot_token = os.environ.get("DISCORD_BOT_TOKEN")
    channel_id = os.environ.get("DISCORD_CHANNEL_ID")
    user_id = os.environ.get("DISCORD_USER_ID")

    if not all([bot_token, channel_id, user_id]):
        print("Error: Missing required environment variables.", file=sys.stderr)
        print("Set: DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID, DISCORD_USER_ID", file=sys.stderr)
        sys.exit(1)

    # Setup output directory
    date_dir = THREADS_DIR / str(target_date)
    date_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching messages from Discord for {target_date}...")
    raw_messages = fetch_messages(channel_id, bot_token)
    filtered = filter_by_author_and_date(raw_messages, user_id, target_date)

    if not filtered:
        print(f"No messages found for {target_date}. Nothing to process.")
        sys.exit(0)

    # Load style examples from previous revisions
    style_examples = load_style_examples(THREADS_DIR)

    print(f"Found {len(filtered)} messages. Processing with Claude...")
    message_texts = [m["content"] for m in filtered if m["content"].strip()]
    tweets = process_to_thread(message_texts, style_examples=style_examples)
    thread_text = "\n\n".join(tweets)

    # Save draft
    draft_path = date_dir / "draft.txt"
    draft_path.write_text(thread_text)

    print(f"\nDraft saved to {draft_path}")
    print("\n" + "=" * 60)
    print("TWITTER THREAD (DRAFT)")
    print("=" * 60 + "\n")
    print(thread_text)
    print("\n" + "=" * 60)
    print(f"{len(tweets)} tweets")
    print(f"\nTo review: read the draft above and tell me your edits.")
    print(f"After revision, final version will be saved to {date_dir / 'final.txt'}")


if __name__ == "__main__":
    main()
