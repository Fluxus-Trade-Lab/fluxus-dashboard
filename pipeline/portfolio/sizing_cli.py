"""CLI for the volatility-adjusted sizing analyzer.

Usage:
    python -m pipeline.portfolio.sizing_cli
"""
from __future__ import annotations

import argparse
import logging
from datetime import date, timedelta
from pathlib import Path

from pipeline.marketcal import market_today
from pipeline.portfolio.trade_parser import parse_csv, find_latest_csv
from pipeline.portfolio.ohlc_cache import fetch_ohlc
from pipeline.portfolio.sizing_analyzer import (
    build_trade_sizings, summarize_by_atr, summarize_by_risk_R,
    find_outliers, write_sizing_report,
)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)


def run(input_path: Path, output_md: Path) -> None:
    logger.info(f"Reading trades from {input_path}")
    trades = parse_csv(input_path)
    closed_with_R = [t for t in trades if t.closed and t.R_dollars > 0]
    logger.info(f"Loaded {len(trades)} total · {len(closed_with_R)} closed-with-R")

    # Fetch OHLC for each unique ticker (for entry ATR)
    unique_tickers = sorted({t.ticker for t in closed_with_R})
    logger.info(f"Fetching OHLC for {len(unique_tickers)} unique tickers...")
    ohlc_by_ticker = {}
    for tk in unique_tickers:
        subset = [t for t in closed_with_R if t.ticker == tk]
        s = min(t.entry_date for t in subset) - timedelta(days=60)
        e = max(t.exit_date or t.entry_date for t in subset) + timedelta(days=5)
        df = fetch_ohlc(tk, s, e)
        if df is not None and len(df):
            ohlc_by_ticker[tk] = df

    sizings = build_trade_sizings(closed_with_R, ohlc_by_ticker)
    by_atr = summarize_by_atr(sizings)
    by_risk = summarize_by_risk_R(sizings)
    outliers = find_outliers(sizings)

    output_md.parent.mkdir(parents=True, exist_ok=True)
    write_sizing_report(sizings, by_atr, by_risk, outliers, output_md)
    print(f"\n✓ Sizing report: {output_md}")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description='Position-sizing analyzer')
    p.add_argument('--input', type=Path, default=None)
    p.add_argument('--output', type=Path, default=None)
    args = p.parse_args(argv)

    if args.input is None:
        args.input = find_latest_csv(Path('data/portfolio'))
        if args.input is None:
            raise SystemExit("ERROR: no CSV found in data/portfolio/")
    if args.output is None:
        today = market_today().isoformat()
        args.output = Path(f'docs/portfolio-sizing-{today}.md')

    run(args.input, args.output)


if __name__ == '__main__':
    main()
