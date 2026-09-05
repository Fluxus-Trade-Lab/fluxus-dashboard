"""ticker_events: 同一天、同一只票，两个筛子记的 change_pct 必须是同一个数。

`ticker_events.csv` 是所有回测的地基 —— 验刀、预设回填、闸门研究都从它读。
它的每一行是「某日某票命中某筛子」，而**同一天同一只票常被多个筛子同时记下**：
2026-03-09 起的归档里有 13,707 例这样的重复记录。它们全都来自同一份当日快照，
所以它们的 `change_pct` 在物理上必须相等 —— 这是一条不需要任何领域知识的恒等式。

它被破坏过一次，而且没有任何闸看见：

  2026-08-17 那天，13,707 例里有 **39 例**读数不一致（该日 235 例中的 16.6%）。
  最大的一处是 AXTI：`gainers_4pct` 记 +17.55%，`preset:sugar_babies` 记 +4.54%。
  EROC：+4.07% vs +9.33%。PTEN：+7.43% vs 0.00%。

  机制不是猜的。当天 17:32 有一个提交 `65bbb080`
  「chore: manual pipeline run 2026-08-17 **(08-14 bars)**」——
  一次用 08-14 K 线、却盖着 2026-08-17 日戳的手动重跑。两天后 `e2554467`
  的预设历史回填从 git 逐日读快照，于是 08-17 的 `preset:*` 行拿到的是 08-14 的价格。
  **验证**：39 例里有 08-14 螺丝刀记录的共 7 例，**7/7 的「08-17 preset 读数」
  与「08-14 screener 读数」逐位相等**（AXTI 0.0454、EROC 0.0933……）。
  另外 32 例当天没到 4%，08-14 的筛子本来就不会记它们 —— 与该解释一致。

  受影响面：08-17 的 604 行 `preset:*`，占全库 preset 行的 **1.70%**。

它还被破坏过**第二次**，而这一次 `change_pct` 看不见 —— 只有 `volume` 看得见：

  2026-08-14，`gainers_4pct` 的**每日中位 volume 是 987 股**（该日 165 行）。
  归档 110 个有 volume 的交易日里，其余每一天的中位都在 286,019 – 2,072,903 之间；
  987 是最小值，比次低那天还小 290 倍。同日 12 只票的 preset 行给出 60×–7,433× 的数
  （NN：302 股 vs 2,244,694 股，而它当天涨 5.43%）。倍率不是常数，所以不是单位错。

  为什么正好是这一天：`e8ac440e` 记着 Finviz 在 2026-08-07 把 `Change` 改名成 `Change %`，
  change_pct 整整一周 100% 为空、「三个 gainers 筛子什么都不返回」。归档逐日印证 ——
  **08-07 至 08-13，gainers_4pct / vol_up_gainers / episodic_pivot 是 0 行**；
  **08-14 是它们复活的第一天**，165 行回来了，带着这份 volume。08-17 起恢复正常（673,632）。
  那次修复盯的是**大声死掉**的那一列；旁边**安静退化**的那一列没有人验收。

  两个候选机制（**没有选中任何一个**，选中它需要一个独立的 volume 源，夜里不抓）：
  ① 盘前/开盘瞬间的快照（最小值到 1 股，与「很早的成交带」一致）；
  ② 改名事故里 volume 被映射到了另一列。

**字段的选法**（不是随手挑的）：只有跨筛子**必须相等**的字段才进这张表。
  ✅ `change_pct` `volume` —— 同一份当日快照的同一个数
  ✅ `sector` `atr_ext` —— 干净对照：全库 26,108 / 18,558 例可比，**0 例不一致**
     （它们证明这把尺子不是「凡是比就报红」）
  ❌ `group`（28.5% 不一致）`rel_volume`（42.4%）—— 分歧**散布在每一个日期上**，
     这是各筛子定义不同，不是快照坏了。把它们放进来，闸就会天天红、然后被人学会跳过。

为什么这条恒等式值得单独立一个闸：**它是少数几个不需要外部真值就能自证的检查。**
「行数对不对」「字段缺不缺」这类计数检查，对一份内部自相矛盾的快照全部是绿的
（`pitfall_row_count_is_not_a_shape_check` / `pitfall_having_a_row_is_not_having_data`）。
两个筛子对同一只票报出两个价格，是这份数据**自己**说自己坏了。

⚠️ 这是**棘轮**不是警报（同 `audit_wiring` / `audit_ci_test_coverage`）。
归档是机器写的、归 DATA ALEX，夜间组不改 `data/history/`。所以已知的那一天在下面
**具名声明**（谁、何时发现、为什么），闸对「恰好是这一天」判绿。声明是欠条，每次都全文打印。

它在情况**变化**时变红：
  E1  某个**没有声明**的日期出现读数不一致 —— 今天这个形状又发生了一次
  E2  某个已声明的日期**不再**不一致 —— 修好了就必须来把这条欠条删掉
      （防腐的那一半；没有它，这张表会退化成一份描述着我们已经不再拥有的仓库的永久豁免名单）
  E3  已声明的日期在归档里根本不存在
  E4  声明缺 owner 或缺理由
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

ARCHIVE = Path("data/history/ticker_events.csv")

# CSV 里的读数由写入方 round(...,4)。归一到 6 位只是为了吃掉 float 的字符串往返，
# 不是容差 —— 真实的分歧都在 10^-2 量级（见 docstring），不会被这一步抹平。
_PLACES = 6

# 跨筛子必须相等的字段（理由见 docstring 的「字段的选法」）。
FIELDS: Tuple[str, ...] = ("change_pct", "volume", "sector", "atr_ext")

# 日期 -> (owner, 发现日, 理由)。改这张表 = 打一张新欠条，请照上面的体例写清出处。
DECLARED: Dict[str, Tuple[str, str, str]] = {
    "2026-08-14": (
        "DATA ALEX", "2026-09-06",
        "Finviz 08-07 把 Change 改名成 Change %（e8ac440e），三个 gainers 筛子 08-07~08-13 零行；"
        "08-14 是复活第一天，当天 gainers_4pct 的中位 volume 是 987 股 —— 归档 110 天里的最小值，"
        "比次低那天小 290 倍。修法归数据端：重算或撤下该日 gainers 家族的 volume",
    ),
    "2026-08-17": (
        "DATA ALEX", "2026-09-06",
        "commit 65bbb080 (08-17 17:32) 是一次用 08-14 K 线、盖 2026-08-17 日戳的手动重跑；"
        "e2554467 的预设回填按 git 快照逐日读，于是该日 604 行 preset:* 携带 08-14 读数。"
        "7/7 有 08-14 对照的票逐位吻合。修法归数据端：重算或撤下该日的 preset:* 行",
    ),
}


def _rows(path: Path) -> Iterable[Mapping[str, str]]:
    with open(path, newline="") as fh:
        yield from csv.DictReader(fh)


def _norm(raw: str):
    """数值归一到 6 位；不是数就按去空白的字符串比（sector 这类）。"""
    try:
        v = round(float(raw), _PLACES)
    except ValueError:
        return raw.strip()
    return None if v != v else v      # NaN 当作没有读数


def readings(path: Path = ARCHIVE,
             fields: Iterable[str] = FIELDS) -> Dict[Tuple[str, str, str], Dict[Any, List[str]]]:
    """(field, date, ticker) -> {读数: [记下这个数的筛子]}，只收非空的。"""
    out: Dict[Tuple[str, str, str], Dict[Any, List[str]]] = defaultdict(lambda: defaultdict(list))
    for r in _rows(path):
        for f in fields:
            raw = (r.get(f) or "").strip()
            if not raw:
                continue
            v = _norm(raw)
            if v is None:
                continue
            out[(f, r.get("date", ""), r.get("ticker", ""))][v].append(r.get("screener", ""))
    return out


def disagreements(path: Path = ARCHIVE, fields: Iterable[str] = FIELDS,
                  _read: Dict | None = None) -> Dict[str, List[dict]]:
    """日期 -> 该日所有读数打架的 (字段, 票)。"""
    by_date: Dict[str, List[dict]] = defaultdict(list)
    for (field, date, ticker), vals in (_read if _read is not None else readings(path, fields)).items():
        if len(vals) > 1:
            by_date[date].append({
                "field": field, "ticker": ticker,
                "readings": {v: sorted(s) for v, s in sorted(vals.items(), key=lambda kv: str(kv[0]))},
            })
    for d in by_date:
        by_date[d].sort(key=lambda x: (x["field"], x["ticker"]))
    return dict(by_date)


def multi_screener_counts(path: Path = ARCHIVE, fields: Iterable[str] = FIELDS,
                          _read: Dict | None = None) -> Dict[str, int]:
    """日期 -> 该日被 ≥2 个筛子记下同一字段的 (字段,票) 数（分歧率的分母）。"""
    n: Dict[str, int] = defaultdict(int)
    for (_, date, _), vals in (_read if _read is not None else readings(path, fields)).items():
        if sum(len(s) for s in vals.values()) > 1:
            n[date] += 1
    return dict(n)


def coverage(path: Path = ARCHIVE, fields: Iterable[str] = FIELDS) -> Dict[str, Any]:
    """这把闸看得见多少 —— 有闸不等于闸盖住了全部（协议：has_X 是个 bool，缺口住在集合里）。"""
    all_dates, seen_dates, rows_total, rows_seen = set(), set(), 0, 0
    for r in _rows(path):
        rows_total += 1
        all_dates.add(r.get("date", ""))
        if any((r.get(f) or "").strip() for f in fields):
            rows_seen += 1
            seen_dates.add(r.get("date", ""))
    return {"dates_total": len(all_dates), "dates_seen": len(seen_dates),
            "dates_blind": sorted(all_dates - seen_dates),
            "rows_total": rows_total, "rows_seen": rows_seen}


def audit(path: Path = ARCHIVE, declared: Mapping[str, Tuple[str, str, str]] | None = None) -> Dict[str, Any]:
    declared = DECLARED if declared is None else declared
    read = readings(path)                     # 整个归档只读这一遍
    bad = disagreements(path, _read=read)
    denom = multi_screener_counts(path, _read=read)
    cov = coverage(path)
    all_dates = {d for (_, d, _) in read}
    v: List[Tuple[str, str]] = []

    for d in sorted(bad):
        if d not in declared:
            n = len(bad[d])
            v.append(("E1", f"{d}: {n} 个 (字段,票) 在筛子之间读数不一致"
                            f"（该日 {denom.get(d, 0)} 只被多筛记录），且没有声明"))
    for d, entry in sorted(declared.items()):
        if len(entry) != 3 or not entry[0] or not entry[2]:
            v.append(("E4", f"{d}: 声明缺 owner 或缺理由"))
            continue
        if d not in all_dates:
            v.append(("E3", f"{d}: 声明的日期在归档里不存在"))
        elif d not in bad:
            v.append(("E2", f"{d}: 已经不再不一致 —— 请删掉这条声明"))
    return {"violations": v, "disagreements": bad, "denominators": denom,
            "declared": dict(declared), "dates": len(all_dates),
            "pairs_checked": sum(denom.values()), "coverage": cov}


def _fmt(res: Dict[str, Any]) -> str:
    cov = res["coverage"]
    L = ["ticker_events 读数自洽 —— 同日同票，多个筛子必须报同一个数", ""]
    L.append(f"  查的字段: {', '.join(FIELDS)}")
    L.append(f"  可比的 (字段,日期,票): {res['pairs_checked']}    归档日期: {cov['dates_total']}")
    L.append("")
    L.append("  这把闸看得见多少（有闸 ≠ 闸盖住了全部）:")
    L.append(f"    行:   {cov['rows_seen']} / {cov['rows_total']} "
             f"({cov['rows_seen'] / cov['rows_total']:.1%}) 至少带一个被查字段")
    L.append(f"    日期: {cov['dates_seen']} / {cov['dates_total']}")
    if cov["dates_blind"]:
        L.append(f"    ⚠️ 完全看不见的日期 {len(cov['dates_blind'])} 天: "
                 f"{', '.join(cov['dates_blind'])} —— 这几天只跑了不写这些字段的筛子")
    L.append("")
    bad, den = res["disagreements"], res["denominators"]
    L.append(f"  读数打架的日期: {len(bad)}    打架的 (字段,票): {sum(len(x) for x in bad.values())}")
    L.append("")
    for d in sorted(bad):
        entry = res["declared"].get(d)
        tag = "[declared]" if entry else "[UNDECLARED]"
        n, t = len(bad[d]), den.get(d, 0)
        L.append(f"  {tag} {d}: {n} / {t}" + (f" ({n / t:.1%})" if t else ""))
        if entry:
            L.append(f"      owner: {entry[0]}  (发现于 {entry[1]})")
            L.append(f"      why:   {entry[2]}")
        for x in bad[d][:3]:
            r = "  ".join(f"{v}={'/'.join(sc)}" for v, sc in x["readings"].items())
            L.append(f"      e.g.   [{x['field']}] {x['ticker']}: {r}")
        if n > 3:
            L.append(f"      ... 另有 {n - 3} 个")
    L.append("")
    L.append("声明是欠条，不是结案。")
    L.append("")
    if res["violations"]:
        L.append(f"{len(res['violations'])} violation(s):")
        L += [f"  {c} {m}" for c, m in res["violations"]]
    else:
        L.append("no violations (打架的日期恰好等于声明的那些)")
    return "\n".join(L)


def main(argv: List[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    path = Path(argv[0]) if argv else ARCHIVE
    if not path.exists():
        # 「红得不是地方」：文件不在 ≠ 数据不自洽。用另一个退出码，别混进 E1。
        print(f"归档不存在: {path} —— 本闸没有结论，不是绿也不是红", file=sys.stderr)
        return 2
    res = audit(path)
    print(_fmt(res))
    return 1 if res["violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
