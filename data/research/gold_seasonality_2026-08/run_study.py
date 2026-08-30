"""「金9银10」季节性检验。预注册见 PREREG.md（commit b8e25a22，跑本脚本之前封存）。

一切数字由本脚本产出并写进 results.json —— 报告散文里不许出现手打的数字
（pitfall_i_misread_my_own_table）。
"""
import json
import numpy as np
import pandas as pd
import yfinance as yf

SEED = 20260831
NPERM = 20000
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _month_is_complete(last_day, month_end):
    """最后一个月走完了吗？

    ⚠️ 别写成 `last_day < month_end`（v1 就是这么写的，是个 bug）：
    `resample("ME")` 的索引是**日历月末**，而行情最后一天是**交易日**。
    2020-05-31 是周日、最后交易日 05-29，那个写法会把**已经走完的 5 月整月丢掉**。
    正确的判据是：last_day 之后到月末之间**还有没有工作日**——有就是还在走。
    （节假日会让这个判据偏保守：把一个只剩假日的完整月当成未走完而丢掉。
    宁可少一个月，也不要把半个月当整月。）
    """
    import pandas as _pd
    remaining = _pd.bdate_range(last_day + _pd.Timedelta(days=1), month_end)
    return len(remaining) == 0


def monthly_returns(ticker, log=False):
    """月末对月末的日历月收益。未收完的当月整月剔除。"""
    px = yf.Ticker(ticker).history(period="max", auto_adjust=True)["Close"].dropna()
    px.index = pd.to_datetime(px.index).tz_localize(None)
    me = px.resample("ME").last()
    if not _month_is_complete(px.index[-1], me.index[-1]):
        me = me.iloc[:-1]
    r = np.log(me / me.shift(1)) if log else me / me.shift(1) - 1
    return r.dropna()


def perm_p(r, month, rng, nperm=NPERM):
    """置换检验：打乱月份标签，看『该月均值 − 其他月均值』的实测值在零分布的位置（双侧）。"""
    labels = r.index.month.values
    vals = r.values
    mask = labels == month
    n_in = int(mask.sum())
    if n_in < 3:
        return np.nan, np.nan, n_in
    obs = vals[mask].mean() - vals[~mask].mean()
    idx = np.arange(len(vals))
    null = np.empty(nperm)
    for i in range(nperm):
        pick = rng.choice(idx, size=n_in, replace=False)
        sel = np.zeros(len(vals), bool)
        sel[pick] = True
        null[i] = vals[sel].mean() - vals[~sel].mean()
    p = (np.sum(np.abs(null) >= abs(obs)) + 1) / (nperm + 1)
    return obs, p, n_in


def holm(pvals):
    """Holm-Bonferroni 校正后的 p（单调化）。"""
    p = np.asarray(pvals, float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * p[i])
        adj[i] = min(1.0, running)
    return adj


def mde(r, month, alpha, power=0.80):
    """在给定 alpha 与该格样本量下，80% 把握能测出的最小月均值差（两样本 t 近似）。"""
    from scipy import stats
    labels = r.index.month.values
    n1 = int((labels == month).sum())
    n2 = int((labels != month).sum())
    if n1 < 3:
        return np.nan
    sd = r.values.std(ddof=1)
    za = stats.norm.ppf(1 - alpha / 2)
    zb = stats.norm.ppf(power)
    return (za + zb) * sd * np.sqrt(1 / n1 + 1 / n2)


def median_cells(series_map, label):
    """变体 5：中位数代替均值。置换检验同法，统计量换成中位数差。"""
    rng = np.random.default_rng(SEED)
    rows = []
    for name, r in series_map.items():
        labels = r.index.month.values
        vals = r.values
        for m in range(1, 13):
            mask = labels == m
            n_in = int(mask.sum())
            obs = np.median(vals[mask]) - np.median(vals[~mask])
            idx = np.arange(len(vals))
            null = np.empty(NPERM)
            for i in range(NPERM):
                pick = rng.choice(idx, size=n_in, replace=False)
                sel = np.zeros(len(vals), bool); sel[pick] = True
                null[i] = np.median(vals[sel]) - np.median(vals[~sel])
            p = (np.sum(np.abs(null) >= abs(obs)) + 1) / (NPERM + 1)
            rows.append({"spec": label, "metal": name, "month": MONTHS[m - 1],
                         "month_num": m, "n": n_in,
                         "mean_diff_pct": round(float(obs) * 100, 4),
                         "p_raw": round(float(p), 5)})
    adj = holm([x["p_raw"] for x in rows])
    for x, a in zip(rows, adj):
        x["p_holm"] = round(float(a), 5)
    return rows


def window21_returns(ticker):
    """变体 6：21 个交易日的窗口代替日历月。

    每个自然月取该月**第一个交易日**起的 21 根 K 线，收益 = 末/首 − 1。
    回答的是「日历月的切法有没有把效应切碎」。
    """
    px = yf.Ticker(ticker).history(period="max", auto_adjust=True)["Close"].dropna()
    px.index = pd.to_datetime(px.index).tz_localize(None)
    firsts = px.groupby([px.index.year, px.index.month]).apply(lambda s: s.index[0])
    vals, idx = [], []
    pos = {d: i for i, d in enumerate(px.index)}
    for d in firsts:
        i = pos[d]
        if i + 21 >= len(px):
            continue
        vals.append(px.iloc[i + 21] / px.iloc[i] - 1)
        idx.append(d)
    return pd.Series(vals, index=pd.DatetimeIndex(idx))


def cells(series_map, label):
    rng = np.random.default_rng(SEED)
    rows = []
    for name, r in series_map.items():
        for m in range(1, 13):
            obs, p, n = perm_p(r, m, rng)
            rows.append({"spec": label, "metal": name, "month": MONTHS[m - 1],
                         "month_num": m, "n": n,
                         "mean_diff_pct": None if np.isnan(obs) else round(obs * 100, 4),
                         "p_raw": None if np.isnan(p) else round(float(p), 5)})
    ps = [x["p_raw"] for x in rows]
    ok = [i for i, v in enumerate(ps) if v is not None]
    adj = holm([ps[i] for i in ok])
    for k, i in enumerate(ok):
        rows[i]["p_holm"] = round(float(adj[k]), 5)
    return rows


def main():
    out = {"seed": SEED, "nperm": NPERM, "specs": {}}

    # ---- 主口径：连续期货，简单收益，全样本 ----
    fut = {"gold": monthly_returns("GC=F"), "silver": monthly_returns("SI=F")}
    out["coverage"] = {k: {"n_months": int(len(v)),
                           "first": str(v.index[0].date()), "last": str(v.index[-1].date())}
                       for k, v in fut.items()}
    out["specs"]["main_full"] = cells(fut, "main_full")

    # ---- 分辨率地板：Holm 下最严的有效 alpha = 0.05/24 ----
    alpha_holm = 0.05 / 24
    out["mde"] = {}
    for name, r in fut.items():
        for m, lbl in [(9, "Sep"), (10, "Oct")]:
            out["mde"][f"{name}_{lbl}"] = {
                "n": int((r.index.month == m).sum()),
                "sd_monthly_pct": round(float(r.values.std(ddof=1) * 100), 3),
                "mde_pct_at_alpha_holm": round(float(mde(r, m, alpha_holm)) * 100, 3),
                "mde_pct_at_alpha_005": round(float(mde(r, m, 0.05)) * 100, 3),
            }

    # ---- 时间切分（稳定性，不是 holdout）----
    for tag, lo, hi in [("train_2000_2015", "2000-01-01", "2015-12-31"),
                        ("holdout_2016_2026", "2016-01-01", "2026-12-31")]:
        sub = {k: v[(v.index >= lo) & (v.index <= hi)] for k, v in fut.items()}
        out["specs"][tag] = cells(sub, tag)

    # ---- 稳健性变体 ----
    out["specs"]["log_returns"] = cells(
        {"gold": monthly_returns("GC=F", log=True),
         "silver": monthly_returns("SI=F", log=True)}, "log_returns")
    out["specs"]["etf_proxy"] = cells(
        {"gold": monthly_returns("GLD"), "silver": monthly_returns("SLV")}, "etf_proxy")
    ex11 = {k: v[v.index.year != 2011] for k, v in fut.items()}
    out["specs"]["ex_2011"] = cells(ex11, "ex_2011")

    # ---- 变体 5、6（预注册里预算了，v1 漏跑，反驳视角的核对员点出后补）----
    out["specs"]["median"] = median_cells(fut, "median")
    out["specs"]["window21"] = cells(
        {"gold": window21_returns("GC=F"), "silver": window21_returns("SI=F")}, "window21")

    # ---- 对照组：理应无效的说法（铜 3 月 / 玉米 7 月），同框同法 ----
    ctrl = {"copper": monthly_returns("HG=F"), "corn": monthly_returns("ZC=F")}
    out["control_coverage"] = {k: int(len(v)) for k, v in ctrl.items()}
    out["specs"]["control"] = cells(ctrl, "control")

    # ---- 牛熊分层（黄金 2000-2011 牛 / 2012-2015 熊 / 2016- 后段）----
    out["specs"]["regime"] = []
    for tag, lo, hi in [("bull_2000_2011", "2000-01-01", "2011-12-31"),
                        ("bear_2012_2015", "2012-01-01", "2015-12-31")]:
        sub = {k: v[(v.index >= lo) & (v.index <= hi)] for k, v in fut.items()}
        out["specs"]["regime"] += [r for r in cells(sub, tag) if r["month"] in ("Sep", "Oct")]

    # ---- 12 个月的完整梯度（主口径，均值排序）----
    out["gradient"] = {}
    for name, r in fut.items():
        g = [(MONTHS[m - 1], round(float(r[r.index.month == m].mean() * 100), 3),
              int((r.index.month == m).sum())) for m in range(1, 13)]
        out["gradient"][name] = sorted(g, key=lambda x: -x[1])

    json.dump(out, open("results.json", "w"), indent=2)
    print("wrote results.json")


if __name__ == "__main__":
    main()
