"""前端不许拿常数去判「家数类」读数。

家数类字段（up_4pct、新高新低、季度价差……）的量级跟着 universe_size 走：
2026-08-10 `2f782b53` 把 Finviz 翻页上限从 150 抬到 600 之后，宇宙从约 2,600
翻到约 5,620，同一个市场的家数直接翻倍。管线那边当天就把 thrust 门槛改成
`max(60, 0.113 × universe_size)`（`breadth_signals.thrust_count`，`16db6a88b`），
那次 commit message 自己写明了防线：

    state_board imports the same function rather than keeping its own copy of
    the constant, which is how the two would have drifted

`state_board.py` 照做了。前端 `MarketStateSummary.jsx` 里那份拷贝没人知道它
存在，于是漂了：2026-08-10..09-16 的 27 场里有 20 场，牌面上那个词和引擎
自己的读数相反（量在 `data/research/breadth_universe_break_2026-09-18/`）。

这条规矩在仓库里被写过五遍（`segments.js`、`VerdictCard.jsx`、`useUniverse.js`、
`VoteGlyphs.jsx`、上面那条 commit message），被违反了一次——所以它该是一道闸，
不是一句注释。

**范围**：只管家数类字段。比率型（ratio_5d、t2108、pct_above_*）不随宇宙规模
变，前端拿它们分配色档是显示，不是这条闸要管的事。
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple

FRONTEND = Path(__file__).resolve().parents[2] / 'frontend' / 'src'

# 随 universe_size 缩放的家数类 payload 字段。比率型字段故意不在这里。
COUNT_FIELDS = (
    'up_4pct', 'down_4pct',
    'new_highs', 'new_lows',
    'up_25pct_qtr', 'down_25pct_qtr',
    'up_25pct_month', 'down_25pct_month',
    'up_50pct_month', 'down_50pct_month',
    'up_13pct_34d', 'down_13pct_34d',
    'advances', 'declines', 'net_advances',
)

# 「字段 …… 比较号 …… 裸数字」或反过来，同一行。
_CMP = re.compile(r'(?:[<>]=?|===|!==)\s*(-?\d+(?:\.\d+)?)'
                  r'|(?<![\w.])(-?\d+(?:\.\d+)?)\s*(?:[<>]=?)')


def _thresholds_in(code: str) -> List[str]:
    """这一行拿来和家数比的那些数字。

    和 0 比是**符号判断**（net advances 是正是负），不随宇宙规模变，所以不算
    阈值——`CourseRead.jsx` 的 `net > 0` 就是这一类，不该报。
    """
    nums = [a or b for a, b in _CMP.findall(code)]
    return [n for n in nums if float(n) != 0]

# 判过的行：key = (相对路径, 该行去空白后的片段)，value = 为什么放行。
# 行号会漂，所以锚在代码文本上。
ALLOWED: dict = {}

# 已知缺陷：闸看得见它，但不因为它把 main 判红（修它的是 UI Claire 的文件）。
# 修好之后这里的条目会匹配不上，下面的测试会要求删掉它——不会烂在这儿。
KNOWN_DEFECTS = {
    ('components/breadth/MarketStateSummary.jsx',
     "(mm.up_4pct??0)>=300&&(mm.down_4pct??0)>=300?'churn/volatile'"):
        '2026-09-18 Nighty Zac：门槛该取 verdict.vote_detail 里 thrust 的 line（今日 634），已门铃 UI Claire',
    ('components/breadth/MarketStateSummary.jsx',
     ":(mm.up_4pct??0)>=300?'bullishthrust'"):
        '同上，同一个 thrustLabel 三元式',
    ('components/breadth/MarketStateSummary.jsx',
     ":(mm.down_4pct??0)>=300?'bearishthrust'"):
        '同上，同一个 thrustLabel 三元式',
}


def _key(line: str) -> str:
    return re.sub(r'\s+', '', line)


def scan_text(text: str) -> List[Tuple[int, str]]:
    """返回 (行号, 原行) —— 拿裸数字去比较家数类字段的那些行。"""
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        code = line.split('//')[0]
        if not any(f in code for f in COUNT_FIELDS):
            continue
        if _thresholds_in(code):
            hits.append((i, line.strip()))
    return hits


def scan_frontend() -> List[Tuple[str, int, str]]:
    out = []
    for path in sorted(FRONTEND.rglob('*.js*')):
        rel = path.relative_to(FRONTEND).as_posix()
        for lineno, line in scan_text(path.read_text(encoding='utf-8')):
            out.append((rel, lineno, line))
    return out


# ─────────────────────────────────────────────── 先证明它报得出阳性，再信它的阴性

def test_scanner_flags_a_count_threshold():
    """阳性对照：正是把 MarketStateSummary 那一行改瘦了也照样命中。"""
    hits = scan_text("const x = (mm.up_4pct ?? 0) >= 300 ? 'thrust' : 'no'\n")
    assert len(hits) == 1, hits


def test_scanner_ignores_ratio_fields_and_comments():
    """阴性对照：比率型字段、以及注释里提到的数字，都不该命中。"""
    assert scan_text("const y = mm.ratio_5d >= 1.5 ? 'bull' : 'bear'\n") == []
    assert scan_text("// up_4pct >= 300 used to mean a thrust\n") == []
    assert scan_text("Today {net > 0 ? '+' : ''} net advances.\n") == [], '和 0 比是符号判断'
    assert scan_text("value={`${mm.up_4pct ?? '—'} / ${mm.down_4pct ?? '—'}`}\n") == []


# ─────────────────────────────────────────────────────────────────────── 真扫描

def test_no_new_count_thresholds_in_the_frontend():
    unknown = []
    for rel, lineno, line in scan_frontend():
        key = (rel, _key(line))
        if key in ALLOWED or key in KNOWN_DEFECTS:
            continue
        unknown.append(f'{rel}:{lineno}  {line}')
    assert not unknown, (
        '前端拿常数判了家数类字段——宇宙规模一变这个判定就错（见本文件顶部）。\n'
        '要么改成读 payload 里管线给的那条线，要么在 ALLOWED 里写明为什么它不受影响：\n  '
        + '\n  '.join(unknown))


def test_known_defect_entries_still_match():
    """缺陷修好之后，这里的条目必须被删掉——否则闸会替一段不存在的代码站岗。"""
    live = {(rel, _key(line)) for rel, _, line in scan_frontend()}
    stale = [f'{rel}  {frag}' for (rel, frag) in KNOWN_DEFECTS if (rel, frag) not in live]
    assert not stale, (
        'KNOWN_DEFECTS 里这些条目已经匹配不上任何一行了——大概是修好了，请删掉它们：\n  '
        + '\n  '.join(stale))
