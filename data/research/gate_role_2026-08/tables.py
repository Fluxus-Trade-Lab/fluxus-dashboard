"""Emit the report's tables as markdown, so the prose never transcribes a number.

Round 1 shipped five wrong counts, every one of them a number read off a
printout by eye. The fix is mechanical: results.md includes what this prints.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = json.load(open(HERE / "results.json"))
B = json.load(open(HERE / "results_robust.json"))
M = json.load(open(HERE / "results_adr_matched.json"))
F = json.load(open(HERE / "facts.json"))
INC = R["included"]


def cell(d, key="p_hac_holm", val="median", pct=False):
    if not d or val not in d:
        return "不可测"
    v = d[val] * (100 if pct else 1)
    p = d.get(key)
    star = "**" if p is not None and p < 0.05 else ""
    unit = "pp" if pct else "R"
    return f"{star}{v:+.3f}{unit}{star} (p={p:.3g})" if p is not None else f"{v:+.3f}{unit}"


print("### 表 2 · 依赖稳健检验（HAC lag=10，Holm 跨 14 道筛子）\n")
print("| 筛子 | 有效日数 n / n_eff | M1 选股 (train) | 幅度·剥掉 ADR (train) | 幅度 (holdout) |")
print("|---|---|---|---|---|")
for s in INC:
    t = B["screeners"].get(s, {}).get("train", {})
    h = B["screeners"].get(s, {}).get("holdout", {})
    m1, amp, ah = t.get("M1_median_excess", {}), t.get("AMP_adr_adjusted", {}), h.get("AMP_adr_adjusted", {})
    n = f"{m1.get('n_days','–')} / {m1.get('n_eff','–')}" if "n_eff" in m1 else "–"
    print(f"| `{s}` | {n} | {cell(m1, val='median', pct=True)} | {cell(amp)} | {cell(ah)} |")
print()
print(f"**HAC+Holm 存活：选股 {len([1 for s in INC if B['screeners'].get(s,{}).get('train',{}).get('M1_median_excess',{}).get('p_hac_holm',1)<.05])} / {len(INC)}"
      f" · 幅度 {len([1 for s in INC if B['screeners'].get(s,{}).get('train',{}).get('AMP_adr_adjusted',{}).get('p_hac_holm',1)<.05])} / {len(INC)}**\n")

print("### 表 1 · 两种去 ADR 方法（train，Holm）\n")
print("| 筛子 | A 曲线除法 | B 同日同十分位配对 | 两法都过？ |")
print("|---|---|---|---|")
for s in INC:
    a = M["screeners"].get(s, {}).get("train", {}).get("A_curve_divide", {})
    b = M["screeners"].get(s, {}).get("train", {}).get("B_decile_matched", {})
    def f(d):
        if d.get("delta") is None:
            return "不可测"
        st = "**" if d.get("p_holm", 1) < 0.05 else ""
        return f"{st}{d['delta']:+.3f}R{st} (p={d['p']:.2g})"
    both = "✅" if s in F["AB_sig_train"] else ""
    print(f"| `{s}` | {f(a)} | {f(b)} | {both} |")
print()

print("### 表 3 · 第一版（朴素除以 ADR）与去伪影后的差\n")
print("| | 第一版说法 | 更正后 |")
print("|---|---|---|")
print(f"| 幅度维度存活的筛子 | {len(F['M2r_sig_pos_train'])} 道（朴素归一，train Holm） | "
      f"{len(F['AB_sig_train'])} 道过两种去 ADR 法；HAC+Holm 后 6 道 |")
print(f"| 只靠朴素归一才成立的 | — | **{', '.join('`'+x+'`' for x in F['naive_only'])}** |")
print(f"| 选股维度 | 「13 道不改善」 | 实为 {len(F['M1_not_sig'])} 道不显著 / {len(F['M1_sig_pos'])} 道显著为正 / "
      f"{len(F['M1_unmeasurable'])} 道不可测；依赖稳健后 **0 道存活** |")
print(f"| 原始幅度 M2 显著为正 | 「10 道」 | **{len(F['M2_sig_pos'])} 道**（另有 {len(F['M2_sig_neg'])} 道显著为负：{', '.join('`'+x+'`' for x in F['M2_sig_neg'])}） |")
print(f"| M3r 训练期显著 | 「5 道」 | **{len(F['M3r_sig_pos_train'])} 道** |")
print(f"| M2r holdout 同向 | 「8/11 同向、4 道显著」 | **{len(F['M2r_same_sign_both_splits'])}/{len(F['M2r_measurable_both_splits'])} 同向、{len(F['M2r_holdout_raw_p_lt_05'])} 道原始 p<.05** |")
print(f"| 阳性对照 +1.0pp 抓到 | 「13/14」 | **{len(F['pc_caught_at_1pp'])}/{len(INC)}**（没抓到：{', '.join('`'+x+'`' for x in F['pc_not_caught_at_1pp'])}） |")
print(f"| 假阳性率在 4–6% | 「13 道」 | **{len(F['fpr_in_band'])} 道**（在带外：{F['fpr_out_of_band']}） |")
print(f"| 「76% 只是 ADR 成分」 | spearman 0.758 被当成占比 | **撤回**；秩相关不是成分份额 |")
