"""宇宙在 2026-06-26 换了人口，不只是换了大小。

半字母表事故档把 06-26 记成「翻页封顶开始咬」。封顶确实是那天开始咬的，
但**它是被另一件事推过去的**：同一晚，`cap_1.0to`（≥$10 亿市值）那道筛选
条件不再生效，1,613 只中位市值 1.43 亿的小票一次性进了宇宙，名单当场超过
3,000，150 页的翻页上限才开始截断。

所以 06-26 那一晚有两件事，不是一件：
  ① 人口变了（≥$1B → 全市值）—— 这件**至今没有回去**
  ② 字母表被截断（A–L）—— 这件 08-10 `2f782b53` 修好了

`coverage_gaps.json` 现在把 08-10 记成「universe size 约 2,590 → 约 5,620」，
但 2,590 是**≥$1B 的那批**，5,620 是**全市值的那批**——两个数之间不是同一批
东西变多了，是换了一批人。跨 06-26 比任何全宇宙家数，比的都是两个人口。

⚠️ 快照按**它自己的 `timestamp`**（转 ET）定日期，不按 git 提交日——
`DATA_RELIABILITY.md` §256 记过这个坑：`backfill_preset_hits.py` 拿
`git log --date=short` 给同一批快照定日期，错了一整轮。本脚本第一版也栽在
同一处（JST 的提交日把 06-25 的快照算成了 06-26），故意留这条注释。

    python3 data/research/breadth_universe_break_2026-09-18/population_break.py
"""
from __future__ import annotations

import datetime
import json
import statistics as st
import subprocess
import zoneinfo
from typing import Dict, List, Optional, Tuple

ET = zoneinfo.ZoneInfo('America/New_York')
BILLION = 1e9
SINCE, UNTIL = '2026-06-15', '2026-09-19'
SHOW = ('2026-06-23', '2026-06-24', '2026-06-25', '2026-06-26',
        '2026-06-29', '2026-08-06', '2026-08-11', '2026-09-15', '2026-09-16')


def snapshots(since: str, until: str) -> Dict[str, Tuple[str, List[Dict]]]:
    """{ET 场次日期: (commit, rows)} —— 同一场次多份时取最后一份。"""
    out: Dict[str, Tuple[str, List[Dict]]] = {}
    hashes = subprocess.run(
        ['git', 'log', '--format=%H', f'--since={since}', f'--until={until}',
         '--', 'data/output/universe.json'],
        capture_output=True, text=True).stdout.split()
    for h in reversed(hashes):               # 旧 → 新
        raw = subprocess.run(['git', 'show', f'{h}:data/output/universe.json'],
                             capture_output=True, text=True).stdout
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        day = _et_day(payload.get('timestamp'))
        if day:
            out[day] = (h, payload['rows'])
    return out


def _et_day(ts: Optional[str]) -> Optional[str]:
    if not ts:
        return None
    try:
        dt = datetime.datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    # 2026-09-19 (Zac, verifier catch): label by the last session CLOSED at that
    # instant, not the ET calendar date -- a snapshot written 02:12 ET holds the
    # previous session and used to be stamped with the next date.
    from pipeline.marketcal import last_completed_session
    return last_completed_session(dt.astimezone(ET)).isoformat()


def caps(rows: List[Dict]) -> List[float]:
    return sorted(float(r['market_cap']) for r in rows
                  if r.get('market_cap') not in (None, ''))


def main() -> None:
    snaps = snapshots(SINCE, UNTIL)
    print(f'{"ET 场次":<12}{"commit":<10}{"只数":>7}{"市值中位":>12}{"<$1B":>8}  字母序最大')
    for day in SHOW:
        if day not in snaps:
            print(f'{day:<12}（当日无快照）')
            continue
        h, rows = snaps[day]
        c = caps(rows)
        share = 100 * sum(1 for x in c if x < BILLION) / len(c)
        print(f'{day:<12}{h[:8]:<10}{len(rows):>7}{st.median(c):>12.4g}'
              f'{share:>7.1f}%  {max(r["ticker"] for r in rows)}')

    before, after = snaps.get('2026-06-25'), snaps.get('2026-06-26')
    if not (before and after):
        print('\n06-25 / 06-26 快照缺失，跳过逐票对账')
        return
    a = {r['ticker']: r for r in before[1]}
    b = {r['ticker']: r for r in after[1]}

    print('\n== 06-25 → 06-26 这一晚，逐票对账 ==')
    common = sorted(set(a) & set(b))
    drift = [abs(float(b[t]['market_cap']) - float(a[t]['market_cap']))
             / max(float(a[t]['market_cap']), 1.0)
             for t in common if a[t].get('market_cap') and b[t].get('market_cap')]
    print(f'交集 {len(common)} 只，同名票市值相对变动中位 {st.median(drift):.4f}'
          f' —— 字段没换口径，换的是名单')

    new = [t for t in b if t not in a]
    nc = sorted(float(b[t]['market_cap']) for t in new
                if b[t].get('market_cap') not in (None, ''))
    print(f'新进 {len(new)} 只：市值中位 {st.median(nc):.4g}，'
          f'{100 * sum(1 for x in nc if x < BILLION) / len(nc):.1f}% 在 $1B 以下')

    gone = [t for t in a if t not in b]
    print(f'掉出 {len(gone)} 只，其中字母序 > L 的 '
          f'{sum(1 for t in gone if t[:1].upper() > "L")} 只 —— 那是翻页截断，不是被筛掉')

    def al_over(s):
        return sum(1 for t in s if t[:1].upper() <= 'L'
                   and float(s[t].get('market_cap') or 0) >= BILLION)
    print(f'A–L 且 ≥$1B 的只数：06-25 {al_over(a)} → 06-26 {al_over(b)}'
          f' —— 老那批人没少，是新来了一批')


if __name__ == '__main__':
    main()
