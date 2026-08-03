#!/usr/bin/env python3
"""Refresh 2-year daily OHLC for the AI-Coach Diagnosis case-study tickers.

The per-trade case-study cards (AI Coach → Analytics → Diagnosis) compute
point-in-time 20EMA / 50SMA / 200SMA + ATR14 at each trade's entry date. That
needs (a) history fresh enough to cover the entry and (b) ~200 trading days of
lookback before it. The daily ticker files only carry 1y OHLC (`ohlc_1y`), which
is too shallow for a 200-SMA at a January entry and often stale.

This writes an `ohlc_2y` array into each ticker JSON (merging, so fundamentals /
news / analyst blocks are preserved). Public market data only — no trade data.

Usage:
    python scripts/refresh_case_study_ohlc.py                # default 7 tickers
    python scripts/refresh_case_study_ohlc.py NVDA AMD ...   # explicit list
"""
import csv
import glob
import json
import sys
from datetime import datetime, timezone

from pipeline.marketcal import market_today
from pathlib import Path

import yfinance as yf

OUTPUT_DIR = Path("data/output/tickers")
LOG_GLOB = "data/portfolio/portfolio_*.csv"
FALLBACK = ["BABA", "CRCL", "LEU", "DOCN", "BE", "ALAB", "ACMR"]


def top_case_study_tickers(n=4):
    """Derive the tickers of the n biggest winners + n biggest losers (by $ P&L)
    from the latest portfolio log, so the set tracks the current case studies."""
    logs = sorted(glob.glob(LOG_GLOB))
    if not logs:
        return FALLBACK
    header, rows = None, []
    for line in csv.reader(open(logs[-1])):
        if not line or line[0] == "_meta":
            continue
        if line[0] == "Ticker":
            header = line
            continue
        rows.append(dict(zip(header, line)))

    def num(x):
        x = (x or "").strip()
        return float(x) if x else None

    trades = []
    for r in rows:
        e, d = num(r["Entry Price"]), r["Direction"]
        pnl = 0.0
        for i in (1, 2, 3):
            p, q = num(r.get(f"Trim{i} Price")), num(r.get(f"Trim{i} Qty"))
            if p is not None and q:
                pnl += (p - e) * q if d == "long" else (e - p) * q
        trades.append((pnl, r["Ticker"]))
    trades.sort()
    picks = [t for _, t in trades[:n]] + [t for _, t in trades[-n:]]
    seen, out = set(), []
    for t in picks:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out or FALLBACK


def fetch_ohlc_2y(symbol: str) -> list[dict]:
    tk = yf.Ticker(symbol)
    hist = tk.history(period="2y", auto_adjust=True)
    if hist is None or hist.empty:
        return []
    out = []
    for ts, row in hist.iterrows():
        c = row.get("Close")
        if c is None or c != c:  # NaN guard
            continue
        out.append({
            "date": ts.date().isoformat(),
            "open": round(float(row["Open"]), 4),
            "high": round(float(row["High"]), 4),
            "low": round(float(row["Low"]), 4),
            "close": round(float(row["Close"]), 4),
            "volume": float(row["Volume"]),
        })
    return out


def _local_last_date(sym: str):
    """Last date already stored locally (ohlc_2y), or None. Check-before-fetch:
    the daily ticker pipeline already writes ohlc_2y, so a fresh file needs no refetch."""
    path = OUTPUT_DIR / f"{sym.upper()}.json"
    if not path.exists():
        return None
    try:
        bars = json.load(open(path)).get("ohlc_2y")
        return bars[-1]["date"] if bars else None
    except (ValueError, OSError, KeyError, IndexError):
        return None


def main(tickers: list[str], force: bool = False, fresh_within=None) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for sym in tickers:
        sym = sym.upper()
        if not force and fresh_within and (last := _local_last_date(sym)) and last >= fresh_within:
            print(f"  {sym}: already fresh (through {last}) — skipped")
            continue
        bars = fetch_ohlc_2y(sym)
        if not bars:
            print(f"  {sym}: no data (skipped)")
            continue
        path = OUTPUT_DIR / f"{sym}.json"
        data = {}
        if path.exists():
            try:
                data = json.load(open(path))
            except (ValueError, OSError):
                data = {}
        data.setdefault("ticker", sym)
        data["ohlc_2y"] = bars
        data["ohlc_2y_fetched_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        json.dump(data, open(path, "w"), separators=(",", ":"))
        print(f"  {sym}: {len(bars)} bars {bars[0]['date']} → {bars[-1]['date']}")


if __name__ == "__main__":
    from datetime import date, timedelta
    argv = [a for a in sys.argv[1:] if a != "--force"]
    force = "--force" in sys.argv
    tickers = argv or top_case_study_tickers()
    # A file whose last bar is within ~4 calendar days is treated as fresh (weekends).
    fresh_cutoff = (market_today() - timedelta(days=4)).isoformat()
    print(f"Refreshing 2y OHLC for: {', '.join(tickers)}{' (force)' if force else ''}")
    main(tickers, force=force, fresh_within=fresh_cutoff)
