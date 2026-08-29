"""WHAT CHANGED -- turn段 2 of the letter from recall into a checklist.

OPS hung this one on 2026-08-30 (`Fluxus_Brand/ops/CONTENT_FLOW.md`, the
"盘面读数" row): the weekly letter's section 2 asks Andy for **one reading
that moved, from what to what**, and today he has to remember which one. The
readings are all already archived. Nobody diffs them.

So: read the archives, diff a week, and hand back a ranked candidate list he
ticks instead of recalls.

WHAT MAKES A READING A CANDIDATE
--------------------------------
Not "it changed" -- everything changes. A candidate is a reading whose weekly
move is **large against its own history of weekly moves**. Each metric is
scored by the percentile of |this week's change| within every overlapping
`span`-session change that metric has ever made.

That percentile is descriptive, not a p-value. Overlapping windows share
sessions, so the changes are heavily autocorrelated and the tail counts are
not independent draws. It answers "have we seen a move this big before, and
how often" -- which is exactly what section 2 needs, and is *not* a claim
that the move is significant.

THE RESOLUTION FLOOR (the reason this file has three tiers)
-----------------------------------------------------------
The three archives do not have the same history, and pretending they do would
manufacture confident numbers out of nothing:

  breadth_archive.csv   574 sessions (2024-05-15 ->)   rankable
  groups_archive.csv      8 sessions (2026-08-19 ->)   not rankable
  regime_ledger.csv       7 sessions (2026-08-20 ->)   not rankable

A percentile off 7 observations has a resolution floor of ~14 percentage
points; it would print `p100` for any move at all. So regime and group
readings are reported with their raw change and explicitly labelled
`no-baseline` -- they are still worth Andy's eye, they just do not get a
rank. When those archives reach MIN_HISTORY they get ranked automatically.

Group *state* flips (Leading <-> Lagging) are the exception: a flip is
categorical, needs no distribution, and is reported from whatever history
exists.

Usage:
    python3 what_changed.py                       # last completed session
    python3 what_changed.py --asof 2026-08-28 --span 5
    python3 what_changed.py --out candidates.md --json candidates.json
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

ROOT = Path(__file__).resolve().parents[3]
BREADTH = ROOT / "data/history/breadth_archive.csv"
REGIME = ROOT / "data/history/regime_ledger.csv"
GROUPS = ROOT / "data/history/groups_archive.csv"

# Fewer than this many span-changes and a percentile is finer than the data.
# 40 overlapping 5-session changes is ~9 non-overlapping weeks; below that the
# floor on the reported percentile is coarser than the differences between
# candidates, so the ranking would be noise wearing a number.
MIN_HISTORY = 40

# label, column, unit, one-line English phrasing for the letter's section 2.
# "{a}" is last week's value, "{b}" this week's.
BREADTH_METRICS: Sequence[Dict[str, str]] = (
    {"label": "20 日线上占比", "col": "pct_above_20sma", "unit": "%",
     "en": "the share of names above their 20-day went from {a} to {b}"},
    {"label": "50 日线上占比", "col": "pct_above_50sma", "unit": "%",
     "en": "the share of names above their 50-day went from {a} to {b}"},
    {"label": "200 日线上占比", "col": "pct_above_200sma", "unit": "%",
     "en": "the share of names above their 200-day went from {a} to {b}"},
    {"label": "T2108", "col": "t2108", "unit": "",
     "en": "T2108 went from {a} to {b}"},
    {"label": "4% 上涨家数", "col": "up_4pct", "unit": "只",
     "en": "names up 4% in a day went from {a} to {b}"},
    {"label": "4% 下跌家数", "col": "down_4pct", "unit": "只",
     "en": "names down 4% in a day went from {a} to {b}"},
    {"label": "5 日涨跌比", "col": "ratio_5d", "unit": "",
     "en": "the 5-day up/down ratio went from {a} to {b}"},
    {"label": "10 日涨跌比", "col": "ratio_10d", "unit": "",
     "en": "the 10-day up/down ratio went from {a} to {b}"},
    {"label": "新高家数", "col": "new_highs", "unit": "只",
     "en": "new highs went from {a} to {b}"},
    {"label": "新低家数", "col": "new_lows", "unit": "只",
     "en": "new lows went from {a} to {b}"},
    {"label": "净上涨", "col": "net_advances", "unit": "",
     "en": "net advances went from {a} to {b}"},
    {"label": "麦克莱伦振荡", "col": "mcclellan_osc", "unit": "",
     "en": "the McClellan oscillator went from {a} to {b}"},
    {"label": "季度 +25% 家数", "col": "up_25pct_qtr", "unit": "只",
     "en": "names up 25% on the quarter went from {a} to {b}"},
    {"label": "季度 -25% 家数", "col": "down_25pct_qtr", "unit": "只",
     "en": "names down 25% on the quarter went from {a} to {b}"},
)

REGIME_METRICS: Sequence[Dict[str, str]] = (
    {"label": "VIX", "col": "vix", "unit": "",
     "en": "VIX went from {a} to {b}"},
    {"label": "趋势 EMA", "col": "ts_ema", "unit": "",
     "en": "the trend EMA went from {a} to {b}"},
    {"label": "3 日下跌概率", "col": "prob_3d", "unit": "",
     "en": "the 3-day drawdown probability went from {a} to {b}"},
    {"label": "新高/新低比", "col": "nhnl_ratio", "unit": "",
     "en": "the new-high/new-low ratio went from {a} to {b}"},
    {"label": "信用利差 OAS", "col": "oas", "unit": "",
     "en": "credit OAS went from {a} to {b}"},
    {"label": "OAS 252 日分位", "col": "oas_rank252", "unit": "",
     "en": "credit OAS sat at the {b} percentile of the last year, from {a}"},
    {"label": "GEX 252 日分位", "col": "gexn_rank252", "unit": "",
     "en": "net GEX sat at the {b} percentile of the last year, from {a}"},
    {"label": "亮灯数", "col": "lamps_on", "unit": "盏",
     "en": "{b} of the risk lamps were lit, from {a}"},
    {"label": "TICK 价差分位", "col": "tick_spread_rank252", "unit": "",
     "en": "the TICK spread percentile went from {a} to {b}"},
)


# --------------------------------------------------------------------------
# reading the archives
# --------------------------------------------------------------------------

def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open() as fh:
        return list(csv.DictReader(fh))


def to_float(value: Any) -> Optional[float]:
    """Empty strings and nulls stay None -- never 0.0, which would be a reading."""
    if value is None:
        return None
    s = str(value).strip()
    if s == "" or s.lower() in {"nan", "none", "null"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def series(rows: Sequence[Dict[str, str]], col: str) -> List[tuple]:
    """(date, value) for every row where the column parses, in file order."""
    out = []
    for r in rows:
        v = to_float(r.get(col))
        if v is not None and r.get("date"):
            out.append((r["date"], v))
    return out


def fmt(value: float, unit: str = "") -> str:
    if value == int(value) and abs(value) < 1e15:
        body = f"{int(value):,}"
    elif abs(value) >= 100:
        body = f"{value:,.1f}"
    elif abs(value) >= 1:
        body = f"{value:,.2f}"
    else:
        body = f"{value:,.4f}".rstrip("0").rstrip(".")
    return f"{body}{unit}"


# --------------------------------------------------------------------------
# scoring
# --------------------------------------------------------------------------

def span_changes(values: Sequence[float], span: int) -> List[float]:
    """Every overlapping `span`-step change in the history."""
    if span < 1:
        raise ValueError("span must be >= 1")
    return [values[i + span] - values[i] for i in range(len(values) - span)]


def percentile_of(value: float, population: Sequence[float]) -> float:
    """Share of the population this value is at least as large as, 0-100."""
    if not population:
        return float("nan")
    at_or_below = sum(1 for p in population if p <= value)
    return 100.0 * at_or_below / len(population)


def score_metric(rows: Sequence[Dict[str, str]], metric: Dict[str, str],
                 asof: Optional[str], span: int) -> Optional[Dict[str, Any]]:
    pairs = series(rows, metric["col"])
    if asof:
        pairs = [p for p in pairs if p[0] <= asof]
    if len(pairs) < span + 1:
        return None

    (date_b, b), (date_a, a) = pairs[-1], pairs[-1 - span]
    change = b - a
    history = span_changes([v for _, v in pairs[:-1]], span)

    rankable = len(history) >= MIN_HISTORY
    pct = percentile_of(abs(change), [abs(h) for h in history]) if rankable else None
    return {
        "label": metric["label"],
        "column": metric["col"],
        "from_date": date_a,
        "to_date": date_b,
        "from": a,
        "to": b,
        "change": change,
        "direction": "up" if change > 0 else ("down" if change < 0 else "flat"),
        "pctile": pct,
        "rankable": rankable,
        "history_n": len(history),
        "sentence": metric["en"].format(a=fmt(a, metric.get("unit", "")),
                                        b=fmt(b, metric.get("unit", ""))),
    }


def group_flips(rows: Sequence[Dict[str, str]], asof: Optional[str],
                span: int, kind: str = "theme") -> List[Dict[str, Any]]:
    """Groups whose state word changed over the window. Categorical -- no rank needed."""
    rows = [r for r in rows if r.get("kind") == kind]
    if asof:
        rows = [r for r in rows if r.get("date", "") <= asof]
    dates = sorted({r["date"] for r in rows})
    if len(dates) < span + 1:
        if len(dates) < 2:
            return []
        d_a, d_b = dates[0], dates[-1]     # shorter history than asked for: use all of it
    else:
        d_a, d_b = dates[-1 - span], dates[-1]

    before = {r["group"]: r for r in rows if r["date"] == d_a}
    after = {r["group"]: r for r in rows if r["date"] == d_b}
    out = []
    for g, row_b in after.items():
        row_a = before.get(g)
        if row_a is None or row_a.get("state") == row_b.get("state"):
            continue
        ex_a, ex_b = to_float(row_a.get("excess_3m")), to_float(row_b.get("excess_3m"))
        out.append({
            "group": g, "kind": kind,
            "from_date": d_a, "to_date": d_b,
            "from_state": row_a.get("state"), "to_state": row_b.get("state"),
            "excess_3m_from": ex_a, "excess_3m_to": ex_b,
            "excess_3m_change": (ex_b - ex_a) if (ex_a is not None and ex_b is not None) else None,
            "window_sessions": dates.index(d_b) - dates.index(d_a),
        })
    out.sort(key=lambda x: abs(x["excess_3m_change"] or 0), reverse=True)
    return out


def build(asof: Optional[str] = None, span: int = 5, top: int = 8) -> Dict[str, Any]:
    breadth_rows, regime_rows, group_rows = (read_csv(BREADTH), read_csv(REGIME),
                                             read_csv(GROUPS))

    ranked: List[Dict[str, Any]] = []
    unranked: List[Dict[str, Any]] = []
    for metric in BREADTH_METRICS:
        got = score_metric(breadth_rows, metric, asof, span)
        if got:
            (ranked if got["rankable"] else unranked).append(got)
    for metric in REGIME_METRICS:
        got = score_metric(regime_rows, metric, asof, span)
        if got:
            (ranked if got["rankable"] else unranked).append(got)

    ranked.sort(key=lambda x: x["pctile"], reverse=True)
    unranked.sort(key=lambda x: abs(x["change"]), reverse=True)

    return {
        "asof": asof,
        "span": span,
        "min_history": MIN_HISTORY,
        "candidates": ranked[:top],
        "also_ranked": ranked[top:],
        "no_baseline": unranked,
        "theme_flips": group_flips(group_rows, asof, span, "theme"),
        "industry_flips": group_flips(group_rows, asof, span, "industry"),
    }


# --------------------------------------------------------------------------
# rendering -- the thing Andy actually ticks
# --------------------------------------------------------------------------

def render(out: Dict[str, Any]) -> str:
    L: List[str] = []
    span = out["span"]
    L.append(f"# WHAT CHANGED · 候选清单（{out['asof'] or '最新'}，回看 {span} 个交易日）")
    L.append("")
    L.append("> 段 2 用：勾一个读数，填「从几到几 / 为什么重要 / 所以我做了什么 / 代价和收获」。")
    L.append("> 排名 = |本周变化| 在该读数**自身历史周变化**里的百分位。**这是描述性排名，不是 p 值**——"
             "重叠窗口高度自相关，它回答的是「这么大的动以前见过几次」。")
    L.append("")

    L.append("## 勾这里（有历史基线，可排名）")
    L.append("")
    if not out["candidates"]:
        L.append("（无——没有任何读数攒够历史基线）")
    else:
        L.append("| | 读数 | 从 → 到 | 变化 | 历史百分位 | 英文句（段 2 直接用） |")
        L.append("|---|---|---|---|---|---|")
        for i, c in enumerate(out["candidates"], 1):
            arrow = "↑" if c["direction"] == "up" else ("↓" if c["direction"] == "down" else "→")
            L.append(f"| ☐ {i} | {c['label']} | {fmt(c['from'])} → {fmt(c['to'])} | "
                     f"{arrow} {fmt(abs(c['change']))} | **p{c['pctile']:.0f}** "
                     f"（{c['history_n']} 次历史周变化） | {c['sentence']} |")
    L.append("")

    if out["theme_flips"]:
        L.append("## 主题翻面（Leading ↔ Lagging，分类判据，不需要基线）")
        L.append("")
        L.append("| | 主题 | 状态 | excess_3m |")
        L.append("|---|---|---|---|")
        for f in out["theme_flips"]:
            ch = f["excess_3m_change"]
            L.append(f"| ☐ | {f['group']} | {f['from_state']} → **{f['to_state']}** | "
                     f"{fmt(f['excess_3m_from'] or 0)} → {fmt(f['excess_3m_to'] or 0)}"
                     f"{f' ({ch:+.4f})' if ch is not None else ''} |")
        L.append("")

    if out["industry_flips"]:
        L.append(f"<details><summary>行业翻面 {len(out['industry_flips'])} 个（展开）</summary>")
        L.append("")
        for f in out["industry_flips"][:20]:
            L.append(f"- {f['group']}: {f['from_state']} → **{f['to_state']}**")
        L.append("")
        L.append("</details>")
        L.append("")

    if out["no_baseline"]:
        L.append(f"## ⚠️ 变了但排不了名（历史不足 {out['min_history']} 次周变化）")
        L.append("")
        L.append("> 这些读数的档案太短，给它们算百分位会印出一个比数据还精细的数字。"
                 "**列出来给眼睛看，不给它们排名**；档案攒够会自动进上面那张表。")
        L.append("")
        L.append("| 读数 | 从 → 到 | 变化 | 历史周变化次数 |")
        L.append("|---|---|---|---|")
        for c in out["no_baseline"]:
            arrow = "↑" if c["direction"] == "up" else ("↓" if c["direction"] == "down" else "→")
            L.append(f"| {c['label']} | {fmt(c['from'])} → {fmt(c['to'])} | "
                     f"{arrow} {fmt(abs(c['change']))} | {c['history_n']} |")
        L.append("")

    L.append("---")
    L.append("")
    L.append("**这份清单看不见什么**（别把它的沉默当成「没事发生」）：")
    L.append("")
    L.append("- **仓位那一半。** 段 2 要的是「读数变了 → 所以我做了什么 → 代价和收获」，"
             "这里只出第一段。后两段在 `data/portfolio/`，得 Andy 自己填。")
    L.append("- **atr_ext 分布**：挂单原文点名要它，但归档里没有它的时间序列"
             "（`ticker_events.csv` 是逐事件的，不是逐日分布）。要出它得先建档，已列门铃。")
    L.append("- **组内换人**：主题翻面只看状态词，一个主题的成分股全换了但状态没变，这里是哑的。")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--asof", help="last session to include (YYYY-MM-DD)")
    ap.add_argument("--span", type=int, default=5, help="sessions to look back")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--out", type=Path, help="write the markdown checklist here")
    ap.add_argument("--json", type=Path, help="write the raw report here")
    args = ap.parse_args(argv)

    out = build(asof=args.asof, span=args.span, top=args.top)
    text = render(out)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
