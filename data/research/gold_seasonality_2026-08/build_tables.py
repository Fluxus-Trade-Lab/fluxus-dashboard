"""从 results*.json 渲染 results.md 里的所有表。散文里不许出现手打的数字。"""
import json

A = json.load(open("results.json"))
B = json.load(open("results_reading_b.json"))
out = []


def cell(spec, metal, month, src=A):
    for r in src["specs"][spec] if src is A else src["cells"]:
        if r["metal"] == metal and r["month"] == month:
            return r
    return None


out.append("### 表 1 · 主口径（连续期货 GC=F / SI=F，2000-09 → 2026-07）\n")
out.append("| 说法 | n | 该月均值 − 其他月均值 | p（置换） | p（Holm，24 格） | 12 个月里排第几 |")
out.append("|---|---|---|---|---|---|")
for metal, month, name in [("gold", "Sep", "金 9"), ("silver", "Oct", "银 10")]:
    r = cell("main_full", metal, month)
    rank = [m for m, _, _ in A["gradient"][metal]].index(month) + 1
    out.append(f"| **{name}** | {r['n']} | **{r['mean_diff_pct']:+.2f} pp** | {r['p_raw']:.3f} | "
               f"**{r['p_holm']:.2f}** | **第 {rank} / 12** |")

out.append("\n### 表 2 · 分辨率地板（先算这个，再谈 NULL）\n")
out.append("| 格 | n | 月收益标准差 | Holm 后 α 下 80% 把握能测出的最小效应 | 单看 α=0.05 时 |")
out.append("|---|---|---|---|---|")
for k, v in A["mde"].items():
    if k.endswith("Sep") and k.startswith("gold") or k.endswith("Oct") and k.startswith("silver"):
        out.append(f"| {k} | {v['n']} | {v['sd_monthly_pct']:.2f}% | "
                   f"**≥ {v['mde_pct_at_alpha_holm']:.2f} pp** | ≥ {v['mde_pct_at_alpha_005']:.2f} pp |")

out.append("\n### 表 3 · 六个稳健性变体，两格都没翻号\n")
out.append("| 变体 | 金 9 效应 / p_raw | 银 10 效应 / p_raw |")
out.append("|---|---|---|")
labels = {"main_full": "主口径（全样本）", "log_returns": "对数收益", "etf_proxy": "ETF 代理 GLD/SLV",
          "ex_2011": "剔除 2011", "train_2000_2015": "2000–2015 段", "holdout_2016_2026": "2016–2026 段"}
for spec, lab in labels.items():
    g, s = cell(spec, "gold", "Sep"), cell(spec, "silver", "Oct")
    out.append(f"| {lab} | {g['mean_diff_pct']:+.2f} pp / {g['p_raw']:.3f} | "
               f"{s['mean_diff_pct']:+.2f} pp / {s['p_raw']:.3f} |")
reg = {(r["spec"], r["metal"], r["month"]): r for r in A["specs"]["regime"]}
for tag, lab in [("bull_2000_2011", "牛市段 2000–2011"), ("bear_2012_2015", "熊市段 2012–2015")]:
    g, s = reg[(tag, "gold", "Sep")], reg[(tag, "silver", "Oct")]
    out.append(f"| {lab} | {g['mean_diff_pct']:+.2f} pp / {g['p_raw']:.3f} (n={g['n']}) | "
               f"{s['mean_diff_pct']:+.2f} pp / {s['p_raw']:.3f} (n={s['n']}) |")

out.append("\n### 表 4 · 十二个月的完整梯度（主口径月均收益 %，不只报被问到的那两格）\n")
out.append("| 名次 | 黄金 | 白银 |")
out.append("|---|---|---|")
for i in range(12):
    gm, gv, _ = A["gradient"]["gold"][i]
    sm, sv, _ = A["gradient"]["silver"][i]
    mark = lambda m, t: f"**{m} {t:+.2f}**" if m in ("Sep", "Oct") else f"{m} {t:+.2f}"
    out.append(f"| {i+1} | {mark(gm, gv)} | {mark(sm, sv)} |")

out.append("\n### 表 5 · 对照组（同一套机器，跑两个没人编成顺口溜的标的）\n")
out.append("| 格 | 效应 | p_raw | p（Holm，24 格） |")
out.append("|---|---|---|---|")
for r in sorted(A["specs"]["control"], key=lambda x: x["p_raw"])[:4]:
    out.append(f"| {r['metal']} {r['month']} | {r['mean_diff_pct']:+.2f} pp | {r['p_raw']:.4f} | "
               f"**{r['p_holm']:.4f}** |")

out.append("\n### 表 6 · 读法 B（旺季读法）——「9 月/10 月是不是强月」\n")
out.append("| 标的 | 覆盖 | 9 月效应 / p_raw / p_Holm | 10 月效应 / p_raw | 9 月在 12 个月里排第几 |")
out.append("|---|---|---|---|---|")
namemap = {"spx": "标普 500", "sse_comp": "上证综指", "csi300": "沪深 300"}
for k in ["spx", "sse_comp", "csi300"]:
    s9 = [c for c in B["sep_oct"] if c["metal"] == k and c["month"] == "Sep"][0]
    s10 = [c for c in B["sep_oct"] if c["metal"] == k and c["month"] == "Oct"][0]
    cov = B["series"][k]
    rank = [m for m, _, _ in B["gradient"][k]].index("Sep") + 1
    out.append(f"| {namemap[k]} | {cov['first']}→{cov['last']}（{cov['n_months']} 月） | "
               f"**{s9['mean_diff_pct']:+.2f} pp** / {s9['p_raw']:.4f} / **{s9['p_holm']:.4f}** | "
               f"{s10['mean_diff_pct']:+.2f} pp / {s10['p_raw']:.3f} | **第 {rank} / 12** |")

open("TABLES.md", "w").write("\n".join(out) + "\n")
print("\n".join(out))
