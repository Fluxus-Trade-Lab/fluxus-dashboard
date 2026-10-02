#!/usr/bin/env python3
"""Reprint every number in this study's README from the archive itself.

The study is about a prose claim that nobody ever re-checked against the data
("universe went 3000 -> 5614 on 2026-08-14"). A study about that failure mode
has no business printing hand-copied numbers, so every figure in the README
comes out of here.

    python3 data/research/universe_break_2026-08-10/verify.py

Reads only `data/history/breadth_archive.csv` at the current checkout. The
standing gate is `pipeline/tests/test_breadth_archive_level_breaks.py`; this
script is the worksheet, that file is the ruler.
"""
from __future__ import annotations

import csv
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ARCHIVE = REPO / "data/history/breadth_archive.csv"

TRUE_BREAK = "2026-08-10"      # first session on the enlarged universe
DOCUMENTED = "2026-08-14"      # the date 7 places in the repo name instead
WINDOW_FROM = "2026-05-01"     # a 3-month pre-break window, long enough that
                               # 4 extra sessions cannot swing a median

COUNT_COLS = ("new_highs", "new_lows", "advances", "declines", "universe_size")
RATIO_COLS = ("pct_above_50sma", "pct_above_200sma", "t2108")


def load() -> list[dict]:
    with ARCHIVE.open() as fh:
        return list(csv.DictReader(fh))


def nums(rows, col, lo, hi, source=None) -> list[float]:
    out = []
    for r in rows:
        if not (lo <= r["date"] < hi):
            continue
        if source is not None and r.get("source") != source:
            continue
        v = (r.get(col) or "").strip()
        if v in ("", "nan"):
            continue
        out.append(float(v))
    return out


def discontinuities(rows, threshold=0.20):
    """Sessions where universe_size jumps by more than `threshold`."""
    out, prev = [], None
    for r in rows:
        v = (r.get("universe_size") or "").strip()
        if v in ("", "nan"):
            continue
        u = float(v)
        if prev and prev[1] > 0 and abs(u / prev[1] - 1) >= threshold:
            out.append((prev[0], prev[1], prev[2], r["date"], u, r["source"]))
        prev = (r["date"], u, r["source"])
    return out


def restated_runs(rows):
    runs, cur = [], None
    for r in rows:
        if r.get("source") != "live":
            if cur and cur[2] == r["source"]:
                cur = (cur[0], r["date"], r["source"], cur[3] + 1)
            else:
                if cur:
                    runs.append(cur)
                cur = (r["date"], r["date"], r["source"], 1)
        elif cur:
            runs.append(cur)
            cur = None
    if cur:
        runs.append(cur)
    return runs


def main() -> None:
    rows = load()
    print(f"archive: {len(rows)} sessions, {rows[0]['date']} .. {rows[-1]['date']}\n")

    print("§1  universe_size discontinuities >= 20%")
    for d0, u0, s0, d1, u1, s1 in discontinuities(rows):
        print(f"     {d0} {u0:.0f} ({s0})  ->  {d1} {u1:.0f} ({s1})"
              f"   {(u1 / u0 - 1) * 100:+.1f}%")

    print("\n§2  restated (source != live) runs")
    for a, b, s, n in restated_runs(rows):
        print(f"     {s:>8}  {a} .. {b}  ({n} sessions)")

    print("\n§3  why a live-only reader lands on the wrong date")
    live_before = [r for r in rows if r["source"] == "live" and r["date"] < TRUE_BREAK]
    live_after = [r for r in rows if r["source"] == "live" and r["date"] >= TRUE_BREAK]
    print(f"     last live row before the break : {live_before[-1]['date']}"
          f"  universe {live_before[-1]['universe_size']}")
    print(f"     first live row after the break : {live_after[0]['date']}"
          f"  universe {live_after[0]['universe_size']}")
    print(f"     -> a live-only reader sees the jump at {live_after[0]['date']},"
          f" {len([r for r in rows if TRUE_BREAK <= r['date'] < live_after[0]['date']])}"
          " sessions late")

    print("\n§4  the two ranges nhnl_4w.md printed, replicated")
    last_live_run = nums(rows, "new_highs", "2026-07-27", TRUE_BREAK, source="live")
    next_live_run = nums(rows, "new_highs", DOCUMENTED, "2026-08-29", source="live")
    print(f"     live 2026-07-27..08-06 new_highs : {min(last_live_run):.0f}"
          f"-{max(last_live_run):.0f}  (n={len(last_live_run)})   doc says 16-39")
    print(f"     live from {DOCUMENTED} new_highs    : {min(next_live_run):.0f}"
          f"-{max(next_live_run):.0f}  (n={len(next_live_run)})   doc says 35-86")

    print("\n§5  cost of splicing 4 sessions late (pre-break window"
          f" {WINDOW_FROM} .. splice)")
    print(f"     {'column':>17} | {'median':>15} | {'max':>15}")
    print(f"     {'':>17} | {'true':>7} {'late':>7} | {'true':>7} {'late':>7}")
    for col in COUNT_COLS + RATIO_COLS:
        a = nums(rows, col, WINDOW_FROM, TRUE_BREAK)
        b = nums(rows, col, WINDOW_FROM, DOCUMENTED)
        if not a or not b:
            continue
        tag = "count" if col in COUNT_COLS else "ratio"
        print(f"     {col:>17} | {st.median(a):>7.2f} {st.median(b):>7.2f}"
              f" | {max(a):>7.1f} {max(b):>7.1f}   {tag}")

    print("\n§6  the four sessions that land on the wrong side")
    for r in rows:
        if TRUE_BREAK <= r["date"] < DOCUMENTED:
            print(f"     {r['date']}  source={r['source']:>8}"
                  f"  universe={r['universe_size']:>5}"
                  f"  new_highs={r['new_highs']:>3}"
                  f"  pct_above_50sma={r['pct_above_50sma']}")


if __name__ == "__main__":
    main()
