"""渲染 v2 的表。散文里不许出现手打的数字。"""
import json

V2 = json.load(open("results_v2.json"))
FL = json.load(open("results_floor.json"))
LS = json.load(open("results_longsample.json"))
A = json.load(open("results.json"))
out = []


def g(rows, metal, month):
    return [r for r in rows if r["metal"] == metal and r["month"] == month][0]


out.append("### 表 A · 分辨率地板 —— **先看这张，它决定了下面几张表能不能读**\n")
out.append(f"循环平移零分布穷举 {FL['n_months']-1} 次旋转，"
           f"**最小可能 p = {FL['min_achievable_p_cyclic']:.4f}**。乘上校正倍数之后：\n")
out.append("| 校正口径 | 倍数 | 校正后最小可能 p | 这个检验**有可能**报出阳性吗 |")
out.append("|---|---|---|---|")
for lab, v in FL["floors"].items():
    out.append(f"| {lab} | ×{v['multiplier']} | **{v['min_p_after_correction']:.4f}** | "
               f"{'✅ 能' if v['can_ever_report_positive_at_0.05'] else '🚫 **不能——它是瞎的**'} |")
out.append("\n**注射实验**（往真实序列的那一格加一个已知效应，看 2 格 Holm 后报不报得出来）：\n")
out.append("| 注射多少 | 金 9 校正后 p | 报出来了吗 | 银 10 校正后 p | 报出来了吗 |")
out.append("|---|---|---|---|---|")
for r in FL["injection_holm2"]:
    out.append(f"| +{r['delta_pct']:.1f} pp | {r['gold_Sep_holm2']:.3f} | "
               f"{'✅' if r['gold_detected'] else '❌'} | {r['silver_Oct_holm2']:.3f} | "
               f"{'✅' if r['silver_detected'] else '❌'} |")
out.append(f"\n**真实读数（未注射，同一口径）**：金 9 = {FL['actual_holm2']['gold_Sep']:.3f}，"
           f"银 10 = {FL['actual_holm2']['silver_Oct']:.3f}。")

out.append("\n### 表 B · 主结果（v2 口径：studentized 统计量 + 循环平移零分布）\n")
out.append("| 说法 | n | 超额 | p（iid 置换） | p（循环平移） | p（循环平移 + 24 格 Holm） |")
out.append("|---|---|---|---|---|---|")
for metal, month, name in [("gold", "Sep", "金 9"), ("silver", "Oct", "银 10")]:
    r = g(V2["metals_month_end"], metal, month)
    out.append(f"| **{name}** | {r['n']} | {r['mean_diff_pct']:+.2f} pp | {r['p_perm_t']:.3f} | "
               f"**{r['p_cyclic_t']:.3f}** | {r['holm_cyclic_t']:.3f}〔见表 A：这一列本来就报不出阳性〕|")

out.append("\n### 表 C · 换一个价格口径，黄金九月符号就翻正 —— 两个都报，谁也不当主\n")
out.append("| 口径 | 数据源 | 窗口 | 金 9 超额 | 金 9 名次 | p_raw |")
out.append("|---|---|---|---|---|---|")
r = g(A["specs"]["main_full"], "gold", "Sep")
rank = [m for m, _, _ in A["gradient"]["gold"]].index("Sep") + 1
out.append(f"| **月末收盘** | Yahoo `GC=F` 连续期货 | 2000-09→2026-07 | "
           f"**{r['mean_diff_pct']:+.2f} pp** | 第 {rank}/12 | {r['p_raw']:.3f} |")
for tag, lab in [("2000_2025", "2000–2025（同年代）"), ("1975_2025", "1975–2025"),
                 ("1975_1999", "1975–1999（我们的窗口切掉的那 25 年）"),
                 ("1968_2025", "1968–2025")]:
    w = LS["windows"][tag]
    c = g(w["cells"], "gold", "Sep")
    rk = [m for m, _ in w["gradient"]["gold"]].index("Sep") + 1
    out.append(f"| **月均价** | World Bank Pink Sheet | {lab} | **{c['mean_diff_pct']:+.2f} pp** | "
               f"**第 {rk}/12** | {c['p_raw']:.3f} |")
out.append("\n银 10 在同样四个长窗口里的名次：" + "、".join(
    f"{tag} 第 {[m for m,_ in LS['windows'][tag]['gradient']['silver']].index('Oct')+1}/12"
    for tag in ["1968_2025", "1975_1999", "1975_2025", "2000_2025"]) + "。")

out.append("\n### 表 D · 标普九月 —— v1 把它当成「全研究唯一存活的发现」，v2 撤回\n")
out.append("| 起始年 | 九月数 | 超额 | p（循环平移，未校正） | ×36（读法 B 家族） |")
out.append("|---|---|---|---|---|")
for e in V2["spx_sep_eras"]:
    out.append(f"| {e['from']} | {e['n_sep']} | {e['diff_pct']:+.2f} pp | "
               f"**{e['p_cyclic_t_raw']:.4f}** | {min(1.0, e['p_cyclic_t_raw']*36):.3f} |")
d = V2["spx_sep_drop3"]
out.append(f"| 1928（剔掉最差三个九月：{', '.join(x[:7] for x in d['dropped'])}） | {d['n_sep']} | "
           f"{d['diff_pct']:+.2f} pp | **{d['p_cyclic_t_raw']:.4f}** | "
           f"{min(1.0, d['p_cyclic_t_raw']*36):.3f} |")

open("TABLES_V2.md", "w").write("\n".join(out) + "\n")
print("\n".join(out))
