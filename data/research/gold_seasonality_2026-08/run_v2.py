"""修正版分析（v2）。v1 = run_study.py / run_reading_b.py，保留不动当审计留痕。

三个独立视角的核对员（统计 / 代码 / 反驳）各自打穿了 v1 的两条结论，v2 逐条修：

① **统计量换成预注册写的那个。** PREREG §2 写「t 统计的置换检验」，v1 置换的是
   未 studentize 的均值差。组间方差不等时它反保守——而股指的 9/10 月正是高波动月。
② **零分布换成循环平移。** 月收益不可交换（|ret| 的自相关 lag1–3 在 +0.24~+0.30），
   iid 置换的零分布因此偏窄，方向是让 p 偏小。循环平移旋转收益序列、固定日历掩码，
   保留自相关与波动聚集。n 次旋转是**穷举**，没有 MC 噪声。
③ **对照组的分辨率论证作废，改用注射实验。** v1 拿「玉米 12 月在 Holm 后存活」证明
   检验有分辨率——错的：那是 Yahoo 连续合约在 12/13–16 换月的跳空伪影（该窗口贡献
   了 12 月均值的 4 成），剔掉换月窗后 Holm 从 0.038 变 0.62。**用一个数据构造伪影
   当阳性对照，等于没有阳性对照。** 改成往真实序列里注射已知效应，直接量地板。

⚠️ 口径也是一个未注册的选择：v1 只用月末价。同一段年份换月均价，黄金 9 月符号翻正。
   v2 两个口径并排报，谁也不当主。
"""
import json
import numpy as np
import pandas as pd
from run_study import monthly_returns, holm, MONTHS

SEED = 20260831
NPERM = 20000


def _stat(vals, mask, studentize):
    a, b = vals[mask], vals[~mask]
    d = a.mean() - b.mean()
    if not studentize:
        return d
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return d / se if se > 0 else 0.0


def perm_test(r, month, rng, studentize=True, nperm=NPERM):
    """iid 置换零分布（打乱月份标签）。"""
    labels, vals = r.index.month.values, r.values
    mask = labels == month
    n_in = int(mask.sum())
    obs = _stat(vals, mask, studentize)
    idx = np.arange(len(vals))
    null = np.empty(nperm)
    for i in range(nperm):
        sel = np.zeros(len(vals), bool)
        sel[rng.choice(idx, size=n_in, replace=False)] = True
        null[i] = _stat(vals, sel, studentize)
    return obs, (np.sum(np.abs(null) >= abs(obs)) + 1) / (nperm + 1)


def cyclic_test(r, month, studentize=True):
    """循环平移零分布：日历掩码不动，把收益序列整体旋转。

    穷举全部 n−1 个非平凡旋转 —— 没有随机源，逐位可复现，也没有 MC 噪声。
    它保留自相关与波动聚集，所以零分布比 iid 置换宽（v1 因此把 p 报小了）。
    """
    labels, vals = r.index.month.values, r.values
    mask = labels == month
    obs = _stat(vals, mask, studentize)
    n = len(vals)
    null = np.array([_stat(np.roll(vals, k), mask, studentize) for k in range(1, n)])
    return obs, (np.sum(np.abs(null) >= abs(obs)) + 1) / (n - 1 + 1)


def family(series_map, tag, rng, studentize=True):
    rows = []
    for name, r in series_map.items():
        for m in range(1, 13):
            mask = r.index.month == m
            diff = float(r.values[mask].mean() - r.values[~mask].mean())
            _, p_perm = perm_test(r, m, rng, studentize)
            _, p_cyc = cyclic_test(r, m, studentize)
            rows.append({"spec": tag, "metal": name, "month": MONTHS[m - 1], "n": int(mask.sum()),
                         "mean_diff_pct": round(diff * 100, 4),
                         "p_perm_t": round(float(p_perm), 5),
                         "p_cyclic_t": round(float(p_cyc), 5)})
    for key in ("p_perm_t", "p_cyclic_t"):
        for x, a in zip(rows, holm([x[key] for x in rows])):
            x[key.replace("p_", "holm_")] = round(float(a), 5)
    return rows


def injection_floor(series_map, rng, deltas=(0.010, 0.020, 0.030, 0.035, 0.040, 0.050)):
    """真·阳性对照：往两格（金9/银10）注射已知效应，看 24 格 Holm 后报不报得出来。

    这是 v1 缺的那件事。v1 用「对照组里最响的一格存活」当分辨率证明，
    而那一格是换月伪影 —— 一个没先验证能报阳性的检验，它的阴性不该信
    （Growth Gary 08-25 总纲）。
    """
    out = []
    for d in deltas:
        inj = {}
        for name, r in series_map.items():
            m = 9 if name == "gold" else 10
            r2 = r.copy()
            r2[r2.index.month == m] = r2[r2.index.month == m] + d
            inj[name] = r2
        rows = family(inj, f"inject_{int(d*1000)}bp", rng)
        g = [x for x in rows if x["metal"] == "gold" and x["month"] == "Sep"][0]
        s = [x for x in rows if x["metal"] == "silver" and x["month"] == "Oct"][0]
        out.append({"delta_pct": round(d * 100, 2),
                    "gold_Sep_holm_cyclic": g["holm_cyclic_t"],
                    "gold_Sep_detected": g["holm_cyclic_t"] < 0.05,
                    "silver_Oct_holm_cyclic": s["holm_cyclic_t"],
                    "silver_Oct_detected": s["holm_cyclic_t"] < 0.05})
    return out


def main():
    rng = np.random.default_rng(SEED)
    out = {"seed": SEED, "nperm": NPERM, "note": "v2：studentized 统计量 + 循环平移零分布"}

    fut = {"gold": monthly_returns("GC=F"), "silver": monthly_returns("SI=F")}
    out["metals_month_end"] = family(fut, "metals_month_end", rng)

    out["injection_floor"] = injection_floor(fut, rng)

    # 读法 B —— 明确标为**探索性**（预注册里没有），且踢掉停更的 csi300
    eq = {"spx": monthly_returns("^GSPC"), "sse_comp": monthly_returns("000001.SS")}
    out["reading_b_exploratory"] = family(eq, "reading_b", rng)

    # 标普 9 月的跨时代稳定性（v1 把它当成唯一存活的发现报了）
    spx = eq["spx"]
    out["spx_sep_eras"] = []
    for lo in (1928, 1950, 1970, 1990, 2000):
        sub = spx[spx.index.year >= lo]
        mask = sub.index.month == 9
        diff = float(sub.values[mask].mean() - sub.values[~mask].mean())
        _, p_cyc = cyclic_test(sub, 9)
        out["spx_sep_eras"].append({"from": lo, "n_sep": int(mask.sum()),
                                    "diff_pct": round(diff * 100, 3),
                                    "p_cyclic_t_raw": round(float(p_cyc), 5)})
    # 去掉 1930 年代最差的三个九月之后还剩什么
    sep = spx[spx.index.month == 9].sort_values()
    drop = set(sep.index[:3])
    trimmed = spx[~spx.index.isin(drop)]
    mask = trimmed.index.month == 9
    _, p_cyc = cyclic_test(trimmed, 9)
    out["spx_sep_drop3"] = {"dropped": [str(d.date()) for d in sorted(drop)],
                            "n_sep": int(mask.sum()),
                            "diff_pct": round(float(trimmed.values[mask].mean()
                                                    - trimmed.values[~mask].mean()) * 100, 3),
                            "p_cyclic_t_raw": round(float(p_cyc), 5)}

    json.dump(out, open("results_v2.json", "w"), indent=2)
    print("wrote results_v2.json")
    for k in ("gold", "silver"):
        m = "Sep" if k == "gold" else "Oct"
        r = [x for x in out["metals_month_end"] if x["metal"] == k and x["month"] == m][0]
        print(f"  {k} {m}: diff {r['mean_diff_pct']:+.2f}pp  p_perm_t {r['p_perm_t']:.3f} "
              f"p_cyclic_t {r['p_cyclic_t']:.3f}  holm_cyclic {r['holm_cyclic_t']:.3f}")
    print("  注射地板:", [(x["delta_pct"], x["gold_Sep_detected"], x["silver_Oct_detected"])
                          for x in out["injection_floor"]])
    print("  spx 9 月分时代:", [(x["from"], x["diff_pct"], x["p_cyclic_t_raw"]) for x in out["spx_sep_eras"]])
    print("  spx 9 月剔掉最差 3 个:", out["spx_sep_drop3"])


if __name__ == "__main__":
    main()
