#!/usr/bin/env python3
"""取件账 09-06·1 的并排评测:第 1 节候选闸的第三条判据,「不在昨天榜首」vs「人数日环比」。

只读 mentions.csv,不改生产逻辑、不改 build_board.py。产出一份 markdown 报告,
逐日列出两种判据各自选出的候选票,供 Steve 周日直接读数决定要不要切换判据。

背景(README.md 取件账 09-06·1):第 1 节候选闸现行第三条是「不在昨天的榜首」——
一旦某票昨天已经上过候选,今天哪怕人数还在涨也一律排除($INTC 1→6→4 被挡掉,
排名不量位移)。09-06 提出改用「人数日环比」,三次承诺评估都没跑成,本脚本把它脚本化。

判据定义(前两条两边共用,只有第三条不同——照抄 runbook 第 70 行「只收同时满足的:
≥2 人提 · 立场是 long/watching(不是 recap/exited) · 不在昨天的榜首」):
  1. 剔清单帖:同一 post_id 覆盖 >6 个不同代码的帖子,整条不计入人数(daily 报告口径,
     `$LITE` `$INTC` 那几行的「剔清单」列就是这么算的)。
  2. 剔指数/宽基 ETF(与 build_board.py 的 INDEX 集合一致,第 1 节只登个股)。
  3. 当天「立场为 long/watching」的不同 handle 数(qualifying people)>= 2。
  4a. 判据 A(现行·不在昨天榜首):今天过 1-3 关,且该票**不在**昨天的候选集合里
      (candidates_A(D-1))才算候选——只要昨天已经候选过,今天无论涨跌一律排除。
  4b. 判据 B(提案·人数日环比):今天过 1-3 关,且 Δ人数 = 今天 qualifying 人数 −
      昨天 qualifying 人数 != 0(有真实位移,涨或跌都算,而不是「昨天出现过就排除」)
      —— 直接对着 INTC 案例设计:1→6(Δ=+5,判据 B 第 2 天选中)→4(Δ=-2,判据 B
      第 3 天仍选中,现行判据 A 排除)。
  首日(D-1 无数据)按 Δ=今天人数、candidates_A(D-1)=空集处理,两边等价。

另附「换人不换数」个案扫描:同一票连续两天都 ≥2 人,但两天的人完全不重叠
(总人数没变,人换了)——判据 A 和字面意义的判据 B 都接不住,这正是 README
09-06·1 引用的 09-14 `$GOOGL` 真实案例的形状,单靠候选表看不出这条。

用法:
  python3 compare_candidate_rules.py --start 2026-09-08 --end 2026-09-18 \
      --out ../scoring/2026-09-19_candidate_rule_compare.md
"""
from __future__ import annotations
import argparse
import csv
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
MENTIONS = BASE / "mentions.csv"

QUALIFYING_STANCE = {"long", "watching"}
LIST_POST_THRESHOLD = 6  # daily 报告口径:一个 post_id 挂 >6 个代码算清单帖,整条剔除

INDEX = {"SPY", "QQQ", "VIX", "SPX", "NDX", "IWM", "DIA", "SMH", "IWF", "IWD",
         "QQQE", "RSP", "TLT", "GLD", "SLV", "USO", "XLK", "XLF", "XLE", "XLV",
         "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC", "ETH", "BTC"}


def load_rows() -> list[dict]:
    with MENTIONS.open(newline="") as fh:
        return list(csv.DictReader(fh))


def list_post_ids(rows: list[dict]) -> set[str]:
    """post_id -> 它挂了几个不同代码;返回超过阈值的 post_id 集合。"""
    tickers_by_post: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        tickers_by_post[r["post_id"]].add(r["ticker"])
    return {pid for pid, syms in tickers_by_post.items() if len(syms) > LIST_POST_THRESHOLD}


def qualifying_counts_by_date(rows: list[dict]) -> dict[str, dict[str, int]]:
    """date -> {ticker: qualifying 人数}。剔清单帖、剔指数,立场限 long/watching。"""
    excluded = list_post_ids(rows)
    people: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for r in rows:
        if r["post_id"] in excluded:
            continue
        sym = r["ticker"]
        if sym in INDEX:
            continue
        if (r.get("stance") or "").strip() not in QUALIFYING_STANCE:
            continue
        people[r["date"]][sym].add(r["handle"])
    return {d: {sym: len(hs) for sym, hs in syms.items()} for d, syms in people.items()}


def daterange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def qualifying_handles_by_date(rows: list[dict]) -> dict[str, dict[str, set[str]]]:
    """date -> {ticker: qualifying handle 集合}——给「换人不换数」扫描用,不进候选表。"""
    excluded = list_post_ids(rows)
    out: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for r in rows:
        if r["post_id"] in excluded:
            continue
        sym = r["ticker"]
        if sym in INDEX:
            continue
        if (r.get("stance") or "").strip() not in QUALIFYING_STANCE:
            continue
        out[r["date"]][sym].add(r["handle"])
    return out


def compare(rows: list[dict], start: date, end: date) -> list[dict]:
    counts = qualifying_counts_by_date(rows)
    out = []
    prev_candidates_a: set[str] = set()
    for d in daterange(start, end):
        ds = d.isoformat()
        today = counts.get(ds, {})
        prev_ds = (d - timedelta(days=1)).isoformat()
        prev = counts.get(prev_ds, {})

        cand_a = {sym: n for sym, n in today.items()
                  if n >= 2 and sym not in prev_candidates_a}
        cand_b = {}
        for sym, n in today.items():
            if n < 2:
                continue
            delta = n - prev.get(sym, 0)
            if delta != 0:
                cand_b[sym] = (n, delta)

        out.append({
            "date": ds,
            "a": cand_a,
            "b": cand_b,
            "a_only": sorted(set(cand_a) - set(cand_b)),
            "b_only": sorted(set(cand_b) - set(cand_a)),
            "both": sorted(set(cand_a) & set(cand_b)),
        })
        prev_candidates_a = set(cand_a)
    return out


def turnover_scan(rows: list[dict], start: date, end: date) -> list[dict]:
    """找「换人不换数」个案:今天、昨天都 >=2 个 qualifying 人,但两天的人**完全不重叠**。
    这类票 A 必挡(昨天已候选过)、B(严格人数环比)在人数没变时也挡不住
    ——直接对应 README 09-06·1 引用的 09-14 $GOOGL 真实案例(2 人→2 人,但换了两个新人)。
    """
    handles = qualifying_handles_by_date(rows)
    out = []
    for d in daterange(start, end):
        ds = d.isoformat()
        prev_ds = (d - timedelta(days=1)).isoformat()
        today_syms = handles.get(ds, {})
        prev_syms = handles.get(prev_ds, {})
        for sym, hs in today_syms.items():
            if len(hs) < 2:
                continue
            prev_hs = prev_syms.get(sym, set())
            if len(prev_hs) >= 2 and not (hs & prev_hs):
                delta_count = len(hs) - len(prev_hs)
                out.append({
                    "date": ds, "sym": sym,
                    "today": sorted(hs), "prev": sorted(prev_hs),
                    "caught_by_a": False,  # A 按定义必排除(昨天已候选过)
                    "caught_by_b": delta_count != 0,
                })
    return out


def render(report: list[dict], start: date, end: date, turnovers: list[dict]) -> str:
    lines = []
    lines.append(f"# 候选闸判据并排评测 · {start}→{end}")
    lines.append("")
    lines.append("取件账 09-06·1 的脚本化并排评测,机制见 "
                  "[`tools/compare_candidate_rules.py`](../tools/compare_candidate_rules.py) "
                  "文件头注释。**判据 A** = 现行「不在昨天榜首」;**判据 B** = 提案"
                  "「人数日环比(Δ≠0)」。前两条(≥2 人、立场 long/watching、剔清单剔指数)"
                  "两边共用,只对比第三条。")
    lines.append("")
    lines.append("| 日期 | 判据 A 候选(不在昨天榜首) | 判据 B 候选(人数日环比) | 两边都选 | 只 A 选 | 只 B 选 |")
    lines.append("|---|---|---|---|---|---|")
    for r in report:
        a_str = " · ".join(f"`${s}`={n}" for s, n in sorted(r["a"].items())) or "—"
        b_str = " · ".join(f"`${s}`={n}(Δ{d:+d})" for s, (n, d) in sorted(r["b"].items())) or "—"
        both = " · ".join(f"`${s}`" for s in r["both"]) or "—"
        a_only = " · ".join(f"`${s}`" for s in r["a_only"]) or "—"
        b_only = " · ".join(f"`${s}`" for s in r["b_only"]) or "—"
        lines.append(f"| {r['date']} | {a_str} | {b_str} | {both} | {a_only} | {b_only} |")

    total_a_only = sorted({s for r in report for s in r["a_only"]})
    total_b_only = sorted({s for r in report for s in r["b_only"]})
    n_days = len(report)
    n_a = sum(len(r["a"]) for r in report)
    n_b = sum(len(r["b"]) for r in report)
    n_overlap = sum(len(r["both"]) for r in report)

    lines.append("")
    lines.append(f"## 小计({n_days} 天)")
    lines.append(f"- 判据 A 选中候选 {n_a} 票-日 · 判据 B 选中候选 {n_b} 票-日 · 重叠 {n_overlap} 票-日")
    lines.append(f"- 只 A 选、B 不选(A 会漏掉的、Δ=0 却仍是新上榜的极少数情形):"
                  f"{'、'.join(f'`${s}`' for s in total_a_only) or '无'}")
    lines.append(f"- 只 B 选、A 不选(A 因为「昨天出现过」误杀,但今天人数其实有真实位移):"
                  f"{'、'.join(f'`${s}`' for s in total_b_only) or '无'}")
    lines.append("")
    lines.append("## 「换人不换数」个案扫描")
    lines.append("")
    lines.append("同一票连续两天都 ≥2 个 qualifying 人,但两天的人**完全不重叠**——"
                  "这类票判据 A 必排除(昨天已候选过),严格「人数环比」(判据 B,总人数之差)"
                  "在人数没变时**也**排除。README 09-06·1 引用的 09-14 `$GOOGL` 真实案例就是这个形状。")
    lines.append("")
    if turnovers:
        lines.append("| 日期 | 票 | 昨天是谁 | 今天是谁 | 判据 A 接住? | 判据 B(严格人数环比)接住? |")
        lines.append("|---|---|---|---|---|---|")
        for t in turnovers:
            a_mark = "✅" if t["caught_by_a"] else "❌"
            b_mark = "✅" if t["caught_by_b"] else "❌"
            lines.append(f"| {t['date']} | `${t['sym']}` | "
                          f"{' / '.join(t['prev'])} | {' / '.join(t['today'])} | {a_mark} | {b_mark} |")
        n_missed_by_b = sum(1 for t in turnovers if not t["caught_by_b"])
        lines.append("")
        lines.append(f"⚠️ **{n_missed_by_b}/{len(turnovers)} 例「换人不换数」,判据 B 按字面"
                      "(总人数之差)也接不住**——因为环比算的是总数的加减,人数刚好没变时 Δ=0,"
                      "跟判据 A 一样把它排除。「人数日环比」如果要真的接住这类假阴性,"
                      "环比的对象得从「总人数」换成「新面孔人数」(今天 qualifying 的人里,"
                      "有几个不在昨天 qualifying 名单上)——这是本次评测发现的、原提案文字"
                      "没写清楚的一个歧义,留给 Steve 周日和这份表一起判。")
    else:
        lines.append("本窗口零个案。")
    lines.append("")
    lines.append("⚠️ 本报告只出对照数据,不改现行判据。Steve 周日按这份数据在 "
                  "README.md 取件账 09-06·1 行定夺。")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)

    rows = load_rows()
    report = compare(rows, start, end)
    turnovers = turnover_scan(rows, start, end)
    text = render(report, start, end, turnovers)
    if args.out:
        out_path = Path(args.out)
        out_path.write_text(text, encoding="utf-8")
        print(f"→ {out_path}")
    else:
        print(text)


if __name__ == "__main__":
    main()
