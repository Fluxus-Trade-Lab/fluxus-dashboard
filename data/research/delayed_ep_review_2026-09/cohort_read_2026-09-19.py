"""Third Delayed-EP read (2026-09-19): cohort_read.py unchanged in method, two additions.

  1. BARS. Reads bars_2026-09-19.csv (one batched fetch on 2026-09-19 04:5x JST,
     the in-progress 2026-09-18 bar dropped) instead of the 09-09 cache, so the
     ledger's 08-13..09-17 rows all have a chance at +10.
  2. POPULATION. Since 2026-06-26 the universe is the whole market; the EP
     screener upstream of this ledger floors at $500M (episodic_pivot.py
     _MIN_MARKET_CAP), so ~1/3 of ledger rows are under $1B -- a population the
     Delayed-EP idea was never framed on. Every read is printed twice: all rows,
     and rows whose market cap on the as_of snapshot is >= $1B (the page's
     tradeable floor). Cap comes from universe.json at that session
     (population_reach.snapshots); a ticker absent from the snapshot is
     "unknown" and kept out of both population splits' core side.

Method, cohort, permutation, exclusions: exactly cohort_read.py (see its docstring).

  PYTHONPATH=. python3 data/research/delayed_ep_review_2026-09/cohort_read_2026-09-19.py
"""

from __future__ import annotations
import csv
import datetime as dt
from pathlib import Path

import numpy as np

from pipeline.marketcal import is_trading_day, last_completed_session

HERE = Path(__file__).parent
LOG = Path("data/history/delayed_ep_log.csv")
HORIZONS = (3, 5, 10)
STAGES = ("breaking", "basing", "drifting", "failed")
N_PERM = 10000
TRUNCATION_CLEARED = "2026-08-11"   # first ticker_events session reaching Z again
REPLAY_SESSION = "2026-09-02"


def main() -> int:
    bars: dict[str, dict[str, float]] = {}
    for r in csv.DictReader((HERE / "bars_2026-09-19.csv").open(newline="")):
        bars.setdefault(r["ticker"], {})[r["date"]] = float(r["close"])
    full = list(csv.DictReader(LOG.open(newline="")))
    clean = [r for r in full
             if r["ep_date"] >= TRUNCATION_CLEARED and r["as_of"] != REPLAY_SESSION]

    d0 = dt.date.fromisoformat(min(r["as_of"] for r in full))
    grid, d = [], d0
    while d <= last_completed_session():
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

    def nonoverlapping(dates, h):
        """Windows are (i, i+h]; count how many can be picked sharing no day."""
        chosen, nxt = 0, -1
        for x in sorted(dates):
            i = pos[x]
            if i >= nxt:
                chosen += 1
                nxt = i + h
        return chosen

    import sys
    sys.path.insert(0, "data/research/breadth_universe_break_2026-09-18")
    from population_reach import snapshots
    snaps = snapshots(since="2026-08-01")
    sdays = sorted(snaps)

    def cap(r):
        earlier = [d for d in sdays if d <= r["as_of"]]
        if not earlier:
            return None
        return snaps[earlier[-1]].get(r["ticker"])

    for r in full:
        r["_cap"] = cap(r)
    known = [r for r in full if r["_cap"] is not None]
    print(f"ledger rows {len(full)} · cap known {len(known)} · <$1B {sum(1 for r in known if r['_cap'] < 1e9)}"
          f" ({sum(1 for r in known if r['_cap'] < 1e9)/max(len(known),1):.1%}) · as_of {min(r['as_of'] for r in full)}..{max(r['as_of'] for r in full)}")
    core = [r for r in clean if r["_cap"] is not None and r["_cap"] >= 1e9]
    small = [r for r in clean if r["_cap"] is not None and r["_cap"] < 1e9]
    for label, log in (("全部行（含截断源与重放场）", full),
                       (f"干净子集（ep_date >= {TRUNCATION_CLEARED}，剔 {REPLAY_SESSION}）", clean),
                       ("干净子集 ∩ 市值 ≥$1B（cohort 也只在这群里算）", core),
                       ("干净子集 ∩ 市值 <$1B（cohort 只在这群里算）", small)):
        print(f"\n=== {label} — 基准＝同日等权 cohort ===")
        for h in HORIZONS:
            raw: dict[str, list[tuple[str, float]]] = {}
            for r in log:
                v = fwd(r["ticker"], r["as_of"], h)
                if v is not None:
                    raw.setdefault(r["as_of"], []).append((r["stage"], v))
            if not raw:
                continue
            coh = {d: float(np.mean([v for _, v in rows])) for d, rows in raw.items()}
            print(f"\n  --- +{h} sessions ---")
            for st in STAGES:
                vals = [(v - coh[d], d) for d, rows in raw.items() for s2, v in rows if s2 == st]
                if not vals:
                    print(f"    {st:>9}: n=0")
                    continue
                ds = {d for _, d in vals}
                print(f"    {st:>9}  med {float(np.median([x for x, _ in vals]))*100:+5.2f}%  "
                      f"n={len(vals):<4} dates={len(ds):<3} 互不重叠日={nonoverlapping(ds, h)}")
            # permutation for the pre-registered bucket only
            k = {d: sum(1 for s2, _ in rows if s2 == "breaking") for d, rows in raw.items()}
            if not sum(k.values()):
                continue
            pool = {d: np.array([v - coh[d] for _, v in rows]) for d, rows in raw.items()}
            obs = float(np.median([v - coh[d] for d, rows in raw.items()
                                   for s2, v in rows if s2 == "breaking"]))
            rng = np.random.default_rng(11)
            null = np.array([np.median(np.concatenate(
                [rng.choice(pool[d], size=kk, replace=False) for d, kk in k.items() if kk]))
                for _ in range(N_PERM)])
            p_low = ((null <= obs).sum() + 1) / (N_PERM + 1)
            p_high = ((null >= obs).sum() + 1) / (N_PERM + 1)
            print(f"    场内置换（{N_PERM} 次，p 下限 {1/(N_PERM+1):.5f}）："
                  f"同场随机 {float(np.median(null))*100:+.2f}%  "
                  f"p_low {p_low:.4f}  p_high {p_high:.4f}")
    print("\n⚠️ 这里没有一格是「注册的那条主张」。注册的比较是**第二次突破 vs day-1 EP 入场**")
    print("   （`delayed_ep_scan` docstring: \"that breakout is a better trade than day 1\"），")
    print("   而账本不记 day-1 那条腿。cohort 只是账本能支持的最接近的替代问题。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
