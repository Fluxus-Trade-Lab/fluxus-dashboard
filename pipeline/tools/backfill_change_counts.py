"""Backfill the change-derived breadth counts for the week change_pct was dead.

Finviz renamed its `Change` header to `Change %` on 2026-08-07 and the column
map only knew the old name, so `change_pct` was 100% null for a week. Every
count computed from it recorded zero: up_4pct, down_4pct, advances, declines.
Those zeros then flowed into every derived series -- the 5- and 10-day ratios,
RANA, the McClellan oscillator, and the A/D line, which is CUMULATIVE and so
carries the wound forward forever unless the raw counts are repaired.

This tool repairs the RAW counts only, from yfinance daily closes, and lets
`breadth_store.derive()` rebuild every derived series -- the same function the
nightly pipeline uses, so the healed rows and the live rows are computed by
one implementation.

Honest limits, stated where they can be read:

* Membership is TODAY's universe. The set of listed names shifted slightly
  over the week; counts over ~5,500 names are insensitive to that, but these
  rows are reconstructions, not observations, and are marked `source=backfill`.
* Coverage is whatever yfinance returns (~98%). The uncovered tail is dead
  units and delistings -- the same names the live scrape also misses.

Run:  python -m pipeline.tools.backfill_change_counts [--apply]

Without --apply it prints the repaired counts next to the stored zeros and
touches nothing.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipeline.screeners import breadth_store

logger = logging.getLogger(__name__)

ARCHIVE = "data/history/breadth_archive.csv"
UNIVERSE = Path("data/output/universe.json")

# The sessions the dead column zeroed out. 08-14 is deliberately absent: the
# rebuilt pipeline recomputes it live from the repaired column.
DEAD_SESSIONS = ["2026-08-07", "2026-08-10", "2026-08-11",
                 "2026-08-12", "2026-08-13"]

BATCH = 500
PASSES = 3


def load_tickers() -> list[str]:
    rows = json.loads(UNIVERSE.read_text())["rows"]
    return sorted({r["ticker"] for r in rows if r.get("ticker")})


def fetch_closes(tickers: list[str]) -> pd.DataFrame:
    """Daily closes since 2026-08-01, wide frame, with block-retry.

    The same lesson as the enrichment retry: throttled batches fail in blocks,
    so the misses from pass N become the (smaller) batches of pass N+1.
    """
    frames: dict[str, pd.Series] = {}
    todo = list(tickers)
    for p in range(1, PASSES + 1):
        if not todo:
            break
        batch_size = max(50, BATCH // p)
        logger.info("pass %d: %d tickers in batches of %d", p, len(todo), batch_size)
        misses: list[str] = []
        for i in range(0, len(todo), batch_size):
            batch = todo[i:i + batch_size]
            try:
                data = yf.download(batch, start="2026-08-01", group_by="ticker",
                                   auto_adjust=True, progress=False, threads=True)
            except Exception:
                misses.extend(batch)
                continue
            for t in batch:
                try:
                    s = data[t]["Close"].dropna()
                except Exception:
                    misses.append(t)
                    continue
                if len(s):
                    frames[t] = s
                else:
                    misses.append(t)
        todo = misses
    logger.info("closes for %d/%d tickers (%d unresolved)",
                len(frames), len(tickers), len(todo))
    wide = pd.DataFrame(frames)
    wide.index = pd.to_datetime(wide.index).strftime("%Y-%m-%d")
    return wide


def repaired_counts(closes: pd.DataFrame) -> dict[str, dict]:
    """Raw counts per dead session, from close-to-close changes."""
    out: dict[str, dict] = {}
    dates = list(closes.index)
    for d in DEAD_SESSIONS:
        if d not in dates:
            logger.warning("%s missing from the close panel — skipped", d)
            continue
        i = dates.index(d)
        if i == 0:
            logger.warning("%s has no prior session in panel — skipped", d)
            continue
        chg = closes.iloc[i] / closes.iloc[i - 1] - 1.0
        chg = chg.dropna()
        out[d] = {
            # Same thresholds as breadth_metrics.compute_snapshot.
            "up_4pct": int((chg >= 0.04).sum()),
            "down_4pct": int((chg <= -0.04).sum()),
            "advances": int((chg > 0).sum()),
            "declines": int((chg < 0).sum()),
            "coverage": int(chg.notna().sum()),
        }
    return out


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                    help="write the repaired archive (default: report only)")
    args = ap.parse_args()

    frame = breadth_store.load_archive(ARCHIVE)
    closes = fetch_closes(load_tickers())
    counts = repaired_counts(closes)

    print(f"\n{'date':<12}{'up4':>6}{'dn4':>6}{'adv':>6}{'dec':>6}{'cover':>7}   stored")
    for d, c in counts.items():
        stored = frame.loc[frame["date"].astype(str) == d]
        s = stored.iloc[0] if len(stored) else {}
        print(f"{d:<12}{c['up_4pct']:>6}{c['down_4pct']:>6}"
              f"{c['advances']:>6}{c['declines']:>6}{c['coverage']:>7}"
              f"   was up4={s.get('up_4pct')} adv={s.get('advances')}")

    if not args.apply:
        print("\n(dry run — nothing written; pass --apply)")
        return

    for d, c in counts.items():
        mask = frame["date"].astype(str) == d
        if not mask.any():
            continue
        for col in ("up_4pct", "down_4pct", "advances", "declines"):
            frame.loc[mask, col] = c[col]
        frame.loc[mask, "source"] = "backfill"

    # One derive over the whole frame heals every downstream series -- the
    # ratios, RANA, McClellan and the cumulative A/D line -- with the same
    # implementation the nightly run uses.
    frame = breadth_store.derive(frame)
    breadth_store.write_archive(frame, ARCHIVE)
    print(f"\narchive repaired: {sum(1 for _ in counts)} sessions rewritten, "
          f"derived series recomputed over {len(frame)} rows")


if __name__ == "__main__":
    main()
