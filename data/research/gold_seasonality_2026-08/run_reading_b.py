"""读法 B：「金九银十」在中文里本来是**旺季**的说法（九月最旺、十月次旺），
原用于地产/汽车/零售的销售季，不是讲金属。若 Andy 那句老话取的是这个意思，
落到市场上该测的是「9 月、10 月是不是强月」，而不是「黄金、白银强不强」。

同一套机器（置换 + Holm），换标的：美股 + 中国股。
"""
import json
import numpy as np
from run_study import monthly_returns, cells, mde, MONTHS

ALPHA_HOLM = 0.05 / 36  # 3 个标的 × 12 月

TARGETS = {
    "spx": "^GSPC",          # 美股基准（1927 起，最长）
    "csi300": "000300.SS",   # 中国 A 股（这句老话的原产地）
    "sse_comp": "000001.SS",  # 上证综指——csi300 在 yfinance 只有 2021 起，n=5 个九月量不了
}

out = {"reading": "B — 旺季读法：9 月/10 月是不是强月", "series": {}}
series = {}
for name, tk in TARGETS.items():
    r = monthly_returns(tk)
    series[name] = r
    out["series"][name] = {"ticker": tk, "n_months": int(len(r)),
                           "first": str(r.index[0].date()), "last": str(r.index[-1].date())}

out["cells"] = cells(series, "reading_B")
out["sep_oct"] = [c for c in out["cells"] if c["month"] in ("Sep", "Oct")]
out["mde"] = {f"{n}_{lbl}": {"n": int((r.index.month == m).sum()),
                             "sd_monthly_pct": round(float(r.values.std(ddof=1) * 100), 3),
                             "mde_pct_at_alpha_holm": round(float(mde(r, m, ALPHA_HOLM)) * 100, 3)}
              for n, r in series.items() for m, lbl in [(9, "Sep"), (10, "Oct")]}
out["gradient"] = {n: sorted([(MONTHS[m - 1], round(float(r[r.index.month == m].mean() * 100), 3),
                              int((r.index.month == m).sum())) for m in range(1, 13)],
                             key=lambda x: -x[1]) for n, r in series.items()}
json.dump(out, open("results_reading_b.json", "w"), indent=2)

print("COVERAGE", json.dumps(out["series"], ensure_ascii=False))
print("\nSep/Oct 两格：")
for c in out["sep_oct"]: print("  ", c)
print("\nMDE:", json.dumps(out["mde"], ensure_ascii=False))
print("\n梯度：")
for n, g in out["gradient"].items(): print("  ", n, [f"{a}:{b}" for a, b, _ in g])
