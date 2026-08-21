"""Rebuild the portfolio equity curve for a date window from CLEAN data.

2026-08-22 (Andy: the equity curve dips suddenly on 08-18, recovery via MRNA
is real, the dip looks wrong). The page marks positions with GAS->Yahoo
chart prices cached in the browser -- a path with no bar_consistency guard.
This probe rebuilds the same window from the Sheet's trades x the repo's
guarded OHLC store (data/output/tickers/), so a dip that exists here is the
market, and a dip that exists only in the browser is the cache.

Stocks only; options positions are listed but held at zero delta (said in
the output). Prints per-day book value (indexed to the window start) and the
top per-position daily contributions. Runs in CI with the GAS secrets.
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

TICKERS = Path("data/output/tickers")


def closes_for(sym: str) -> dict:
    p = TICKERS / f"{sym.upper()}.json"
    if not p.exists():
        return {}
    try:
        d = json.loads(p.read_text())
    except Exception:  # noqa: BLE001
        return {}
    return {b["date"]: b["close"] for b in (d.get("ohlc_2y") or []) if b.get("close")}


def main(argv=None) -> int:
    start, end = (argv or sys.argv[1:])[:2] if (argv or sys.argv[1:]) else ("2026-08-11", "2026-08-21")
    from pipeline.portfolio.sheets_source import fetch_trades
    trades = fetch_trades()
    opts = []  # fetch_trades reads the Stock Trades tab only; options are a separate tab and excluded by construction
    days = []
    d0 = date.fromisoformat(start)
    while d0 <= date.fromisoformat(end):
        if d0.weekday() < 5:
            days.append(d0.isoformat())
        d0 += timedelta(days=1)
    px = {}
    vals = {}
    contrib = {}
    for ds in days:
        total = 0.0
        for t in trades:
            if str(t.entry_date) > ds:
                continue
            qty = t.current_qty if not t.closed else 0
            if t.closed and str(t.exit_date or "") > ds:
                qty = t.original_qty
            if not qty:
                continue
            sym = t.ticker.upper()
            if sym not in px:
                px[sym] = closes_for(sym)
            series = px[sym]
            c = series.get(ds) or next((series[k] for k in sorted(series, reverse=True) if k <= ds), None)
            if c is None:
                continue
            sign = 1 if getattr(t, "direction", "long") == "long" else -1
            total += sign * qty * c
            contrib.setdefault(ds, {}).setdefault(sym, 0.0)
            contrib[ds][sym] += sign * qty * c
        vals[ds] = total
    base = next((v for v in vals.values() if v), None) or 1.0
    print(f"stocks-only book, indexed to {days[0]} (options tab EXCLUDED by construction):")
    prev = None
    for ds in days:
        v = vals[ds]
        chg = f" {((v - prev) / prev * 100):+6.2f}%" if prev else "        "
        print(f"  {ds}  {v / base * 100:7.2f}{chg}")
        prev = v or prev
    for ds in days:
        if ds not in contrib:
            continue
        prev_d = days[days.index(ds) - 1] if days.index(ds) else None
        if not prev_d or prev_d not in contrib:
            continue
        moves = {s: contrib[ds].get(s, 0) - contrib[prev_d].get(s, 0)
                 for s in set(contrib[ds]) | set(contrib[prev_d])}
        big = sorted(moves.items(), key=lambda kv: abs(kv[1]), reverse=True)[:3]
        tot = vals[prev_d] or 1
        line = "  ".join(f"{s} {v / tot * 100:+.2f}pp" for s, v in big if abs(v / tot) > 0.005)
        if line:
            print(f"  {ds} movers: {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
