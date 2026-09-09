"""Is `breaking` worse than the pool it was drawn from, or is it a small
random draw that happens to look bad?

The stage medians cannot be read against zero, because the whole candidate
pool ran below SPY over this window (pooled excess -0.5% / -0.7% / -1.0% at
+3 / +5 / +10). The only question the ledger can answer is the RELATIVE one:
given the same 17 sessions and the same names, does the label `breaking` pick
out rows that did worse than a same-day random pick of the same size?

So the null is "labels are exchangeable WITHIN a session", and the test
shuffles them there. Shuffling across sessions would be the wrong null -- one
day's market move sits inside every window opened that day, so a cross-session
shuffle would mostly measure which days got sampled
([[pitfall_a_median_hides_the_worst_day]] is the same failure in reverse).

Statistic: median excess of the `breaking` rows. One-sided in the DIRECTION WE
PRE-REGISTERED AGAINST -- the scan's premise says breaking should be the best
bucket, so `p_high` (how often a shuffle beats what we saw) is the number that
would have supported it, and `p_low` is the number that condemns it. Both are
printed; neither is chosen after the fact.

Resolution floor, computed before the test and not after: with the (k+1)/(N+1)
convention the smallest p this design can return is 1/(n_perm+1) = 1/10001.

⚠️ 2026-09-09: the code below computes `(null<=obs).mean()`, whose floor is 0,
not 1/10001 -- the docstring described the convention I meant to use and the
code used another. `cohort_read.py` uses (k+1)/(N+1). Kept here unchanged
because the printed numbers in run_2026-09-09_perm.txt came from it, and none
of them are anywhere near either floor.

  PYTHONPATH=. python3 data/research/delayed_ep_review_2026-09/label_permutation.py
"""
from __future__ import annotations
import csv
import datetime as dt
from pathlib import Path

import numpy as np

from pipeline.marketcal import is_trading_day, last_completed_session

HERE = Path(__file__).parent
LOG = Path("data/history/delayed_ep_log.csv")
BENCH = "SPY"
HORIZONS = (3, 5, 10)
N_PERM = 10000
DROP = {"2026-09-02"}          # replay session, see join_by_date.py


def main() -> int:
    bars: dict[str, dict[str, float]] = {}
    for r in csv.DictReader((HERE / "bars.csv").open(newline="")):
        bars.setdefault(r["ticker"], {})[r["date"]] = float(r["close"])
    log = [r for r in csv.DictReader(LOG.open(newline="")) if r["as_of"] not in DROP]

    d0 = dt.date.fromisoformat(min(r["as_of"] for r in log))
    d1 = last_completed_session()
    grid, d = [], d0
    while d <= d1:
        if is_trading_day(d):
            grid.append(str(d))
        d += dt.timedelta(days=1)
    pos = {x: i for i, x in enumerate(grid)}

    def fwd(t, day, h):
        i = pos.get(day)
        if i is None or i + h >= len(grid):
            return None
        tgt = grid[i + h]
        s = bars.get(t)
        if not s or day not in s or tgt not in s:
            return None
        return s[tgt] / s[day] - 1.0

    print(f"null: stage labels exchangeable WITHIN a session | {N_PERM} shuffles | "
          f"p floor = {1/(N_PERM+1):.5f}")
    rng = np.random.default_rng(11)
    for h in HORIZONS:
        by_date: dict[str, list[tuple[str, float]]] = {}
        for r in log:
            rt, rb = fwd(r["ticker"], r["as_of"], h), fwd(BENCH, r["as_of"], h)
            if rt is None or rb is None:
                continue
            by_date.setdefault(r["as_of"], []).append((r["stage"], rt - rb))
        obs_rows = [v for rows in by_date.values() for st, v in rows if st == "breaking"]
        if not obs_rows:
            print(f"\n+{h}d: no breaking rows resolvable"); continue
        obs = float(np.median(obs_rows))
        k_per_date = {d: sum(1 for st, _ in rows if st == "breaking")
                      for d, rows in by_date.items()}
        pool_per_date = {d: np.array([v for _, v in rows]) for d, rows in by_date.items()}
        null = np.empty(N_PERM)
        for b in range(N_PERM):
            draw = []
            for d, k in k_per_date.items():
                if k:
                    draw.append(rng.choice(pool_per_date[d], size=k, replace=False))
            null[b] = np.median(np.concatenate(draw))
        p_low = float((null <= obs).mean())
        p_high = float((null >= obs).mean())
        print(f"\n+{h:>2}d  breaking median {obs*100:+.2f}%  "
              f"(n={len(obs_rows)}, dates={sum(1 for v in k_per_date.values() if v)})")
        print(f"      same-day random picks of the same size: "
              f"median {np.median(null)*100:+.2f}%  "
              f"[p5 {np.percentile(null,5)*100:+.2f}%, p95 {np.percentile(null,95)*100:+.2f}%]")
        print(f"      p_low (breaking is WORSE than a same-day pick)  = {p_low:.4f}")
        print(f"      p_high (breaking is BETTER -- what the premise predicts) = {p_high:.4f}")
    print("\nThree horizons, one pre-registered family -> Bonferroni x3 on whichever side is read.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
