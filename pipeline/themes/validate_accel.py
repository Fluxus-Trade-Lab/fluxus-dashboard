"""Sensitivity study: which RS-acceleration definition actually works.

A single day's snapshot cannot tell you whether a state definition is any
good.  Two things matter and both need history:

**Stability** -- if the state flips every few days it is noise wearing a
label, and a "Leading" group you cannot hold for a week is useless.

**Separation** -- Leading should, on average, outperform Lagging over the
following weeks.  If it does not, the classification is decoration.

The test bed is the ~138 ETFs already tracked in ``pipeline/constants``:
liquid, clean, long history, and they span sectors, themes and countries.
The arithmetic is identical to what runs on industries, so what holds here
holds there.

    python -m pipeline.themes.validate_accel --refresh   # fetch prices once
    python -m pipeline.themes.validate_accel             # run the study
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

logger = logging.getLogger(__name__)

CACHE = Path(".cache/etf_prices.pkl")
BENCH = "SPY"
SESSIONS_PER_WEEK = 5
FORWARD_HORIZON = 21  # ~1 month of sessions


@dataclass(frozen=True)
class Scheme:
    """A window scheme: how far back each bucket reaches, in sessions."""
    name: str
    near: int        # near bucket: 0 .. near
    mid: int         # prior bucket: near .. mid
    far: int         # level window: 0 .. far
    note: str = ""


SCHEMES: List[Scheme] = [
    Scheme("V1  1w/1m  lvl=1m", near=5, mid=21, far=21,
           note="current implementation"),
    Scheme("V2  2w/4w  lvl=1m", near=10, mid=21, far=21,
           note="TSF's 2-week bucket width"),
    Scheme("V3  2w/4w  lvl=3m", near=10, mid=21, far=63),
    Scheme("V4  1m/3m  lvl=3m", near=21, mid=63, far=63,
           note="slow: everything >= 1 month"),
    Scheme("V5  1m/2m  lvl=3m", near=21, mid=42, far=63),
    Scheme("V6  1w/1m  lvl=3m", near=5, mid=21, far=63),
]


def fetch_prices(tickers: List[str]) -> pd.DataFrame:
    import yfinance as yf
    logger.info("Downloading %d tickers", len(tickers))
    data = yf.download(tickers, period="2y", interval="1d",
                       auto_adjust=True, progress=False)
    close = data["Close"] if isinstance(data.columns, pd.MultiIndex) else data
    close = close.dropna(axis=1, how="all").ffill()
    logger.info("Got %d sessions x %d tickers", *close.shape)
    return close


def load_prices(refresh: bool = False) -> pd.DataFrame:
    if CACHE.exists() and not refresh:
        return pd.read_pickle(CACHE)
    from pipeline.constants.tickers import STOCK_GROUPS  # noqa: PLC0415

    tickers = sorted({t for group in STOCK_GROUPS.values() for t in group} | {BENCH})
    close = fetch_prices(tickers)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    close.to_pickle(CACHE)
    return close


def states_for_scheme(close: pd.DataFrame, s: Scheme) -> pd.DataFrame:
    """State label per (date, ticker) under one window scheme.

    Buckets are disjoint by construction: the near bucket is the last
    ``near`` sessions, the prior bucket is the stretch from ``near`` to
    ``mid``.  Both are measured as excess over the benchmark.
    """
    if BENCH not in close.columns:
        raise ValueError(f"{BENCH} missing from price panel")

    def window_return(span_start: int, span_end: int) -> pd.DataFrame:
        # return from span_end sessions ago to span_start sessions ago
        return close.shift(span_start) / close.shift(span_end) - 1.0

    near_r = window_return(0, s.near)
    prior_r = window_return(s.near, s.mid)
    level_r = window_return(0, s.far)

    bench = lambda df: df[BENCH]  # noqa: E731
    rs_near = near_r.sub(bench(near_r), axis=0)
    rs_prior = prior_r.sub(bench(prior_r), axis=0)
    level = level_r.sub(bench(level_r), axis=0)
    accel = rs_near - rs_prior

    state = pd.DataFrame(np.nan, index=close.index, columns=close.columns, dtype=object)
    pos, acc = level > 0, accel > 0
    state = state.mask(pos & acc, "Leading")
    state = state.mask(pos & ~acc, "Weakening")
    state = state.mask(~pos & acc, "Improving")
    state = state.mask(~pos & ~acc, "Lagging")
    state[level.isna() | accel.isna()] = np.nan
    return state.drop(columns=[BENCH])


def flip_rate(state: pd.DataFrame) -> float:
    """Fraction of consecutive session pairs where the label changes."""
    prev = state.shift(1)
    both = state.notna() & prev.notna()
    changed = (state != prev) & both
    return float(changed.values.sum() / max(both.values.sum(), 1))


def median_run_length(state: pd.DataFrame) -> float:
    runs: List[int] = []
    for col in state.columns:
        series = state[col].dropna()
        if series.empty:
            continue
        grp = (series != series.shift(1)).cumsum()
        runs.extend(series.groupby(grp).size().tolist())
    return float(np.median(runs)) if runs else float("nan")


def forward_excess(close: pd.DataFrame, state: pd.DataFrame,
                   horizon: int = FORWARD_HORIZON) -> Dict[str, float]:
    """Mean forward excess return over the benchmark, per state label."""
    fwd = close.shift(-horizon) / close - 1.0
    fwd = fwd.sub(fwd[BENCH], axis=0).drop(columns=[BENCH])

    out: Dict[str, float] = {}
    for label in ("Leading", "Weakening", "Improving", "Lagging"):
        mask = state == label
        vals = fwd.where(mask).values.ravel()
        vals = vals[np.isfinite(vals)]
        out[label] = float(np.mean(vals)) if vals.size else float("nan")
    return out


def run_study(close: pd.DataFrame) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for s in SCHEMES:
        state = states_for_scheme(close, s)
        fwd = forward_excess(close, state)
        spread = fwd["Leading"] - fwd["Lagging"]
        counts = state.stack().value_counts(normalize=True).to_dict()
        rows.append({
            "scheme": s.name,
            "note": s.note,
            "flip_rate": flip_rate(state),
            "median_run": median_run_length(state),
            "fwd": fwd,
            "spread": spread,
            "monotone": (fwd["Leading"] > fwd["Weakening"]
                         and fwd["Weakening"] > fwd["Lagging"]),
            "dist": {k: counts.get(k, 0.0) for k in
                     ("Leading", "Weakening", "Improving", "Lagging")},
        })
    return rows


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()

    close = load_prices(refresh=args.refresh)
    rows = run_study(close)

    print(f"\nPanel: {close.shape[0]} sessions x {close.shape[1]} tickers "
          f"({close.index[0].date()} -> {close.index[-1].date()})")
    print(f"Forward horizon: {FORWARD_HORIZON} sessions\n")

    hdr = (f"{'scheme':22s} {'flip%':>6s} {'run':>5s} "
           f"{'Lead':>7s} {'Weak':>7s} {'Impr':>7s} {'Lagg':>7s} "
           f"{'L-Lg':>7s} {'mono':>5s}")
    print(hdr)
    print("-" * len(hdr))
    for r in sorted(rows, key=lambda x: -x["spread"]):
        f = r["fwd"]
        print(f"{r['scheme']:22s} {100*r['flip_rate']:6.2f} {r['median_run']:5.0f} "
              f"{100*f['Leading']:+7.2f} {100*f['Weakening']:+7.2f} "
              f"{100*f['Improving']:+7.2f} {100*f['Lagging']:+7.2f} "
              f"{100*r['spread']:+7.2f} {'yes' if r['monotone'] else 'no':>5s}")

    print("\nflip% = share of sessions where the label changes (lower = more stable)")
    print("run   = median sessions a label survives")
    print("Lead..Lagg = mean forward excess return vs SPY, in %, by label")
    print("L-Lg  = Leading minus Lagging (the separation the label is supposed to buy)")
    print("mono  = Leading > Weakening > Lagging")


if __name__ == "__main__":
    main()
