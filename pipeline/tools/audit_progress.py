"""归档里的**计数器**和**累积极值**：变了不够，得往该走的方向走。

`audit_archives` I3 已经问过一次「这一场的读数和上一场逐位相同吗」——
那是**变没变**。本文件问的是另一个问题：**往前走了没有。**

两者的差别不是措辞，是 2026-09-02 那一整天。

那天 `delayed_ep_log` 的 36 行，是 09-01 的 36 行原样重来：
`stage` / `held` / `near` / `contracting` / `breakout` / `close` /
`vs_ep_close_pct` / `base_high` / `today_change_pct` / `days_since`
**十列全部 36/36 逐位相同**。整场吃的是上一场的 bars。

而它**没有**被「变没变」抓到，因为有两列确实变了：
`today_relvol` **36/36 都变了**，`recent_range_pct` 19/36 变了 ——
都在第 4~5 位小数上。供应商在两次抓取之间修订了上一场的成交量（合并行情盘后才结算），
于是同一根 bar 被重抓时**带着微幅修订回来**，在「有没有变化」这个维度上完美伪装成新的一天。
一个只问「变了没有」的闸，那天会 36/36 报绿。

计数器不吃这一套。`days_since = len(post)` 是「EP 那根之后有几根 bar」，
它跟价格无关，**只要今天真的收了一根新 bar 就必须 +1**。那天 36/36 是 0。

## 三条恒等式（全部只需要这一个文件，不需要任何外部真值）

    P1  同一 (ticker, ep_date) 轨迹，相邻两次出现之间 days_since 必须 ≥ +1。
        =0 ⇒ 这只票的 bar 帧那天没有前进。
    P2  某一场里 P1 违规占该场可比轨迹的 100%，且这些轨迹的 close 逐位相同
        ⇒ 整场是上一场的复制品（比 P1 严重一级：不是几只票掉了 bar，是整次运行）。
    P3  base_high 单调不减。base_high = EP+1..昨天 的最高 high，
        随着日子过去只能升或平 —— **降下来在结构上不可能**，除非有一根
        post-EP 的 bar 从帧里消失了。

## 全库实测（2026-09-08 建成当晚，103 条轨迹 / 731 个相邻对）

| 场 | P1 冻住 | 那些票 close 也冻住吗 | 读作 |
|---|---|---|---|
| 2026-08-17 | 12/59 (20%) | **0/12** | 部分票掉了一根 bar，价格照常更新 |
| 2026-08-19 | 12/57 (21%) | **0/12** | 同上，几乎是同一批票（11/12 重合）|
| 2026-09-02 | **36/36 (100%)** | **36/36** | 整场复制品 → P2 |

P3 全库只响 **1 次 / 731**（0.14%）：CORT 的 base_high 在 08-14→08-17
从 118.53 **掉到** 115.00 —— 独立地指回 08-17 那天，且指出了掉的是哪一根。

⚠️ 08-17 本来就是已知坏日（`DATA_RELIABILITY` §六.7：`65bbb080` 那次
「manual pipeline run 2026-08-17 (08-14 bars)」）。**它是本闸的真实阳性对照** ——
不是我注射的，是档案自己留下的。而 **08-19 的 12 只此前没有任何闸报过**。

⚠️ 反过来说清楚本闸**看不见**什么：P1/P2 只能说「帧没前进」，
不能说「状态错在哪」。`held` 和 `contracting` 吃的是当天的 high/low，
归档里没有存 —— 拿别的文件的 close 只能核 `near` 与 `close > base_high`
两个必要条件（09-02 那 11 只可核票上**零翻转**），
`held` 翻没翻**查不了**。别把「零翻转」读成「无害」。

Run:  python -m pipeline.tools.audit_progress [归档路径]
      退出码 0=无违规 · 1=有违规 · 2=文件不在（本闸没有结论，不是绿）
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

ARCHIVE = Path(__file__).resolve().parents[2] / "data" / "history" / "delayed_ep_log.csv"

# 轨迹键 / 场键 / 计数器列 / 单调不减列 / 「整场复制」的佐证列
KEY = ("ticker", "ep_date")
SESSION = "as_of"
COUNTER = "days_since"
NONDECREASING = "base_high"
ECHO = "close"          # P2 的佐证：帧没前进时这一列必须逐位相同


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


def audit(path: Path) -> Dict[str, Any]:
    rows = _rows(path)
    missing = [c for c in (SESSION, COUNTER, NONDECREASING, ECHO) + KEY
               if rows and c not in rows[0]]
    if missing:
        # 「报绿是因为它什么都没看」：列不在，就没有结论，不许走进零违规那条路。
        raise KeyError(f"归档缺列，本闸无法判定: {', '.join(missing)}")

    tracks = _tracks(rows)
    pairs = 0
    p1: Dict[str, List[Dict[str, Any]]] = defaultdict(list)   # 按「到达的那一场」归集
    p3: List[Dict[str, Any]] = []
    comparable: Dict[str, int] = defaultdict(int)             # 每场有几条轨迹可比

    for key, rs in tracks.items():
        for a, b in zip(rs, rs[1:]):
            pairs += 1
            sess = b[SESSION]
            comparable[sess] += 1
            if int(b[COUNTER]) - int(a[COUNTER]) <= 0:
                p1[sess].append({"ticker": key[0], "ep_date": key[1],
                                 "prev": a[SESSION], "counter": int(a[COUNTER]),
                                 "close_frozen": a[ECHO] == b[ECHO]})
            if float(b[NONDECREASING]) < float(a[NONDECREASING]) - 1e-9:
                p3.append({"ticker": key[0], "ep_date": key[1], "prev": a[SESSION],
                           "session": sess, "from": float(a[NONDECREASING]),
                           "to": float(b[NONDECREASING])})

    # P2：整场复制品 —— 全部可比轨迹都冻住，且冻住的那些 close 也逐位相同。
    # 两个条件缺一不可：只有「全冻」可能是别的原因（比如那天所有票都停牌），
    # 只有「close 相同」在单只票上是巧合；一起出现才是一次运行吃了上一场的 bars。
    duplicated = sorted(
        s for s, hits in p1.items()
        if comparable[s] and len(hits) == comparable[s]
        and all(h["close_frozen"] for h in hits))

    violations: List[tuple] = []
    for s in duplicated:
        violations.append(("P2", f"{s}: 整场是上一场的复制品 —— "
                                 f"{comparable[s]}/{comparable[s]} 条轨迹 {COUNTER} 没前进，"
                                 f"且 {ECHO} 全部逐位相同"))
    for s in sorted(p1):
        if s in duplicated:
            continue
        hits = p1[s]
        frozen_close = sum(h["close_frozen"] for h in hits)
        violations.append(("P1", f"{s}: {len(hits)}/{comparable[s]} 条轨迹 {COUNTER} 没前进"
                                 f"（其中 {ECHO} 也冻住的 {frozen_close} 条）—— "
                                 f"这些票那天的 bar 帧掉了一根"))
    for x in p3:
        violations.append(("P3", f"{x['session']}: {x['ticker']} 的 {NONDECREASING} "
                                 f"从 {x['from']:.2f} 降到 {x['to']:.2f} —— "
                                 f"累积极值降不了，除非有一根 bar 从帧里消失"))

    return {"violations": violations, "tracks": len(tracks), "pairs": pairs,
            "sessions": len({r[SESSION] for r in rows}), "rows": len(rows),
            "p1": {s: p1[s] for s in sorted(p1)}, "p2": duplicated, "p3": p3,
            "comparable": dict(comparable)}


def render(res: Dict[str, Any]) -> str:
    L = ["计数器与累积极值 —— 变了不够，得往该走的方向走", ""]
    L.append(f"  {res['rows']} 行 / {res['sessions']} 场 / {res['tracks']} 条轨迹 / "
             f"{res['pairs']} 个相邻对")
    L.append(f"  P1 {COUNTER} 必须 ≥+1 · P2 整场复制 · P3 {NONDECREASING} 单调不减")
    L.append("")
    if res["p2"]:
        L.append("  🔴 整场复制品（P2）:")
        for s in res["p2"]:
            L.append(f"      {s} —— {res['comparable'][s]} 条轨迹全部没前进，close 全部相同")
    partial = [s for s in res["p1"] if s not in res["p2"]]
    if partial:
        L.append("  🟠 部分票掉了一根 bar（P1）:")
        for s in partial:
            h = res["p1"][s]
            L.append(f"      {s} —— {len(h)}/{res['comparable'][s]}: "
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
    L.append("⚠️ 本闸只说「帧有没有前进」，不说「状态错在哪」——"
             "held/contracting 吃当天的 high/low，归档没存，查不了。")
    L.append("")
    if res["violations"]:
        L.append(f"{len(res['violations'])} violation(s):")
        L += [f"  [{c}] {m}" for c, m in res["violations"]]
    return "\n".join(L)


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    path = Path(argv[0]) if argv else ARCHIVE
    if not path.exists():
        print(f"归档不存在: {path} —— 本闸没有结论，不是绿也不是红", file=sys.stderr)
        return 2
    res = audit(path)
    print(render(res))
    return 1 if res["violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
