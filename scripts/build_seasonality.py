#!/usr/bin/env python3
"""Build the SPX (or any index) monthly-seasonality reference.

Pulls ~15y of daily closes from IBKR ONCE, caches the computed stats to
data/reference/seasonality_<SYMBOL>.json, and renders a shareable HTML view
next to it. Re-run only to refresh (e.g. yearly) — everything downstream reads
the JSON, so nothing recomputes the history at read time.

Usage:
    .venv/bin/python scripts/build_seasonality.py --symbol SPX --years 15 --focus 8
    .venv/bin/python scripts/build_seasonality.py --render-only        # rebuild HTML from cached JSON
"""
import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.reference.seasonality import monthly_seasonality
from pipeline.reference.render import render_seasonality_html
from pipeline.marketcal import market_now

OUT_DIR = Path("data/reference")


def _pull_daily_closes(symbol: str, years: int) -> pd.Series:
    from ib_async import IB, Index
    ib = IB()
    for port in (7496, 4001, 4002):
        try:
            ib.connect("127.0.0.1", port, clientId=91, timeout=15)
            break
        except Exception:
            continue
    if not ib.isConnected():
        raise ConnectionError("no IBKR endpoint on 7496/4001/4002 — is TWS logged in?")
    try:
        idx = Index(symbol, "CBOE")
        ib.qualifyContracts(idx)
        bars = ib.reqHistoricalData(
            idx, endDateTime="", durationStr=f"{years} Y",
            barSizeSetting="1 day", whatToShow="TRADES", useRTH=True, formatDate=1,
        )
        if not bars:
            raise RuntimeError("no bars returned")
        s = pd.Series({pd.Timestamp(b.date): b.close for b in bars}).sort_index()
        s.index.name = "date"
        return s
    finally:
        ib.disconnect()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="SPX")
    ap.add_argument("--years", type=int, default=15)
    ap.add_argument("--focus", type=int, default=8, help="Calendar month to detail (1-12).")
    ap.add_argument("--render-only", action="store_true",
                    help="Rebuild HTML from the cached JSON without pulling IBKR.")
    ap.add_argument("--csv", help="Compute from a local daily CSV (date,close) instead of IBKR.")
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / f"seasonality_{args.symbol}.json"
    html_path = OUT_DIR / f"seasonality_{args.symbol}.html"
    now = market_now()

    if args.render_only:
        if not json_path.exists():
            sys.exit(f"no cache at {json_path} — run without --render-only first")
        data = json.loads(json_path.read_text())
        print(f"loaded cache: {json_path}")
    else:
        if args.csv:
            print(f"reading {args.symbol} daily closes from {args.csv} ...")
            df = pd.read_csv(args.csv, parse_dates=["date"])
            close = df.set_index("date")["close"].sort_index()
        else:
            print(f"pulling {args.years}y of {args.symbol} daily closes from IBKR ...")
            close = _pull_daily_closes(args.symbol, args.years)
        data = monthly_seasonality(close)
        data["symbol"] = args.symbol
        data["generated_at"] = now.isoformat(timespec="seconds")
        data["focus_month"] = args.focus
        json_path.write_text(json.dumps(data, indent=2))
        print(f"cached: {json_path}  ({data['history']['start']} → {data['history']['end']})")

    data.setdefault("focus_month", args.focus)
    html = render_seasonality_html(data, args.symbol, data.get("generated_at", now.isoformat(timespec="seconds")))
    html_path.write_text(html)
    print(f"rendered: {html_path}")
    # quick console recap of the focus month
    fm = next((m for m in data["months"] if m["month"] == data["focus_month"]), None)
    if fm:
        print(f"\n{fm['name']}: mean {fm['mean_pct']:+.2f}%  median {fm['median_pct']:+.2f}%  "
              f"win {fm['win_pct']:.0f}%  stdev {fm['stdev_pct']:.2f}%  rvol {fm['rvol_pct']:.1f}%")


if __name__ == "__main__":
    main()
