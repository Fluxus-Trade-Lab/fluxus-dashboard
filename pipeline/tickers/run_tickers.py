"""CLI for the per-ticker fundamentals fetcher.

Auto-detects tracker-relevant tickers from the latest portfolio CSV
(open positions + closed within last 90 days) and refreshes
data/output/tickers/<SYM>.json for each.

Usage:
    python -m pipeline.tickers.run_tickers                          # auto
    python -m pipeline.tickers.run_tickers --tickers AAOI,MU,PLTR  # explicit
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import date, timedelta
from pathlib import Path

from pipeline.marketcal import market_today

import json
import yfinance as yf

from pipeline.portfolio.trade_parser import parse_csv, find_latest_csv
from pipeline.tickers.ticker_data_fetcher import fetch_ticker_data, write_ticker_json, OUTPUT_DIR, _safe

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)


def relevant_tickers(csv_path: Path, closed_window_days: int = 90) -> list[str]:
    """Open positions + tickers from trades closed in the last N days."""
    trades = parse_csv(csv_path)
    cutoff = market_today() - timedelta(days=closed_window_days)
    seen = set()
    for t in trades:
        # Always include open positions
        if not t.closed and t.current_qty > 0:
            seen.add(t.ticker)
            continue
        # Closed within window?
        ex = t.exit_date
        if ex and ex >= cutoff:
            seen.add(t.ticker)
    return sorted(seen)


def run(tickers: list[str], output_dir: Path, sleep_between: float = 0.3) -> dict:
    """Fetch all tickers. Returns a summary dict."""
    output_dir.mkdir(parents=True, exist_ok=True)
    succeeded = []
    failed = []
    for i, sym in enumerate(tickers, start=1):
        try:
            logger.info(f"[{i}/{len(tickers)}] {sym}")
            data = fetch_ticker_data(sym)
            write_ticker_json(sym, data, output_dir)
            succeeded.append(sym)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"  {sym}: FAILED — {e}")
            failed.append(sym)
        # gentle rate limit
        if sleep_between > 0 and i < len(tickers):
            time.sleep(sleep_between)
    return {'succeeded': succeeded, 'failed': failed, 'total': len(tickers)}


def write_benchmarks(output_dir: Path) -> None:
    """Fetch 1y daily closes for SPY + QQQ for the RS rebased chart."""
    output_dir.mkdir(parents=True, exist_ok=True)
    out: dict = {'fetched_at': None, 'benchmarks': {}}
    from datetime import datetime
    out['fetched_at'] = datetime.utcnow().isoformat(timespec='seconds') + 'Z'
    for sym in ('SPY', 'QQQ'):
        try:
            tk = yf.Ticker(sym)
            hist = tk.history(period='1y', auto_adjust=True)
            out['benchmarks'][sym] = [
                {'date': ts.date().isoformat(), 'close': _safe(row.get('Close'))}
                for ts, row in hist.iterrows()
            ]
            logger.info(f"Benchmark {sym}: {len(out['benchmarks'][sym])} closes")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"benchmark fetch {sym} failed: {e}")
            out['benchmarks'][sym] = []
    path = output_dir / '_benchmarks.json'
    with open(path, 'w') as f:
        json.dump(out, f, indent=2, default=str)
    logger.info(f"Wrote benchmarks to {path}")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description='Per-ticker fundamentals fetcher')
    p.add_argument('--input', type=Path, default=None,
                   help='Portfolio CSV (defaults to latest in data/portfolio/)')
    p.add_argument('--tickers', type=str, default=None,
                   help='Comma-separated explicit ticker list (overrides --input)')
    p.add_argument('--output', type=Path, default=OUTPUT_DIR)
    p.add_argument('--closed-days', type=int, default=90,
                   help='Include tickers closed within N days (default 90)')
    args = p.parse_args(argv)

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(',') if t.strip()]
    else:
        csv = args.input or find_latest_csv(Path('data/portfolio'))
        if not csv or not csv.exists():
            print("ERROR: no portfolio CSV found and no --tickers given", file=sys.stderr)
            sys.exit(1)
        logger.info(f"Auto-detecting tickers from {csv}")
        tickers = relevant_tickers(csv, args.closed_days)

    if not tickers:
        print("ERROR: no tickers to fetch", file=sys.stderr)
        sys.exit(1)

    logger.info(f"Fetching {len(tickers)} tickers → {args.output}")
    summary = run(tickers, args.output)
    print(f"\n✓ Succeeded: {len(summary['succeeded'])}/{summary['total']}")
    if summary['failed']:
        print(f"✗ Failed: {', '.join(summary['failed'])}")

    # Always refresh benchmarks alongside tickers
    write_benchmarks(args.output)


if __name__ == '__main__':
    main()
