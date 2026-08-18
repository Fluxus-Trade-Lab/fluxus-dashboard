"""Backfill Screener-preset hits into the ticker event archive from git.

The presets were only ever evaluated in the browser, so until 2026-08-19 the
archive had no `preset:*` rows and four presets could not be validated. But
`data/output/universe.json` -- the file the page filters -- has been committed
nightly since 2026-03, so every past day's preset membership is recoverable
by replaying the same port the cron now uses (pipeline/screeners/preset_hits).

Only dates the archive ALREADY holds (i.e. days the core seven screeners
judged plausible) are filled; a universe snapshot on a day the archive
rejected is not trusted here either. Merge is per date: existing `preset:*`
rows for that date are replaced, the seven screeners' rows are untouched.

    python3 -m pipeline.tools.backfill_preset_hits --dry-run
    python3 -m pipeline.tools.backfill_preset_hits

Caveats the numbers carry: before 2026-08-14 universe.json shipped ~3,000
rows (not the full 5,600), and `ema21_atr_dist` / `atr_from_sma50` did not
exist -- so 21EMA Watch is empty before then by construction, and every
preset's count is over the smaller file. Recorded, not interpolated.
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from pipeline.screeners.preset_hits import PREFIX, extract_preset_events, load_presets
from pipeline.screeners.ticker_events import EVENT_COLUMNS, load_events, write_events
from pipeline.tools.backfill_ticker_events import snapshot_dates

logger = logging.getLogger(__name__)
_REPO = Path(__file__).resolve().parents[2]
_DEFAULT_CSV = _REPO / 'data' / 'history' / 'ticker_events.csv'


def _git(args: List[str]) -> str:
    return subprocess.run(['git', *args], cwd=_REPO, check=True,
                          capture_output=True, text=True).stdout


def merge_preset_rows(frame: pd.DataFrame, rows: List[Dict[str, Any]]) -> pd.DataFrame:
    """Replace `preset:*` rows for the dates in `rows`; keep everything else."""
    if not rows:
        return frame
    dates = {r['date'] for r in rows}
    is_preset = frame['screener'].astype(str).str.startswith(PREFIX)
    kept = frame[~(frame['date'].astype(str).isin(dates) & is_preset)]
    new = pd.DataFrame([{c: r.get(c) for c in EVENT_COLUMNS} for r in rows])
    out = pd.concat([kept, new], ignore_index=True)
    return out.sort_values(['date', 'ticker', 'screener']).reset_index(drop=True)


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--csv', default=str(_DEFAULT_CSV))
    ap.add_argument('--since', default=None, help='ISO date; only dates >= this')
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

    frame = load_events(args.csv)
    archive_dates = set(frame['date'].astype(str)) if len(frame) else set()
    pairs = snapshot_dates(_git(['log', '--format=%H %ad', '--date=short', '--',
                                 'data/output/universe.json']))
    presets = load_presets()
    rows: List[Dict[str, Any]] = []
    skipped = Counter()
    for sha, date in pairs:
        if args.since and date < args.since:
            continue
        if date not in archive_dates:
            skipped['not in archive'] += 1
            continue
        try:
            payload = json.loads(_git(['show', f'{sha}:data/output/universe.json']))
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            skipped['unreadable'] += 1
            continue
        urows = payload.get('rows') or []
        day = extract_preset_events(urows, presets, date)
        rows.extend(day)
        logger.info("%s  %s universe rows -> %d preset hits", date, len(urows), len(day))

    by = Counter(r['screener'] for r in rows)
    print(f"\n{len(rows)} preset rows over {len({r['date'] for r in rows})} dates; skipped {dict(skipped)}")
    for k, v in sorted(by.items(), key=lambda kv: -kv[1]):
        print(f"  {k:<28}{v}")
    if args.dry_run:
        print("\n(dry run -- nothing written)")
        return 0
    out = merge_preset_rows(frame, rows)
    write_events(out, args.csv)
    print(f"\nWrote {len(out)} rows to {args.csv}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
