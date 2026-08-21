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
    args = (argv or sys.argv[1:])
    start, end = args[:2] if len(args) >= 2 else ("2026-08-11", "2026-08-21")
    from pipeline.portfolio.sheets_source import fetch_trades
    trades = fetch_trades()
    days = []
    d0 = date.fromisoformat(start)
    while d0 <= date.fromisoformat(end):
        if d0.weekday() < 5:
            days.append(d0.isoformat())
        d0 += timedelta(days=1)
    px = {}

    def close(sym, ds):
        if sym not in px:
            px[sym] = closes_for(sym)
        series = px[sym]
        return series.get(ds) or next((series[k] for k in sorted(series, reverse=True) if k <= ds), None)

    print("held-overnight mark-to-market only (entries/exits/cash excluded; options tab excluded):")
    for i in range(1, len(days)):
        p_, d_ = days[i - 1], days[i]
        pnl = 0.0
        gross = 0.0
        moves = {}
        for t in trades:
            if str(t.entry_date) > p_:
                continue
            if t.closed and str(t.exit_date or "9999") <= d_ if False else False:
                pass
            ex = str(t.exit_date) if (t.closed and t.exit_date) else None
            if ex is not None and ex <= p_:      # fully closed before the pair
                continue
            qty = t.current_qty if not t.closed else t.original_qty
            if not qty:
                continue
            sym = t.ticker.upper()
            c0, c1 = close(sym, p_), close(sym, d_)
            if c0 is None or c1 is None:
                continue
            sign = 1 if getattr(t, "direction", "long") == "long" else -1
            pnl += sign * qty * (c1 - c0)
            gross += qty * c0
            moves[sym] = moves.get(sym, 0.0) + sign * qty * (c1 - c0)
        if not gross:
            continue
        big = sorted(moves.items(), key=lambda kv: abs(kv[1]), reverse=True)[:4]
        line = "  ".join(f"{s_} {v / gross * 100:+.2f}pp" for s_, v in big if abs(v / gross) > 0.002)
        print(f"  {d_}  book day P&L {pnl / gross * 100:+6.2f}%   | {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
