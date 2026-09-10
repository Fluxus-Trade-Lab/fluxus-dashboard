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
from pipeline.content.processor import process_to_thread  # noqa: E402 (dual-mode: CLI locally, API in CI)
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


def _read_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def read_watermark(channel_id: str | None = None) -> datetime | None:
    """Last consumed message timestamp for one channel (None = no prior run).

    Multi-channel (2026-09-10): each channel keeps its own watermark under
    "channels"; the legacy top-level "last_message_utc" (single-channel era)
    is honoured as a fallback so an existing state file keeps working.
    """
    state = _read_state()
    ts = None
    if channel_id:
        ts = state.get("channels", {}).get(channel_id)
    if ts is None:
        ts = state.get("last_message_utc")
    return datetime.fromisoformat(ts) if ts else None


def write_watermark(dt_utc: datetime, channel_id: str | None = None) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    state = _read_state()
    if channel_id:
        state.setdefault("channels", {})[channel_id] = dt_utc.isoformat()
    else:
        state["last_message_utc"] = dt_utc.isoformat()
    STATE_PATH.write_text(json.dumps(state, indent=2))


def parse_channel_specs() -> list[tuple[str, str]]:
    """[(channel_id, label), ...] from env.

    DISCORD_CHANNEL_IDS takes precedence: comma-separated entries, each either
    "id" or "id:label". Falls back to the single DISCORD_CHANNEL_ID (labelled
    "live-commentary" — the original channel).
    """
    multi = os.environ.get("DISCORD_CHANNEL_IDS", "").strip()
    if multi:
        out = []
        for entry in multi.split(","):
            entry = entry.strip()
            if not entry:
                continue
            cid, _, label = entry.partition(":")
            out.append((cid.strip(), label.strip() or cid.strip()))
        return out
    single = os.environ.get("DISCORD_CHANNEL_ID", "").strip()
    return [(single, "live-commentary")] if single else []


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
    parser.add_argument(
        "--fetch-only", action="store_true",
        help="Fetch + filter messages and write messages.json only; no Claude call. "
             "The generation step runs later (cloud session or --generate).",
    )
    parser.add_argument(
        "--generate", type=str, default=None, metavar="FOLDER",
        help="Generate draft.txt from an existing threads/{FOLDER}/messages.json "
             "(written by a --fetch-only run). Skips Discord entirely.",
    )
    args = parser.parse_args()

    if args.after_noon:
        print("Note: --after-noon is deprecated and ignored (windowing is now 'since last run').",
              file=sys.stderr)

    if args.generate:
        out_dir = THREADS_DIR / args.generate
        msg_path = out_dir / "messages.json"
        if not msg_path.exists():
            print(f"Error: {msg_path} not found (run --fetch-only first).", file=sys.stderr)
            sys.exit(1)
        message_texts = [m["content"] for m in json.loads(msg_path.read_text())
                         if m["content"].strip()]
        style_examples = load_style_examples(THREADS_DIR)
        print(f"Generating thread from {len(message_texts)} stored messages...")
        tweets = process_to_thread(message_texts, style_examples=style_examples)
        draft_path = out_dir / "draft.txt"
        draft_path.write_text("\n\n".join(tweets))
        print(f"Draft saved to {draft_path} ({len(tweets)} tweets)")
        return

    bot_token = os.environ.get("DISCORD_BOT_TOKEN")
    user_id = os.environ.get("DISCORD_USER_ID")
    channels = parse_channel_specs()

    if not all([bot_token, user_id]) or not channels:
        print("Error: Missing required environment variables.", file=sys.stderr)
        print("Set: DISCORD_BOT_TOKEN, DISCORD_USER_ID, and DISCORD_CHANNEL_ID "
              "or DISCORD_CHANNEL_IDS (comma-separated id[:label]).", file=sys.stderr)
        sys.exit(1)

    backfill = args.date is not None
    label_suffix = f"-{args.label}" if args.label else ""

    # Fetch each channel independently; tag every message with its channel label.
    # Watermarks are per-channel (a shared one would drop messages whenever one
    # channel's newest consumed timestamp outruns another channel's fresh posts).
    filtered = []
    per_channel_max: dict[str, datetime] = {}
    for cid, clabel in channels:
        raw_messages = fetch_messages(cid, bot_token)
        if backfill:
            target_date = date.fromisoformat(args.date)
            got = filter_by_author_and_date(raw_messages, user_id, target_date)
        else:
            watermark = read_watermark(cid)
            if watermark is None:
                watermark = datetime.now(timezone.utc) - timedelta(hours=COLD_START_HOURS)
                print(f"[{clabel}] no prior run — cold start, looking back {COLD_START_HOURS}h.")
            got = filter_since(raw_messages, user_id, watermark)
        print(f"[{clabel}] {len(got)} messages")
        for m in got:
            m["channel"] = clabel
        if got:
            per_channel_max[cid] = max(_msg_timestamp(m) for m in got)
        filtered.extend(got)

    filtered.sort(key=_msg_timestamp)

    if backfill:
        out_folder = f"{args.date}{label_suffix}"
        empty_msg = f"No messages found for {args.date}. Nothing to process."
    else:
        out_folder = f"{market_today()}{label_suffix}"
        empty_msg = "No new messages since the last run. Nothing to process."

    if not filtered:
        # Do NOT advance any watermark on an empty run, so nothing is skipped next time.
        print(empty_msg)
        sys.exit(0)

    # Setup output directory
    out_dir = THREADS_DIR / out_folder
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.fetch_only:
        msg_path = out_dir / "messages.json"
        msg_path.write_text(json.dumps(
            [{"content": m["content"], "timestamp": m["timestamp"],
              "channel": m.get("channel", "live-commentary")} for m in filtered],
            ensure_ascii=False, indent=1))
        if not backfill:
            for cid, ts in per_channel_max.items():
                write_watermark(ts, cid)
        print(f"Fetched {len(filtered)} messages -> {msg_path}. "
              "Generation happens in the cloud session (or --generate).")
        return

    # Load style examples from previous revisions
    style_examples = load_style_examples(THREADS_DIR)

    print(f"Found {len(filtered)} messages. Processing with Claude...")
    message_texts = [m["content"] for m in filtered if m["content"].strip()]
    tweets = process_to_thread(message_texts, style_examples=style_examples)
    thread_text = "\n\n".join(tweets)

    # Save draft
    draft_path = out_dir / "draft.txt"
    draft_path.write_text(thread_text)

    # Advance the rolling watermarks only after a draft is successfully written,
    # and only in rolling mode (backfill must not disturb the live window).
    if not backfill:
        for cid, ts in per_channel_max.items():
            write_watermark(ts, cid)

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
