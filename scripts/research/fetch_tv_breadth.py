"""Fetch long-history exchange breadth series from TradingView (tvdatafeed,
anonymous websocket -- no login, no API key) and store them as CSVs.

Series (INDEX: namespace unless noted):
    ADVN / DECN   NYSE advancing / declining issues     2007-09-28 ->
    ADVQ / DECQ   Nasdaq advancing / declining issues   2007-09-28 ->
    HIGN / LOWN   NYSE new 52w highs / lows             2001-06-05 ->
    HIGQ / LOWQ   Nasdaq new 52w highs / lows           2001-06-05 ->
    USI:ADVN.NY / USI:ADVN.NQ  old-vintage advancing series back to 1971;
                  stored for inspection -- date structure unverified.

Output: data/reference/breadth_tv/<EXCHANGE>_<SYMBOL>.csv  (date,close)
Re-run any time; full overwrite (the feed is the source of truth).
Provenance: TradingView anonymous feed; counts are exchange-reported issues,
NOT our screener universe. 2026-08-21 established for the Turin E1/Phase-2 work.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from tvDatafeed import Interval, TvDatafeed

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/reference/breadth_tv"

SERIES = [
    ("ADVN", "INDEX"), ("DECN", "INDEX"), ("ADVQ", "INDEX"), ("DECQ", "INDEX"),
    ("HIGN", "INDEX"), ("LOWN", "INDEX"), ("HIGQ", "INDEX"), ("LOWQ", "INDEX"),
    ("ADVN.NY", "USI"), ("ADVN.NQ", "USI"),
    ("S5TH", "INDEX"), ("MMTH", "INDEX"),
    ("BAMLH0A0HYM2", "FRED"),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    tv = TvDatafeed()
    failures = []
    for sym, ex in SERIES:
        ok = False
        for attempt in range(3):
            try:
                df = tv.get_hist(symbol=sym, exchange=ex,
                                 interval=Interval.in_daily, n_bars=20000)
                if df is None or len(df) == 0:
                    raise RuntimeError("empty")
                out = df[["close"]].copy()
                out.index = out.index.normalize().date
                out.index.name = "date"
                path = OUT / f"{ex}_{sym.replace('.', '_')}.csv"
                out.to_csv(path)
                print(f"{ex}:{sym:10s} n={len(out):5d}  {out.index[0]} -> {out.index[-1]}  -> {path.name}")
                ok = True
                break
            except Exception as e:  # transient websocket timeouts are common
                time.sleep(3 * (attempt + 1))
                last = str(e)[:60]
        if not ok:
            failures.append((f"{ex}:{sym}", last))
            print(f"{ex}:{sym:10s} FAILED after 3 attempts: {last}")
    if failures:
        print(f"\n{len(failures)} series failed -- rerun; partial files are fine (full overwrite per series).")
        return 1
    print("\nall series stored.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
