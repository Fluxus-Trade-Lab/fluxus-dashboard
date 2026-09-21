"""规则 3：「难买的日子」体检 —— 指数收红那天守住前一天低点的票，之后是不是更强？（T-0921-100）

原话（801010athlete）：03-25「最近最好的几笔都是在很难下手的日子买的——指数难看、个股价格却突出」；
04-29「前一天几乎所有票都破了周一低点，只有 SGML、FSLY、BB 守住，三只当天全部开新仓」；
05-15「NBIS、DOCN、TWLO 都守住了前一天低点，这不是巧合，它们就是这轮的龙头」。→ 书稿 §04.3。

口径来源（宪法「先找口径」）：
**这条有公开口径，不用自造。** TraderLion / Deepvue 把它叫 **RS Day**：
「市场创新低而这只票没跌破自己的前低，就是 RS」（TraderLion, Relative Strength Essentials;
Deepvue "Find Strong Stocks On Down Days"）。Deepvue 还给了一个可检验的说法：
**在修正期间 RS Day 占比 >60% 的票是潜在龙头。** 本脚本照这个口径测，并补测那个 60% 的说法。
自造的只有两处，已标明：①「难买」的分档阈值（全部收红日 / 跌 ≥1% / 指数自己跌破前一日低点）；
②控制变量用的 63 日相对强弱分位（用来回答「除了『它本来就强』还剩什么」）。

两个版本都测：
  A. 守住**前一天**低点：Low_t ≥ Low_{t-1}
  B. 守住**本周一**低点：Low_t ≥ 本自然周第一个交易日的 Low

被测的两件事（都对照当天**没守住**的票）：
  - 之后 21 / 63 个交易日的收益减 SPY 同期（超额）
  - 之后 63 个交易日内是否创 52 周**收盘**新高（Close ≥ 过去 252 根收盘最大值，不含当日；
    与 SwingMasterclass appJ 同口径）

⚠️ 幸存者偏差：名单是今天还活着的 1826 只。守住组和没守住组用的是同一份名单，
   但当年守住、后来退市的票两组都缺 —— 缺的那批更可能是输家，所以**两组都被读高了**，
   差值受影响小于水平值。水平值不要单独引用。

输出：r3_hard_days.json
"""
from __future__ import annotations

import json
import pickle
import statistics
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BENCH = REPO / ".cache" / "fr_bench_panel.pkl"
STOCKS = REPO / ".cache" / "fr_stock_panel.pkl"
OUT = HERE / "r3_hard_days.json"

H = (21, 63)
NH_WINDOW = 63       # 「先创 52 周新高」的观察窗
LOOKBACK_52W = 252
MIN_HIST = 260       # 当天之前至少这么多根，52 周口径才成立


def build():
    bench = pickle.loads(BENCH.read_bytes())
    panel = pickle.loads(STOCKS.read_bytes())
    spy = bench["SPY"].Close
    ixic = bench["^IXIC"].Close
    idx = spy.index
    tickers = sorted(panel)
    close = pd.DataFrame({t: panel[t].Close for t in tickers}).reindex(idx)
    low = pd.DataFrame({t: panel[t].Low for t in tickers}).reindex(idx)
    return idx, tickers, close, low, spy, ixic.reindex(idx)


def monday_low(low: pd.DataFrame, idx: pd.DatetimeIndex) -> pd.DataFrame:
    """本自然周第一个交易日的 Low，前向填充到本周每一天。"""
    week = pd.Series(idx, index=idx).dt.isocalendar()
    key = week.year.astype(str) + "-" + week.week.astype(str)
    first = ~key.duplicated()
    wk_low = low.where(pd.Series(first, index=idx), other=np.nan)
    return wk_low.ffill()


def main():
    idx, tickers, close, low, spy, ixic = build()
    C = close.to_numpy(float)
    L = low.to_numpy(float)
    n_days, n_t = C.shape

    # 52 周收盘新高矩阵（不含当日）
    prior_max = close.shift(1).rolling(LOOKBACK_52W, min_periods=LOOKBACK_52W).max().to_numpy(float)
    is_nh = C >= prior_max

    # 远期超额
    spy_a = spy.to_numpy(float)
    fwd = {}
    for h in H:
        f = np.full_like(C, np.nan)
        f[:-h] = C[h:] / C[:-h] - 1.0
        s = np.full(n_days, np.nan)
        s[:-h] = spy_a[h:] / spy_a[:-h] - 1.0
        fwd[h] = f - s[:, None]

    # 63 日内是否创 52 周新高
    nh_soon = np.full(C.shape, np.nan)
    nh_ok = np.isfinite(prior_max)
    for i in range(n_days - NH_WINDOW):
        w = is_nh[i + 1:i + 1 + NH_WINDOW] & nh_ok[i + 1:i + 1 + NH_WINDOW]
        nh_soon[i] = w.any(axis=0).astype(float)
    nh_soon[~np.isfinite(prior_max)] = np.nan

    # 控制变量：63 日相对强弱（个股 63 日收益 − SPY 63 日收益）当日横截面分位
    rs = np.full_like(C, np.nan)
    rs[63:] = C[63:] / C[:-63] - 1.0
    srs = np.full(n_days, np.nan)
    srs[63:] = spy_a[63:] / spy_a[:-63] - 1.0
    rs = rs - srs[:, None]
    rs_q = pd.DataFrame(rs, index=idx).rank(axis=1, pct=True).to_numpy(float)

    hist_ok = np.isfinite(prior_max)          # 有 252 根历史

    held_A = np.full(C.shape, np.nan)
    held_A[1:] = (L[1:] >= L[:-1]).astype(float)
    held_A[~np.isfinite(L)] = np.nan
    held_A[1:][~np.isfinite(L[:-1])] = np.nan

    ml = monday_low(low, idx).to_numpy(float)
    held_B = (L >= ml).astype(float)
    held_B[~np.isfinite(L) | ~np.isfinite(ml)] = np.nan

    ix = ixic.to_numpy(float)
    ix_ret = np.full(n_days, np.nan)
    ix_ret[1:] = ix[1:] / ix[:-1] - 1.0
    ix_low_break = np.full(n_days, False)     # 指数自己跌破前一日低点
    ixl = bench_low()
    ix_low_break[1:] = ixl[1:] < ixl[:-1]

    day_sets = {
        "red_any": ix_ret < 0,
        "red_1pct": ix_ret <= -0.01,
        "red_and_index_broke_prior_low": (ix_ret < 0) & ix_low_break,
    }

    result = {"meta": {
        "generated": "2026-09-21",
        "claim": "指数收红那天守住前一天低点（或本周一低点）的票，之后 1/3 个月更可能跑赢、"
                 "先创 52 周新高（801010athlete，X 2026-03/04/05）",
        "standard_checked": "有公开口径：TraderLion / Deepvue 的 RS Day —— "
                            "「市场创新低而这只票没跌破自己前低」。照抄，未自造定义。"
                            "Deepvue 另给「修正期 RS Day 占比 >60% 是潜在龙头」，一并测",
        "self_made": ["「难买」的三档阈值（收红 / 跌≥1% / 指数自己跌破前一日低点）",
                      "控制变量：63 日超额收益的当日横截面分位"],
        "universe": f"{len(tickers)} 只（今天 universe.json 里 close×avg_volume≥$20M "
                    f"且 market_cap≥$2B 且 groups.json 有行业），日线 2010-01-01 起",
        "survivorship": "今天还活着的名单；守住组与没守住组同源，水平值两边都偏高，"
                        "差值受影响较小。水平值不要单独引用",
        "nasdaq": "^IXIC（纳斯达克综合指数），不是 QQQ",
    }, "tests": {}}

    for dname, dmask in day_sets.items():
        for vname, held in (("A_prior_day_low", held_A), ("B_monday_low", held_B)):
            rows = np.where(dmask & (np.arange(n_days) > LOOKBACK_52W))[0]
            cell = {"n_days": int(len(rows))}
            for h in H:
                hv, bv = [], []
                for i in rows:
                    ok = np.isfinite(held[i]) & np.isfinite(fwd[h][i]) & hist_ok[i]
                    hv.extend(fwd[h][i][ok & (held[i] == 1)])
                    bv.extend(fwd[h][i][ok & (held[i] == 0)])
                cell[f"h{h}"] = pack(hv, bv)
            hv, bv = [], []
            for i in rows:
                ok = np.isfinite(held[i]) & np.isfinite(nh_soon[i]) & hist_ok[i]
                hv.extend(nh_soon[i][ok & (held[i] == 1)])
                bv.extend(nh_soon[i][ok & (held[i] == 0)])
            cell["new_52w_high_within_63d"] = {
                "held_pct": round(100 * float(np.mean(hv)), 1) if hv else None,
                "broke_pct": round(100 * float(np.mean(bv)), 1) if bv else None,
                "n_held": len(hv), "n_broke": len(bv),
                "gap_pp": round(100 * (float(np.mean(hv)) - float(np.mean(bv))), 1)
                if hv and bv else None,
            }
            # 控制「它本来就强」：只在 RS 最高的五分之一里比
            hv, bv = [], []
            for i in rows:
                strong = rs_q[i] >= 0.8
                ok = np.isfinite(held[i]) & np.isfinite(fwd[63][i]) & hist_ok[i] & strong
                hv.extend(fwd[63][i][ok & (held[i] == 1)])
                bv.extend(fwd[63][i][ok & (held[i] == 0)])
            cell["h63_within_top_RS_quintile"] = pack(hv, bv)
            result["tests"][f"{dname}__{vname}"] = cell

    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    for k, v in result["tests"].items():
        print(f"== {k} (days={v['n_days']}) ==")
        print("   h21 :", v["h21"])
        print("   h63 :", v["h63"])
        print("   52wh:", v["new_52w_high_within_63d"])
        print("   h63 只在 RS 前 20%:", v["h63_within_top_RS_quintile"])


def pack(held, broke):
    def s(v):
        return {"n": len(v),
                "median_excess_pct": round(100 * float(np.median(v)), 2) if v else None,
                "mean_excess_pct": round(100 * float(np.mean(v)), 2) if v else None,
                "win_rate_pct": round(100 * float(np.mean(np.array(v) > 0)), 1) if v else None}
    out = {"held": s(held), "broke": s(broke)}
    if held and broke:
        out["gap_median_pp"] = round(100 * (float(np.median(held)) - float(np.median(broke))), 2)
        out["gap_mean_pp"] = round(100 * (float(np.mean(held)) - float(np.mean(broke))), 2)
    return out


def bench_low():
    bench = pickle.loads(BENCH.read_bytes())
    spy_idx = bench["SPY"].Close.index
    return bench["^IXIC"].Low.reindex(spy_idx).to_numpy(float)


if __name__ == "__main__":
    main()
