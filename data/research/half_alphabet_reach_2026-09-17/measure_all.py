"""Every dated archive in data/history/, measured against the half-alphabet window.

Successor to `dirty_window_reach_2026-09-02/measure.py`, which silently skipped
any CSV without a ticker column -- and so never saw `breadth_archive.csv`, whose
06-26..08-07 rows were counted on a ~3,000-name (A-to-L) universe. Nothing is
skipped silently here: a file that cannot be judged is printed with the reason.

"DATES OK" only means no row is dated inside the window. It does NOT clear a
derived archive whose writer looks back into the window -- `shortlist_log` and
`shortlist_seat_log` are DATES OK yet their heat seat reads 15 archive dates of
`ticker_events` (dirty through 2026-08-28). Inheritance lives in the writer's
code, so read the README table before trusting a DATES OK line.

Two tells, because not every archive has tickers:
  * ticker archives  -> share of first letters M-Z (healthy ~45%)
  * aggregate rows   -> `universe_size` if present (window rows sit at ~3,000,
                        the 150-page x 20-row cap; before ~2,590, after ~5,620)

    python3 data/research/half_alphabet_reach_2026-09-17/measure_all.py
"""
from __future__ import annotations

import csv
import io
import subprocess

START, END = "2026-06-26", "2026-08-07"   # as the studies saw it (08-07 was
                                          # recomputed only on 2026-09-13)
CAP = 3000

DATE_COLS = ("date", "session", "as_of", "asof", "day", "trade_date", "entry_date")
TICK_COLS = ("ticker", "symbol", "tkr", "t")


def git(*args):
    out = subprocess.run(["git", *args], capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else None


def pick(fields, names):
    low = {f.lower(): f for f in fields if f}
    for n in names:
        if n in low:
            return low[n]
    return None


def judge(path):
    raw = git("show", f"origin/main:{path}")
    if raw is None:
        return ("SKIP", "unreadable")
    rdr = csv.DictReader(io.StringIO(raw))
    if not rdr.fieldnames:
        return ("SKIP", "no header")
    dcol = pick(rdr.fieldnames, DATE_COLS)
    if not dcol:
        return ("SKIP", f"no date column in {rdr.fieldnames[:6]}")
    tcol = pick(rdr.fieldnames, TICK_COLS)
    ucol = "universe_size" if "universe_size" in rdr.fieldnames else None
    first = last = None
    n_in = n_all = mz_in = mz_out = t_in = t_out = 0
    capped = set()
    win_dates = set()
    for r in rdr:
        d = (r.get(dcol) or "")[:10]
        if len(d) != 10:
            continue
        n_all += 1
        first = d if first is None or d < first else first
        last = d if last is None or d > last else last
        inside = START <= d <= END
        if inside:
            n_in += 1
            win_dates.add(d)
        if tcol:
            t = (r.get(tcol) or "").strip().upper()
            if t[:1].isalpha():
                is_mz = t[0] >= "M"
                if inside:
                    t_in += 1; mz_in += is_mz
                else:
                    t_out += 1; mz_out += is_mz
        if ucol and inside:
            try:
                if abs(int(float(r[ucol])) - CAP) <= 30:
                    capped.add(d)
            except (TypeError, ValueError):
                pass
    if n_in == 0:
        return ("DATES OK", f"{first}..{last}, {n_all} rows, 0 in window "
                "(inheritance through a writer's lookback is NOT visible here)")
    bits = [f"{first}..{last}", f"{n_in}/{n_all} rows in window ({len(win_dates)} dates)"]
    if tcol:
        bits.append(f"M-Z in {mz_in/max(t_in,1):.1%} vs out {mz_out/max(t_out,1):.1%}")
    if ucol:
        bits.append(f"universe_size within {CAP}±30 on {len(capped)}/{len(win_dates)} window dates")
    if not tcol and not ucol:
        bits.append("no ticker and no universe_size: cannot tell from the file -- check the writer")
    return ("IN WINDOW", "; ".join(bits))


def main():
    paths = (git("ls-tree", "-r", "--name-only", "origin/main", "data/history/") or "").split()
    print(f"window {START}..{END} (as seen by studies run before 2026-09-13)\n")
    for p in sorted(x for x in paths if x.endswith(".csv") or x.endswith(".csv.gz")):
        if p.endswith(".gz"):
            print(f"{'SKIP':10s} {p}: gzip, not read by this script")
            continue
        verdict, detail = judge(p)
        print(f"{verdict:10s} {p}: {detail}")


if __name__ == "__main__":
    main()
