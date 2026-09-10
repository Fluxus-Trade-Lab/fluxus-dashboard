"""ticker_events 的每一行 change_pct，都得能被一根**别人家的 K 线**证实。

已有的两把尺子都在归档**内部**量：`audit_event_agreement` 问「同一天同一只票，
两个筛子记的是不是同一个数」；`audit_progress` 问「days_since 对不对得上交易日历」。
它们都很强，但都有同一个盲区 —— **整场用错帧时，一份内部完美自洽的快照全绿**
（`pitfall_internally_consistent_and_wrong`）。2026-09-02 那场就是这么躲过去的，
最后是靠**跨文件**才看见的。

这把尺子把边界画到**仓库外的厂商**上：`data/output/tickers/*.json` 的 `ohlc_2y`
是 yfinance 的日线，而 `ticker_events` 的 change_pct 来自 **Finviz** 的筛子快照。
**两个不同的厂商、两次不同的取数**，所以它们对不上时，不可能是「同一个错被抄了两遍」。

  恒等式：`change_pct(某日, 某票)` 应该等于 `close(某日)/close(前一交易日) - 1`。

**它一上来就抓到了一天没人报过的**（2026-08-07，见 DECLARED）：
当天 72 个可比读数里 **0 个**配得上 08-07 的 K 线、**72/72 配得上 08-06 的**；
`volume` 独立复述同一句话（77/77 配 08-06、2/77 配自己）。整场偏了一天。

---

**口径**（宪法 08-31「先找口径，别自己造」）：
「拿独立厂商的数据核对自家记录」的行业叫法是 **reconciliation / cross-source validation**，
这部分照抄标准做法（逐单元格比 + 容差 + 覆盖率同报）。
**自造的是「帧归属」那一步**（best-matching bar date）—— 查过数据质量文献没有现成名字，
它是本仓 `audit_progress` 的 P2「整场复制」的推广：不止问「像不像前一场」，
而是问「最像哪一场」。自造，且只在**已经判红之后**用来给机制提供线索，不单独判红。

**分辨率（先量再信，别信没量过的阴性）**：
* 干净日的基线：116 个日期里 **110 个**可比行数 ≥15，其中 **108 个匹配率 ≥0.95**，
  中位 **1.000**；最差的干净日是 2026-05-04 的 **0.956**。
* 坏日：08-07 = **0.014**、08-17 = **0.328**。**判定线 0.90 落在 0.328 和 0.956 之间的空档里**，
  不是拍的。
* 非配对日的噪声底 ≈ **0.10–0.14**（任取一个不相干的日子都能偶然对上一成）。
  所以「配得上某一天」要 ≥0.70 才敢具名，见 `NAME_FRAME_MIN`。

**它看不见什么（明写，不留给读者猜）**：
1. **覆盖只有 13%**。本地 K 线库只有 222 只票，`ticker_events` 有 5,068 只。
   一次只毁掉库外票的损坏，这把尺子是瞎的。它量的是**整场**级别的错，不是逐行体检。
2. **change_pct 恒为 0 的筛子测不了**：`healthy_charts` `ema21_watch` `momentum_97` `vcp`
   全史 100% 写 0.0（那是「本列不填」不是「涨跌为零」），本闸整列跳过。
   于是 **2026-08-11/12/13/14 与 03-12/13 这 6 天可比行 <15 → 判「查不了」，不判绿**
   （08-07~08-13 gainers 家族零行，正是 Finviz 改名事故那一周）。
3. **K 线是复权价**：除息日的单日涨跌会差一个股息率量级（<1% 的量级）。
   容差 0.005 吃掉的正是这一类，代价是同量级的真错误也会被吃掉。
4. **本地 K 线库是一张快照**（`fetched_at` 全库同一晚），它自己也可能是坏的。
   厂商若在某天发过坏 bar，本闸会把责任推给归档。**两边同时错才会静默** —— 概率低，但不是零。

⚠️ 这是**棘轮**不是警报（同 `audit_event_agreement` / `audit_ci_test_coverage`）。
归档归 DATA ALEX，夜间组不改 `data/history/`。已知的坏日在 DECLARED 里**具名声明**
（谁、何时发现、为什么、修法归谁），闸对「恰好是这些天」判绿。**声明是欠条，不是结案。**
"""
from __future__ import annotations

import csv
import glob
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Mapping, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "data" / "history" / "ticker_events.csv"
STORE_DIR = ROOT / "data" / "output" / "tickers"

# 容差：0.5pp（绝对，作用在小数形式的涨跌幅上）。
# 依据：干净日的 |偏差| 中位 3e-5、p90 5e-5（纯粹是写入方 round(...,4) 的往返），
# 而真实分歧在 10^-2 量级。0.005 同时吃掉复权/除息带来的量级差（见 docstring 盲区 3）。
TOL = 0.005

# 一天至少要有这么多可比读数才判它。少于此 = 「查不了」，既不绿也不红。
MIN_N = 15

# 判定线。落在实测空档里（最差干净日 0.956 / 最好坏日 0.328），不是拍的。
OK_RATE = 0.90

# 具名「这一帧来自 X 日」的门槛。噪声底实测 0.10–0.14，0.70 有 5 倍余量。
NAME_FRAME_MIN = 0.70

# 帧归属搜索的半径（交易日）。只在已经判红之后跑，用来给机制提供线索。
FRAME_SPAN = 8

# 全史 100% 写 0.0 的筛子 —— 那是「本列不填」，不是涨跌为零。逐行按值跳过（见 _comparable）。
_BLANK = {"", "0", "0.0", "0.00", "0.0000"}

# 日期 -> (owner, 发现日, 理由)。改这张表 = 打一张新欠条，请照体例写清出处。
DECLARED: Dict[str, Tuple[str, str, str]] = {
    "2026-08-07": (
        "DATA ALEX", "2026-09-11",
        "整场偏一天：当日 72 个可比 change_pct **0 个**配 08-07 的 K 线、**72/72 配 08-06 的**；"
        "volume 独立复述同一句话（77/77 配 08-06、2/77 配自己）。当天 604 行全部来自 preset:* "
        "（gainers 家族因 Finviz 改名 e8ac440e 在 08-07~08-13 是零行）。"
        "此前三把闸都看不见它：内部一致、行数正常、days_since 不适用。"
        "修法归数据端：重算或撤下该日的 604 行",
    ),
    "2026-08-17": (
        "DATA ALEX", "2026-09-06",
        "已由 audit_event_agreement / audit_progress 声明（65bbb080 的手动重跑 + e2554467 的预设回填）。"
        "⚠️ 本闸给的补充是**否定性**的：该日 preset 行在厂商 K 线下配不上**任何**单日"
        "（±25 日内最高 0.202，噪声底 0.10–0.14），也配不上任何累计窗口 —— "
        "所以『整日携带 08-14 读数』这个机制，在我能测的 99 只票上得不到外部支持。"
        "『撤下该日 preset:* 行』这个动作不受影响；受影响的是写在旁边的那句机制",
    ),
}


def load_store(store_dir: Path | None = None) -> Dict[str, Dict[str, dict]]:
    """票 -> {日期: bar}。只读，不抓网络。

    ⚠️ 默认值走 None 再回落到模块常量，**不写成 `= STORE_DIR`** ——
    默认参数在 def 那一刻就被绑死，monkeypatch 模块常量对它无效，
    于是测试里「空 K 线库」会静默读到真库、拿到一个假绿（本文件的测试逮到过一次）。
    """
    store_dir = STORE_DIR if store_dir is None else store_dir
    out: Dict[str, Dict[str, dict]] = {}
    for p in sorted(glob.glob(str(store_dir / "*.json"))):
        try:
            with open(p) as fh:
                blob = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        bars = blob.get("ohlc_2y") or blob.get("ohlc_1y") or []
        if not bars:
            continue
        out[os.path.basename(p)[:-5]] = {b["date"]: b for b in bars if b.get("date")}
    return out


def calendar(store: Mapping[str, Mapping[str, dict]]) -> List[str]:
    """K 线库里出现过的所有交易日，升序。用作帧归属的候选集。"""
    days: set = set()
    for bars in store.values():
        days |= set(bars)
    return sorted(days)


def _bar_pct(store, cal_index: Mapping[str, int], cal: Sequence[str],
             ticker: str, day: str) -> float | None:
    """厂商 K 线给出的当日涨跌幅。前一交易日按**该票自己**有 bar 的上一天取。"""
    bars = store.get(ticker)
    if not bars or day not in bars or day not in cal_index:
        return None
    i = cal_index[day]
    prev = None
    for j in range(i - 1, -1, -1):
        if cal[j] in bars:
            prev = bars[cal[j]]
            break
    if not prev or not prev.get("close"):
        return None
    return bars[day]["close"] / prev["close"] - 1.0


def _comparable(rows: Sequence[Mapping[str, str]], day: str) -> List[Tuple[str, float]]:
    out = []
    for r in rows:
        if r.get("date") != day:
            continue
        raw = (r.get("change_pct") or "").strip()
        if raw in _BLANK:
            continue
        try:
            out.append((r["ticker"], float(raw)))
        except ValueError:
            continue
    return out


def _rate(pairs: Sequence[Tuple[str, float]], store, cal_index, cal, day: str,
          tol: float = TOL) -> Tuple[int, int]:
    hit = n = 0
    for ticker, cp in pairs:
        b = _bar_pct(store, cal_index, cal, ticker, day)
        if b is None:
            continue
        n += 1
        if abs(cp - b) <= tol:
            hit += 1
    return hit, n


def attribute_frame(pairs, store, cal_index, cal, day: str,
                    span: int = FRAME_SPAN) -> List[Tuple[float, str, int]]:
    """这一帧最像哪一天？**自造的量**，只在判红之后用来提供线索，不单独判红。"""
    if day not in cal_index:
        return []
    i = cal_index[day]
    out = []
    for cand in cal[max(0, i - span): i + span + 1]:
        hit, n = _rate(pairs, store, cal_index, cal, cand)
        if n >= MIN_N:
            out.append((hit / n, cand, n))
    out.sort(reverse=True)
    return out


def audit(archive: Path | None = None, store_dir: Path | None = None,
          declared: Mapping[str, Tuple[str, str, str]] | None = None) -> dict:
    archive = ARCHIVE if archive is None else archive
    store_dir = STORE_DIR if store_dir is None else store_dir
    declared = DECLARED if declared is None else declared
    with open(archive, newline="") as fh:
        rows = list(csv.DictReader(fh))
    store = load_store(store_dir)
    cal = calendar(store)
    cal_index = {d: i for i, d in enumerate(cal)}

    days = sorted({r["date"] for r in rows if r.get("date")})
    judged: Dict[str, dict] = {}
    unjudgeable: List[Tuple[str, int]] = []
    for day in days:
        pairs = _comparable(rows, day)
        hit, n = _rate(pairs, store, cal_index, cal, day)
        if n < MIN_N:
            unjudgeable.append((day, n))
            continue
        rate = hit / n
        rec = {"rate": rate, "hit": hit, "n": n, "frame": None, "frames": []}
        if rate < OK_RATE:
            frames = attribute_frame(pairs, store, cal_index, cal, day)
            rec["frames"] = frames[:5]
            if frames and frames[0][0] >= NAME_FRAME_MIN and frames[0][1] != day:
                rec["frame"] = frames[0][1]
        judged[day] = rec

    bad = {d: r for d, r in judged.items() if r["rate"] < OK_RATE}
    violations = [
        f"{d}: change_pct 只有 {r['hit']}/{r['n']} ({r['rate']:.1%}) 配得上厂商 K 线"
        + (f" —— 整场配的是 {r['frame']} 的帧" if r["frame"] else " —— 配不上任何单日")
        for d, r in sorted(bad.items()) if d not in declared
    ]
    return {
        "judged": judged, "bad": bad, "unjudgeable": unjudgeable,
        "declared": dict(declared), "violations": violations,
        "store_tickers": len(store),
        "archive_tickers": len({r["ticker"] for r in rows if r.get("ticker")}),
    }


def _fmt(res: dict) -> str:
    L = ["ticker_events × 厂商 K 线 —— 一条不需要归档自己作证的恒等式", ""]
    ok = sum(1 for r in res["judged"].values() if r["rate"] >= OK_RATE)
    L.append(f"  判过的交易日: {len(res['judged'])}  (其中 {ok} 天 ≥{OK_RATE:.0%})")
    L.append(f"  覆盖: 本地 K 线库 {res['store_tickers']} 只 / 归档 {res['archive_tickers']} 只 "
             f"—— **这把尺子只量整场级别的错，不是逐行体检**")
    if res["unjudgeable"]:
        L.append(f"  查不了（可比读数 <{MIN_N}）: {len(res['unjudgeable'])} 天 —— "
                 "不判绿，见 docstring 盲区 2")
        for d, n in res["unjudgeable"]:
            L.append(f"      {d}  n={n}")
    L.append("")
    for d, r in sorted(res["bad"].items()):
        entry = res["declared"].get(d)
        L.append(f"  {'[declared]' if entry else '[UNDECLARED]'} {d}: "
                 f"{r['hit']}/{r['n']} ({r['rate']:.1%}) 配得上当日 K 线")
        if entry:
            L.append(f"      owner: {entry[0]}  (发现于 {entry[1]})")
            L.append(f"      why:   {entry[2]}")
        if r["frame"]:
            L.append(f"      帧归属: **{r['frame']}** —— 整场配的是那一天的 K 线")
        elif r["frames"]:
            top = ", ".join(f"{c}={x:.3f}" for x, c, _ in r["frames"][:3])
            L.append(f"      帧归属: 配不上任何单日（最高 {top}；噪声底 0.10–0.14）")
    L.append("")
    L.append("声明是欠条，不是结案。")
    L.append("")
    L.append("\n".join(f"E1 {v}" for v in res["violations"])
             or "no violations (判红的日子恰好等于声明的那些)")
    return "\n".join(L)


def main(argv: List[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    archive = Path(argv[0]) if argv else ARCHIVE
    if not archive.exists():
        print(f"归档不存在: {archive} —— 本闸没有结论，不是绿也不是红", file=sys.stderr)
        return 2
    store = load_store()
    if not store:
        print(f"本地 K 线库为空: {STORE_DIR} —— 本闸没有结论，不是绿也不是红", file=sys.stderr)
        return 2
    res = audit(archive)
    print(_fmt(res))
    return 1 if res["violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
