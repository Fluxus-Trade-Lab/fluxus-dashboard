"""06-26 那个人口断点，咬到归档里多少行——以及给研究用的分类器。

`population_break.py` 证明的是：2026-06-26 那一晚宇宙从「≥$10 亿市值」变成
「全市值」。本脚本量它在事件归档里的份额，并留一个 `is_core()` 给别的研究调用，
用来把「老宇宙本来就有的票」和「06-26 之后才进来的票」分开算。

口径：每个场次用**当日（取不到就最近一份更早的）** `data/output/universe.json`
快照里的 `market_cap`，$10 亿为界。快照按自身 `timestamp` 转 ET 定场次
（不按 git 提交日——DATA_RELIABILITY §256 的坑，本目录另一个脚本栽过一次）。

⚠️ 这是**自造的分类**，不是任何标准口径：$10 亿这条线取自 Finviz 筛选串
`f=cap_1.0to` 在 06-25 之前实际生效时的效果（那天 $1B 以下占 0.0%），
不是外部方法书里的定义。引用时写明它是自造的。

    python3 data/research/breadth_universe_break_2026-09-18/population_reach.py
"""
from __future__ import annotations

import collections
import csv
import datetime
import json
import subprocess
import zoneinfo
from functools import lru_cache
from typing import Dict, Optional

ET = zoneinfo.ZoneInfo('America/New_York')
BILLION = 1e9
BREAK = '2026-06-26'


def _et_day(ts) -> Optional[str]:
    try:
        dt = datetime.datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    # 2026-09-19 (Zac, verifier catch): label by the last session CLOSED at that
    # instant, not the ET calendar date -- a snapshot written 02:12 ET holds the
    # previous session and used to be stamped with the next date.
    from pipeline.marketcal import last_completed_session
    return last_completed_session(dt.astimezone(ET)).isoformat()


@lru_cache(maxsize=1)
def snapshots(since: str = '2026-03-01') -> Dict[str, Dict[str, float]]:
    """{ET 场次: {ticker: market_cap}}，取自 universe.json 的历史提交。"""
    out: Dict[str, Dict[str, float]] = {}
    hashes = subprocess.run(
        ['git', 'log', '--format=%H', f'--since={since}', '--',
         'data/output/universe.json'], capture_output=True, text=True).stdout.split()
    for h in reversed(hashes):
        raw = subprocess.run(['git', 'show', f'{h}:data/output/universe.json'],
                             capture_output=True, text=True).stdout
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        day = _et_day(payload.get('timestamp'))
        if day:
            out[day] = {r['ticker']: float(r.get('market_cap') or 0)
                        for r in payload['rows']}
    return out


def _caps_for(day: str) -> Optional[Dict[str, float]]:
    snaps = snapshots()
    earlier = [d for d in sorted(snaps) if d <= day]
    return snaps[earlier[-1]] if earlier else None


def is_core(day: str, ticker: str) -> Optional[bool]:
    """这只票在这个场次属不属于「06-26 之前那个宇宙」（市值 ≥$10 亿）。

    返回 None＝那天的快照里没有这只票，判不了（别当成 False）。
    """
    caps = _caps_for(day)
    if caps is None:
        return None
    cap = caps.get(ticker)
    return None if cap is None else cap >= BILLION


def main() -> None:
    per = collections.defaultdict(lambda: [0, 0, 0])   # 行数 / 非核心 / 判不了
    with open('data/history/ticker_events.csv') as fh:
        for row in csv.DictReader(fh):
            day = row['date'][:10]
            core = is_core(day, row['ticker'])
            per[day][0] += 1
            if core is None:
                per[day][2] += 1
            elif not core:
                per[day][1] += 1

    by_month = collections.defaultdict(lambda: [0, 0, 0])
    for day, (n, small, unknown) in per.items():
        m = by_month[day[:7]]
        m[0] += n
        m[1] += small
        m[2] += unknown
    print(f'{"月":8s}{"事件行":>9s}{"<$1B":>9s}{"占比":>8s}{"判不了":>8s}')
    for month in sorted(by_month):
        n, small, unknown = by_month[month]
        known = n - unknown
        print(f'{month:8s}{n:9d}{small:9d}'
              f'{100 * small / known if known else 0:7.1f}%{unknown:8d}')

    print(f'\n断点两侧逐日（{BREAK} 前后）：')
    for day in sorted(per):
        if '2026-06-22' <= day <= '2026-07-02':
            n, small, unknown = per[day]
            known = n - unknown
            print(f'  {day}  n={n:5d}  <$1B {small:4d}'
                  f'  {100 * small / known if known else 0:5.1f}%')


if __name__ == '__main__':
    main()
