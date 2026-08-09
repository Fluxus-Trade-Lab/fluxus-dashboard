"""Discord -> Twitter thread pipeline.

Two modes:

  Rolling window (default) — process messages posted *since the last run*.
  This is how the scheduled AM/PM reports work: the AM run (late morning JST)
  picks up everything since the previous PM run, the PM run picks up everything
  since the AM run. A single shared watermark (the timestamp of the newest
  message already consumed) partitions the day cleanly, so no message is ever
  dropped or double-counted, even though the US session straddles JST midnight.

      python -m pipeline.content.discord_to_thread --label am
      python -m pipeline.content.discord_to_thread --label pm

  Backfill (--date) — process one whole UTC day, ignoring the watermark.
  Use for reprocessing a past day; it does not advance the rolling watermark.

      python -m pipeline.content.discord_to_thread --date 2026-03-21

Output is saved to data/output/threads/{folder}/draft.txt automatically, where
{folder} is "{today}-{label}" in rolling mode (e.g. 2026-07-13-am) or "{date}"
in backfill mode. After revision, the final version is saved as final.txt in the
same folder.

Environment variables required:
    DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID, DISCORD_USER_ID
"""
import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

from pipeline.marketcal import market_today
from pipeline.content.discord_fetch import fetch_messages, filter_by_author_and_date
from pipeline.content.processor import process_to_thread
from pipeline.content.revision import load_style_examples

# Base output directory
THREADS_DIR = Path(__file__).parent.parent.parent / "data" / "output" / "threads"

# Rolling-window watermark: timestamp (UTC, ISO 8601) of the newest message
# already turned into a draft. The next run only considers messages after it.
STATE_PATH = THREADS_DIR / ".run_state.json"

# Cold-start lookback when there is no watermark yet (first ever rolling run).
COLD_START_HOURS = 24


def _msg_timestamp(msg: dict) -> datetime:
    """Discord message timestamp as a tz-aware (UTC) datetime."""
    return datetime.fromisoformat(msg["timestamp"])


def read_watermark() -> datetime | None:
    """Return the last consumed message timestamp, or None if there is none."""
    if not STATE_PATH.exists():
        return None
    try:
        ts = json.loads(STATE_PATH.read_text()).get("last_message_utc")
    except (json.JSONDecodeError, OSError):
        return None
    return datetime.fromisoformat(ts) if ts else None


def write_watermark(dt_utc: datetime) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps({"last_message_utc": dt_utc.isoformat()}, indent=2))


def filter_since(messages: list[dict], user_id: str, since_utc: datetime) -> list[dict]:
    """Author's messages posted strictly after `since_utc`, oldest-first."""
    out = [
        msg
        for msg in messages
        if msg["author"]["id"] == user_id and _msg_timestamp(msg) > since_utc
    ]
    # Discord returns newest-first — reverse to chronological.
    out.reverse()
    return out


def main():
    # Load .env from pipeline/content/ (override=True in case vars are set but empty)
    load_dotenv(Path(__file__).parent / ".env", override=True)
    parser = argparse.ArgumentParser(description="Convert Discord posts into a Twitter thread")
    parser.add_argument(
        "--date", type=str, default=None,
        help="Backfill mode: process this whole UTC day (YYYY-MM-DD). Ignores the rolling watermark.",
    )
    parser.add_argument(
        "--label", type=str, default=None,
        help="Tag for this run (e.g. 'am'/'pm'). Names the output folder; report window is still 'since last run'.",
    )
    # Deprecated: the AM/PM split is now a rolling 'since last run' window, so this
    # flag no longer does anything. Accepted (ignored) so older task files don't break.
    parser.add_argument("--after-noon", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.after_noon:
        print("Note: --after-noon is deprecated and ignored (windowing is now 'since last run').",
              file=sys.stderr)

    bot_token = os.environ.get("DISCORD_BOT_TOKEN")
    channel_id = os.environ.get("DISCORD_CHANNEL_ID")
    user_id = os.environ.get("DISCORD_USER_ID")

    if not all([bot_token, channel_id, user_id]):
        print("Error: Missing required environment variables.", file=sys.stderr)
        print("Set: DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID, DISCORD_USER_ID", file=sys.stderr)
        sys.exit(1)

    backfill = args.date is not None
    label_suffix = f"-{args.label}" if args.label else ""

    raw_messages = fetch_messages(channel_id, bot_token)

    if backfill:
        target_date = date.fromisoformat(args.date)
        print(f"Fetching messages from Discord for {target_date} (backfill)...")
        filtered = filter_by_author_and_date(raw_messages, user_id, target_date)
        out_folder = f"{target_date}{label_suffix}"
        empty_msg = f"No messages found for {target_date}. Nothing to process."
    else:
        watermark = read_watermark()
        if watermark is None:
            watermark = datetime.now(timezone.utc) - timedelta(hours=COLD_START_HOURS)
            print(f"No prior run recorded — cold start, looking back {COLD_START_HOURS}h.")
        label_desc = f" [{args.label}]" if args.label else ""
        print(f"Fetching messages since {watermark:%Y-%m-%d %H:%M UTC}{label_desc}...")
        filtered = filter_since(raw_messages, user_id, watermark)
        out_folder = f"{market_today()}{label_suffix}"
        empty_msg = "No new messages since the last run. Nothing to process."

    if not filtered:
        # Do NOT advance the watermark on an empty run, so nothing is skipped next time.
        print(empty_msg)
        sys.exit(0)

    # Setup output directory
    out_dir = THREADS_DIR / out_folder
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load style examples from previous revisions
    style_examples = load_style_examples(THREADS_DIR)

    print(f"Found {len(filtered)} messages. Processing with Claude...")
    message_texts = [m["content"] for m in filtered if m["content"].strip()]
    tweets = process_to_thread(message_texts, style_examples=style_examples)
    thread_text = "\n\n".join(tweets)

    # Save draft
    draft_path = out_dir / "draft.txt"
    draft_path.write_text(thread_text)

    # Advance the rolling watermark only after a draft is successfully written,
    # and only in rolling mode (backfill must not disturb the live window).
    if not backfill:
        write_watermark(max(_msg_timestamp(m) for m in filtered))

    print(f"\nDraft saved to {draft_path}")
    print("\n" + "=" * 60)
    print("TWITTER THREAD (DRAFT)")
    print("=" * 60 + "\n")
    print(thread_text)
    print("\n" + "=" * 60)
    print(f"{len(tweets)} tweets")
    print(f"\nTo review: read the draft above and tell me your edits.")
    print(f"After revision, final version will be saved to {out_dir / 'final.txt'}")


if __name__ == "__main__":
    main()
