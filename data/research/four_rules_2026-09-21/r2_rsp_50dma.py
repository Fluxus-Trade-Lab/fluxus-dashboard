"""规则 2：RSP 跌破 50 日线，领涨族群是不是就失去趋势了？（T-0921-100）

原话（Shake Pryzby，X 2026-09-15）：「RSP 跌破 50 日线＝那些撑住大盘的轮动型名字的趋势改变。」
→ 书稿「轮动」一节第 6 点、§04.8、§07.4（目前标待测）。

口径来源（宪法「先找口径」）：
- **RSP/SPY 比值**是有公开出处的广度量（CXO Advisory 做过检验；optionstradingiq 同口径）。
  **「RSP 相对它自己的 50 日线」不是标准指标**——标准的广度量是「%above-50MA」。
  所以这条规则是作者自造的，我们照他的原话测，同时把有出处的 RSP/SPY 比值作对照一起报。
- 「领涨族群」用**我们自己的四态**（`pipeline/themes/rs_engine.py:181` classify），逐字照抄公式，
  不另造：excess_3m = perf_3m(组) − perf_3m(SPY)；
  rs_accel = (perf_1m(组) − perf_1m(SPY)) − rs_1m_3m（1m..3m 的不相交桶超额）；
  Leading = excess_3m > 0 且 rs_accel > 0。
  ⚠️ 自造的一处：生产线的 perf_* 来自 Finviz 的**日历**口径，这里用**交易日** 5/21/63/126 近似。

两套互不依赖的「族群」代理（两套都指同一个方向才算数）：
  A. 39 个板块/行业 ETF（真实可交易的组）。
  B. 用 1826 只个股按 groups.json 的行业标签搭的**等权行业指数**（≥8 只成员的行业，
     与 Finviz 组均值同为等权）。⚠️ 行业标签是**今天**这一份，历史上不重构。

为什么不直接用 groups_archive.csv：它只从 2026-08-07 起，6 周，连一个 63 日远期窗口都放不下。
本脚本末尾仍拿它做一次同期对照（21 日窗，样本极小，只当方向核对，不当证据）。

输出：r2_rsp_50dma.json
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
OUT = HERE / "r2_rsp_50dma.json"

W = {"perf_1w": 5, "perf_1m": 21, "perf_3m": 63, "perf_6m": 126}
HORIZONS = (21, 63)
MIN_MEMBERS = 8


def cum(close: pd.Series, n: int) -> pd.Series:
    return close / close.shift(n) - 1.0


def four_state(g_close: pd.Series, spy_close: pd.Series) -> pd.DataFrame:
    """照抄 rs_engine 的 excess_3m / acceleration / classify，只换了窗口为交易日。"""
    idx = g_close.index
    spy = spy_close.reindex(idx)
    gp = {k: cum(g_close, n) for k, n in W.items()}
    sp = {k: cum(spy, n) for k, n in W.items()}

    def disjoint(p, far, near):
        # (1+cum_far)/(1+cum_near) - 1
        return (1.0 + p[far]) / (1.0 + p[near]) - 1.0

    g_1m_3m = disjoint(gp, "perf_3m", "perf_1m")
    s_1m_3m = disjoint(sp, "perf_3m", "perf_1m")
    excess_3m = gp["perf_3m"] - sp["perf_3m"]
    rs_near = gp["perf_1m"] - sp["perf_1m"]
    rs_accel = rs_near - (g_1m_3m - s_1m_3m)
    state = pd.Series(index=idx, dtype=object)
    lead = (excess_3m > 0) & (rs_accel > 0)
    weak = (excess_3m > 0) & ~(rs_accel > 0)
    imp = (excess_3m <= 0) & (rs_accel > 0)
    state[lead] = "Leading"
    state[weak] = "Weakening"
    state[imp] = "Improving"
    state[(excess_3m <= 0) & ~(rs_accel > 0)] = "Lagging"
    state[excess_3m.isna() | rs_accel.isna()] = None
    return pd.DataFrame({"state": state, "excess_3m": excess_3m, "rs_accel": rs_accel})


def equal_weight_industry(stock_panel, industries, spy_index):
    """等权行业指数：成员日收益的等权平均，再累乘成净值。"""
    out = {}
    for group, tickers in industries.items():
        cols = {}
        for t in tickers:
            df = stock_panel.get(t)
            if df is None:
                continue
            cols[t] = df.Close.reindex(spy_index).pct_change()
        if len(cols) < MIN_MEMBERS:
            continue
        mat = pd.DataFrame(cols)
        # 至少 MIN_MEMBERS 只有数的日子才算，避免早年只剩两三只时的噪声
        valid = mat.notna().sum(axis=1) >= MIN_MEMBERS
        ret = mat.mean(axis=1).where(valid)
        nav = (1.0 + ret.fillna(0.0)).cumprod().where(valid.cummax())
        out[group] = nav
    return out


def collect(states: dict, spy: pd.Series, rsp_below: pd.Series, label: str):
    """按 RSP 在 50 日线哪一侧，分箱收集 Leading 组的远期**超额**收益。"""
    buckets = {h: defaultdict(list) for h in HORIZONS}
    counts = defaultdict(int)
    for group, (st, nav) in states.items():
        s = st["state"]
        for h in HORIZONS:
            fwd_g = nav.shift(-h) / nav - 1.0
            fwd_s = spy.shift(-h) / spy - 1.0
            exc = (fwd_g - fwd_s)
            mask = (s == "Leading") & exc.notna() & rsp_below.notna()
            for date, v in exc[mask].items():
                side = "below50" if bool(rsp_below.loc[date]) else "above50"
                buckets[h][side].append(float(v))
                if h == HORIZONS[0]:
                    counts[side] += 1
    res = {"label": label, "n_groups": len(states), "leading_days": dict(counts)}
    for h in HORIZONS:
        for side in ("above50", "below50"):
            v = buckets[h][side]
            res[f"h{h}_{side}"] = {
                "n": len(v),
                "median_excess_pct": round(100 * statistics.median(v), 2) if v else None,
                "mean_excess_pct": round(100 * float(np.mean(v)), 2) if v else None,
                "win_rate_pct": round(100 * sum(1 for x in v if x > 0) / len(v), 1) if v else None,
            }
        a, b = buckets[h]["above50"], buckets[h]["below50"]
        if a and b:
            res[f"h{h}_gap_median_pp"] = round(
                100 * (statistics.median(b) - statistics.median(a)), 2)
    return res


def main():
    bench = pickle.loads(BENCH.read_bytes())
    spy = bench["SPY"].Close
    rsp = bench["RSP"].Close
    rsp50 = rsp.rolling(50).mean()
    rsp_below = (rsp < rsp50).where(rsp50.notna())

    meta = {
        "generated": "2026-09-21",
        "claim": "RSP 跌破 50 日线＝轮动型名字的趋势改变（Shake Pryzby X 2026-09-15）",
        "standard_checked": "RSP/SPY 比值是有出处的广度量（CXO Advisory）；"
                            "「RSP 对自己的 50 日线」查无标准，是作者自造，照原话测",
        "leading_definition": "pipeline/themes/rs_engine.py:181 classify 逐字照抄；"
                              "perf_* 窗口由 Finviz 日历口径近似为交易日 5/21/63/126（自造近似）",
        "survivorship": "代理 B 的成员是今天还活着的 1826 只；行业标签取 2026-09-18 一份，"
                        "历史不重构。两侧（RSP 线上/线下）用同一套名单，偏差方向相同，"
                        "但线下那一侧更可能少掉后来退市的输家 —— 若有偏，是把线下读得偏好。",
    }

    # ── 代理 A：板块/行业 ETF ───────────────────────────────
    etf_states = {}
    for s, df in bench.items():
        if s in {"SPY", "QQQ", "RSP", "IWM", "^IXIC"}:
            continue
        nav = df.Close.reindex(spy.index).dropna()
        if len(nav) < 400:
            continue
        etf_states[s] = (four_state(nav, spy), nav)
    a = collect(etf_states, spy, rsp_below.reindex(spy.index), "A_sector_industry_etfs")

    # ── 代理 B：等权行业指数 ─────────────────────────────────
    stock_panel = pickle.loads(STOCKS.read_bytes())
    groups_json = json.loads((REPO / "data/output/groups.json").read_text())["stocks"]
    industries = defaultdict(list)
    for t, rec in groups_json.items():
        if t in stock_panel:
            industries[rec["group"]].append(t)
    navs = equal_weight_industry(stock_panel, industries, spy.index)
    ew_states = {g: (four_state(nav.dropna(), spy), nav.dropna()) for g, nav in navs.items()}
    b = collect(ew_states, spy, rsp_below.reindex(spy.index), "B_equal_weight_industries")

    # ── 对照：RSP/SPY 比值在自己 50 日线哪一侧（有出处的那个量）──
    ratio = (rsp / spy.reindex(rsp.index))
    ratio_below = (ratio < ratio.rolling(50).mean()).where(ratio.rolling(50).mean().notna())
    c = collect(ew_states, spy, ratio_below.reindex(spy.index), "C_ratio_RSP_over_SPY_50dma")

    # ── 同期对照：真 groups_archive（6 周，只核方向）────────────
    arch_note = {}
    try:
        arch = pd.read_csv(REPO / "data/history/groups_archive.csv")
        arch = arch[arch["kind"] == "industry"]
        lead_days = arch[arch["state"] == "Leading"]
        arch_note = {
            "window": f"{arch['date'].min()} .. {arch['date'].max()}",
            "n_rows": int(len(arch)),
            "n_leading_rows": int(len(lead_days)),
            "usable_for_63d_forward": False,
            "note": "只有 6 周，放不下 63 日远期窗口；不作证据，只记它存在",
        }
    except Exception as exc:  # pragma: no cover
        arch_note = {"error": str(exc)}

    result = {"meta": meta, "proxy_A": a, "proxy_B": b, "control_ratio": c,
              "groups_archive": arch_note,
              "rsp_below_50_share_pct": round(
                  100 * float(rsp_below.mean()), 1)}
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    for k in ("proxy_A", "proxy_B", "control_ratio"):
        r = result[k]
        print(f"== {r['label']} (groups={r['n_groups']}) ==")
        for h in HORIZONS:
            print(f"  h{h} above50: {r[f'h{h}_above50']}")
            print(f"  h{h} below50: {r[f'h{h}_below50']}")
            print(f"  h{h} gap(below-above) median pp: {r.get(f'h{h}_gap_median_pp')}")
    print("RSP 在 50 日线下方的交易日占比:", result["rsp_below_50_share_pct"], "%")


if __name__ == "__main__":
    main()


# ── 追加：把两个信号拆开，并用不重叠样本重数一遍 ───────────────────
# 为什么要这一节：上面每一行都是「某组某天」的 63 日远期，相邻 63 天的窗口几乎完全重叠，
# n=4 万是**假的**样本量。真实独立样本 ≈ 覆盖年数 × 4（63 日窗一年约 4 个）。
# 所以这里(a) 每 63 个交易日只取一天，(b) 把「RSP 对自己 50 日线」和
# 「RSP/SPY 比值对自己 50 日线」摆成 2×2，看信号到底长在哪一维上。

def decompose():
    import itertools
    bench = pickle.loads(BENCH.read_bytes())
    spy = bench["SPY"].Close
    rsp = bench["RSP"].Close
    stock_panel = pickle.loads(STOCKS.read_bytes())
    groups_json = json.loads((REPO / "data/output/groups.json").read_text())["stocks"]
    industries = defaultdict(list)
    for t, rec in groups_json.items():
        if t in stock_panel:
            industries[rec["group"]].append(t)
    navs = equal_weight_industry(stock_panel, industries, spy.index)

    rsp_below = (rsp < rsp.rolling(50).mean()).reindex(spy.index)
    ratio = rsp / spy.reindex(rsp.index)
    ratio_below = (ratio < ratio.rolling(50).mean()).reindex(spy.index)

    h = 63
    cells = defaultdict(list)
    step_cells = defaultdict(list)
    fwd_s = spy.shift(-h) / spy - 1.0
    dates = list(spy.index)
    keep = set(dates[::h])          # 不重叠取样：每 63 个交易日一次
    for group, nav in navs.items():
        nav = nav.dropna()
        st = four_state(nav, spy)["state"]
        fwd_g = nav.shift(-h) / nav - 1.0
        exc = fwd_g - fwd_s.reindex(nav.index)
        for date, v in exc.items():
            if not np.isfinite(v) or st.get(date) != "Leading":
                continue
            rb, cb = rsp_below.get(date), ratio_below.get(date)
            if rb is None or cb is None or pd.isna(rb) or pd.isna(cb):
                continue
            key = f"rsp{'<' if rb else '>'}50 / ratio{'<' if cb else '>'}50"
            cells[key].append(float(v))
            if date in keep:
                step_cells[key].append(float(v))

    def stat(v):
        return {"n": len(v),
                "median_excess_pct": round(100 * statistics.median(v), 2) if v else None,
                "mean_excess_pct": round(100 * float(np.mean(v)), 2) if v else None}

    out = {
        "horizon_sessions": h,
        "note": "每格是 Leading 组的 63 日远期超额（减 SPY）。overlapping 是每天一行（n 虚高），"
                "non_overlapping 是每 63 个交易日取一天（真独立样本）。",
        "overlapping": {k: stat(v) for k, v in sorted(cells.items())},
        "non_overlapping": {k: stat(v) for k, v in sorted(step_cells.items())},
    }
    res = json.loads(OUT.read_text())
    res["decomposition_2x2"] = out
    OUT.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print("\n== 2x2 分解（Leading 组 63 日远期超额，%）==")
    for k in sorted(cells):
        print(f"  {k:26s} overlap {stat(cells[k])}  | indep {stat(step_cells[k])}")


if __name__ == "__main__":
    decompose()
