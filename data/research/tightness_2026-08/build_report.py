"""Build the tightness comparison report (HTML, artifact-ready).

Inputs: grid_sample.csv (pipeline.tools.tightness_grid), grid_dedup_with_vcs.csv,
and a cases JSON built from live bars for the seven names Andy named.
Output: data/research/tightness_2026-08/report/index.html

    python data/research/tightness_2026-08/build_report.py --study <study.json> --cases <cases.json>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

TOK = """
:root{--bg:#F3F5F7;--card:#FFFFFF;--ink:#14202B;--muted:#66727E;--line:#D9DEE3;--grid:#E6EAEE;
--acc:#0E7C7B;--acc-ink:#0A5E5D;--tight:#1F6FEB;--loose:#C2410C;--good:#1B7F3B;--bad:#B3261E;
--goodbg:#E4F3E8;--badbg:#FBE7E5;--warnbg:#FDF3E3;--ema:#D97706;
--mono:"SF Mono",Menlo,Consolas,monospace;--sans:"Avenir Next","Helvetica Neue",Helvetica,Arial,sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0F1418;--card:#171D23;--ink:#E6EAEE;
--muted:#9AA6B2;--line:#2A333C;--grid:#232B33;--acc:#3FB5B2;--acc-ink:#7ED4D1;--tight:#6FA8FF;--loose:#F0894A;
--good:#5CBF6A;--bad:#F08A80;--goodbg:#173321;--badbg:#3A1E1B;--warnbg:#332A17;--ema:#F0A030}}
:root[data-theme="dark"]{--bg:#0F1418;--card:#171D23;--ink:#E6EAEE;--muted:#9AA6B2;--line:#2A333C;--grid:#232B33;
--acc:#3FB5B2;--acc-ink:#7ED4D1;--tight:#6FA8FF;--loose:#F0894A;--good:#5CBF6A;--bad:#F08A80;
--goodbg:#173321;--badbg:#3A1E1B;--warnbg:#332A17;--ema:#F0A030}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.55;margin:0}
.wrap{max-width:1040px;margin:0 auto;padding:32px 20px 80px}
h1{font-size:30px;line-height:1.2;margin:0 0 6px;text-wrap:balance;letter-spacing:-.01em}
h2{font-size:20px;margin:48px 0 12px;padding-top:12px;border-top:1px solid var(--line)}
h3{font-size:18px;margin:0}
h4{font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:0 0 6px}
p{max-width:72ch}.lede{font-size:16px;color:var(--muted);max-width:80ch}
.eyebrow{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:20px 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:14px 16px}
.kpi b{display:block;font-size:26px;font-family:var(--mono);font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:13px}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{color:var(--muted);font-weight:600;font-size:12px}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.mono{font-family:var(--mono);font-size:12px}
.tw{overflow-x:auto}
td.good{background:var(--goodbg);color:var(--good);font-weight:600}
td.bad{background:var(--badbg);color:var(--bad);font-weight:600}
td.warn{background:var(--warnbg)}
.case{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:18px 18px 12px;margin:18px 0}
.case header{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
.ytd{font-family:var(--mono);font-size:13px;color:var(--acc-ink)}
.sub{color:var(--muted);margin:2px 0 8px;font-size:14px}
figure{margin:0}figcaption{font-size:11.5px;color:var(--muted);margin-top:4px}
.two{display:grid;grid-template-columns:1.35fr 1fr;gap:20px;margin-top:12px}
@media(max-width:760px){.two{grid-template-columns:1fr}}
.verdict{border-left:3px solid var(--acc);padding-left:10px;color:var(--acc-ink)}
.rule{background:var(--badbg);border-left:3px solid var(--bad);padding:8px 12px;margin:8px 0;max-width:80ch}
.ok{background:var(--goodbg);border-left:3px solid var(--good);padding:8px 12px;margin:8px 0;max-width:80ch}
.note{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--muted);padding:8px 12px;margin:8px 0;max-width:80ch}
.small{font-size:12.5px;color:var(--muted)}
.pill{display:inline-block;font-family:var(--mono);font-size:11px;padding:1px 7px;border-radius:10px;
background:var(--grid);color:var(--muted)}
.pill.t{background:var(--goodbg);color:var(--good)}.pill.l{background:var(--badbg);color:var(--bad)}
.steps{counter-reset:s;display:grid;gap:14px;margin:12px 0}
.step{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px 16px 14px 56px;position:relative}
.step::before{counter-increment:s;content:counter(s);position:absolute;left:16px;top:14px;width:26px;height:26px;
border-radius:50%;background:var(--acc);color:#fff;font-weight:700;display:grid;place-items:center;font-size:14px}
.step h4{color:var(--ink);text-transform:none;letter-spacing:0;font-size:15px}.step p{margin:4px 0}
.legend span{display:inline-block;margin-right:14px;font-size:12px;color:var(--muted)}
"""


def heat(v, lo=-6, hi=12):
    if v is None:
        return ""
    if v >= hi * 0.6:
        return " good"
    if v <= lo:
        return " bad"
    if v >= 3:
        return " warn"
    return ""


def case_svg(ser, episodes, w=840, hp=170, hv=64):
    """Price panel over an ATR%-percentile panel: the compression band is the point."""
    d, c, vr, e21 = ser["d"], ser["c"], ser["vr"], ser["e21"]
    n = len(d)
    if n < 5:
        return ""
    x = lambda i: 44 + i * (w - 56) / max(1, n - 1)
    lo, hi = min(c), max(c)
    pad = (hi - lo) * 0.08 or 1
    y = lambda v: 12 + (hi + pad - v) * (hp - 24) / ((hi - lo) + 2 * pad)
    yv = lambda v: hp + 26 + (100 - v) * (hv - 12) / 100
    out = [f'<svg viewBox="0 0 {w} {hp+hv+44}" width="100%" role="img" '
           f'style="font-family:var(--mono);font-size:10px">']
    # compression shading behind price
    for ep in episodes:
        try:
            i0 = d.index(ep["from"])
        except ValueError:
            continue
        i1 = n - 1 if ep["to"] == "进行中" else (d.index(ep["to"]) if ep["to"] in d else n - 1)
        out.append(f'<rect x="{x(i0):.1f}" y="10" width="{max(2,x(i1)-x(i0)):.1f}" '
                   f'height="{hp+hv+16}" fill="var(--tight)" opacity="0.10"/>')
    for gy in (0.25, 0.5, 0.75):
        yy = 12 + gy * (hp - 24)
        out.append(f'<line x1="44" x2="{w-12}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="var(--grid)"/>')
    out.append(f'<text x="40" y="16" text-anchor="end" fill="var(--muted)">{hi:.0f}</text>')
    out.append(f'<text x="40" y="{hp-8:.0f}" text-anchor="end" fill="var(--muted)">{lo:.0f}</text>')
    out.append('<path d="' + " ".join(
        f'{"M" if i==0 else "L"}{x(i):.1f},{y(e21[i]):.1f}' for i in range(n)) +
        '" fill="none" stroke="var(--ema)" stroke-width="1.1" opacity=".8"/>')
    out.append('<path d="' + " ".join(
        f'{"M" if i==0 else "L"}{x(i):.1f},{y(c[i]):.1f}' for i in range(n)) +
        '" fill="none" stroke="var(--ink)" stroke-width="1.6"/>')
    # percentile panel
    out.append(f'<line x1="44" x2="{w-12}" y1="{yv(20):.1f}" y2="{yv(20):.1f}" '
               f'stroke="var(--tight)" stroke-dasharray="3,3"/>')
    out.append(f'<line x1="44" x2="{w-12}" y1="{yv(80):.1f}" y2="{yv(80):.1f}" '
               f'stroke="var(--loose)" stroke-dasharray="3,3"/>')
    pts = [(i, v) for i, v in enumerate(vr) if v is not None]
    if pts:
        area = " ".join(f'{"M" if k==0 else "L"}{x(i):.1f},{yv(v):.1f}' for k, (i, v) in enumerate(pts))
        out.append(f'<path d="{area} L{x(pts[-1][0]):.1f},{yv(0):.1f} L{x(pts[0][0]):.1f},{yv(0):.1f} Z" '
                   f'fill="var(--tight)" opacity=".14"/>')
        out.append(f'<path d="{area}" fill="none" stroke="var(--tight)" stroke-width="1.3"/>')
    out.append(f'<text x="40" y="{yv(100)+4:.0f}" text-anchor="end" fill="var(--muted)">100</text>')
    out.append(f'<text x="40" y="{yv(20)+4:.0f}" text-anchor="end" fill="var(--tight)">20</text>')
    # month ticks
    seen = set()
    for i, dd in enumerate(d):
        mo = dd[:7]
        if mo not in seen:
            seen.add(mo)
            out.append(f'<line x1="{x(i):.1f}" x2="{x(i):.1f}" y1="10" y2="{hp+hv+16}" stroke="var(--grid)"/>')
            out.append(f'<text x="{x(i)+3:.1f}" y="{hp+hv+34}" fill="var(--muted)">{dd[5:7]}月</text>')
    out.append("</svg>")
    return "".join(out)


def build(study: dict, cases: dict) -> str:
    S, H = study, []
    A = H.append
    A('<title>紧凑度指标横评</title>')
    A(f"<style>{TOK}</style>")
    A('<div class="wrap">')
    A('<div class="eyebrow">Fluxus · 数据端 · 2026-08-23</div>')
    A("<h1>「紧」到底该怎么量：五个指标、两个轴、七只票</h1>")
    A(f'<p class="lede">Andy 问「以 ATR 为基准是不是更精准」。要回答就得把问题拆成两半：'
      f'<b>测什么量</b>（bar 幅 / ATR / 布林带宽 / σ）和 <b>跟谁比</b>（绝对值 / 15 根 min-max / 63 日 / 252 日自百分位）。'
      f'两个轴各测一遍，再把 RMV、3WT、COIL、VCS、CTR 放进同一个交易框打分。'
      f'样本：{S["n_tickers"]} 只票 {S["n_all"]:,} 个回踩候选日，其中 {S["n_first"]:,} 个是「刚进入回踩区的第一天」——'
      f'结论都以这批为准。计分：R = ATR14，20 日内先 +2R 记赢、先 −1.5R 记输。</p>')

    A('<div class="kpis">')
    A('<div class="kpi"><b>是的</b><span>ATR 确实是更好的基准 —— 但必须<b>跟自己的历史比</b>，'
      '换成 bar 幅或 15 根 min-max 就全没了</span></div>')
    A('<div class="kpi"><b>+19.6pp</b><span>ATR% 的 252 日自百分位：最紧 20% 赢率 48.3% vs 最松 20% 28.7%（p&lt;1e-8）</span></div>')
    A('<div class="kpi"><b>−5.7pp</b><span>RMV&lt;20（TraderLion 的口径）在同一批日子上<b>低于基线</b>，'
      '不是无优势是负优势（p&lt;1e-4）</span></div>')
    A('<div class="kpi"><b>0</b><span>压缩单独用的优势：全池任意一天 −2.4pp。它不是信号，是<b>回踩场景里的排序器</b></span></div>')
    A("</div>")

    A("<h2>一、两个轴：测什么 × 跟谁比</h2>")
    A('<p class="small">每格 = 该口径下「最紧 20%」的交易框赢率减「最松 20%」的赢率（百分点）。'
      '一个<b>量</b>成立要在多种归一下同号；一个<b>归一</b>成立要在多种量下同号。表里只有一行一列同时成立。</p>')
    A('<div class="tw"><table><thead><tr><th>测什么量</th><th class="n">绝对值</th>'
      '<th class="n">15 根 min-max<br><span class="small">RMV 的口径</span></th>'
      '<th class="n">63 日自百分位</th><th class="n">252 日自百分位<br><span class="small">LuxAlgo 的口径</span></th></tr></thead><tbody>')
    NAMES = {"rng1": "当日 bar 幅 (H−L)/C", "rng5": "5 日幅 / C（现名片读数）", "atr14": "<b>ATR14 / C</b>",
             "bbw": "布林带宽 (20,2)", "sd20": "20 日收益率 σ"}
    for m, label in NAMES.items():
        A(f"<tr><td>{label}</td>")
        for nm in ("abs", "mm15", "pct63", "pct252"):
            v = S["grid"][m][nm]
            A(f'<td class="n{heat(v)}">{"—" if v is None else f"{v:+.1f}"}</td>')
        A("</tr>")
    A("</tbody></table></div>")
    A('<div class="ok"><b>读法</b>：<b>ATR 那一行</b>是唯一在三种归一下都为正的量（+7.9 / +17.0 / +19.6），'
      '<b>自百分位那两列</b>是唯一让多种量都变好的归一。两者交叉处 = ATR% 的 252 日自百分位。'
      '而 bar 幅那一行（RMV 的原料）无论怎么归一都不成立 —— 这不是参数没调好，是量选错了。</div>')
    A('<div class="rule"><b>反直觉的一格</b>：ATR × 15 根 min-max = −0.2。'
      '同一个 ATR，换成短窗 min-max 就归零。<b>「跟谁比」和「测什么」一样重要</b>，'
      '这也是 RMV 两处都踩空的原因：短窗 × bar 幅。</div>')

    A("<h2>二、所有指标同框打分</h2>")
    A(f'<p class="small">同一批日子（{S["n_first"]:,} 个「刚进入回踩区」的候选日）、同一个交易框、'
      f'同一条基线（赢率 {S["base"]}%）。绿 = 显著好于基线，红 = 显著差于。p 为 Fisher 精确检验。</p>')
    A('<div class="tw"><table><thead><tr><th>指标</th><th class="n">亮起 n</th><th class="n">赢率</th>'
      '<th class="n">Δ基线</th><th class="n">fwd20 中位</th><th class="n">MAE 中位</th><th class="n">p</th><th>备注</th></tr></thead><tbody>')
    for r in S["table"]:
        p = float(r["p"])
        cls = " good" if (r["Δ"] > 2 and p < 0.05) else (" bad" if (r["Δ"] < -2 and p < 0.05) else "")
        ps = "&lt;0.0001" if p < 0.0001 else f"{p:.3f}"
        A(f'<tr><td>{r["指标"]}</td><td class="n">{r["n"]}</td><td class="n">{r["赢率"]}%</td>'
          f'<td class="n{cls}">{r["Δ"]:+.1f}</td><td class="n">{r["fwd20"]:+.2f}%</td>'
          f'<td class="n">{r["MAE"]:+.2f}%</td><td class="n mono">{ps}</td>'
          f'<td class="small">{r["note"]}</td></tr>')
    A("</tbody></table></div>")
    A('<p><b>三句话</b>：① <b>ATR 系全线在前</b>——252 日百分位 +9.0、63 日 +7.9、连绝对值都有 +7.9；'
      '② <b>RMV −5.7、CTR −2.2、3WT 在这个场景样本太小</b>，微观紧那一族在回踩雷达上没有位置；'
      '③ <b>最值钱的一行是最后一行的反面</b>：ATR% 处在自己一年高位的那 20%，赢率只有 28.7%（−10.6）。'
      '躲开它比追最紧的更可靠。</p>')
    A('<div class="note"><b>VCS 的处理</b>：VCS ≥60 的 +5.8 没有通过显著性（p=0.19，n=124）。'
      '它和 ATR% 百分位的相关只有 −0.16，量的确实是另一个东西 —— 维持「无优势、留作对照」的判词不变。</div>')

    A("<h2>三、两个必须知道的条件</h2>")
    A('<div class="steps">')
    A('<div class="step"><h4>条件一：只在「刚进入回踩区的那一天」最强</h4>'
      '<p>同一个读数，在刚进入回踩区的第一天分辨力是 <b>+19.6pp</b>；'
      '在已经泡在区里的第 5、第 12 天只剩 <b>+7.2pp</b>，而且最紧那一档不再单调。</p>'
      '<p class="small">这解释了为什么全样本（28,676 个候选日，87% 是「泡着」的日子）几乎看不到效果 —— 被稀释了。</p></div>')
    A('<div class="step"><h4>条件二：它不是独立信号，是趋势内的排序器</h4>'
      f'<p>把同一个「压缩」拿到没有 setup 的地方测：全池任意一天 <b>{S["standalone"]["any"]}pp</b>、'
      f'上升趋势内 <b>{S["standalone"]["uptrend"]}pp</b>。<b>单独用一点优势都没有。</b></p>'
      '<p class="small">RBRK 和 HOOD 今年 1 月都进过压缩区，之后 20 天分别 −27.9% 和 −27.2% —— '
      '那两次压缩不在回踩 setup 里（趋势已破）。压缩是乘数，不是信号源。</p></div>')
    A("</div>")

    A('<div class="tw"><table><thead><tr><th>ATR% 的 252 日自百分位</th>'
      '<th class="n">刚进入回踩区 · n</th><th class="n">赢率</th><th class="n">fwd20</th>'
      '<th class="n">已在区内泡着 · n</th><th class="n">赢率</th></tr></thead><tbody>')
    lbl = {"Q1": "Q1 最紧 20%", "Q2": "Q2", "Q3": "Q3", "Q4": "Q4", "Q5": "Q5 最松 20%"}
    stay = {r["atr14__pct252"]: r for r in S["quint_stay"]}
    for r in S["quint_first"]:
        k = r["atr14__pct252"]
        s = stay.get(k, {})
        cls = " good" if k == "Q1" else (" bad" if k == "Q5" else "")
        A(f'<tr><td>{lbl[k]}</td><td class="n">{r["n"]}</td><td class="n{cls}">{r["win"]}%</td>'
          f'<td class="n">{r["fwd20"]:+.1f}%</td><td class="n">{s.get("n","—")}</td>'
          f'<td class="n">{s.get("win","—")}%</td></tr>')
    A("</tbody></table></div>")

    A('<h4 style="margin-top:22px">季度稳健性（去重叠样本，最紧 1/3 vs 最松 1/3）</h4>')
    A('<div class="tw"><table><thead><tr><th>季度</th><th class="n">n</th><th class="n">最紧 1/3</th>'
      '<th class="n">最松 1/3</th><th class="n">差</th></tr></thead><tbody>')
    for q in S["quarters"]:
        diff = q["tight"] - q["loose"]
        A(f'<tr><td>{q["q"]}</td><td class="n">{q["n"]}</td><td class="n">{q["tight"]}%</td>'
          f'<td class="n">{q["loose"]}%</td><td class="n{heat(diff,-2,8)}">{diff:+.1f}</td></tr>')
    A("</tbody></table></div>")
    A('<p class="small">三个季度全部同号，但 <b>2026Q2 只有 +1.6</b> —— 那是个普涨季，最松的一档也有 47.9% 赢率，'
      '压缩没什么可分辨的。Q1（最差的季度）分辨力最大：28.4% vs 17.2%。<b>它在难做的市场里最值钱</b>，'
      '这与「躲开最松那 20%」是同一件事的两种说法。</p>')

    A("<h2>四、七只票：压缩带长什么样</h2>")
    A('<p class="small">上panel = 2026 年收盘（黑）与 21EMA（橙）；下 panel = <b>ATR% 的 252 日自百分位</b>'
      '（蓝，0 = 一年来最压缩，100 = 一年来最松）；蓝色竖带 = 该读数 &lt;20 的压缩期。'
      '表里给出今天全部指标的读数，标注它们互相打架的地方。</p>')
    for t, cs in cases.items():
        td = cs["today"]
        ytd = cs["ytd"]
        A('<article class="case">')
        A(f'<header><h3>{t}</h3><span class="ytd">YTD {ytd:+.0f}%</span>'
          f'<span class="small">最新 {td["date"]} 收 {td["close"]}</span></header>')
        A(f'<p class="sub">{cs["blurb"]}</p>')
        A("<figure>" + case_svg(cs["series"], cs["episodes"]) +
          '<figcaption>黑 = 收盘 · 橙 = 21EMA · 蓝面积 = ATR% 的 252 日自百分位（下轴 0–100，蓝虚线 20 / 橙虚线 80）'
          ' · 蓝竖带 = 压缩期</figcaption></figure>')
        A('<div class="two"><div><h4>今天的全部读数</h4><div class="tw"><table><tbody>')
        vr = td["atr_pct252"]
        pill = ('<span class="pill t">压缩</span>' if vr < 20 else
                '<span class="pill l">一年高位</span>' if vr >= 80 else '<span class="pill">中性</span>')
        A(f'<tr><td><b>ATR% 252 日自百分位</b>（本轮冠军）</td><td class="n mono"><b>{vr}</b></td><td>{pill}</td></tr>')
        A(f'<tr><td>ATR% 63 日自百分位</td><td class="n mono">{td["atr_pct63"]}</td><td></td></tr>')
        A(f'<tr><td>ATR% 绝对值</td><td class="n mono">{td["atr_abs"]}%</td><td></td></tr>')
        A(f'<tr><td>RMV（15 根 min-max）</td><td class="n mono">{td["rmv"]}</td>'
          f'<td class="small">{"与冠军矛盾" if abs(td["rmv"]-vr)>=40 else ""}</td></tr>')
        A(f'<tr><td>5 日幅%（现名片读数）</td><td class="n mono">{td["rng5"]}</td><td></td></tr>')
        A(f'<tr><td>VCS</td><td class="n mono">{td["vcs"]}</td><td></td></tr>')
        A(f'<tr><td>COIL / CTR / 3WT</td><td class="n mono">'
          f'{"✓" if td["coil"] else "—"} / {"✓" if td["ctr"] else "—"} / {"✓" if td["wt3"] else "—"}</td><td></td></tr>')
        A("</tbody></table></div></div>")
        A("<div><h4>2026 年的压缩期</h4>")
        if cs["episodes"]:
            A('<div class="tw"><table><thead><tr><th>区间</th><th class="n">天</th><th class="n">最低</th>'
              '<th class="n">入区后 20 日</th></tr></thead><tbody>')
            for e in cs["episodes"]:
                f20 = e["fwd20_from_entry"]
                cls = " good" if (f20 is not None and f20 > 8) else (" bad" if (f20 is not None and f20 < -8) else "")
                A(f'<tr><td class="mono">{e["from"]} → {e["to"]}</td><td class="n">{e["days"]}</td>'
                  f'<td class="n mono">{e["min_vr"]}</td>'
                  f'<td class="n{cls}">{"进行中" if f20 is None else f"{f20:+.1f}%"}</td></tr>')
            A("</tbody></table></div>")
        else:
            A('<p class="small">2026 年没有进过 &lt;20 的压缩区。</p>')
        A(f'<p class="verdict">{cs["verdict"]}</p>')
        A("</div></div></article>")

    A("<h2>五、可动的三件事</h2>")
    A('<div class="steps">')
    A('<div class="step"><h4>名片加一个读数：<code>atr_pct252</code></h4>'
      '<p>引擎现成（ATR 每晚都在算），加的是「跟自己一年比」这一步。'
      '卡上同时印 <b>百分位</b> 和 <b>ATR% 绝对值</b>——前者判紧松，后者定止损距离，两个用途不能混。</p></div>')
    A('<div class="step"><h4>否决语言换一个词</h4>'
      '<p>「不紧」这把刀在百人小结里错杀率 67%。它量的是微观紧（bar 幅），'
      '而这个场景里付钱的是长窗压缩。卡上有了读数之后，「不紧」应该写成'
      '<b>「ATR 在自己一年的第 N 百分位」</b>——可证伪，也可复盘。</p></div>')
    A('<div class="step"><h4>RMV 不接，3WT 留在突破场景</h4>'
      '<p>RMV 在回踩场景是负优势，两个实现变体都一样，先记 NULL。'
      '3WT 在这里只有 30 个样本不足以判断，它本来就是 O\'Neil 的<b>突破加仓</b>工具——'
      '之前的突破口径测出 +1.11 edge，那个结论不受本轮影响。</p></div>')
    A("</div>")

    A("<h2>六、这份报告不能证明什么</h2>")
    A('<p class="small">① <b>票池自带幸存偏差</b>：event_bars 是 2026 年触发过信号的名字，'
      '整体强于全市场，各组绝对赢率都被抬高；组间相对比较不受影响。'
      '② <b>只测了一个 setup</b>（fresh-high pullback）和一个交易框（+2R/−1.5R/20 日），'
      '换止损口径结论可能变。'
      '③ <b>七只票是插图不是证据</b>：13 个压缩期的样本量什么也证明不了，'
      '证据是那 4,107 个第一天。'
      '④ <b>RMV 是开源近似</b>（Deepvue 原版公式未公开），已用原版与 SMA3 平滑两个变体交叉验证，结论一致。'
      '⑤ <b>2026Q2 几乎没有分辨力</b>，普涨市里这个读数不重要。</p>')
    A('<p class="small" style="margin-top:18px">数据：<code>data/research/tightness_2026-08/grid_sample.csv</code>'
      '（28,676 行全读数）· 引擎：<code>pipeline/tools/tightness_grid.py</code> · '
      '前情：<code>rmv_volrank_study.md</code>（本报告修正了它「窗口决定一切」的说法：量与窗口同等重要）</p>')
    A("</div>")
    return "\n".join(H)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--study", type=Path, required=True)
    ap.add_argument("--cases", type=Path, required=True)
    ap.add_argument("--out", type=Path,
                    default=Path("data/research/tightness_2026-08/report/index.html"))
    a = ap.parse_args(argv)
    study = json.loads(a.study.read_text())
    cases = json.loads(a.cases.read_text())
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(build(study, cases), encoding="utf-8")
    print(f"wrote {a.out} ({a.out.stat().st_size/1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
