"""06-26 那晚之后，页面上那几张单子换了什么人。

筛子本身从来没有市值条件——市值条件在**宇宙**那一层（Finviz 筛选串 `cap_1.0to`）。
06-26 那道条件不再生效之后，筛子原样照跑，但它挑的池子换了人，
于是页面上那几张单子一夜之间从「全是 ≥$10 亿」变成「三分之一到三分之二是小票」。
**没有任何一次提交决定过这件事。**

被闸住的那两张（`watchlist` / `shortlist`，走 tradeable：市值 ≥$300M 且日成交额 ≥$2M）
没有跟着变——这条边界很重要，别把两类混为一谈。

    python3 data/research/breadth_universe_break_2026-09-18/panels_after_the_break.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from typing import List, Optional

sys.path.insert(0, 'data/research/breadth_universe_break_2026-09-18')
from population_reach import snapshots        # noqa: E402

BILLION = 1e9
# (当日 universe.json 快照所在的 commit, 该 commit 的 ET 场次)
COLUMNS = (('552e929d', '2026-06-25'),      # 断点前最后一场
           ('31f983ef', '2026-06-26'),      # 断点当晚
           ('88295474', '2026-09-15'))      # 最近一场完整正班
FILES = ('gainers_4pct', 'vol_up_gainers', 'momentum_97',
         'healthy_charts', 'ema21_watch', 'watchlist')


def tickers(obj, out: List[str]) -> None:
    if isinstance(obj, dict):
        t = obj.get('ticker') or obj.get('symbol')
        if isinstance(t, str) and 1 <= len(t) <= 6 \
                and t.replace('.', '').isalpha() and t.isupper():
            out.append(t)
        for v in obj.values():
            tickers(v, out)
    elif isinstance(obj, list):
        for v in obj:
            tickers(v, out)


def payload(commit: str, path: str) -> Optional[dict]:
    raw = subprocess.run(['git', 'show', f'{commit}:{path}'],
                         capture_output=True, text=True).stdout
    if not raw.strip():
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def main() -> None:
    snaps = snapshots()
    print(f'{"发布的单子":18s}' + ''.join(f'{day:>24s}' for _, day in COLUMNS))
    for name in FILES:
        cells = []
        for commit, day in COLUMNS:
            caps = snaps.get(day)
            data = payload(commit, f'data/output/{name}.json')
            if data is None or caps is None:
                cells.append('（当日无此文件）')
                continue
            found: List[str] = []
            tickers(data, found)
            known = [t for t in sorted(set(found)) if t in caps]
            if not known:
                cells.append('（无可判票）')
                continue
            small = 100 * sum(1 for t in known if caps[t] < BILLION) / len(known)
            cells.append(f'n={len(known):4d}  <$1B {small:5.1f}%')
        print(f'{name:18s}' + ''.join(f'{c:>24s}' for c in cells))
    print('\n（`watchlist` 走 tradeable 闸，没有跟着变；上面五张没有闸。）')


if __name__ == '__main__':
    main()
