#!/usr/bin/env python3
"""取件账 09-06·1 的并排评测:第 1 节候选闸的第三条判据——「不在昨天榜首」(A) vs
「人数日环比」(B) vs **「新面孔人数」(C,Steve 09-27 裁决版,T-0927-66 实装)**。

只读 mentions.csv,不改生产逻辑。产出一份 markdown 报告,逐日列出三种判据各自
选出的候选票。**判据从 09-27 起就是 C**,A/B 留着只为继续并排对照,不再是待裁项。

背景(README.md 取件账 09-06·1 → 09-25d·3):第 1 节候选闸现行第三条曾是「不在
昨天的榜首」——一旦某票昨天已经上过候选,今天哪怕人数还在涨也一律排除($INTC
1→6→4 被挡掉,排名不量位移)。09-06 提出改用「人数日环比」,但 09-25 评测发现
字面版(B,只看 Δ人数≠0、不分方向)会把**降温**的票也当新鲜——09-25 `$AMD`
(Δ−1)`$INTC`(Δ−1)都被 B 误选。Steve 09-27 裁决:切「新面孔人数」版(C)——
今天 qualifying 的人里有几个**不在**昨天的名单上,≥1 才算新鲜。

判据定义(前两条三边共用,只有第三条不同——照抄 runbook 第 70 行「只收同时满足的:
≥2 人提 · 立场是 long/watching(不是 recap/exited) · 不在昨天的榜首」):
  1. 剔清单帖:同一 post_id 覆盖 >6 个不同代码的帖子,整条不计入人数(daily 报告口径,
     `$LITE` `$INTC` 那几行的「剔清单」列就是这么算的)。
  2. 剔指数/宽基 ETF(与 build_board.py 的 INDEX 集合一致,第 1 节只登个股)。
  3. 当天「立场为 long/watching」的不同 handle 数(qualifying people)>= 2。
  4a. 判据 A(旧现行·不在昨天榜首):今天过 1-3 关,且该票**不在**昨天的候选集合里
      (candidates_A(D-1))才算候选——只要昨天已经候选过,今天无论涨跌一律排除。
  4b. 判据 B(字面提案·人数日环比):今天过 1-3 关,且 Δ人数 = 今天 qualifying 人数 −
      昨天 qualifying 人数 != 0(有真实位移,涨或跌都算)——**已确认的坏形状**:
      09-25 `$AMD`/`$INTC` 降温(Δ<0)也会被它当新鲜候选选中。
  4c. 判据 C(现行·新面孔人数,09-27 起生效):今天过 1-3 关,且今天 qualifying
      的 handle 集合减去昨天 qualifying 的 handle 集合非空(至少 1 个新面孔)。
      能接住 A/B 都接不住的「换人不换数」(09-14 `$GOOGL`、09-21 `$INTC`、
      09-21/09-24 `$MU`),也能正确排除「总数降、且没有一张新面孔」的纯降温票
      ——⚠️ **09-25 `$AMD`/`$INTC` 不是后一种的真实个案**:两票当天各来了 1 位
      新面孔,C 按定义仍会选中它们,只是理由从「B 的纯数量变化」变成「确有新
      声音」,不是被排除;真实数据下本窗口的「纯降温、零新面孔」个案数是 0
      (见 `cooldown_scan` 与其调用处)。
  首日(D-1 无数据)按 Δ=今天人数、candidates_A(D-1)=空集、昨天 handle 集合=空集
  处理,三边等价(首日全员都是「新面孔」)。

另附两组个案扫描:
  ①「换人不换数」:同一票连续两天都 ≥2 人,但两天的人完全不重叠(总人数没变,
    人换了)——A 和字面意义的 B 都接不住,C 靠「有新面孔」接住。
  ②「降温不算新鲜」:今天人数比昨天**少**,但今天的人是昨天名单的**纯子集**
    (一张新面孔都没有)——B 会误选,C 靠「没有新面孔」正确排除。这是纯假设
    形状的扫描,09-25 `$AMD`/`$INTC` 因为各带 1 位新面孔,不落在这组个案里
    (真实数据下本窗口零命中,见下方 `cooldown_scan`)。

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


def daterange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def qualifying_handles_by_date(rows: list[dict]) -> dict[str, dict[str, set[str]]]:
    """date -> {ticker: qualifying handle 集合}——判据 C(新面孔人数)与两组个案扫描的底数据。"""
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
    handles = qualifying_handles_by_date(rows)
    counts = {d: {sym: len(hs) for sym, hs in syms.items()} for d, syms in handles.items()}
    out = []
    prev_candidates_a: set[str] = set()
    for d in daterange(start, end):
        ds = d.isoformat()
        today = counts.get(ds, {})
        today_handles = handles.get(ds, {})
        prev_ds = (d - timedelta(days=1)).isoformat()
        prev = counts.get(prev_ds, {})
        prev_handles = handles.get(prev_ds, {})

        cand_a = {sym: n for sym, n in today.items()
                  if n >= 2 and sym not in prev_candidates_a}
        cand_b = {}
        for sym, n in today.items():
            if n < 2:
                continue
            delta = n - prev.get(sym, 0)
            if delta != 0:
                cand_b[sym] = (n, delta)
        cand_c = {}
        for sym, hs in today_handles.items():
            if len(hs) < 2:
                continue
            new_faces = hs - prev_handles.get(sym, set())
            if new_faces:
                cand_c[sym] = (len(hs), len(new_faces))

        out.append({
            "date": ds,
            "a": cand_a,
            "b": cand_b,
            "c": cand_c,
            "a_only": sorted(set(cand_a) - set(cand_b)),
            "b_only": sorted(set(cand_b) - set(cand_a)),
            "both": sorted(set(cand_a) & set(cand_b)),
            "c_only": sorted(set(cand_c) - set(cand_a) - set(cand_b)),
            "abc_agree": sorted(set(cand_a) & set(cand_b) & set(cand_c)),
        })
        prev_candidates_a = set(cand_a)
    return out


def turnover_scan(rows: list[dict], start: date, end: date) -> list[dict]:
    """找「换人不换数」个案:今天、昨天都 >=2 个 qualifying 人,但两天的人**完全不重叠**。
    这类票 A 必挡(昨天已候选过)、B(严格人数环比)在人数没变时也挡不住,C(新面孔
    人数)靠「有新面孔」接住——直接对应 README 09-06·1 引用的 09-14 $GOOGL 真实案例
    (2 人→2 人,但换了两个新人)。
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
                new_faces = hs - prev_hs
                out.append({
                    "date": ds, "sym": sym,
                    "today": sorted(hs), "prev": sorted(prev_hs),
                    "caught_by_a": False,  # A 按定义必排除(昨天已候选过)
                    "caught_by_b": delta_count != 0,
                    "caught_by_c": bool(new_faces),
                })
    return out


def cooldown_scan(rows: list[dict], start: date, end: date) -> list[dict]:
    """找「降温不算新鲜」个案:今天 qualifying 人数比昨天**少**,且今天的人是昨天
    名单的**纯子集**(一张新面孔都没有)——B(字面人数环比,只看 Δ≠0 不分方向)
    会把这类票误选成候选,C(新面孔人数)靠「没有新面孔」正确排除。⚠️ 09-25
    `$AMD`/`$INTC` 虽然也是 Δ<0,但两票当天各带 1 位新面孔,不满足「纯子集」,
    不落在这组个案里(C 仍会选中它们,理由是那位新面孔,不是被排除)——这组
    扫描量的是理论上更极端的形状:总量在降、且连一个新声音都没有。
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
            if len(prev_hs) < 2:
                continue
            delta_count = len(hs) - len(prev_hs)
            new_faces = hs - prev_hs
            if delta_count < 0 and not new_faces:
                out.append({
                    "date": ds, "sym": sym,
                    "today": sorted(hs), "prev": sorted(prev_hs),
                    "caught_by_b": delta_count != 0,   # 字面口径的假阳性,恒 True
                    "caught_by_c": bool(new_faces),    # C 正确排除,恒 False
                })
    return out


def render(report: list[dict], start: date, end: date, turnovers: list[dict],
          cooldowns: list[dict]) -> str:
    lines = []
    lines.append(f"# 候选闸判据并排评测 · {start}→{end}")
    lines.append("")
    lines.append("取件账 09-06·1 → 09-25d·3 的脚本化并排评测,机制见 "
                  "[`tools/compare_candidate_rules.py`](../tools/compare_candidate_rules.py) "
                  "文件头注释。**判据 A** = 旧现行「不在昨天榜首」;**判据 B** = 字面提案"
                  "「人数日环比(Δ≠0)」;**判据 C** = **现行(09-27 起生效)「新面孔人数」**"
                  "(今天 qualifying 的人里有几个不在昨天名单上,≥1 才算新鲜)。"
                  "前两条(≥2 人、立场 long/watching、剔清单剔指数)三边共用,只对比第三条。")
    lines.append("")
    lines.append("| 日期 | 判据 A 候选(不在昨天榜首) | 判据 B 候选(人数日环比) | "
                  "判据 C 候选(新面孔人数) | 只 C 选(A、B 都没选) |")
    lines.append("|---|---|---|---|---|")
    for r in report:
        a_str = " · ".join(f"`${s}`={n}" for s, n in sorted(r["a"].items())) or "—"
        b_str = " · ".join(f"`${s}`={n}(Δ{d:+d})" for s, (n, d) in sorted(r["b"].items())) or "—"
        c_str = " · ".join(f"`${s}`={n}(+{k}新)" for s, (n, k) in sorted(r["c"].items())) or "—"
        c_only = " · ".join(f"`${s}`" for s in r["c_only"]) or "—"
        lines.append(f"| {r['date']} | {a_str} | {b_str} | {c_str} | {c_only} |")

    n_days = len(report)
    n_a = sum(len(r["a"]) for r in report)
    n_b = sum(len(r["b"]) for r in report)
    n_c = sum(len(r["c"]) for r in report)
    n_abc = sum(len(r["abc_agree"]) for r in report)
    total_c_only = sorted({s for r in report for s in r["c_only"]})

    lines.append("")
    lines.append(f"## 小计({n_days} 天)")
    lines.append(f"- 判据 A 选中候选 {n_a} 票-日 · 判据 B 选中候选 {n_b} 票-日 · "
                  f"判据 C 选中候选 {n_c} 票-日 · 三者都选 {n_abc} 票-日")
    lines.append(f"- 只 C 选、A/B 都不选(新面孔但总数没有真实位移,B 会漏掉的形状):"
                  f"{'、'.join(f'`${s}`' for s in total_c_only) or '无'}")
    lines.append("")
    lines.append("## 「换人不换数」个案扫描(C 的收益 ①:接住 A/B 的假阴性)")
    lines.append("")
    lines.append("同一票连续两天都 ≥2 个 qualifying 人,但两天的人**完全不重叠**——"
                  "这类票判据 A 必排除(昨天已候选过),严格「人数环比」(判据 B,总人数之差)"
                  "在人数没变时**也**排除,判据 C 靠「有新面孔」接住。"
                  "README 09-06·1 引用的 09-14 `$GOOGL` 真实案例就是这个形状。")
    lines.append("")
    if turnovers:
        lines.append("| 日期 | 票 | 昨天是谁 | 今天是谁 | 判据 A 接住? | 判据 B 接住? | 判据 C 接住? |")
        lines.append("|---|---|---|---|---|---|---|")
        for t in turnovers:
            a_mark = "✅" if t["caught_by_a"] else "❌"
            b_mark = "✅" if t["caught_by_b"] else "❌"
            c_mark = "✅" if t["caught_by_c"] else "❌"
            lines.append(f"| {t['date']} | `${t['sym']}` | "
                          f"{' / '.join(t['prev'])} | {' / '.join(t['today'])} | "
                          f"{a_mark} | {b_mark} | {c_mark} |")
        n_missed_by_b = sum(1 for t in turnovers if not t["caught_by_b"])
        n_missed_by_c = sum(1 for t in turnovers if not t["caught_by_c"])
        lines.append("")
        lines.append(f"{n_missed_by_b}/{len(turnovers)} 例判据 B 按字面(总人数之差)接不住,"
                      f"**{n_missed_by_c}/{len(turnovers)} 例判据 C 接不住**"
                      "(定义上 C 恒接住此类:换人即有新面孔)。")
    else:
        lines.append("本窗口零个案。")
    lines.append("")
    lines.append("## 「降温不算新鲜」个案扫描(C 的收益 ②:排除 B 的假阳性)")
    lines.append("")
    lines.append("今天 qualifying 人数比昨天**少**,且今天的人是昨天名单的**纯子集**"
                  "(一张新面孔都没有)——判据 B(字面人数环比)会把这类票误选成候选,"
                  "判据 C 靠「没有新面孔」正确排除。⚠️ 09-25 `$AMD`/`$INTC` 虽然也是 Δ<0"
                  "(见上面主表判据 B 那两格),但两票当天各带 1 位新面孔,不满足「纯子集」,"
                  "不落在下面这组扫描里——判据 C 仍会选中它们(理由是那位新面孔,不是被排除)。"
                  "这组扫描量的是更极端的形状,是 B 被否掉、切 C 的理论理由,不是逐个案例都要在"
                  "本窗口找到。")
    lines.append("")
    if cooldowns:
        lines.append("| 日期 | 票 | 昨天是谁 | 今天是谁 | 判据 B 误选? | 判据 C 正确排除? |")
        lines.append("|---|---|---|---|---|---|")
        for c in cooldowns:
            b_mark = "⚠️ 误选" if c["caught_by_b"] else "—"
            c_mark = "✅ 排除" if not c["caught_by_c"] else "❌ 仍误选"
            lines.append(f"| {c['date']} | `${c['sym']}` | "
                          f"{' / '.join(c['prev'])} | {' / '.join(c['today'])} | "
                          f"{b_mark} | {c_mark} |")
    else:
        lines.append("本窗口零个案。")
    lines.append("")
    lines.append("⚠️ **判据从 09-27 起就是 C(新面孔人数),本报告是切换后的核验读数,"
                  "不再是待裁的并排评测。** Steve 09-27 裁决见 README.md 取件账 09-25d·3。")
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
    cooldowns = cooldown_scan(rows, start, end)
    text = render(report, start, end, turnovers, cooldowns)
    if args.out:
        out_path = Path(args.out)
        out_path.write_text(text, encoding="utf-8")
        print(f"→ {out_path}")
    else:
        print(text)


if __name__ == "__main__":
    main()
