"""Print our breadth %>MA series for manual TradingView cross-checking.

Usage:  python3 -m pipeline.tools.validate_breadth_tv [--days 10] [--csv PATH]

Compare against TradingView symbols (read via the local TV MCP or the app):
  S5TH / MMTH  — % of S&P 500 / all stocks above 200-day MA
  S5FI / MMFI  — above 50-day
  S5TW / MMTW  — above 20-day

Levels WILL differ (different universes); direction and turning points should
agree. If direction disagrees for several days, investigate our pipeline first.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pipeline.screeners.breadth_store import load_archive

_DEFAULT_CSV = Path(__file__).resolve().parents[2] / 'data' / 'history' / 'breadth_archive.csv'


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--days', type=int, default=10)
    parser.add_argument('--csv', default=str(_DEFAULT_CSV))
    args = parser.parse_args(argv)

    frame = load_archive(args.csv).tail(args.days)
    print(f"{'date':<12}{'src':<10}{'%>200':>8}{'%>50':>8}{'%>20':>8}{'T2108':>8}")
    for _, r in frame.iterrows():
        print(f"{r['date']:<12}{r['source']:<10}"
              f"{float(r['pct_above_200sma']):>8.1f}{float(r['pct_above_50sma']):>8.1f}"
              f"{float(r['pct_above_20sma']):>8.1f}{float(r['t2108']):>8.1f}")
    print("\nCompare vs TV: S5TH/MMTH (200), S5FI/MMFI (50), S5TW/MMTW (20).")
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
