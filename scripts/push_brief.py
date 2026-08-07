#!/usr/bin/env python3
"""Render the day's brief to a card and push it into Discord.

The image is the deliverable, not the text. A Discord message caps at 2000
characters and a forwarded wall of text loses its structure on a phone; a PNG
forwards intact, reads at a glance, and carries its own date and provenance, so
a screenshot found two weeks later still says what it is and when it was true.

Credentials come from the environment. `.env` in the repo root is read if
present and is gitignored — nothing here ever prints or logs a token.

Usage:
    .venv/bin/python scripts/push_brief.py --window post-close
    .venv/bin/python scripts/push_brief.py --dry-run       # render, do not send
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.marketcal import market_now, market_today
from pipeline.reference.card import caption, render_card

SNAP_DIR = Path("data/snapshots")
DISCORD_API = "https://discord.com/api/v10"


def load_env(path: str | Path = ".env") -> None:
    """Read KEY=VALUE (with or without a leading `export`) into os.environ.

    Existing environment wins, so a launchd-provided value is never clobbered by
    a stale file.
    """
    p = Path(path)
    if not p.exists():
        return
    for raw in p.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        line = line.removeprefix("export ").strip()
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip("'\""))


def send(image: Path, text: str, channel: str, token: str) -> bool:
    """Upload the card with its caption as one message."""
    import requests

    with image.open("rb") as fh:
        resp = requests.post(
            f"{DISCORD_API}/channels/{channel}/messages",
            headers={"Authorization": f"Bot {token}"},
            data={"payload_json": json.dumps({"content": text})},
            files={"files[0]": (image.name, fh, "image/png")},
            timeout=30,
        )
    if resp.status_code not in (200, 201):
        # Never echo the body wholesale — an auth error can carry the token back.
        print(f"discord: HTTP {resp.status_code} ({resp.reason})")
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="SPX")
    ap.add_argument("--date", help="YYYYMMDD (ET). Default: today's snapshot.")
    ap.add_argument("--window", default="", help="premarket | post-close")
    ap.add_argument("--dry-run", action="store_true",
                    help="render the card and print the caption; send nothing")
    args = ap.parse_args()

    load_env()
    day = args.date or market_today().strftime("%Y%m%d")
    snap = SNAP_DIR / f"snapshot_{args.symbol}_{day}.json"
    if not snap.exists():
        # Silence here would look like a successful push of nothing.
        sys.exit(f"no snapshot at {snap} — run build_snapshot.py first")

    data = json.loads(snap.read_text())
    card = render_card(data, SNAP_DIR / f"card_{args.symbol}_{day}.png",
                       window=args.window)
    text = caption(data, args.window)

    if args.dry_run:
        print(f"card: {card}\n--- caption ({len(text)} chars) ---\n{text}")
        return

    token = os.environ.get("DISCORD_BOT_TOKEN")
    # A dedicated variable rather than the general DISCORD_CHANNEL_ID: that one
    # points at a community channel, and a daily brief landing somewhere public
    # is a different act from a brief landing in an inbox. Naming the
    # destination separately means the choice has to be made on purpose.
    channel = os.environ.get("DISCORD_BRIEF_CHANNEL_ID")
    if not token or not channel:
        sys.exit("DISCORD_BOT_TOKEN / DISCORD_BRIEF_CHANNEL_ID not set "
                 "(checked the environment and .env)")

    ok = send(card, text, channel, token)
    print(f"pushed {card.name} to Discord" if ok else "push FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
