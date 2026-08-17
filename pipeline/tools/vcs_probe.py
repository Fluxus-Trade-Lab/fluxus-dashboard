"""Print the VCS v2 port's parts for tickers, in the PROBE table's shape.

Companion to indicators/third_party/oratnek_vcs_probe.pine. Bars: yfinance
daily, auto_adjust=False (TV daily default). --end pins the last session.

Run:  python -m pipeline.tools.vcs_probe AEHR SMCI --end 2026-08-14
"""
from __future__ import annotations

import argparse, sys, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd  # noqa: E402
from pipeline.screeners import vcs as V  # noqa: E402
warnings.filterwarnings("ignore")


def bars_for(t, end):
    import yfinance as yf
    df = yf.download(t, period="420d", interval="1d", auto_adjust=False, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    return df[df.index <= pd.Timestamp(end)] if end else df


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("tickers", nargs="+"); ap.add_argument("--end", default=None)
    a = ap.parse_args()
    for t in a.tickers:
        df = bars_for(t, a.end)
        r = V.vcs(df)
        # recompute the parts the table shows
        h, l, c, v = df["High"], df["Low"], df["Close"], df["Volume"].astype(float)
        tr = V.true_range(h, l, c)
        ratio_atr = (V.pine_sma(tr, 13) / V.pine_sma(tr, 63).clip(lower=1e-6)).iloc[-1]
        ratio_std = (V.pine_stdev(c, 13) / V.pine_stdev(c, 63).clip(lower=1e-6)).iloc[-1]
        vol_ratio = (V.pine_sma(v, 5) / V.pine_sma(v, 50).clip(lower=1.0)).iloc[-1]
        eff = (abs(c - c.shift(13)) / V.pine_sum(tr, 13).clip(lower=1e-6)).iloc[-1]
        f4 = lambda x: "na" if x is None or x != x else f"{x:.4f}"
        print(f"\n== {t} ==")
        for k, val in [("bar date", df.index[-1].strftime("%Y-%m-%d")), ("ratioATR", f4(ratio_atr)),
                       ("ratioStd", f4(ratio_std)), ("volRatio", f4(vol_ratio)), ("efficiency", f4(eff)),
                       ("physics", f4(r.physics_last)), ("smooth", f4(r.smooth_last)),
                       ("daysTight", r.days_tight), ("isHigherLow", str(r.higher_low).lower()),
                       ("total", f4(r.total)), ("VCS", f4(r.score))]:
            print(f"  {k:<12} {val}")


if __name__ == "__main__":
    main()
