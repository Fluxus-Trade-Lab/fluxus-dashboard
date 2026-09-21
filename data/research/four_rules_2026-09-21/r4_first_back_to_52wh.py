"""规则 4：一次修正之后，族群里**最先**回到 52 周新高的那只，之后跑不跑赢同族群其他票？（T-0921-100）

原话（801010athlete）：04-24 为什么选 NBIS 不选 IREN——「NBIS 一上来就创新高，IREN 离历史高点
还差 45% 以上」；03-24「大家都在说 LITE，光通信组的老大是 CIEN」。→ 书稿 §04.5、§04.6。

口径来源（宪法「先找口径」）：
- 「买创新高」有一手出处：O'Neil 1959 年的原始研究（100 多只赢家全部是在创新高时被买入的），
  O'Neil Global Advisors 的量化复核给出 breakout 3 个月 +1.1% alpha / +3.2% 收益。
- **「同族群里谁先回新高」不是标准指标**，是作者自己的排序法。这条自造，已标明。
- 修正识别与 52 周新高口径**照抄** SwingMasterclass `_bench/appJ_correction_leaders.py`：
  SPY 日内 52 周新高之间、High→最低 Low 跌幅 ≥10% 记一次修正；
  52 周新高 = Close ≥ 过去 252 根收盘最大值（不含当日）。
  ✅ appJ 的 corrections_intraday_all 那 11 次与本脚本逐条一致（peak/trough/跌幅全对上）；
     本脚本多出 2007-07-19、2007-10-11 两次（appJ 的 SPY 缓存从 2010 起，我们从 2004 起）。
     13 次里只有 10 次产出事件——个股面板从 2010-01-01 起，52 周回看要到 2011 年初才满。

两种读法，都测：
  - **可交易版（头条）**：从「该组第一只创新高的那一天 D」起算。那天你才看得见这件事。
    比较：那只票 vs 同组其他票的等权组合，往后 21/63/126/252 日。
  - **事后版**：从修正低点起算，按「第几天创新高」排序，第一名 vs 其余。这版有前视，只作描述。

必须做的那道控制（r3 已经栽过同一个坑）：
  最先回新高的那只，很可能只是**跌得最少**的那只；而 appJ 已经测出跌得最少的那批
  **反弹更小**（pooled: A_less reb42 中位 15.6% vs B_more 22.1%）。
  所以这里同时报：① F 在组内跌幅排名的分布；② 把「跌得最少的那只」当成对照选法，
  看两者差多少 —— 如果「先创新高」只是「跌得最少」的影子，两条曲线会叠在一起。

⚠️ 幸存者偏差：1826 只今天还活着的票。**这条规则受偏差影响最大**——当年先回新高、
   后来被并购/退市的票整只缺席，而并购退出通常是高价成交。方向：把「先回新高」这一组读低了。

输出：r4_first_back_to_52wh.json
"""
from __future__ import annotations

import json
import pickle
import statistics
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BENCH = REPO / ".cache" / "fr_bench_panel.pkl"
STOCKS = REPO / ".cache" / "fr_stock_panel.pkl"
OUT = HERE / "r4_first_back_to_52wh.json"

LOOKBACK = 252
H = (21, 63, 126, 252)
MIN_GROUP = 5
NH_SEARCH = 252          # 低点后最多找 252 个交易日


def main():
    bench = pickle.loads(BENCH.read_bytes())
    panel = pickle.loads(STOCKS.read_bytes())
    spy = bench["SPY"]
    idx = spy.Close.index
    tickers = sorted(panel)
    close = pd.DataFrame({t: panel[t].Close for t in tickers}).reindex(idx)
    C = close.to_numpy(float)
    n_days = len(idx)
    spy_c = spy.Close.to_numpy(float)

    prior_max = close.shift(1).rolling(LOOKBACK, min_periods=LOOKBACK).max().to_numpy(float)
    is_nh = (C >= prior_max) & np.isfinite(prior_max)

    gj = json.loads((REPO / "data/output/groups.json").read_text())["stocks"]
    col = {t: k for k, t in enumerate(tickers)}
    groups = defaultdict(list)
    for t, rec in gj.items():
        if t in col:
            groups[rec["group"]].append(col[t])

    # 修正识别（照抄 appJ）
    hi, lo = spy.High.reindex(idx), spy.Low.reindex(idx)
    roll = hi.rolling(LOOKBACK, min_periods=1).max()
    peaks = [k for k, v in enumerate((hi >= roll).to_numpy()) if v]
    corrections = []
    for a, b in zip(peaks, peaks[1:] + [n_days]):
        if b - a < 2:
            continue
        seg = lo.iloc[a:b]
        t = int(np.argmin(seg.to_numpy())) + a
        dd = float(seg.min()) / float(hi.iloc[a]) - 1.0
        if dd <= -0.10:
            corrections.append({"peak_i": a, "trough_i": t, "peak": str(idx[a].date()),
                                "trough": str(idx[t].date()), "dd_pct": round(dd * 100, 2)})

    events = []
    for corr in corrections:
        p, tr = corr["peak_i"], corr["trough_i"]
        for gname, cols in groups.items():
            alive = [c for c in cols
                     if np.isfinite(C[p, c]) and np.isfinite(C[tr, c])
                     and np.isfinite(prior_max[tr, c])]
            if len(alive) < MIN_GROUP:
                continue
            # 每只票：低点后第几天创 52 周新高
            nh_day, nh_col = {}, {}
            for c in alive:
                hit = None
                end = min(tr + 1 + NH_SEARCH, n_days)
                for k in range(tr + 1, end):
                    if is_nh[k, c]:
                        hit = k
                        break
                if hit is not None:
                    nh_day[c] = hit - tr
                    nh_col[c] = hit
            if not nh_day:
                continue
            first_k = min(nh_day, key=lambda c: nh_day[c])
            D = nh_col[first_k]                       # 可观测的那一天
            if D + H[0] >= n_days:
                continue
            others = [c for c in alive if c != first_k and np.isfinite(C[D, c])]
            if len(others) < MIN_GROUP - 1:
                continue
            dds = {c: C[tr, c] / C[p, c] - 1.0 for c in alive}
            dd_rank = sorted(alive, key=lambda c: -dds[c])   # 跌得最少的排第一
            least_dd = dd_rank[0]
            ev = {"group": gname, "correction_trough": corr["trough"],
                  "signal_date": str(idx[D].date()),
                  "first_ticker": tickers[first_k],
                  "n_group": len(alive),
                  "nh_days_from_trough": nh_day[first_k],
                  "first_dd_rank_pct": round(100 * (dd_rank.index(first_k) + 1) / len(alive), 1),
                  "first_is_least_dd": bool(first_k == least_dd)}
            for h in H:
                j = D + h
                if j >= n_days:
                    ev[f"exc{h}_vs_group"] = None
                    ev[f"exc{h}_vs_spy"] = None
                    ev[f"leastdd_exc{h}_vs_group"] = None
                    continue
                r_f = C[j, first_k] / C[D, first_k] - 1.0
                peer = [C[j, c] / C[D, c] - 1.0 for c in others
                        if np.isfinite(C[j, c]) and np.isfinite(C[D, c])]
                ev[f"exc{h}_vs_group"] = (round(float(r_f - np.mean(peer)), 4)
                                          if peer and np.isfinite(r_f) else None)
                ev[f"exc{h}_vs_spy"] = (round(float(r_f - (spy_c[j] / spy_c[D] - 1.0)), 4)
                                        if np.isfinite(r_f) else None)
                if least_dd != first_k and np.isfinite(C[j, least_dd]) and np.isfinite(C[D, least_dd]):
                    r_l = C[j, least_dd] / C[D, least_dd] - 1.0
                    peer_l = [C[j, c] / C[D, c] - 1.0 for c in alive
                              if c != least_dd and np.isfinite(C[j, c]) and np.isfinite(C[D, c])]
                    ev[f"leastdd_exc{h}_vs_group"] = (round(float(r_l - np.mean(peer_l)), 4)
                                                      if peer_l else None)
                else:
                    ev[f"leastdd_exc{h}_vs_group"] = ev[f"exc{h}_vs_group"]
            events.append(ev)

    def agg(key):
        v = [e[key] for e in events if e.get(key) is not None]
        if not v:
            return None
        return {"n": len(v),
                "median_pct": round(100 * float(np.median(v)), 2),
                "mean_pct": round(100 * float(np.mean(v)), 2),
                "win_rate_pct": round(100 * float(np.mean(np.array(v) > 0)), 1)}

    # 按修正分，看结论是不是被某一次修正扛着
    by_corr = {}
    for corr in corrections:
        sub = [e for e in events if e["correction_trough"] == corr["trough"]]
        v = [e["exc63_vs_group"] for e in sub if e.get("exc63_vs_group") is not None]
        if v:
            by_corr[corr["trough"]] = {"n_groups": len(v),
                                       "median_exc63_vs_group_pct": round(100 * float(np.median(v)), 2),
                                       "win_rate_pct": round(100 * float(np.mean(np.array(v) > 0)), 1)}

    result = {"meta": {
        "generated": "2026-09-21",
        "claim": "同一族群一次修正后，最先回到 52 周新高的那只，之后跑赢同族群其他票"
                 "（801010athlete，X 2026-03/04）",
        "standard_checked": "O'Neil 新高研究 + O'Neil Global Advisors 量化复核（breakout 3M "
                            "+1.1% alpha）是「买新高」的一手出处；"
                            "「组内谁先回新高」查无标准，是作者自造的排序法",
        "inherited": "修正识别与 52 周新高口径照抄 SwingMasterclass _bench/appJ_correction_leaders.py；"
                     "appJ 那 11 次与本脚本逐条一致，本脚本多出 2007 年两次（数据起点不同）；"
                     "13 次里 10 次产出事件（个股面板 2010 起，52 周回看 2011 初才满）",
        "tradeable_version": "从「该组第一只创新高的那一天」起算，不用低点起算（低点起算有前视）",
        "universe": f"{len(tickers)} 只，按 groups.json 2026-09-18 的行业分组，组内 ≥{MIN_GROUP} 只",
        "survivorship": "⚠️ 四条规则里这条受偏差最重：当年先回新高、后来被并购/退市的票整只缺席，"
                        "而并购多在高价成交 —— 方向是把「先回新高」这组读低",
    },
        "n_corrections": len(corrections),
        "corrections": corrections,
        "n_events": len(events),
        "first_to_new_high_vs_group": {f"h{h}": agg(f"exc{h}_vs_group") for h in H},
        "first_to_new_high_vs_spy": {f"h{h}": agg(f"exc{h}_vs_spy") for h in H},
        "control_least_drawdown_vs_group": {f"h{h}": agg(f"leastdd_exc{h}_vs_group") for h in H},
        "first_is_least_drawdown_pct": round(
            100 * float(np.mean([e["first_is_least_dd"] for e in events])), 1) if events else None,
        "first_dd_rank_pct_median": round(
            float(np.median([e["first_dd_rank_pct"] for e in events])), 1) if events else None,
        "median_nh_days_from_trough": round(
            float(np.median([e["nh_days_from_trough"] for e in events])), 1) if events else None,
        "by_correction_h63": by_corr,
        "events": events,
    }
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False))

    print(f"修正 {len(corrections)} 次，事件（组×修正）{len(events)} 个")
    print("先回新高那只 vs 同组其余（等权）：")
    for h in H:
        print(f"  h{h:3d}: {result['first_to_new_high_vs_group'][f'h{h}']}")
    print("先回新高那只 vs SPY：")
    for h in H:
        print(f"  h{h:3d}: {result['first_to_new_high_vs_spy'][f'h{h}']}")
    print("对照 —— 改选「组内跌得最少的那只」 vs 同组其余：")
    for h in H:
        print(f"  h{h:3d}: {result['control_least_drawdown_vs_group'][f'h{h}']}")
    print("先回新高的那只就是跌得最少的那只的比例:",
          result["first_is_least_drawdown_pct"], "%")
    print("它在组内跌幅排名的中位分位（1%=跌得最少）:", result["first_dd_rank_pct_median"], "%")
    print("低点后多少个交易日出现组内第一只新高（中位）:", result["median_nh_days_from_trough"])
    print("按修正拆 h63:", json.dumps(by_corr, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
