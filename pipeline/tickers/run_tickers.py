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


def heat_tickers(heating_up_path: Path, top_n: int = 25) -> list[str]:
    """Top N tickers from data/output/heating_up.json (rows already sorted by score
    descending). Pure and total: returns [] on any missing/malformed input, never raises.
    heating_up.json is optional input — a failure here must never break a fetch run.
    """
    if top_n <= 0:
        return []
    try:
        with open(heating_up_path) as f:
            payload = json.load(f)
    except (OSError, ValueError):
        return []

    if not isinstance(payload, dict):
        return []
    rows = payload.get('rows')
    if not isinstance(rows, list):
        return []

    out: list[str] = []
    seen: set[str] = set()
    for row in rows:
        if len(out) >= top_n:
            break
        if not isinstance(row, dict):
            continue
        ticker = row.get('ticker')
        if not ticker or not isinstance(ticker, str):
            continue
        sym = ticker.strip().upper()
        if not sym or sym in seen:
            continue
        seen.add(sym)
        out.append(sym)
    return out


def merge_ticker_sources(portfolio: list[str], heat: list[str]) -> list[str]:
    """Union portfolio + heat tickers, portfolio first, de-duplicated case-insensitively,
    order preserved (portfolio names fetch first if a run is interrupted)."""
    out: list[str] = []
    seen: set[str] = set()
    for sym in list(portfolio) + list(heat):
        key = sym.upper()
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def _relevant_from_trades(trades, closed_window_days: int) -> list[str]:
    """Open positions + tickers from trades closed in the last N days."""
    cutoff = market_today() - timedelta(days=closed_window_days)
    seen = set()
    for t in trades:
        if not t.closed and t.current_qty > 0:
            seen.add(t.ticker)
            continue
        ex = t.exit_date
        if ex and ex >= cutoff:
            seen.add(t.ticker)
    return sorted(seen)


def _sheet_trades():
    """Live trades from the Sheet (indirection so tests can stub it)."""
    from pipeline.portfolio.sheets_source import fetch_trades
    return fetch_trades()


def relevant_tickers_from_sheet(closed_window_days: int = 90) -> list[str] | None:
    """Same relevance rule as `relevant_tickers`, read straight off the Sheet
    the browser writes to. Returns None (not []) when the Sheet is
    unavailable -- no credentials, GAS cold-start timeout -- so the caller can
    fall back rather than fetch nothing and call it done.

    Why: the OHLC store was refreshed by hand from a CSV export; every name
    opened after the last export had no OHLC and trade_postmortem skipped it
    (7/355 on 2026-08-16, all of them current open positions).
    """
    from pipeline.portfolio.sheets_source import SheetsUnavailable
    try:
        trades = _sheet_trades()
    except SheetsUnavailable as e:
        logger.warning(f"Sheet unavailable ({e}); portfolio tickers not refreshed from Sheet")
        return None
    return _relevant_from_trades(trades, closed_window_days)


def relevant_tickers(csv_path: Path, closed_window_days: int = 90) -> list[str]:
    """Open positions + tickers from trades closed in the last N days (CSV)."""
    return _relevant_from_trades(parse_csv(csv_path), closed_window_days)


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
    p.add_argument('--source', choices=['auto', 'sheet', 'csv'], default='auto',
                   help='Portfolio tickers from the live Sheet, the CSV export, or Sheet '
                        'with CSV fallback (default auto)')
    p.add_argument('--output', type=Path, default=OUTPUT_DIR)
    p.add_argument('--closed-days', type=int, default=90,
                   help='Include tickers closed within N days (default 90)')
    p.add_argument('--heat-top', type=int, default=25,
                   help='Include the top N Heating Up tickers (default 25; 0 disables)')
    p.add_argument('--no-heat', action='store_true',
                   help='Disable Heating Up tickers entirely (equivalent to --heat-top 0)')
    p.add_argument('--heating-up', type=Path, default=Path('data/output/heating_up.json'),
                   help='Path to heating_up.json (default data/output/heating_up.json)')
    args = p.parse_args(argv)

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(',') if t.strip()]
        portfolio_count = len(tickers)
        heat_only_count = 0
    else:
        portfolio_list = None
        if args.source in ('auto', 'sheet'):
            portfolio_list = relevant_tickers_from_sheet(args.closed_days)
            if portfolio_list is not None:
                logger.info(f"Portfolio tickers from the Sheet: {len(portfolio_list)}")
            elif args.source == 'sheet':
                print("ERROR: Sheet unavailable and --source sheet was requested", file=sys.stderr)
                sys.exit(1)
        if portfolio_list is None:
            csv = args.input or find_latest_csv(Path('data/portfolio'))
            if not csv or not csv.exists():
                print("ERROR: no portfolio CSV found and no --tickers given", file=sys.stderr)
                sys.exit(1)
            logger.info(f"Auto-detecting tickers from {csv}")
            portfolio_list = relevant_tickers(csv, args.closed_days)
        heat_top = 0 if args.no_heat else args.heat_top
        heat_list = heat_tickers(args.heating_up, heat_top)
        tickers = merge_ticker_sources(portfolio_list, heat_list)
        portfolio_count = len(portfolio_list)
        heat_only_count = len(tickers) - portfolio_count

    if not tickers:
        print("ERROR: no tickers to fetch", file=sys.stderr)
        sys.exit(1)

    if portfolio_count and heat_only_count:
        logger.info(
            f"Fetching {len(tickers)} tickers "
            f"({portfolio_count} portfolio + {heat_only_count} heat-only) → {args.output}"
        )
    else:
        logger.info(f"Fetching {len(tickers)} tickers → {args.output}")
    summary = run(tickers, args.output)
    print(f"\n✓ Succeeded: {len(summary['succeeded'])}/{summary['total']}")
    if summary['failed']:
        print(f"✗ Failed: {', '.join(summary['failed'])}")

    # Always refresh benchmarks alongside tickers
    write_benchmarks(args.output)


if __name__ == '__main__':
    main()
