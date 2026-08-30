"""检验自己的分辨率地板 —— 在看任何结论之前先算它。

08-29 的坑（pitfall_a_stricter_test_can_be_blind）：块翻符号检验在 Holm 后
**物理上**报不出阳性，最小可能 p 在看到任何数据之前就越过了 0.05。
v2 换上循环平移之后一头撞进同一个坑，注射到 +5pp 仍然 0/6 检出。
本脚本把地板算清楚，并给出一个不瞎的校正口径。
"""
import json
import numpy as np
from run_study import monthly_returns
from run_v2 import cyclic_test, holm, family, SEED

fut = {"gold": monthly_returns("GC=F"), "silver": monthly_returns("SI=F")}
n = len(fut["gold"])
min_p = 1 / n                      # 循环平移：n-1 个非平凡旋转，(0+1)/((n-1)+1)
out = {"n_months": n, "min_achievable_p_cyclic": round(min_p, 6),
       "floors": {}}
for m, lab in [(24, "24 格家族（12 月 × 2 金属）"), (2, "2 格家族（老话预先指定的那两格）"),
               (1, "不校正")]:
    out["floors"][lab] = {"multiplier": m, "min_p_after_correction": round(min_p * m, 5),
                          "can_ever_report_positive_at_0.05": bool(min_p * m < 0.05)}

# 用「2 格家族」重跑注射：老话事先就点名了金9与银10，24 格是给「去捞」的人准备的罚款
rng = np.random.default_rng(SEED)
inj = []
for d in (0.005, 0.010, 0.015, 0.020, 0.030, 0.040):
    cells = []
    for name, r in fut.items():
        mth = 9 if name == "gold" else 10
        r2 = r.copy()
        r2[r2.index.month == mth] = r2[r2.index.month == mth] + d
        _, p = cyclic_test(r2, mth)
        cells.append((name, float(p)))
    adj = holm([p for _, p in cells])
    inj.append({"delta_pct": round(d * 100, 2),
                "gold_Sep_holm2": round(float(adj[0]), 5), "gold_detected": bool(adj[0] < 0.05),
                "silver_Oct_holm2": round(float(adj[1]), 5), "silver_detected": bool(adj[1] < 0.05)})
out["injection_holm2"] = inj

# 未注射的真实读数，同一口径
real = []
for name, r in fut.items():
    mth = 9 if name == "gold" else 10
    _, p = cyclic_test(r, mth)
    real.append((name, float(p)))
adj = holm([p for _, p in real])
out["actual_holm2"] = {"gold_Sep": round(float(adj[0]), 5), "silver_Oct": round(float(adj[1]), 5)}

json.dump(out, open("results_floor.json", "w"), indent=2)
print(json.dumps(out, ensure_ascii=False, indent=2))
