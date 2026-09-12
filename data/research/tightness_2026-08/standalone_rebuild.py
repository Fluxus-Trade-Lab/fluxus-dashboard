"""Rebuild study.json "standalone" (any / uptrend / setup_all) and give it a resolution.

2026-09-13 (Nighty Zac). The 08-23 report printed three numbers -- compression
outside the setup: any day -2.4pp, uptrend -0.1pp, setup_all -0.9pp -- and the
claim `tightness-compression-no-standalone-edge` rests on them, but no committed
code produced them (tightness_grid.py only scores setup days). The sampling and
context definitions below were RECOVERED by searching a grid of plausible
choices (see standalone_rebuild.md), not read from the original session:

  sample     every 5th session from bar 130 (i >= 130, (i-130) % 5 == 0)
  outcome    tightness_grid.frame_outcome: +2R before -1.5R within 20 sessions
  tight      atr14__pct252 < 20   (the `volrank20` detector)
  delta      win% of tight days minus win% of the rest, in that context
  any        every sampled day
  uptrend    close > SMA50 and close within 20% of the 252-day closing high
             (the trend half of tightness_grid.setup_mask) -- a GUESS that
             rounds to the printed -0.1; the grid search found it among 15
  setup_all  tightness_grid.setup_mask, every setup day (no de-overlap)

Resolution: bootstrap over ISO weeks (W-FRI) -- setup windows overlap and the
whole market moves together inside a week, so a day is not an observation.
Ticker clusters are reported alongside; week is the one the claim uses because
it is the wider of the two.

    python data/research/tightness_2026-08/standalone_rebuild.py \
        --bars data/research/scanner_validation_2026-08/event_bars.pkl
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pipeline.tools.tightness_grid import frame_outcome, grid, setup_mask  # noqa: E402

START, STEP, TIGHT_BELOW = 130, 5, 20
SEED, B = 20260913, 2000


def rows(bars: dict) -> pd.DataFrame:
    out = []
    for t, df in bars.items():
        if t == "SPY" or len(df) < 150:
            continue
        m = grid(df)
        setup = setup_mask(df, m).values
        c = df["Close"]
        hi252 = c.rolling(252, min_periods=130).max()
        up = ((c > c.rolling(50).mean()) & (c / hi252 - 1 >= -0.20)).values
        pct, atr = m["atr14__pct252"].values, m["atr"].values
        for i in range(START, len(c), STEP):
            res = frame_outcome(c, i, float(atr[i]))
            if res is None or pct[i] != pct[i]:
                continue
            out.append((t, c.index[i], res == "win", pct[i] < TIGHT_BELOW, bool(up[i]), bool(setup[i])))
    return pd.DataFrame(out, columns=["ticker", "date", "win", "tight", "uptrend", "setup"])


def delta(x: pd.DataFrame) -> float:
    return (x.win[x.tight].mean() - x.win[~x.tight].mean()) * 100


def cluster_boot(x: pd.DataFrame, key: pd.Series, rng) -> np.ndarray:
    agg = x.assign(k=key).groupby(["k", "tight"]).win.agg(["sum", "count"]).unstack(fill_value=0)
    s1, n1 = agg[("sum", True)].values, agg[("count", True)].values
    s0, n0 = agg[("sum", False)].values, agg[("count", False)].values
    k = len(agg)
    bs = np.empty(B)
    for b in range(B):
        w = np.bincount(rng.integers(0, k, k), minlength=k)
        bs[b] = ((w @ s1) / (w @ n1) - (w @ s0) / (w @ n0)) * 100
    return bs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bars", type=Path, default=ROOT / "data/research/scanner_validation_2026-08/event_bars.pkl")
    ap.add_argument("--out", type=Path, default=Path(__file__).with_name("standalone_rebuild.json"))
    args = ap.parse_args(argv)
    d = rows(pickle.load(open(args.bars, "rb")))
    printed = json.load(open(Path(__file__).with_name("report") / "study.json"))["standalone"]
    rng = np.random.default_rng(SEED)
    result = {"sample": {"start": START, "step": STEP, "tight": f"atr14__pct252 < {TIGHT_BELOW}",
                         "compare": "tight minus rest", "bootstrap": B, "seed": SEED}}
    for name, x in (("any", d), ("uptrend", d[d.uptrend]), ("setup_all", d[d.setup])):
        est = delta(x)
        r = {"n": len(x), "n_tight": int(x.tight.sum()), "delta_pp": round(est, 2),
             "printed_pp": printed[name], "reproduces": bool(round(est, 1) == printed[name])}
        for cl, key in (("week", pd.to_datetime(x.date).dt.to_period("W-FRI").astype(str)), ("ticker", x.ticker)):
            bs = cluster_boot(x, key, rng)
            lo, hi = np.percentile(bs, [2.5, 97.5])
            r[cl] = {"ci95": [round(lo, 2), round(hi, 2)], "halfwidth_pp": round((hi - lo) / 2, 2),
                     "mde80_pp": round(2.8 * bs.std(), 2)}
        result[name] = r
        print(name, json.dumps(r))
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
