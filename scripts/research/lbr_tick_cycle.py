"""Python twin of indicators/fluxus-lbr-tick-cycle.pine -- Linda Raschke's
intermediate-cycle indicator: n-day SMAs of NYSE TICK daily high/close/low.

TV's TICK daily bars are close-only (high==low==close), so the true daily
extremes are rebuilt from hourly bars (a bar's high/low contain the intrabar
extreme, so max/min over the day's hourly bars IS the daily extreme on this
feed). Derivation + golden check vs her printed 502/-27/-433: see the .txt.

Usage:  python3 scripts/research/lbr_tick_cycle.py [--n 15]
Output: data/reference/breadth_tv/USI_TICK_hlc.csv (rebuilt daily H/L/C,
        full overwrite) + printed current readings/zone state.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/reference/breadth_tv/USI_TICK_hlc.csv"

UP_TH, DN_TH = 650.0, -650.0  # TV-feed calibrated (her chart's +-500 x feed scale)


def main() -> int:
    n = 15
    if "--n" in sys.argv:
        n = int(sys.argv[sys.argv.index("--n") + 1])
    from tvDatafeed import Interval, TvDatafeed
    tv = TvDatafeed()
    h = tv.get_hist(symbol="TICK", exchange="USI", interval=Interval.in_1_hour, n_bars=5000)
    if h is None or len(h) == 0:
        print("lbr_tick_cycle: no TICK data")
        return 1
    h = h.copy()
    h["day"] = h.index.normalize()
    daily = h.groupby("day").agg(high=("high", "max"), low=("low", "min"), close=("close", "last"))
    daily.index = daily.index.date
    daily.index.name = "date"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    daily.to_csv(OUT)

    m_hi = daily["high"].rolling(n).mean().iloc[-1]
    m_cl = daily["close"].rolling(n).mean().iloc[-1]
    m_lo = daily["low"].rolling(n).mean().iloc[-1]
    zone = "SELL zone" if m_hi >= UP_TH else ("BUY zone" if m_lo <= DN_TH else "neutral")
    print(f"as of {daily.index[-1]}  (n={n} SMA, {len(daily)} sessions rebuilt)")
    print(f"  MA(high)  {m_hi:8.1f}")
    print(f"  MA(close) {m_cl:8.1f}")
    print(f"  MA(low)   {m_lo:8.1f}")
    print(f"  zone: {zone}  (thresholds {UP_TH:+.0f}/{DN_TH:+.0f}, TV-feed calibrated)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
