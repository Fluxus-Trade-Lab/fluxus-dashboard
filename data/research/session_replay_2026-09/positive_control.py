"""Can the scan fire on the archives it just reported clean?

`scan_replays.py` found exactly one replayed session, in `delayed_ep_log`. That
is a REAL positive control for that one file. It says nothing about whether the
same detector could have fired on `leaders_log` or `ticker_events` -- and an
all-clear from a detector that has never been shown to fire on a given file is
not evidence about that file
(Growth Gary, 2026-08-25: 没有先验证一个检查能报出阳性,就不该信它的阴性).

So: take each archive, forge a replay in it (overwrite the last session's rows
with the previous session's values, keeping the date stamp -- exactly the shape
09-02 has), and check the detector calls it out.

  PYTHONPATH=. python3 data/research/session_replay_2026-09/positive_control.py
"""
from __future__ import annotations
import csv
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from scan_replays import DATE_COLS, MIN_COMMON, TICK_COLS  # noqa: E402

HIST = pathlib.Path("data/history")


def pair_share(a_rows, b_rows, datacols):
    common = set(a_rows) & set(b_rows)
    if len(common) < MIN_COMMON:
        return None, 0, 0
    cells = same = full = 0
    for c in datacols:
        cs = sum(1 for t in common if a_rows[t].get(c) == b_rows[t].get(c))
        cells += len(common); same += cs
        full += (cs == len(common))
    return same / cells, full, len(common)


def main() -> int:
    print("阳性对照 —— 在每个归档里伪造一场重放,看扫描报不报得出来\n")
    print(f"  {'归档':<26}{'基线中位':>10}{'伪造场':>10}{'报出?':>8}")
    ok = bad = 0
    for path in sorted(HIST.glob("*.csv")):
        with path.open(newline="") as fh:
            rows = list(csv.DictReader(fh))
        if not rows:
            continue
        hdr = list(rows[0])
        dcol = next((c for c in DATE_COLS if c in hdr), None)
        tcol = next((c for c in TICK_COLS if c in hdr), None)
        if not dcol or not tcol:
            continue
        datacols = [c for c in hdr if c not in (dcol, tcol)]
        by_date: dict[str, dict[str, dict]] = {}
        for r in rows:
            by_date.setdefault(r[dcol], {})[r[tcol]] = r
        dates = sorted(by_date)
        if len(dates) < 3:
            continue
        shares = []
        for a, b in zip(dates, dates[1:]):
            s, _, _ = pair_share(by_date[a], by_date[b], datacols)
            if s is not None:
                shares.append(s)
        if not shares:
            continue
        med = statistics.median(shares)
        # forge: last session becomes a copy of the one before it
        prev, last = dates[-2], dates[-1]
        forged = {t: dict(r) for t, r in by_date[prev].items()}
        for r in forged.values():
            r[dcol] = last
        s, full, n = pair_share(by_date[prev], forged, datacols)
        fired = s is not None and s > 0.80 and s - med > 0.30
        ok += fired; bad += (not fired)
        print(f"  {path.name:<26}{med*100:9.1f}%{(s or 0)*100:9.1f}%{'  ✅ 报出' if fired else '  ❌ 漏报'}")
    print(f"\n  {ok} 个归档上报得出,{bad} 个漏报。")
    print("  漏报的那些,`scan_replays.py` 对它们的「干净」不构成证据 —— 它在那里是瞎的。")

    # ---------------------------------------------------------------- 分辨率
    print("\n完美重放太容易了。真实的 09-02 是 90.5%,不是 100% —— 它有一列全变了")
    print("(`today_relvol` 36/36 都变),而那正是它躲过所有新鲜度检查的原因。")
    print("所以真正要问的是:一场重放里可以有几列是新的,这个扫描还看得见?\n")
    print(f"  {'归档':<26}{'数据列':>7}{'还能看见的最多新列数':>22}")
    for path in sorted(HIST.glob("*.csv")):
        with path.open(newline="") as fh:
            rows = list(csv.DictReader(fh))
        if not rows:
            continue
        hdr = list(rows[0])
        dcol = next((c for c in DATE_COLS if c in hdr), None)
        tcol = next((c for c in TICK_COLS if c in hdr), None)
        if not dcol or not tcol:
            continue
        datacols = [c for c in hdr if c not in (dcol, tcol)]
        by_date = {}
        for r in rows:
            by_date.setdefault(r[dcol], {})[r[tcol]] = r
        dates = sorted(by_date)
        if len(dates) < 3:
            continue
        shares = []
        for a, b in zip(dates, dates[1:]):
            s, _, _ = pair_share(by_date[a], by_date[b], datacols)
            if s is not None:
                shares.append(s)
        if not shares:
            continue
        med = statistics.median(shares)
        prev, last = dates[-2], dates[-1]
        common = set(by_date[prev]) & set(by_date[last])
        if len(common) < MIN_COMMON:
            continue
        # order columns by how much they actually move between these two sessions;
        # the most-moving ones are the realistic candidates for "genuinely new"
        movement = sorted(datacols, key=lambda c: sum(
            1 for t in common if by_date[prev][t].get(c) != by_date[last][t].get(c)), reverse=True)
        limit = -1
        for k in range(len(datacols) + 1):
            forged = {t: dict(by_date[prev][t]) for t in common}
            for t in common:
                forged[t][dcol] = last
                for c in movement[:k]:
                    forged[t][c] = by_date[last][t].get(c)
            s, _, _ = pair_share({t: by_date[prev][t] for t in common}, forged, datacols)
            if s is not None and s > 0.80 and s - med > 0.30:
                limit = k
            else:
                break
        print(f"  {path.name:<26}{len(datacols):>7}{limit:>22}")
    print("\n  「最多新列数」是这个扫描的分辨率地板:超过它,一场重放就变成看不见的。")
    print("  delayed_ep 的 09-02 只有 1~2 列是新的,所以它在带宽之内 —— 这是运气不是设计。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
