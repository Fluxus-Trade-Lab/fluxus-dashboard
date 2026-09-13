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
   于是 08-07 与 08-11/12/13 这一周（Finviz 改名，gainers 家族零行）在 change_pct 上可比行 <15。
   **这一格 2026-09-14 起由第二条恒等式补上**（Nighty Zac）：`volume(某日, 某票)` 应等于
   厂商 K 线**当日**那根 bar 的成交量。它和 change_pct 同行同快照，但**不共用任何算术**
   （一个是两根收盘价之比，一个是一根 bar 的量），所以能在 change_pct 整列为空时单独判。
   两条都 <15 才判「查不了」：现存只剩 **03-12 / 03-13**。
   * **带是单边的，而且是自造的**：Finviz 快照量 ÷ yfinance 当日量 ∈ [0.90, 1.01]。
     查过（reconciliation 的标准做法只规定「逐单元格比 + 容差」，不规定成交量容差是多少），无标准，
     按实测定：Finviz 取数早于最终合并成交量，春夏的日子系统性偏低 1–3%（04-29 比值中位 0.981），
     08-20 起中位 1.000；全史 7,275 行里比值 >1.01 的只有 5 行。对称 ±2% 会把 04-29 判成 0.567。
   * **分辨率**（全史 113 个可判日）：干净日最差 **0.925**（08-14），中位 1.000；
     非自身日的噪声底中位 0.17、最高 **0.304**；冻结坏行 08-07 = **0.125**（帧 = 08-06，1.000）、
     08-17 = **0.24**（配不上任何单日）。判定线 `VOL_OK_RATE = 0.70` 落在 0.304 与 0.925 的空档里。
     **时间切分复核**：带只用 06-15 前 66 天选，06-15 起 52 天上干净日最差 0.925 / 噪声最高 0.304，站得住。
   * 看不见的：一场只偏了成交量级别（不是整场换帧）的错；以及量恰好在 ±10% 内相邻两日的票（噪声底就是它）。
3. **K 线是复权价**：除息日的单日涨跌会差一个股息率量级（<1% 的量级）。
   容差 0.005 吃掉的正是这一类，代价是同量级的真错误也会被吃掉。
4. **本地 K 线库是一张快照**（`fetched_at` 全库同一晚），它自己也可能是坏的。
   厂商若在某天发过坏 bar，本闸会把责任推给归档。**两边同时错才会静默** —— 概率低，但不是零。
5. **最新一场常常查不了**：cron 写完归档时，K 线库可能还停在上一场
   （2026-09-11 实测：归档已有 09-10，库的最后一根 bar 是 09-09）。于是写入当晚最该查的那一场
   恰好判「查不了」。生产接线必须放在**K 线库刷新之后**，否则它每晚都对最新一场是瞎的。

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

# 第二条恒等式（volume）的单边带与判定线。**自造**，依据见 docstring 盲区 2 的实测。
# 下沿宽、上沿紧：Finviz 快照早于最终合并成交量，只会少记不会多记（全史 >1.01 的 5/7,275 行）。
VOL_LO = 0.90
VOL_HI = 1.01
# 干净日最差 0.925 / 噪声底最高 0.304 / 冻结坏行 0.125 与 0.24。0.70 落在空档里。
VOL_OK_RATE = 0.70

# 全史 100% 写 0.0 的筛子 —— 那是「本列不填」，不是涨跌为零。逐行按值跳过（见 _comparable）。
_BLANK = {"", "0", "0.0", "0.00", "0.0000"}

# 日期 -> (owner, 发现日, 理由)。改这张表 = 打一张新欠条，请照体例写清出处。
#
# 已还清的欠条（2026-09-13 DATA ALEX，原行冻在 pipeline/tests/fixtures/events_vs_bars/ 当真阳性对照）：
#   2026-08-07  整场偏一天 —— backfill_preset_hits 用 UTC 日历日给 universe.json 快照定日期，
#               08-06 21:08 ET 的 69754ed3 被记成 08-07。snapshot_dates 改按 ET 场次挑、并排除下一场盘前
#               之后的提交，重算后该日 preset 行来自 7c162f49；change_pct 那周因 Finviz 改名为空，判「查不了」。
#   2026-08-17  配不上任何单日 —— 旧快照是周一盘前的手动重跑 65bbb080；重算改用 422e9270（行内 bar_date=08-17），
#               151/151 配当日 K 线。
DECLARED: Dict[str, Tuple[str, str, str]] = {}


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


def _comparable_volume(rows: Sequence[Mapping[str, str]], day: str) -> List[Tuple[str, float]]:
    """day 这一场每只票一个 volume。同一只票被几个筛子写了几遍，只算一次 ——
    否则一只票出现在五个筛子里就投五票，坏日会被少数几只票的重复稀释或放大。"""
    seen: Dict[str, float] = {}
    for r in rows:
        if r.get("date") != day:
            continue
        t = r.get("ticker")
        if not t or t in seen:
            continue
        try:
            v = float((r.get("volume") or "").strip())
        except ValueError:
            continue
        if v > 0:
            seen[t] = v
    return list(seen.items())


def _vol_rate(pairs: Sequence[Tuple[str, float]], store, cal_index, cal, day: str,
              lo: float = VOL_LO, hi: float = VOL_HI) -> Tuple[int, int]:
    """volume 对**当日**那根 bar 的成交量（不是前一日 —— 与 change_pct 不同，这里没有前收）。"""
    hit = n = 0
    for ticker, v in pairs:
        bar = (store.get(ticker) or {}).get(day)
        if not bar or not bar.get("volume"):
            continue
        n += 1
        if lo <= v / bar["volume"] <= hi:
            hit += 1
    return hit, n


def attribute_frame(pairs, store, cal_index, cal, day: str,
                    span: int = FRAME_SPAN, rate_fn=None) -> List[Tuple[float, str, int]]:
    """这一帧最像哪一天？**自造的量**，只在判红之后用来提供线索，不单独判红。"""
    rate_fn = _rate if rate_fn is None else rate_fn
    if day not in cal_index:
        return []
    i = cal_index[day]
    out = []
    for cand in cal[max(0, i - span): i + span + 1]:
        hit, n = rate_fn(pairs, store, cal_index, cal, cand)
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

    # 第二条恒等式：volume 对当日 bar。和上面独立判、独立报；声明对两条都生效。
    vjudged: Dict[str, dict] = {}
    vunjudgeable: List[Tuple[str, int]] = []
    for day in days:
        vpairs = _comparable_volume(rows, day)
        hit, n = _vol_rate(vpairs, store, cal_index, cal, day)
        if n < MIN_N:
            vunjudgeable.append((day, n))
            continue
        rate = hit / n
        rec = {"rate": rate, "hit": hit, "n": n, "frame": None, "frames": []}
        if rate < VOL_OK_RATE:
            frames = attribute_frame(vpairs, store, cal_index, cal, day, rate_fn=_vol_rate)
            rec["frames"] = frames[:5]
            if frames and frames[0][0] >= NAME_FRAME_MIN and frames[0][1] != day:
                rec["frame"] = frames[0][1]
        vjudged[day] = rec
    vbad = {d: r for d, r in vjudged.items() if r["rate"] < VOL_OK_RATE}
    violations += [
        f"{d}: volume 只有 {r['hit']}/{r['n']} ({r['rate']:.1%}) 配得上厂商 K 线当日成交量"
        + (f" —— 整场配的是 {r['frame']} 的帧" if r["frame"] else " —— 配不上任何单日")
        for d, r in sorted(vbad.items()) if d not in declared
    ]
    return {
        "judged": judged, "bad": bad, "unjudgeable": unjudgeable,
        "volume": {"judged": vjudged, "bad": vbad, "unjudgeable": vunjudgeable},
        "blind": [(d, n) for d, n in unjudgeable if d not in vjudged],
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
    vol = res["volume"]
    vok = sum(1 for r in vol["judged"].values() if r["rate"] >= VOL_OK_RATE)
    L.append(f"  volume 恒等式判过: {len(vol['judged'])} 天  (其中 {vok} 天 ≥{VOL_OK_RATE:.0%})")
    rescued = [(d, n) for d, n in res["unjudgeable"] if d in vol["judged"]]
    if rescued:
        L.append(f"  change_pct 查不了、改由 volume 判: {len(rescued)} 天")
        for d, n in rescued:
            r = vol["judged"][d]
            L.append(f"      {d}  change_pct n={n} · volume {r['hit']}/{r['n']} ({r['rate']:.1%})")
    if res["blind"]:
        L.append(f"  查不了（两条恒等式可比读数都 <{MIN_N}）: {len(res['blind'])} 天 —— "
                 "不判绿，见 docstring 盲区 2")
        for d, n in res["blind"]:
            L.append(f"      {d}  n={n}")
    L.append("")
    for d, r in sorted(vol["bad"].items()):
        entry = res["declared"].get(d)
        L.append(f"  {'[declared]' if entry else '[UNDECLARED]'} {d}: "
                 f"volume {r['hit']}/{r['n']} ({r['rate']:.1%}) 配得上当日成交量")
        if entry and d not in res["bad"]:
            L.append(f"      owner: {entry[0]}  (发现于 {entry[1]})")
            L.append(f"      why:   {entry[2]}")
        if r["frame"]:
            L.append(f"      帧归属: **{r['frame']}** —— 整场的成交量是那一天的")
        elif r["frames"]:
            top = ", ".join(f"{c}={x:.3f}" for x, c, _ in r["frames"][:3])
            L.append(f"      帧归属: 配不上任何单日（最高 {top}；噪声底 0.17–0.30）")
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
