"""How far does the half-alphabet window reach into the archives we do research on?

2026-06-26..2026-08-07: Finviz's pagination cap cut the universe in the MIDDLE
OF THE ALPHABET, so 21 sessions carry roughly the A-to-L half only
(`incidents/2026-09-01_half_the_alphabet_missing_for_six_weeks.md`).

Row counts cannot see this -- 06-26 has MORE rows than 06-25. The quantity that
can is the share of tickers whose first letter is M-Z, which a healthy session
puts near 45%. This walks every dated archive with a ticker column and prints
that share for the three periods, so the next study knows before it starts
whether its sample sits inside the window.

    python3 data/research/dirty_window_reach_2026-09-02/measure.py
"""
from __future__ import annotations

import csv
import io
import subprocess
from pathlib import Path

START, END = "2026-06-26", "2026-08-07"      # inclusive, from the incident file

DATE_COLS = ("date", "session", "as_of", "asof", "day", "trade_date", "entry_date")
TICK_COLS = ("ticker", "symbol", "tkr", "t")


def read(path):
    out = subprocess.run(["git", "show", f"origin/main:{path}"],
                         capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else None


def pick(fields, names):
    low = {f.lower(): f for f in fields if f}
    for n in names:
        if n in low:
            return low[n]
    return None


def period(d):
    if d < START:
        return "窗口前"
    if d <= END:
        return "⚠️ 窗口内"
    return "窗口后"


def main():
    paths = subprocess.run(["git", "ls-tree", "origin/main", "data/history/",
                            "--name-only", "-r"],
                           capture_output=True, text=True).stdout.split()
    rows = []
    for p in sorted(paths):
        if not p.endswith(".csv"):
            continue
        raw = read(p)
        if not raw:
            continue
        rdr = csv.DictReader(io.StringIO(raw))
        if not rdr.fieldnames:
            continue
        dcol = pick(rdr.fieldnames, DATE_COLS)
        tcol = pick(rdr.fieldnames, TICK_COLS)
        if not (dcol and tcol):
            continue
        buckets = {}
        for r in rdr:
            d = (r.get(dcol) or "")[:10]
            t = (r.get(tcol) or "").strip().upper()
            if len(d) != 10 or not t or not t[0].isalpha():
                continue
            b = buckets.setdefault(period(d), [0, 0, set()])
            b[0] += 1
            b[1] += t[0] >= "M"
            b[2].add(d)
        if not buckets:
            continue
        rows.append((p, buckets))

    print(f"窗口 = {START} .. {END}（含），判据 = 首字母 M–Z 占比（健康值约 45%）\n")
    hdr = f"{'归档':40s} {'期间':10s} {'行':>8s} {'M–Z%':>7s} {'日期数':>6s}"
    print(hdr); print("-" * len(hdr))
    for p, buckets in rows:
        for name in ("窗口前", "⚠️ 窗口内", "窗口后"):
            b = buckets.get(name)
            if not b:
                continue
            n, mz, dates = b
            print(f"{p:40s} {name:10s} {n:8d} {mz/n:6.1%} {len(dates):6d}")
        print()


if __name__ == "__main__":
    main()
