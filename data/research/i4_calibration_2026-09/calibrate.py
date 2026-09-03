"""What does the I4 band actually do on our own history?

`audit_archives` I4 warns when a session's row count falls outside
[0.30x, 3.0x] of the trailing-20 median. DATA_RELIABILITY §六.1 has said since
2026-08-22 that those two numbers were "拍的" -- picked, not measured -- and
that they should be calibrated once enough history had accumulated.

I4 only ever looks at the LAST session. This replays it over EVERY session in
every counts-checked archive, which is the only way to see what the band does.

Two numbers decide whether a threshold is worth having:

  fire rate   how often it warns on history we believe is healthy. Near 0%
              means the band is decoration; high means it is noise.
  headroom    how far the widest healthy session sits from the wall. A band
              the data never approaches is not protecting anything.

Reports the ratio distribution per archive so the two can be read off, and
prints the sessions that would have fired.

Read-only. Writes nothing into data/history.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pipeline.tools.audit_archives import ARCHIVES, COUNT_FLOOR, COUNT_CEIL, HISTORY

WINDOW = 20


def ratios(per: pd.Series) -> pd.DataFrame:
    """For each session from the 6th on, n / trailing-window median."""
    rows = []
    for i in range(5, len(per)):
        prev = per.iloc[max(0, i - WINDOW):i]
        med = prev.median()
        if not med:
            continue
        rows.append({"date": per.index[i], "n": int(per.iloc[i]),
                     "median": float(med), "ratio": per.iloc[i] / med})
    return pd.DataFrame(rows)


def main() -> int:
    print(f"I4 band = [{COUNT_FLOOR}x, {COUNT_CEIL}x] of the trailing-{WINDOW} median\n")
    grand = []
    for name, spec in ARCHIVES.items():
        if not spec["counts"]:
            continue
        path = HISTORY / name
        if not path.exists():
            print(f"{name:<24} MISSING"); continue
        f = pd.read_csv(path, low_memory=False)
        dcol = spec["date"]
        if dcol not in f.columns or not len(f):
            print(f"{name:<24} no '{dcol}' column or empty"); continue
        per = f.groupby(f[dcol].astype(str)).size().sort_index()
        r = ratios(per)
        if r.empty:
            print(f"{name:<24} {len(per)} sessions -- too few to judge"); continue
        fires = r[(r.ratio < COUNT_FLOOR) | (r.ratio > COUNT_CEIL)]
        r = r.assign(archive=name)
        grand.append(r)
        print(f"{name:<24} {len(per):>4} sessions, {len(r):>4} judged | "
              f"ratio min {r.ratio.min():.2f}  p05 {r.ratio.quantile(.05):.2f}  "
              f"med {r.ratio.median():.2f}  p95 {r.ratio.quantile(.95):.2f}  "
              f"max {r.ratio.max():.2f} | fires {len(fires)} "
              f"({100*len(fires)/len(r):.1f}%)")
        for _, x in fires.iterrows():
            print(f"    I4 {x.date}: {x.n} rows vs trailing median "
                  f"{x['median']:.0f}  (ratio {x.ratio:.2f})")

    if not grand:
        print("\nnothing to calibrate")
        return 1
    g = pd.concat(grand, ignore_index=True)
    fires = g[(g.ratio < COUNT_FLOOR) | (g.ratio > COUNT_CEIL)]
    print(f"\nALL: {len(g)} session-checks, {len(fires)} fire "
          f"({100*len(fires)/len(g):.2f}%)")
    print(f"     ratio p01 {g.ratio.quantile(.01):.2f}  p05 {g.ratio.quantile(.05):.2f}  "
          f"p95 {g.ratio.quantile(.95):.2f}  p99 {g.ratio.quantile(.99):.2f}")
    print("\nfire rate if the band were tightened:")
    for lo, hi in [(0.30, 3.0), (0.50, 2.0), (0.60, 1.8), (0.70, 1.5), (0.80, 1.25)]:
        k = ((g.ratio < lo) | (g.ratio > hi)).sum()
        print(f"  [{lo:.2f}x, {hi:.2f}x]  {k:>4} / {len(g)}  ({100*k/len(g):.2f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
