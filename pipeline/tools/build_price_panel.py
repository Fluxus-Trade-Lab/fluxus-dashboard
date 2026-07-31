"""Build the OHLC price panel the sequence research needs.

The event archive records what fired and when, never what happened next.
This tool downloads daily bars for every ticker the archive mentions (plus
SPY) across the archive window, with lead-in for ATR warm-up and tail for
the longest forward horizon.

Coverage is REPORTED, not hidden: delisted and renamed tickers fail to
download, and those failures skew toward losers — dropping them silently
would bias every downstream result upward.

Not part of the cron. Run manually:
    python3 -m pipeline.tools.build_price_panel
    python3 -m pipeline.tools.build_price_panel --refresh
"""

from __future__ import annotations

import argparse
import json
import logging
import pickle
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from pipeline.screeners.ticker_events import load_events

logger = logging.getLogger(__name__)

_REPO = Path(__file__).resolve().parents[2]
_DEFAULT_EVENTS = _REPO / 'data' / 'history' / 'ticker_events.csv'
_DEFAULT_CACHE = _REPO / '.cache' / 'price_panel.pkl'
_COVERAGE = _REPO / 'data' / 'research' / 'price_coverage.json'

LEAD_IN_DAYS = 60      # ATR(14) warm-up plus slack
TAIL_DAYS = 25         # longest forward horizon (21) plus slack
BATCH_SIZE = 200


def panel_tickers(events: pd.DataFrame) -> List[str]:
    """Sorted distinct tickers in the archive, plus SPY."""
    if len(events) == 0:
        return ['SPY']
    return sorted(set(events['ticker'].astype(str)) | {'SPY'})


def coverage_report(requested: List[str], returned: List[str]) -> Dict[str, Any]:
    """What we asked for vs what we got — the survivorship disclosure."""
    missing = sorted(set(requested) - set(returned))
    return {'requested': len(requested), 'returned': len(returned),
            'missing': missing}


# ── network (not unit-tested) ────────────────────────────────────────

def _download(tickers: List[str], start: str, end: str) -> Dict[str, pd.DataFrame]:
    import yfinance as yf
    panel: Dict[str, pd.DataFrame] = {}
    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i:i + BATCH_SIZE]
        logger.info("Downloading %d-%d of %d", i, i + len(batch), len(tickers))
        data = yf.download(batch, start=start, end=end, group_by='ticker',
                           auto_adjust=True, progress=False, threads=True)
        for t in batch:
            try:
                frame = data[t][['Open', 'High', 'Low', 'Close']].dropna(how='all')
            except (KeyError, TypeError):
                continue
            if frame.empty:
                continue
            frame.index = pd.DatetimeIndex(frame.index).tz_localize(None)
            panel[t] = frame.sort_index()
    return panel


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--cache', default=str(_DEFAULT_CACHE))
    parser.add_argument('--events', default=str(_DEFAULT_EVENTS))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

    cache = Path(args.cache)
    if cache.exists() and not args.refresh:
        print(f"Cache already present at {cache} — use --refresh to rebuild.")
        return 0

    events = load_events(args.events)
    if len(events) == 0:
        print("Event archive is empty — nothing to download.")
        return 1

    tickers = panel_tickers(events)
    first, last = str(events['date'].min()), str(events['date'].max())
    start = (pd.Timestamp(first) - pd.tseries.offsets.BDay(LEAD_IN_DAYS)).strftime('%Y-%m-%d')
    end = (pd.Timestamp(last) + pd.tseries.offsets.BDay(TAIL_DAYS)).strftime('%Y-%m-%d')
    logger.info("Panel: %d tickers, %s .. %s", len(tickers), start, end)

    panel = _download(tickers, start, end)
    rep = coverage_report(tickers, sorted(panel))

    spy = panel.get('SPY')
    if spy is not None:
        # A duplicated date makes spy_close.loc[date] return a Series instead
        # of a scalar, and every excess-return measurement blows up. Fail here,
        # where the cause is visible, rather than 3,829 tickers downstream.
        assert spy.index.is_unique, (
            "SPY has duplicate dates in the downloaded panel — refusing to "
            "write a cache that would break outcome measurement.")

    cache.parent.mkdir(parents=True, exist_ok=True)
    with open(cache, 'wb') as f:
        pickle.dump(panel, f)
    _COVERAGE.parent.mkdir(parents=True, exist_ok=True)
    _COVERAGE.write_text(json.dumps(rep, indent=2), encoding='utf-8')

    print(f"\nPanel written to {cache}")
    print(f"Coverage: {rep['returned']}/{rep['requested']} tickers "
          f"({len(rep['missing'])} missing — see {_COVERAGE})")
    if 'SPY' not in panel:
        print("WARNING: SPY missing — excess returns cannot be computed.")
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
