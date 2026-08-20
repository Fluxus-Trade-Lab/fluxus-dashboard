"""Tightness & reversal patterns -- definitions and forward test.

2026-08-20 (Andy: "tightness 怎么去策略是个学问…VCS / Minervini VCP / IBD mini
coil / oops reversal 这些都是知识,你可以去掌握测试").

Already judged elsewhere (not re-run here): our VCS score (validation: no
standalone edge, ~baseline) and the Minervini VCP detector (old7 study:
+2.9%/20d, 64% win, the one stable positive of the seven). This tool tests
the three we never had:

  3WT   O'Neil 3-weeks-tight: three consecutive weekly closes inside a 1.5%
        band, in an uptrend (>50sma, within 15% of 52wh). His usage: an
        ADD-ON point for a stock already owned, buy the tight-range breakout.
        Fires both the pattern day (3rd Friday) and the breakout day.
  COIL  "mini coil", our operationalization (IBD's is not crisply public):
        5-session total range <= 5% of close, within 3% of the 20d high,
        >50sma. Fires the day the coil completes.
  OOPS  Larry Williams' Oops (bullish): today OPENS below yesterday's LOW
        (panic gap), then trades back up through yesterday's low -- his
        entry is a buy stop AT yesterday's low intraday. Close-to-close
        approximation: fire when open < prior low and close > prior low;
        entry = today's close (worse than his fill; noted).
  CTR   generic contraction ratio: last-5-session range <= half of the
        prior-15-session range, within 5% of the 20d high, >50sma.

Forward stats: close-to-close +5/+10/+20 sessions, vs the same-day pool
median (every name with bars that day) -- the harness the validation used.
Bars: event_bars.pkl (names that fired signals in 2026; selection bias noted
in the write-up).

    python -m pipeline.tools.tightness_study --bars data/research/scanner_validation_2026-08/event_bars.pkl \\
        --out data/research/tightness_2026-08/fires.csv
"""

from __future__ import annotations

import argparse
import pickle
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

HORIZONS = (5, 10, 20)


def detect(hist: pd.DataFrame) -> List[dict]:
    """All pattern fires for one ticker. Pure; daily bars in, events out."""
    c, h, l, o = hist["Close"], hist["High"], hist["Low"], hist["Open"]
    n = len(c)
    if n < 120:
        return []
    sma50 = c.rolling(50).mean()
    hi20 = c.rolling(20).max()
    hi52 = c.rolling(min(252, n), min_periods=60).max()
    wk = c.resample("W-FRI").last().dropna()
    wk_tight_end = set()
    for k in range(3, len(wk)):
        w3 = wk.iloc[k - 2:k + 1]
        if (w3.max() - w3.min()) / w3.iloc[-1] <= 0.015:
            wk_tight_end.add(wk.index[k])
    out = []
    tight_rng_hi = None
    for i in range(60, n):
        dt = c.index[i]
        px = float(c.iloc[i])
        up = not pd.isna(sma50.iloc[i]) and px > float(sma50.iloc[i])
        near_hi = px >= 0.85 * float(hi52.iloc[i])
        # 3WT pattern day: this session is the Friday that completes the band
        if dt in wk_tight_end and up and near_hi:
            out.append({"pattern": "3WT_pattern", "date": dt})
            tight_rng_hi = float(c.iloc[max(0, i - 15):i + 1].max())
        # 3WT breakout: close clears the tight range high within 15 sessions
        if tight_rng_hi is not None and px > tight_rng_hi:
            out.append({"pattern": "3WT_breakout", "date": dt})
            tight_rng_hi = None
        # COIL
        if i >= 5 and up:
            rng5 = float(h.iloc[i - 4:i + 1].max() - l.iloc[i - 4:i + 1].min())
            if rng5 / px <= 0.05 and px >= 0.97 * float(hi20.iloc[i]):
                out.append({"pattern": "COIL", "date": dt})
        # CTR
        if i >= 20 and up:
            rng5 = float(h.iloc[i - 4:i + 1].max() - l.iloc[i - 4:i + 1].min())
            rng15 = float(h.iloc[i - 19:i - 4].max() - l.iloc[i - 19:i - 4].min())
            if rng15 > 0 and rng5 <= 0.5 * rng15 and px >= 0.95 * float(hi20.iloc[i]):
                out.append({"pattern": "CTR", "date": dt})
        # OOPS (bullish): open below yesterday's low, close back above it
        if float(o.iloc[i]) < float(l.iloc[i - 1]) and px > float(l.iloc[i - 1]):
            out.append({"pattern": "OOPS", "date": dt, "up": up})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bars", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    bars: Dict[str, pd.DataFrame] = pickle.load(open(args.bars, "rb"))
    closes = {t: df["Close"] for t, df in bars.items()}
    # pool median forward return per (date, horizon) for the baseline
    dates = closes["SPY"].index
    fires = []
    for t, df in bars.items():
        if t == "SPY":
            continue
        try:
            for ev in detect(df):
                ev["ticker"] = t
                fires.append(ev)
        except Exception:  # noqa: BLE001
            continue
    rows = []
    # precompute pool matrix
    mat = pd.DataFrame({t: s for t, s in closes.items() if len(s) >= 120}).reindex(dates)
    fwd = {k: mat.shift(-k) / mat - 1 for k in HORIZONS}
    pool_med = {k: fwd[k].median(axis=1) for k in HORIZONS}
    for ev in fires:
        t, dt = ev["ticker"], ev["date"]
        if t not in mat.columns or dt not in mat.index:
            continue
        row = {"ticker": t, "date": str(dt.date()), "pattern": ev["pattern"], "up": ev.get("up")}
        ok = True
        for k in HORIZONS:
            v = fwd[k].at[dt, t]
            b = pool_med[k].get(dt)
            if pd.isna(v) or pd.isna(b):
                ok = False
                break
            row[f"fwd{k}"] = float(v)
            row[f"base{k}"] = float(b)
        if ok:
            rows.append(row)
    out = pd.DataFrame(rows)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"{len(out)} scored fires -> {args.out}")
    for pat, g in out.groupby("pattern"):
        line = f"{pat:14s} n={len(g):6d}"
        for k in HORIZONS:
            edge = (g[f"fwd{k}"] - g[f"base{k}"]).median() * 100
            win = (g[f"fwd{k}"] > 0).mean() * 100
            line += f" | {k}d med {g[f'fwd{k}'].median()*100:+.2f}% edge {edge:+.2f} win {win:.0f}%"
        print(line)
    if (out.pattern == "OOPS").any():
        for lbl, g in out[out.pattern == "OOPS"].groupby("up"):
            e = (g.fwd10 - g.base10).median() * 100
            print(f"  OOPS up={lbl}: n={len(g)} 10d med {g.fwd10.median()*100:+.2f}% edge {e:+.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
