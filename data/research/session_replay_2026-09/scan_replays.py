"""Has any other archive ever replayed a whole session?

2026-09-02's `delayed_ep_log` is a bit-for-bit copy of 09-01 (same 36 tickers,
16 of 17 data columns identical row-for-row). Three witnesses now agree on that
one day. The question this asks is the obvious next one and nobody has asked
it: is that day unique in the repo, or is it the one instance we happened to
trip over?

The test needs no vendor data and no calendar. For every archive that carries a
date and a ticker, take consecutive sessions, restrict to the tickers present
in both, and ask what fraction of the (row x column) cells are byte-identical.

Two things this deliberately does NOT do:

  * It does not use "did anything change" as the verdict. A replayed session can
    have a column that changes -- 09-02's `today_relvol` changed in 36/36 rows,
    which is exactly why every freshness check passed it
    ([[pitfall_ask_whether_it_advanced_not_whether_it_changed]]).
  * It does not compare rows positionally. Rows are keyed by ticker, so a
    reordered file is not a false positive.

The number reported per column is "of the tickers in both sessions, how many
held the identical string". A column that is SUPPOSED to be sticky (sector,
a name, a seat label) will sit near 100% on every pair -- so the read is not the
absolute level, it is whether ONE pair stands away from that archive's own
baseline. Each archive is its own control.

  PYTHONPATH=. python3 data/research/session_replay_2026-09/scan_replays.py
"""
from __future__ import annotations
import csv
import pathlib
import statistics

HIST = pathlib.Path("data/history")
DATE_COLS = ("as_of", "date")
TICK_COLS = ("ticker", "symbol")
MIN_COMMON = 5          # fewer shared names than this and the pair says nothing


def load(path: pathlib.Path):
    with path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        return None
    hdr = list(rows[0])
    dcol = next((c for c in DATE_COLS if c in hdr), None)
    tcol = next((c for c in TICK_COLS if c in hdr), None)
    if not dcol or not tcol:
        return None
    return rows, dcol, tcol, [c for c in hdr if c not in (dcol, tcol)]


def main() -> int:
    print("整场重放扫描 —— 相邻两场之间,共同票的单元格逐字相同比例")
    print("(每个归档拿自己的历史当基线;要看的是有没有 ONE 对站得离基线特别远)\n")
    findings = []
    for path in sorted(HIST.glob("*.csv")):
        got = load(path)
        if not got:
            continue
        rows, dcol, tcol, datacols = got
        by_date: dict[str, dict[str, dict]] = {}
        for r in rows:
            by_date.setdefault(r[dcol], {})[r[tcol]] = r
        dates = sorted(by_date)
        if len(dates) < 3:
            continue
        pairs = []
        for a, b in zip(dates, dates[1:]):
            common = set(by_date[a]) & set(by_date[b])
            if len(common) < MIN_COMMON:
                continue
            cells = same = 0
            full_cols = 0
            for c in datacols:
                col_same = sum(1 for t in common if by_date[a][t].get(c) == by_date[b][t].get(c))
                cells += len(common)
                same += col_same
                if col_same == len(common):
                    full_cols += 1
            pairs.append((b, same / cells, full_cols, len(common), a))
        if not pairs:
            continue
        shares = [p[1] for p in pairs]
        med = statistics.median(shares)
        worst = max(pairs, key=lambda p: p[1])
        print(f"{path.name:<28} {len(pairs):>3} 对相邻场 | 逐字相同比例 中位 {med*100:5.1f}%  "
              f"最高 {worst[1]*100:5.1f}% ({worst[4]} -> {worst[0]}, "
              f"{worst[2]}/{len(datacols)} 列整列相同, 共同票 {worst[3]})")
        # a pair is called out only if it stands away from this archive's own baseline
        if worst[1] > 0.80 and worst[1] - med > 0.30:
            findings.append((path.name, worst))
    print()
    if findings:
        print("🔴 站得离自己基线特别远的场次:")
        for name, w in findings:
            print(f"  {name}: {w[4]} -> {w[0]}  逐字相同 {w[1]*100:.1f}%  "
                  f"整列相同 {w[2]} 列  共同票 {w[3]}")
    else:
        print("没有任何一对站得离自己的基线特别远。")
    print("\n⚠️ 这个扫描只看得见「整场复制」这一种坏法。一场重新跑过、但用了错的输入,")
    print("   在这里是完全正常的 —— 它要另一类检查(对日历 / 跨归档 / 对厂商)。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
