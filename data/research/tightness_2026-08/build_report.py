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
      f'结论都以这批为准。计分：R = ATR14，20 日内先 +2R 记赢、先 −1.5R 记输。'
      '<b>08-23 晚追加了三节</b>：选股 vs timing 的分解、PURR 引出的「一个数字两种状态」、'
      '以及一次独立样本复制（结论被诚实降级）。</p>')

    A('<div class="kpis">')
    A('<div class="kpi"><b>是的</b><span>ATR 确实是更好的基准 —— 但必须<b>跟自己的历史比</b>，'
      '换成 bar 幅或 15 根 min-max 就全没了</span></div>')
    A('<div class="kpi"><b>timing</b><span>它是<b>时钟不是选股器</b>：票内排名 +13.3pp，'
      '同日候选之间只有 +4.3pp（第五节）</span></div>')
    A('<div class="kpi"><b>+19.6pp</b><span>ATR% 的 252 日自百分位：最紧 20% 赢率 48.3% vs 最松 20% 28.7%（p&lt;1e-8）</span></div>')
    A('<div class="kpi"><b>−5.7pp</b><span>RMV&lt;20（TraderLion 的口径）在同一批日子上<b>低于基线</b>，'
      '不是无优势是负优势（p&lt;1e-4）</span></div>')
    A('<div class="kpi"><b>+11.8pp</b><span>独立样本（172 只票两年）复制到的幅度，p=0.047 —— '
      '方向稳、<b>幅度不稳</b>，2026 那段几乎是平的（第七节）</span></div>')
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

    # ── 追加轮（Andy 08-23 追问）─────────────────────────────────────
    A("<h2>五、选股还是 timing（08-23 追问）</h2>")
    A('<p>同一个读数可以因为两种完全不同的原因赢，用法相反：<b>选股</b> = 在今天可选的名字里排出该买谁'
      '（测法：只在同一天的候选之间排名，市况被抵消）；<b>timing</b> = 对一只票说它现在是不是时候'
      '（测法：只在这只票自己的历史里排名，票与票的差异被抵消）。分开测：</p>')
    A('<div class="tw"><table><thead><tr><th>轴</th><th class="n">最紧 1/3 赢率</th>'
      '<th class="n">最松 1/3 赢率</th><th class="n">差</th><th>读法</th></tr></thead><tbody>')
    A('<tr><td>原始（两种混在一起）</td><td class="n">46.0%</td><td class="n">32.2%</td>'
      '<td class="n good">+13.8</td><td class="small">混合值，不能直接当任何一种用</td></tr>')
    A('<tr><td><b>选股轴</b>：同一天的候选之间排名</td><td class="n">41.4%</td><td class="n">37.1%</td>'
      '<td class="n">+4.3</td><td class="small">弱。它不擅长在今天的名单里挑人</td></tr>')
    A('<tr><td><b>timing 轴</b>：同一只票自己历史里排名</td><td class="n">57.1%</td><td class="n">43.8%</td>'
      '<td class="n good">+13.3</td><td class="small">强。无前视（只用该票此前的读数做扩张排名，n=367）</td></tr>')
    A("</tbody></table></div>")
    A('<div class="ok"><b>答案</b>：<code>atr_pctl</code> 是 <b>timing</b>，不是选股。'
      '它回答「这只票现在是不是时候」，不回答「今天买哪只」。'
      '这也解释了第三节那两个条件——时钟只有在你已经选好了票、且票在趋势里的时候才有意义。</div>')

    A("<h4>那选股轴是谁？</h4>")
    A('<p class="small">把同一批日子按各信号做同日横截面排名，看谁能在「今天的候选之间」分出胜负：</p>')
    A('<div class="tw"><table><thead><tr><th>信号</th><th class="n">同日分辨力</th><th>结论</th></tr></thead><tbody>')
    for name, v, note in [
        ("距 52 周高的距离（越近越好）", "+4.7", "最好的选股维度，且与压缩独立"),
        ("ATR% 252 日自百分位", "+4.3", "同日比就弱了 —— 它本来就不是干这个的"),
        ("RS 线 63 日自百分位", "+2.6", "几乎无分辨力"),
        ("ATR% 绝对值", "+2.0", "无"),
        ("RS 线 21 日自百分位", "−2.7", "反向：短窗 RS 最强的那批反而差"),
        ("近 10 日口袋支点数", "−0.0", "无（第一版报了 +10.7，是空列造成的假象，已修）"),
    ]:
        cls = " good" if v.startswith("+4") else (" bad" if v.startswith("−") else "")
        A(f'<tr><td>{name}</td><td class="n{cls}">{v}pp</td><td class="small">{note}</td></tr>')
    A("</tbody></table></div>")
    A("<h4>两层叠起来</h4>")
    A('<div class="tw"><table><thead><tr><th>timing（压缩）</th><th>选股（距 52 周高）</th>'
      '<th class="n">n</th><th class="n">赢率</th><th class="n">fwd20 中位</th></tr></thead><tbody>')
    for t_, s_, n_, w_, f_, cls in [
        ("紧", "近高", 1119, "48.5%", "+2.49%", " good"),
        ("紧", "远高", 935, "40.2%", "+0.43%", ""),
        ("松", "远高", 1118, "36.0%", "−0.74%", ""),
        ("松", "近高", 935, "31.3%", "−1.14%", " bad"),
    ]:
        A(f'<tr><td>{t_}</td><td>{s_}</td><td class="n">{n_}</td>'
          f'<td class="n{cls}">{w_}</td><td class="n">{f_}</td></tr>')
    A("</tbody></table></div>")
    A('<p class="small">最好格 48.5% vs 最差格 36.0%，<b>+12.5pp，p=2.6e-9</b>。'
      '第三层（口袋支点）没有加成（−1.9pp，p=0.57）；RS 线 63 日只加收益不加赢率（fwd20 +2.39 vs +1.28）。</p>')

    A("<h2>六、一个数字里混着两种状态（PURR 引出的）</h2>")
    A('<p>Andy：「PURR 现在还是压缩？这个有点反直觉」。查下来<b>直觉是对的，而读数没错——它们在说两件事</b>。'
      'PURR 08-19 单日 +30%，ATR14 绝对值三天涨了 53%（0.45→0.69），但价格同期涨 47%，'
      '所以 <code>ATR/收盘</code> 几乎没动，百分位还是 4；而它的 5 日幅在自己一年里排第 99。</p>')
    A('<div class="tw"><table><thead><tr><th>状态</th><th>atr_pctl</th><th>range5_pctl</th>'
      '<th class="n">n</th><th class="n">赢率</th><th class="n">fwd20</th></tr></thead><tbody>')
    A('<tr><td><b>真压缩</b>（确实安静）</td><td>低</td><td>低</td><td class="n">4129</td>'
      '<td class="n">40.5%</td><td class="n">+0.85%</td></tr>')
    A('<tr><td><b>ATR 还没追上价格</b></td><td>低</td><td>高</td><td class="n">1607</td>'
      '<td class="n good">47.0%</td><td class="n">+2.17%</td></tr>')
    A("</tbody></table></div>")
    A('<div class="rule"><b>我差点做错的事</b>：本来打算加一道闸把「假压缩」滤掉。'
      '实测发现<b>被我判定为假的那一半反而更好</b>（47.0% vs 40.5%，p&lt;1e-4）——'
      '「ATR 还没追上价格」在趋势里是动能，不是噪声。所以 <code>range5_pctl_252</code> 作为'
      '<b>标签</b>入库，不作为过滤器。</div>')

    A("<h4>七只票今天在四种分母下的读数</h4>")
    A('<p class="small">同一天同一只票，换个分母读数就变——这正是为什么口径要钉死。'
      '「ATR/20 日前收盘」是唯一能中和价格暴涨效应的变体。</p>')
    A('<div class="tw"><table><thead><tr><th>票</th><th class="n">ATR/收盘<br><span class="small">入库口径</span></th>'
      '<th class="n">ATR/50 日均线</th><th class="n">ATR/20 日前收盘</th><th class="n">ATR 绝对值</th>'
      '<th class="n">5 日幅</th><th>状态</th></tr></thead><tbody>')
    for t_, a_, b_, c_, d_, e_, st in [
        ("MRNA", 100, 100, 100, 100, 100, "一年高位（四个口径一致）"),
        ("P", 41, 88, 95, 94, 52, "只有入库口径显得温和 —— 涨出来的"),
        ("HOOD", 41, 66, 71, 56, 70, "上周真压缩过（08-17 读 23），已展开"),
        ("RBRK", 32, 75, 88, 95, 26, "8 月初的「压缩」大半是价格涨出来的"),
        ("MP", 10, 45, 87, 17, 34, "真压缩，第 10 个交易日"),
        ("IBIT", 23, 45, 45, 16, 97, "压缩已结束，正在展开"),
        ("PURR", 4, 26, 54, 71, 99, "ATR 还没追上价格（历史最强格）"),
    ]:
        A(f'<tr><td><b>{t_}</b></td><td class="n">{a_}</td><td class="n">{b_}</td><td class="n">{c_}</td>'
          f'<td class="n">{d_}</td><td class="n">{e_}</td><td class="small">{st}</td></tr>')
    A("</tbody></table></div>")

    A("<h4>Andy 点名的六个时间窗，逐日读数</h4>")
    A('<div class="steps">')
    A('<div class="step"><h4>HOOD 上周 —— 信号完整跑通的那个</h4>'
      '<p>08-12 读 41 → <b>08-13 读 29、08-17 读 23</b>（63 日口径只有 6，5 日幅 7.9 = 真安静），'
      '然后 <b>08-21 单日 +13.7%</b>（95.10 → 108.13），读数回到 41。'
      '压缩 → 展开，是七只里最干净的一次。</p></div>')
    A('<div class="step"><h4>IBIT —— 你说的对，已经走出来了</h4>'
      '<p>08-05 进压缩，08-17/08-18 读到 <b>0</b>（一年最静），08-19 起连续三天放大，'
      '今天读 23、5 日幅 97。入区 36.74 → 今天 43.68 = <b>+18.9%</b>。</p></div>')
    A('<div class="step"><h4>MP —— 不是「即将走出」，是还在里面</h4>'
      '<p>08-10 进压缩到今天第 10 个交易日，读数在 7–15 之间，今天 10；'
      '且 5 日幅 34、ATR 绝对值 17 —— <b>两个口径都说安静，是七只里唯一的真压缩</b>。'
      '价格已从 54.66 走到 60.05（+9.9%），压缩里在慢慢抬。</p></div>')
    A('<div class="step"><h4>RBRK 8 月初 —— 读数会骗人的那个</h4>'
      '<p>07-28 读 86（一年高位）→ 08-13 读 15（压缩）。但这段价格从 71.45 涨到 105.09（<b>+47%</b>），'
      'ATR 绝对值同期从 4.12 涨到 4.88（<b>+18%</b>）—— 波动其实在变大，'
      '是分母（价格）涨得更快才把比值压下去。<b>「ATR/20 日前收盘」这个口径读 88，说的才是实话。</b></p></div>')
    A('<div class="step"><h4>P 7–8 月 —— 同一个陷阱的慢速版</h4>'
      '<p>07-16 读 93（一年高位，当时刚跌到 68.37）→ 08-17 读 34，其间价格 68 → 117（+71%）。'
      '今天四个口径：入库 41 / 50 均线 88 / 20 日前 95 / 绝对值 94。'
      '<b>只有入库口径认为它温和</b>，其余三个都说这是一只很吵的票。</p></div>')
    A('<div class="step"><h4>PURR 过去两周 —— 先真后假</h4>'
      '<p>08-03 到 08-18 是<b>真压缩</b>（读数 1–17，5 日幅 7–15），'
      '08-19 单日 +30% 之后变成<b>「ATR 还没追上」</b>（读数 4，5 日幅 41.4 排第 99）。'
      '同一个数字，两周里换了含义 —— 所以必须配 range5 一起看。'
      '⚠️ 另外它上市只有 180 根 K 线，252 日百分位是拿不满一年的样本算的，读数比其余六只脆。</p></div>')
    A("</div>")

    A("<h2>七、样本外复制：诚实的降级</h2>")
    A('<p>上面所有数字来自 event_bars 池（2026 年触发过信号的名字，252 根日线）。'
      '拿 <b>完全独立的一批</b>重跑：<code>data/output/tickers/</code> 里 172 只票的两年日线。</p>')
    A('<div class="tw"><table><thead><tr><th>样本</th><th class="n">n（第一天）</th>'
      '<th class="n">最紧 20%</th><th class="n">最松 20%</th><th class="n">差</th><th class="n">p</th></tr></thead><tbody>')
    A('<tr><td>event_bars（原样本）</td><td class="n">4107</td><td class="n">48.3%</td>'
      '<td class="n">28.7%</td><td class="n good">+19.6</td><td class="n mono">&lt;1e-8</td></tr>')
    A('<tr><td>tickers 库（独立样本）</td><td class="n">817</td><td class="n">53.7%</td>'
      '<td class="n">41.9%</td><td class="n warn">+11.8</td><td class="n mono">0.047</td></tr>')
    A('<tr><td>└ 其中 2025</td><td class="n">443</td><td class="n">54.1%</td>'
      '<td class="n">39.0%</td><td class="n good">+15.1</td><td class="n mono">—</td></tr>')
    A('<tr><td>└ 其中 2026</td><td class="n">374</td><td class="n">48.8%</td>'
      '<td class="n">47.6%</td><td class="n bad">+1.2</td><td class="n mono">—</td></tr>')
    A("</tbody></table></div>")
    A('<div class="rule"><b>怎么读这张表</b>：方向在我跑过的每一个切法里都是正的，'
      '从来没有反过来；但<b>幅度极不稳定</b>——独立样本弱一半、非单调，2026 年那一段几乎是平的'
      '（和第三节里 2026Q2 只有 +1.6 是同一件事）。'
      '所以字段的定位是<b>加权项 / 平手时的裁决者</b>，不是闸门，也别拿某个阈值去卡。'
      '我已经把这段写进 <code>atr_pctl</code> 的 docstring，免得三个月后有人只看到 48.3% vs 28.7%。</div>')
    A('<p class="small">顺带排除了一个我自己提出的怀疑：涨得多的票是不是会被结构性地读成「紧」'
      '（分母被抬高一整年）。实测相关是 <b>+0.162</b>（略正，方向相反），'
      'σ 百分位这个尺度无关的对照也是 +0.132 —— <b>没有这个偏差</b>。</p>')

    A("<h2>八、可动的三件事</h2>")
    A('<div class="steps">')
    A('<div class="step"><h4>名片加一个读数：<code>atr_pct252</code></h4>'
      '<p><b>已落地</b>（08-23 合进 main，今晚 cron 起有值）：universe 行与名片 readings 现在带 '
      '<code>atr_pctl_252</code> / <code>atr_pctl_63</code> / <code>range5_pctl_252</code>，'
      '外加原有的 <code>adr_pct</code>。卡上同时印 <b>百分位</b>（判紧松）和 <b>ATR% 绝对值</b>'
      '（定止损距离）——同一个量两个职责，不能互相替代。前端展示形态待定。</p></div>')
    A('<div class="step"><h4>否决语言换一个词</h4>'
      '<p>「不紧」这把刀在百人小结里错杀率 67%。它量的是微观紧（bar 幅），'
      '而这个场景里付钱的是长窗压缩。卡上有了读数之后，「不紧」应该写成'
      '<b>「ATR 在自己一年的第 N 百分位」</b>——可证伪，也可复盘。</p></div>')
    A('<div class="step"><h4>RMV 不接，3WT 留在突破场景</h4>'
      '<p>RMV 在回踩场景是负优势，两个实现变体都一样，先记 NULL。'
      '3WT 在这里只有 30 个样本不足以判断，它本来就是 O\'Neil 的<b>突破加仓</b>工具——'
      '之前的突破口径测出 +1.11 edge，那个结论不受本轮影响。</p></div>')
    A("</div>")

    A("<h2>九、这份报告不能证明什么</h2>")
    A('<p class="small">① <b>票池自带幸存偏差</b>：event_bars 是 2026 年触发过信号的名字，'
      '整体强于全市场，各组绝对赢率都被抬高；组间相对比较不受影响。'
      '② <b>只测了一个 setup</b>（fresh-high pullback）和一个交易框（+2R/−1.5R/20 日），'
      '换止损口径结论可能变。'
      '③ <b>七只票是插图不是证据</b>：13 个压缩期的样本量什么也证明不了，'
      '证据是那 4,107 个第一天。'
      '④ <b>RMV 是开源近似</b>（Deepvue 原版公式未公开），已用原版与 SMA3 平滑两个变体交叉验证，结论一致。'
      '⑤ <b>2026Q2 几乎没有分辨力</b>，普涨市里这个读数不重要。'
      '⑥ <b>最重要的一条</b>：独立样本只复制到一半幅度（+11.8pp，p=0.047），且 2026 段几乎是平的 —— '
      '把它当加权项，别建阈值闸门（第七节）。</p>')
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
