"""归档里的**计数器**和**累积极值**：变了不够，得往该走的方向走。

`audit_archives` I3 已经问过一次「这一场的读数和上一场逐位相同吗」——
那是**变没变**。本文件问的是另一个问题：**走到该到的地方了没有。**

两者的差别不是措辞，是 2026-09-02 那一整天。

那天 `delayed_ep_log` 的 36 行，是 09-01 的 36 行原样重来：
`stage` / `held` / `near` / `contracting` / `breakout` / `close` /
`vs_ep_close_pct` / `base_high` / `today_change_pct` / `days_since`
**十列全部 36/36 逐位相同**。整场吃的是上一场的 bars。

而它**没有**被「变没变」抓到，因为有两列确实变了：`today_relvol` **36/36 都变了**
（相对变化中位 0.30%，但**最大 +46.4%**：HTHT 0.5643→0.8262；34/36 是变大），
`recent_range_pct` 19/36 变了（最大 1.07%，17/19 变宽）。
方向对得上「晚报的成交量回来了、已结算 bar 的极值印记补齐了」——
⚠️ 但**不能只归给成交量修订**：`recent_range_pct = mean((H-L)/Close)` 里
一个成交量字段都没有，所以那 19 只的 **H/L 也被改过**。
一根已经收掉的 bar 被重抓时会带着修订回来，于是在「有没有变化」这个维度上完美伪装成新的一天。
**一个 46% 的 relvol 跳动，会让任何朴素的「变没变」检查判定这是新鲜的一场。**

计数器不吃这一套。`days_since = len(post)` 是「EP 那根之后帧里有几根 bar」，
它跟价格无关，**必须等于日历上 (ep_date, as_of] 之间的交易日数**。

## 三条恒等式

    P1  days_since 必须等于交易日历上 (ep_date, as_of] 的交易日数。
        对不上 ⇒ 那一班拿到的帧里，这只票的 bar 少了（或多了）。
    P2  一场里 P1 违规占该场全部行的 100%，且这些行相对上一次出现 close 逐位相同
        ⇒ 整场是上一场的复制品（比 P1 严重一级：不是几只票掉了 bar，是整次运行）。
    P3  base_high 单调不减。base_high = EP+1..昨天 的最高 high，
        随着日子过去只能升或平 —— 降下来在结构上不可能，除非有一根 bar 从帧里消失。

⚠️ **P1 必须按日历算绝对值，不能看相邻场的差分。** 第一版就是差分写的，
它在真档案上漏掉了 **8 行**：赤字一旦形成就会**持续**，之后每天 Δ 都是正常的 +1，
差分从此全瞎。实测 —— 差分口径报出 60 行，绝对口径报出 **68** 行（漏报 8/32 = 25%）。

⚠️ **本闸需要一份交易日历**（`pipeline.marketcal`，我们自己的），
但**不需要第二份价格读数** —— 这才是它和 `audit_event_agreement` 跨文件层的分工。

## 全库实测（2026-09-08 建成当晚，837 行）

| 场 | days_since 对不上日历 | 那些行 close 相对上一次也冻住吗 | 读作 |
|---|---|---|---|
| 2026-08-17 | 12 / 59 | **0/12** | 部分票的帧掉了一根 bar，价格照常更新 |
| 2026-08-19 | 12 / 57 | **0/12** | 同上，与 08-17 重合 11/12 |
| 2026-08-20 | **8 / 57** | 0/8 | **差分口径看不见这一天** —— 赤字持续着，Δ 已恢复正常 |
| 2026-09-02 | **36 / 36** | **36/36** | 整场重放 → P2 |

全部偏差都是 **−1**（帧少一根），没有一行是多的。

**下游实害**：08-20 那 8 行里有 **6** 行（AVTR CBZ EXLS GRMN HURN LAD）记着
`days_since=15`，日历说 16 —— `delayed_ep_scan` 的 `--max-days` 默认 15，
**它们本该被窗口踢掉，是 6 行幽灵**。

P3 全库只响 **1 次 / 836 次相邻转移**：CORT 的 base_high 在 08-17
从 118.53 **掉到** 115.00，08-18 又弹回 118.53 —— **那一班的瞬时缺陷，不是永久丢失**。
它独立地指回 08-17，且指出掉的是哪一根。

⚠️ 08-17 本来就是已知坏日（`DATA_RELIABILITY` §六.7：`65bbb080` 那次
「manual pipeline run 2026-08-17 **(08-14 bars)**」）。**它是本闸的真实阳性对照** ——
不是我注射的，是档案自己留下的。而 **08-19 / 08-20 此前没有任何闸报过**。

⚠️ **受影响的票只有下界，没有上界。** 三天冻住的 13 只票 `ep_date` **全部 ≤ 2026-07-30**，
这不是「老 EP 的票特殊」，是**幸存者偏差**：掉的那根 bar 只有落在该票 `ep_date` 之后
才会影响 `days_since`。`ep_date` 更晚的票**可能同样掉了那根 bar，在结构上不可观测**。

⚠️ 反过来说清楚本闸**看不见**什么：它只说「帧对不对得上日历」，
不说「状态错在哪」。`held` 和 `contracting` 吃的是当天的 high/low，归档里没有存。

## 第二个模式：`--sweep` —— 不需要日历、不需要计数器、不需要懂这张表

P1 要一份交易日历，P3 要知道哪一列是累积极值 —— 两条都得懂这张表。
`--sweep` 不需要：它只问「**这一场有多少列，整列逐位重复了上一场？**」

⚠️ **必须逐列问，不能逐行问。** 同一个查法写成「整行逐位相同的行占比」，
在 2026-09-02 那一对上报 **0.0%** —— 16 个非键列里有 2 列带着供应商修订回来，
**整行比法就此全废**。逐列问的话，那天是 **14/16 = 87.5%**。

全库实测（`data/history` 的 8 个归档、**208** 个相邻场对，键列不计）：
中位 14.3% · P95 37.5% · **最大 87.5% = `delayed_ep_log` 2026-09-02**，
与第二名（`shortlist_log` 08-28 的 50.0%）差 **37.5 个百分点**。
**除它之外没有第二个整场重放。**

⚠️ 所以 `--sweep` **只报不判**，退出码永远 0：全库只有**一个**已知阳性，
拿它凑一个阈值就是过拟合 —— 「没有先验证一个检查能报出阳性，就不该信它的阴性」
在这里的形态是「只有一个阳性，就不该信它划出来的线」。它是给人读的排行，不是闸。

Run:  python -m pipeline.tools.audit_progress [归档路径]
      python -m pipeline.tools.audit_progress --sweep [目录]
      退出码 0=无违规 · 1=有违规 · 2=文件不在（本闸没有结论，不是绿）
"""
from __future__ import annotations

import csv
import datetime as dt
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

ARCHIVE = Path(__file__).resolve().parents[2] / "data" / "history" / "delayed_ep_log.csv"

# 轨迹键 / 场键 / 计数器列 / 单调不减列 / 「整场复制」的佐证列
KEY = ("ticker", "ep_date")
SESSION = "as_of"
COUNTER = "days_since"
NONDECREASING = "base_high"
ECHO = "close"          # P2 的佐证：整场重放时这一列相对上一次出现必须逐位相同
EP = "ep_date"          # P1 的起点：日历从这一天的**次日**开始数
WINDOW = (3, 15)        # delayed_ep_scan 的 --min-days / --max-days 默认值


def _sessions_between(ep: str, as_of: str, is_trading_day: Callable) -> int:
    """(ep, as_of] 之间的交易日数 —— days_since 该等于的那个数。

    起点开区间：`classify` 里 `post = b.iloc[i_ep+1:]`，EP 那根自己不算。
    """
    d = dt.date.fromisoformat(ep) + dt.timedelta(days=1)
    end = dt.date.fromisoformat(as_of)
    n = 0
    while d <= end:
        if is_trading_day(d):
            n += 1
        d += dt.timedelta(days=1)
    return n


def _rows(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def _tracks(rows: Sequence[Dict[str, str]]) -> Dict[tuple, List[Dict[str, str]]]:
    t: Dict[tuple, List[Dict[str, str]]] = defaultdict(list)
    for r in rows:
        t[tuple(r[k] for k in KEY)].append(r)
    for v in t.values():
        v.sort(key=lambda r: r[SESSION])
    return t


def audit(path: Path, is_trading_day: Optional[Callable] = None) -> Dict[str, Any]:
    if is_trading_day is None:                      # 注入点：测试用假日历，不吃 pandas
        from pipeline.marketcal import is_trading_day as _itd
        is_trading_day = _itd

    rows = _rows(path)
    missing = [c for c in (SESSION, COUNTER, NONDECREASING, ECHO, EP) + KEY
               if rows and c not in rows[0]]
    if missing:
        # 「报绿是因为它什么都没看」：列不在，就没有结论，不许走进零违规那条路。
        raise KeyError(f"归档缺列，本闸无法判定: {', '.join(missing)}")

    tracks = _tracks(rows)
    prev_of: Dict[int, Dict[str, str]] = {}         # 每行 -> 它上一次出现的那行
    for rs in tracks.values():
        for a, b in zip(rs, rs[1:]):
            prev_of[id(b)] = a

    per_session: Dict[str, int] = defaultdict(int)
    p1: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        per_session[r[SESSION]] += 1
        expected = _sessions_between(r[EP], r[SESSION], is_trading_day)
        got = int(r[COUNTER])
        if got == expected:
            continue
        prev = prev_of.get(id(r))
        p1[r[SESSION]].append({
            "ticker": r[KEY[0]], "ep_date": r[EP], "got": got, "expected": expected,
            "close_frozen": bool(prev) and prev[ECHO] == r[ECHO],
            # 修正后落到扫描窗口之外 ⇒ 这一行本不该在归档里
            "ghost": not (WINDOW[0] <= expected <= WINDOW[1]),
        })

    p3: List[Dict[str, Any]] = []
    pairs = 0
    for key, rs in tracks.items():
        for a, b in zip(rs, rs[1:]):
            pairs += 1
            if float(b[NONDECREASING]) < float(a[NONDECREASING]) - 1e-9:
                p3.append({"ticker": key[0], "ep_date": key[1], "prev": a[SESSION],
                           "session": b[SESSION], "from": float(a[NONDECREASING]),
                           "to": float(b[NONDECREASING])})

    # P2：整场复制品 —— 该场**每一行**都对不上日历，且每一行的 close 相对上一次出现
    # 逐位相同。两个条件缺一不可：只有「全错」分不开「整场重放」和「整场都掉了一根」，
    # 只有「close 相同」在单只票上是巧合；一起出现才是一次运行吃了上一场的 bars。
    duplicated = sorted(
        s_ for s_, hits in p1.items()
        if per_session[s_] and len(hits) == per_session[s_]
        and all(h["close_frozen"] for h in hits))

    violations: List[tuple] = []
    for s_ in duplicated:
        violations.append(("P2", f"{s_}: 整场是上一场的复制品 —— "
                                 f"{per_session[s_]}/{per_session[s_]} 行 {COUNTER} 与日历对不上，"
                                 f"且 {ECHO} 全部逐位等于上一次出现"))
    for s_ in sorted(p1):
        if s_ in duplicated:
            continue
        hits = p1[s_]
        ghosts = sum(h["ghost"] for h in hits)
        violations.append(("P1", f"{s_}: {len(hits)}/{per_session[s_]} 行 {COUNTER} 与日历对不上"
                                 f"（偏差 {sorted({h['got'] - h['expected'] for h in hits})}）"
                                 + (f"，其中 {ghosts} 行修正后落在扫描窗口 "
                                    f"{WINDOW[0]}..{WINDOW[1]} 之外 —— 那些行本不该在归档里"
                                    if ghosts else "")))
    for x in p3:
        violations.append(("P3", f"{x['session']}: {x['ticker']} 的 {NONDECREASING} "
                                 f"从 {x['from']:.2f} 降到 {x['to']:.2f} —— "
                                 f"累积极值降不了，除非有一根 bar 从帧里消失"))

    return {"violations": violations, "tracks": len(tracks), "pairs": pairs,
            "sessions": len(per_session), "rows": len(rows),
            "p1": {k: p1[k] for k in sorted(p1)}, "p2": duplicated, "p3": p3,
            "per_session": dict(per_session)}


def render(res: Dict[str, Any]) -> str:
    L = ["计数器与累积极值 —— 变了不够，得往该走的方向走", ""]
    L.append(f"  {res['rows']} 行 / {res['sessions']} 场 / {res['tracks']} 条轨迹 / "
             f"{res['pairs']} 个相邻对")
    L.append(f"  P1 {COUNTER} 对交易日历绝对重算 · P2 整场复制 · "
             f"P3 {NONDECREASING} 单调不减")
    L.append("")
    if res["p2"]:
        L.append("  🔴 整场复制品（P2）:")
        for s in res["p2"]:
            L.append(f"      {s} —— {res['per_session'][s]} 行全部与日历对不上，"
                     f"close 全部逐位等于上一次出现")
    partial = [s for s in res["p1"] if s not in res["p2"]]
    if partial:
        L.append("  🟠 帧与日历对不上（P1）:")
        for s in partial:
            h = res["p1"][s]
            g = sum(x["ghost"] for x in h)
            L.append(f"      {s} —— {len(h)}/{res['per_session'][s]}"
                     + (f"（{g} 行是窗口外的幽灵）" if g else "") + ": "
                     + " ".join(x["ticker"] for x in h[:14])
                     + (" …" if len(h) > 14 else ""))
    if res["p3"]:
        L.append(f"  🟠 {NONDECREASING} 降过（P3）:")
        for x in res["p3"]:
            L.append(f"      {x['session']} {x['ticker']}: "
                     f"{x['from']:.2f} → {x['to']:.2f}")
    if not res["violations"]:
        L.append("  零违规")
    L.append("")
    L.append("⚠️ 本闸只说「帧对不对得上日历」，不说「状态错在哪」——"
             "held/contracting 吃当天的 high/low，归档没存，查不了。")
    L.append("⚠️ 受影响的票只有下界：掉的那根 bar 落在某票 ep_date 之前时，"
             "它在结构上不可观测。")
    L.append("")
    if res["violations"]:
        L.append(f"{len(res['violations'])} violation(s):")
        L += [f"  [{c}] {m}" for c, m in res["violations"]]
    return "\n".join(L)


# --sweep 的口径表：(文件名, 场次列, 行键列)。
# ticker_events 的行键是 (ticker, screener) —— 同一天同一只票会被多个筛子各记一行。
SWEEP: Sequence[tuple] = (
    ("asset_signals.csv", "date", ("ticker",)),
    ("delayed_ep_log.csv", "as_of", ("ticker",)),
    ("groups_archive.csv", "date", ("group",)),
    ("leaders_log.csv", "date", ("ticker",)),
    ("momentum97_shadow.csv", "date", ("ticker",)),
    ("shortlist_log.csv", "date", ("ticker",)),
    ("watchlist_hits.csv", "date", ("ticker",)),
    ("ticker_events.csv", "date", ("ticker", "screener")),
)
MIN_KEYS = 5            # 共同键太少时占比是噪声，不进排行


def frozen_columns(rows: Sequence[Dict[str, str]], date_col: str,
                   key_cols: Sequence[str]) -> List[Dict[str, Any]]:
    """每对相邻场：有多少列在**全部共同键**上逐位重复了上一场。

    逐列，不逐行 —— 见模块 docstring 里 2026-09-02 那个 0.0% vs 87.5%。

    ⚠️ **键列不计**：它们按定义逐场相同，算进去就是白送的分母上的分子，
    而且各归档的键列数不一样，会让归档之间不可比。
    """
    cols = [c for c in rows[0] if c != date_col and c not in key_cols]
    by: Dict[str, Dict[tuple, Dict[str, str]]] = defaultdict(dict)
    for r in rows:
        by[r[date_col]][tuple(r.get(k, "") for k in key_cols)] = r
    out = []
    for a, b in zip(sorted(by), sorted(by)[1:]):
        common = set(by[a]) & set(by[b])
        if len(common) < MIN_KEYS:
            continue
        frozen = [c for c in cols
                  if all(by[a][k][c] == by[b][k][c] for k in common)]
        out.append({"session": b, "prev": a, "frozen": len(frozen),
                    "columns": len(cols), "keys": len(common),
                    "share": len(frozen) / len(cols)})
    return out


def sweep(history: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for fn, date_col, key_cols in SWEEP:
        p = history / fn
        if not p.exists():
            continue
        data = _rows(p)
        if not data or date_col not in data[0]:
            continue
        for x in frozen_columns(data, date_col, key_cols):
            x["archive"] = fn
            rows.append(x)
    rows.sort(key=lambda x: -x["share"])
    return rows


def render_sweep(rows: List[Dict[str, Any]], top: int = 8) -> str:
    if not rows:
        return "没有可比的相邻场对 —— 本次扫描没有结论，不是绿。"
    shares = sorted(x["share"] for x in rows)
    med = shares[len(shares) // 2]
    L = ["整场重复度 —— 这一场有多少**列**逐位重复了上一场（逐列，不逐行）", ""]
    L.append(f"  {len(rows)} 个相邻场对 · 中位 {100 * med:.1f}% · "
             f"P95 {100 * shares[int(.95 * len(shares))]:.1f}% · "
             f"最大 {100 * shares[-1]:.1f}%")
    gap = 100 * (rows[0]["share"] - rows[1]["share"]) if len(rows) > 1 else 0.0
    L.append(f"  第一名与第二名差 {gap:.1f} 个百分点")
    L.append("")
    for x in rows[:top]:
        L.append(f"  {100 * x['share']:>5.1f}%  {x['archive']:<22} {x['session']}  "
                 f"{x['frozen']}/{x['columns']} 列  ({x['keys']} 个共同键)")
    L.append("")
    L.append("只报不判：全库只有一个已知阳性（delayed_ep_log 2026-09-02），"
             "拿它凑阈值就是过拟合。这是给人读的排行，不是闸。")
    return "\n".join(L)


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv and argv[0] == "--sweep":
        d = Path(argv[1]) if len(argv) > 1 else ARCHIVE.parent
        print(render_sweep(sweep(d)))
        return 0
    path = Path(argv[0]) if argv else ARCHIVE
    if not path.exists():
        print(f"归档不存在: {path} —— 本闸没有结论，不是绿也不是红", file=sys.stderr)
        return 2
    res = audit(path)
    print(render(res))
    return 1 if res["violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
