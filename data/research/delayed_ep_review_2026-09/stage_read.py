"""⚠️ 2026-09-09 起：**这个脚本的分母是错的**（保留原样，因为它是历史读数的出处）。

此脚本用 SPY 当基准。本目录 `results.md`（2026-09-01）§三 自己就裁定过
「SPY 是错的尺子；对 stage 分类器，正确基准是它自己的同日 cohort」——
而这个脚本写在那条裁决**之前**，从没跟着改。2026-09-09 我跑了它、信了它的输出，
写出一条「预注册方向被证伪」的结论，换回 cohort 之后 +5d 符号就翻正了。
**要读 stage 的结论请用 `cohort_read.py`。** 这里留着的是 SPY 口径的历史值。

Does the stage label separate anything -- and does the answer survive
dropping the one session we know is a replay?

Same measurement as `review_benchmarked.py` (excess over SPY on the marketcal
grid, median with a bootstrap that resamples whole AS-OF DATES), reading the
cached bars.csv so it costs no vendor calls. Two things are new:

1. A `--drop` switch. 2026-09-02 is a replay of 09-01 (join_by_date.py:
   0/36 rows match their own day, 36/36 match the previous one). The forward
   RETURNS are unaffected -- both endpoints come from vendor bars, never from
   the ledger's stored close -- but the STAGE LABELS on those 36 rows were
   computed from 09-01's prices, so they describe a day that did not happen.
   Any read of "what does stage X predict" has to survive their removal.

2. The pre-registered direction. `breaking` is not one of twenty-four cells to
   go fishing in; it is the claim the scanner exists to test, and its direction
   was fixed before we had a ledger: the second breakout is supposed to be the
   BETTER trade. So the question is one-sided and named in advance, and the
   other three stages are context, not competitors
   ([[pitfall_compute_the_minimum_possible_p_first]]).

  PYTHONPATH=. python3 data/research/delayed_ep_review_2026-09/stage_read.py
  PYTHONPATH=. python3 data/research/delayed_ep_review_2026-09/stage_read.py --drop 2026-09-02
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
from pathlib import Path

import numpy as np

from pipeline.marketcal import is_trading_day, last_completed_session

HERE = Path(__file__).parent
LOG = Path("data/history/delayed_ep_log.csv")
BENCH = "SPY"
HORIZONS = (3, 5, 10)
STAGES = ("breaking", "basing", "drifting", "failed")


def load_bars() -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for r in csv.DictReader((HERE / "bars.csv").open(newline="")):
        out.setdefault(r["ticker"], {})[r["date"]] = float(r["close"])
    return out


def trading_grid(start: dt.date, end: dt.date) -> list[str]:
    out, d = [], start
    while d <= end:
        if is_trading_day(d):
            out.append(str(d))
        d += dt.timedelta(days=1)
    return out


def block_bootstrap_median(vals, blocks, n_boot=4000, seed=7):
    if not vals:
        return (None, None)
    rng = np.random.default_rng(seed)
    by_block: dict[str, list[float]] = {}
    for v, b in zip(vals, blocks):
        by_block.setdefault(b, []).append(v)
    keys = list(by_block)
    meds = []
    for _ in range(n_boot):
        pick = rng.choice(len(keys), size=len(keys), replace=True)
        pool = [v for i in pick for v in by_block[keys[i]]]
        if pool:
            meds.append(float(np.median(pool)))
    return (float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5)))


def describe(name, rows):
    if not rows:
        return f"  {name:>22}  (n=0)"
    vals = [r[0] for r in rows]
    blocks = [r[1] for r in rows]
    lo, hi = block_bootstrap_median(vals, blocks)
    nd = len(set(blocks))
    ci = f"[{lo*100:+.1f},{hi*100:+.1f}]" if lo is not None else "[--]"
    flag = "  <-- dates<4, no resolution" if nd < 4 else ""
    return (f"  {name:>22}  med {float(np.median(vals))*100:+5.1f}%  CI {ci:>14}  "
            f"n={len(vals):<4} dates={nd:<3} "
            f">0:{sum(1 for v in vals if v>0)/len(vals)*100:3.0f}%{flag}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--drop", nargs="*", default=[], help="as_of sessions to exclude")
    a = ap.parse_args()

    log = [r for r in csv.DictReader(LOG.open(newline="")) if r["as_of"] not in a.drop]
    bars = load_bars()
    log_dates = sorted({r["as_of"] for r in log})
    last_ok = str(last_completed_session())
    grid = trading_grid(dt.date.fromisoformat(log_dates[0]), dt.date.fromisoformat(last_ok))
    pos = {d: i for i, d in enumerate(grid)}
    print(f"log: {len(log)} rows | {len(log_dates)} sessions {log_dates[0]}..{log_dates[-1]}"
          f"{'  | DROPPED ' + ','.join(a.drop) if a.drop else ''}")

    def fwd(t, d, h):
        i = pos.get(d)
        if i is None or i + h >= len(grid):
            return None
        tgt = grid[i + h]
        s = bars.get(t)
        if not s or d not in s or tgt not in s:
            return None
        return s[tgt] / s[d] - 1.0

    for h in HORIZONS:
        pooled, per = [], {s: [] for s in STAGES}
        for r in log:
            rt, rb = fwd(r["ticker"], r["as_of"], h), fwd(BENCH, r["as_of"], h)
            if rt is None or rb is None:
                continue
            pooled.append((rt - rb, r["as_of"]))
            if r["stage"] in per:
                per[r["stage"]].append((rt - rb, r["as_of"]))
        print(f"\n  --- +{h} sessions (excess over {BENCH}) ---")
        print(describe("POOLED", pooled))
        for st in STAGES:
            print(describe(st, per[st]))
        b = [v for v, _ in per["breaking"]]
        if b:
            print(f"     pre-registered direction: breaking should be POSITIVE. "
                  f"observed median {float(np.median(b))*100:+.1f}% "
                  f"({'WRONG' if np.median(b) < 0 else 'right'} sign), "
                  f"{sum(1 for v in b if v>0)}/{len(b)} rows above zero")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
