"""Tightness, decomposed -- what you measure vs what you compare it to.

2026-08-23 (Andy: "所以我的理解以 atr 为基准更加的精准? rmv, 3WT, COIL, VCS,
还有别的嘛?"). The 08-23 RMV/VolRank test found one tight thing that predicts
(252d ATR% percentile) and one that does not (RMV, a 15-bar min-max), but it
confounded two choices. This separates them into a grid:

  MEASURE (the raw quantity)      NORMALIZATION (what it is compared to)
  ------------------------        --------------------------------------
  rng1   today's H-L / close      abs     the measure itself (price-scaled)
  rng5   5-session range / close  mm15    min-max over the prior 15 bars (RMV)
  atr14  ATR14 / close            pct63   self-percentile, 63 sessions
  bbw    Bollinger width (20,2)   pct252  self-percentile, 252 sessions
  sd20   stdev of 20d returns

Every cell is scored the same way, inside the one setup we practise (fresh-high
pullback): split the setup-days into terciles by that cell's reading and take
the trade-frame win rate (R = ATR14, +2R before -1.5R within 20 sessions).
The number that matters is the SPREAD -- tightest tercile minus loosest. A
measure that "works" shows the same sign across normalizations; a normalization
that works shows the same sign across measures. Only one of those is true.

Named detectors (VCS / 3WT / COIL / VCP / CTR / RMV<20 / VolRank<20) are scored
on the same days with the same frame so the table is one comparison, not five.

De-overlap (one setup per ticker per 30 calendar days) is the headline sample:
setup-days cluster, and 28k overlapping windows overstate significance.

    python -m pipeline.tools.tightness_grid --out data/research/tightness_2026-08/
"""
from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

BARS = Path("data/research/scanner_validation_2026-08/event_bars.pkl")
FRAME_TARGET_R = 2.0        # +2R first = win
FRAME_STOP_R = 1.5          # -1.5R first = loss
FRAME_DAYS = 20

MEASURES = ("rng1", "rng5", "atr14", "bbw", "sd20")
NORMS = ("abs", "mm15", "pct63", "pct252")


def _pct_rank(s: pd.Series, window: int) -> pd.Series:
    """Self-percentile: share of the trailing `window` readings at or below now."""
    return s.rolling(window, min_periods=max(30, window // 4)).rank(pct=True) * 100


def _minmax(s: pd.Series, window: int = 15) -> pd.Series:
    """RMV-style 0-100 min-max against the PRIOR `window` bars (current excluded,
    so a new low in volatility registers as 0 immediately)."""
    lo = s.shift(1).rolling(window).min()
    hi = s.shift(1).rolling(window).max()
    return (100 * (s - lo) / (hi - lo)).clip(0, 100)


def measures(df: pd.DataFrame) -> pd.DataFrame:
    """The five raw volatility quantities, all price-scaled so they are
    comparable across names before any further normalization."""
    c, h, l, v = df["Close"], df["High"], df["Low"], df["Volume"]
    out = pd.DataFrame(index=df.index)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    out["atr"] = tr.ewm(alpha=1 / 14, adjust=False).mean()          # absolute, for R
    out["rng1"] = (h - l) / c * 100
    out["rng5"] = (h.rolling(5).max() - l.rolling(5).min()) / c * 100
    out["atr14"] = out["atr"] / c * 100
    sma20, sd = c.rolling(20).mean(), c.rolling(20).std()
    out["bbw"] = (4 * sd) / sma20 * 100
    out["sd20"] = c.pct_change().rolling(20).std() * 100
    # RMV -- OUR APPROXIMATION, not Deepvue's formula. Their knowledge base
    # describes the output only ("current range against the average of the
    # past 15 bars, 0-100, near 0 when tight") and publishes no calculation;
    # the TraderLion Trade-Lab model book on this machine uses "Low RMV" and
    # "RMV Tight Signal" purely as chart labels. The volume damping below is
    # a guess of ours. The comment here used to read "RMV as its authors
    # define it", which was a claim we could not support -- and naming a
    # quantity after someone else's indicator is how a house measurement ends
    # up read as a standard one. Research column; not shipped to any page.
    volratio = (v / v.rolling(30).mean()).clip(upper=1.0)
    out["rmv"] = _minmax((h - l) * volratio, 15)
    return out


def grid(df: pd.DataFrame) -> pd.DataFrame:
    """MEASURES x NORMS, one column per cell, named `<measure>__<norm>`."""
    m = measures(df)
    out = pd.DataFrame(index=df.index)
    for name in MEASURES:
        s = m[name]
        out[f"{name}__abs"] = s
        out[f"{name}__mm15"] = _minmax(s, 15)
        out[f"{name}__pct63"] = _pct_rank(s, 63)
        out[f"{name}__pct252"] = _pct_rank(s, 252)
    out["rmv"] = m["rmv"]
    out["atr"] = m["atr"]
    return out


def setup_mask(df: pd.DataFrame, m: pd.DataFrame) -> pd.Series:
    """The Selection Lab setup: fresh-high pullback (see selection_lab.candidates)."""
    c, h, l, v = df["Close"], df["High"], df["Low"], df["Volume"]
    hi252 = c.rolling(252, min_periods=130).max()
    days_hi = c.rolling(252, min_periods=130).apply(
        lambda w: len(w) - 1 - int(np.argmax(w)), raw=True)
    dist = c / hi252 - 1
    sma50 = c.rolling(50).mean()
    ema21 = c.ewm(span=21, adjust=False).mean()
    dv20 = (v * c).rolling(20).mean()
    return ((dist >= -0.20) & (dist <= -0.03) & (days_hi <= 60) & (c > sma50)
            & ((c - ema21).abs() / m["atr"] <= 1.5) & (dv20 >= 2e7))


def frame_outcome(c: pd.Series, i: int, atr: float) -> Optional[str]:
    """R-framed outcome from bar i: +2R first = win, -1.5R first = loss."""
    if i + FRAME_DAYS >= len(c) or not atr or atr != atr:
        return None
    p0 = float(c.iloc[i])
    for px in c.iloc[i + 1:i + 1 + FRAME_DAYS]:
        if px >= p0 + FRAME_TARGET_R * atr:
            return "win"
        if px <= p0 - FRAME_STOP_R * atr:
            return "loss"
    return "flat"


def detectors(df: pd.DataFrame, m: pd.DataFrame) -> pd.DataFrame:
    """Named tightness detectors as the repo defines them, as boolean columns.

    3WT / COIL / CTR mirror pipeline/tools/tightness_study.py; VCS is the Pine
    port in pipeline/screeners/vcs.py (run separately -- it is slow per name).
    """
    c, h, l = df["Close"], df["High"], df["Low"]
    out = pd.DataFrame(index=df.index)
    sma50 = c.rolling(50).mean()
    hi20 = c.rolling(20).max()
    hi52 = c.rolling(252, min_periods=60).max()
    uptrend = (c > sma50) & (c / hi52 - 1 >= -0.15)
    # 3WT: three consecutive weekly closes inside a 1.5% band
    wk = c.resample("W-FRI").last().dropna()
    band = (wk.rolling(3).max() / wk.rolling(3).min() - 1) <= 0.015
    tight_weeks = set(wk.index[band.fillna(False)])
    out["wt3"] = pd.Series([d in tight_weeks for d in c.index], index=c.index) & uptrend
    # COIL: 5-session range <= 5% of close, within 3% of the 20d high
    rng5 = (h.rolling(5).max() - l.rolling(5).min()) / c * 100
    out["coil"] = (rng5 <= 5) & (c / hi20 - 1 >= -0.03) & (c > sma50)
    # CTR: last-5 range <= half the prior-15 range
    prior15 = (h.rolling(15).max() - l.rolling(15).min()).shift(5)
    out["ctr"] = (((h.rolling(5).max() - l.rolling(5).min()) <= 0.5 * prior15)
                  & (c / hi20 - 1 >= -0.05) & (c > sma50))
    out["rmv20"] = m["rmv"] < 20
    out["volrank20"] = m["atr14__pct252"] < 20
    return out


def run(bars_path: Path = BARS, min_gap_days: int = 30) -> pd.DataFrame:
    bars = pickle.load(open(bars_path, "rb"))
    rows = []
    for t, df in bars.items():
        if t == "SPY" or len(df) < 150:
            continue
        m = grid(df)
        det = detectors(df, m)
        mask = setup_mask(df, m).values
        c = df["Close"]
        for i in np.where(mask)[0]:
            if i < 130:
                continue
            atr = float(m["atr"].iloc[i])
            res = frame_outcome(c, i, atr)
            if res is None:
                continue
            p0 = float(c.iloc[i])
            seg = c.iloc[i:i + FRAME_DAYS + 1]
            row = {"ticker": t, "date": c.index[i],
                   "fwd20": (float(c.iloc[i + FRAME_DAYS]) / p0 - 1) * 100,
                   "mae20": (seg / p0 - 1).min() * 100,
                   "mfe20": (seg / p0 - 1).max() * 100,
                   "outcome": res}
            for col in m.columns:
                if col != "atr":
                    row[col] = float(m[col].iloc[i])
            for col in det.columns:
                row[col] = bool(det[col].iloc[i])
            rows.append(row)
    d = pd.DataFrame(rows)
    # de-overlap: one setup per ticker per `min_gap_days` calendar days
    keep = []
    for _, g in d.sort_values("date").groupby("ticker"):
        last = None
        for idx, r in g.iterrows():
            if last is None or (r["date"] - last).days >= min_gap_days:
                keep.append(idx)
                last = r["date"]
    d["dedup"] = d.index.isin(keep)
    return d


def tercile_spread(d: pd.DataFrame, col: str) -> dict:
    """Win-rate of the tightest tercile minus the loosest, by `col`."""
    x = d[[col, "outcome"]].dropna()
    if len(x) < 90 or x[col].nunique() < 10:
        return {"n": len(x), "tight": np.nan, "loose": np.nan, "spread": np.nan}
    q = pd.qcut(x[col], 3, labels=["tight", "mid", "loose"], duplicates="drop")
    if q.nunique() < 3:
        return {"n": len(x), "tight": np.nan, "loose": np.nan, "spread": np.nan}
    w = x.assign(q=q).groupby("q", observed=True)["outcome"].apply(lambda s: (s == "win").mean() * 100)
    return {"n": len(x), "tight": w.get("tight", np.nan), "loose": w.get("loose", np.nan),
            "spread": w.get("tight", np.nan) - w.get("loose", np.nan)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bars", type=Path, default=BARS)
    ap.add_argument("--out", type=Path, default=Path("data/research/tightness_2026-08"))
    args = ap.parse_args(argv)
    d = run(args.bars)
    args.out.mkdir(parents=True, exist_ok=True)
    d.to_csv(args.out / "grid_sample.csv", index=False)
    sub = d[d["dedup"]]
    print(f"{len(d)} setup-days ({len(sub)} de-overlapped), "
          f"{d['ticker'].nunique()} tickers, base win {(d.outcome=='win').mean():.1%}")
    print("\nMEASURE x NORM -- tightest-tercile win rate minus loosest (de-overlapped):")
    tbl = pd.DataFrame({n: {m: tercile_spread(sub, f"{m}__{n}")["spread"] for m in MEASURES}
                        for n in NORMS})
    print(tbl.round(1).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
