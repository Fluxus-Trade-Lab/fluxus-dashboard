"""Print the Structure Pivot port's state for tickers, in the PROBE table's shape.

Golden-check companion to ``indicators/third_party/oratnek_asp_probe.pine``:
paste that script into TradingView (web), put it on a DAILY chart of the same
tickers, read the yellow table, and compare against this output row by row.

Bars: yfinance daily, ``auto_adjust=False`` -- split-adjusted only, like a
TradingView daily chart with dividend adjustment OFF (its default). With
``auto_adjust=True`` every price shifts by the dividend factor and nothing
lines up. ``--end`` pins the last bar so both sides look at the same session.

Run:  python -m pipeline.tools.structure_pivot_probe AEHR SMCI CRWD --end 2026-08-14
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd  # noqa: E402

from pipeline.screeners import structure_pivot as SP  # noqa: E402

warnings.filterwarnings("ignore")


def bars_for(ticker: str, end: str | None, lookback_days: int = 420) -> pd.DataFrame:
    import yfinance as yf
    df = yf.download(ticker, period=f"{lookback_days}d", interval="1d",
                     auto_adjust=False, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    df = df.rename(columns=str.lower)[["open", "high", "low", "close"]].dropna()
    if end:
        df = df[df.index <= pd.Timestamp(end)]
    return df


def f4(v):
    return "na" if v is None else f"{v:.4f}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("tickers", nargs="+")
    ap.add_argument("--end", default=None, help="last session to include (YYYY-MM-DD)")
    a = ap.parse_args()
    for t in a.tickers:
        df = bars_for(t, a.end)
        r = SP.run(df)
        n = len(df)
        w = r.winner
        rows = [
            ("symbol", t),
            ("bar date", df.index[-1].strftime("%Y-%m-%d")),
            ("setup", str(bool(r.setup)).lower() if r.setup is not None else "na"),
            ("len", str(w.len) if w else "na"),
            ("LL", f4(w.prev_p if w else None)),
            ("LL idx-from-end", "na" if not w or w.prev_idx is None else str(n - 1 - w.prev_idx)),
            ("HL", f4(w.curr_p if w else None)),
            ("HL idx-from-end", "na" if not w or w.curr_idx is None else str(n - 1 - w.curr_idx)),
            ("1st", f4(r.pivot_1st)),
            ("2nd", f4(r.pivot_2nd)),
            ("TP1", f4(r.tp1)),
            ("TP2", f4(r.tp2)),
            ("phase", str(r.phase) if r.setup else "1"),
            ("stop", f4(r.stop)),
            ("MA21low", f4(r.ma)),
            ("signal", r.signal or "none"),
        ]
        print(f"\n== {t} ==")
        for k, v in rows:
            print(f"  {k:<16} {v}")


if __name__ == "__main__":
    main()
