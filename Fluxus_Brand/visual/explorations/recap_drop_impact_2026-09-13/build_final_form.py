#!/usr/bin/env python3
"""Final form of the recap masthead (Andy 09-13, priority=speed): bold drop line + hollow dot at the
close, subtitle line removed. Real SPX windows from origin/main, five most recent issues.

    python3 build_final_form.py [out.html]
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SP = HERE.parents[3] if False else Path("/private/tmp/claude-501/-Users-taolezhu-Documents-AI-Trading-System-Fluxus-Marketing-Visual-Design/ee3710aa-d552-414c-9357-4584bfc6459a/scratchpad")
WINDOWS = json.loads((SP / "drop_windows.json").read_text())

TITLES = {
    "2026-09-11": ("A Hot Core Print Gets Bought — AI Hardware Runs, the Average Stock Doesn't",
                    "Four-day slide ends · HPE/DELL +12% · RSP and IWM still under the 50-day · Friday, September 11, 2026"),
    "2026-09-10": ("Fourth Down Day in a Row, and the Average Stock Is the Weak Link",
                    "SPX −0.6% · breadth still negative · Thursday, September 10, 2026"),
    "2026-09-09": ("A Second Down Day, Quieter Than the First",
                    "SPX −0.5% · Wednesday, September 9, 2026"),
    "2026-09-08": ("The Slide Starts, on Thin Volume",
                    "SPX −0.6% · Monday, September 8, 2026"),
    "2026-09-04": ("Semis & Memory Lead",
                    "September 4, 2026 (Friday)"),
}

def bold_stroke(H, px=6, box_px=46, pad=6):
    return px * (H + 2 * pad) / box_px

def drop_svg(w, stroke, cls, pad=6, dot=False, label=""):
    d = w["d"]; H = w["H"]
    ex, ey = (float(v) for v in d.split()[-1].split(","))
    mark = (f'<circle class="dropdot" style="stroke-width:{stroke*0.5:.1f}" cx="{ex}" cy="{ey}" '
            f'r="{stroke*1.7:.1f}"/>') if dot else ""
    return (f'<svg class="drop {cls}" viewBox="{-pad} {-pad} {1000+2*pad} {H+2*pad:.1f}" role="img" '
            f'aria-label="{label}"><path style="stroke-width:{stroke}" d="{d}"/>{mark}</svg>')

def reg(w, tag):
    return (f'<p class="reg">1m · drop <span class="m">#{tag}</span> · {w["D0"]} → {w["D"]} · SPX · '
            f'∫ = {w["arc"]:.3f} m</p>')

def page(D, before):
    w = WINDOWS[D]
    tag = D[5:].replace("-", "")
    title, sub = TITLES[D]
    stroke = 2.5 if before else bold_stroke(w["H"])
    svg = drop_svg(w, stroke, "thin", dot=not before, label=f"SPX drop line, 21 sessions to {D}")
    subline = f'<p class="byline">{sub}</p>' if before else ""
    return (f'<div class="mast"><span class="brand">Fluxus Capital</span><span>Daily Market Recap · No. {tag}</span></div>'
            f'{svg}{reg(w, tag)}<h2 class="hl-a">{title}</h2>{subline}')

TEMPLATE = r"""<title>落点定稿</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@600;700&display=swap">
<style>
:root{
  --paper:#F2F1ED; --sheet:#FBFAF7; --ink:#1A1917; --ink2:#4A463F; --rule:#D9D6CD; --soft:#E8E5DD;
  --muted:#8A857A; --accent:#D1600F;
  --sans:"IBM Plex Sans",-apple-system,"PingFang SC",sans-serif;
  --cond:"IBM Plex Sans Condensed","IBM Plex Sans",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;
}
@media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){
  --paper:#12110F; --sheet:#1A1917; --ink:#E9E7E2; --ink2:#B7B4AC; --rule:#35312B; --soft:#28251F;
  --muted:#8E8A80; --accent:#E8843C;
}}
:root[data-theme="dark"]{
  --paper:#12110F; --sheet:#1A1917; --ink:#E9E7E2; --ink2:#B7B4AC; --rule:#35312B; --soft:#28251F;
  --muted:#8E8A80; --accent:#E8843C;
}
*{box-sizing:border-box}
body{background:var(--paper);color:var(--ink);font-family:var(--sans);margin:0;padding:40px 20px 90px;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:1100px;margin:0 auto}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);margin:0 0 10px}
h1{font-family:var(--cond);font-weight:700;font-size:clamp(26px,4vw,38px);line-height:1.1;margin:0 0 10px;text-wrap:balance}
.lede{font-size:15px;color:var(--ink2);max-width:68ch;margin:0}
.lede b{color:var(--ink);font-weight:600}
h2.sh{font-family:var(--cond);font-weight:700;font-size:19px;margin:44px 0 4px}
.note{font-size:13.5px;color:var(--ink2);max-width:66ch;margin:0 0 14px}

.duo{display:grid;grid-template-columns:1fr;gap:20px;margin-top:14px}
@media(min-width:900px){.duo{grid-template-columns:1fr 1fr}}
figure{margin:0}
figcaption{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:0 0 8px}
figcaption b{color:var(--ink);font-weight:600}
.pg{background:var(--sheet);border:1px solid var(--rule);padding:38px 44px 30px;max-width:100%}
.mast{display:flex;justify-content:space-between;font-family:var(--mono);font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);padding-bottom:12px;border-bottom:1.5px solid var(--ink)}
.mast .brand{color:var(--ink);font-weight:600;letter-spacing:.26em}
.drop{display:block;width:100%;height:auto;overflow:visible}
.drop path{fill:none;stroke:var(--accent);stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}
.drop .dropdot{fill:var(--sheet);stroke:var(--accent);vector-effect:non-scaling-stroke}
.drop.thin{margin-top:14px;height:46px}
.reg{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:9px 0 0}
.reg .m{color:var(--ink);font-weight:600}
.hl-a{font-family:var(--cond);font-weight:700;font-size:27px;line-height:1.15;margin:20px 0 0;max-width:32ch}
.byline{font-family:var(--mono);font-size:11px;letter-spacing:.08em;color:var(--muted);margin:6px 0 0}

.strip{margin-top:14px;border-top:1.5px solid var(--ink)}
.row{display:grid;grid-template-columns:minmax(0,460px) 1fr;gap:8px 30px;align-items:center;padding:15px 0 13px;border-bottom:1px solid var(--rule)}
.row .drop.thin{height:38px;margin:0}
.row .reg{margin:0}
@media(max-width:760px){.row{grid-template-columns:1fr}}

.foot{margin-top:52px;padding-top:14px;border-top:1px solid var(--rule);font-family:var(--mono);font-size:11px;line-height:1.85;color:var(--muted)}
.foot b{color:var(--ink);font-weight:500}
</style>

<main class="wrap">
  <p class="eyebrow">Fluxus Capital · 复盘视觉 · 落点定稿</p>
  <h1>加粗 + 空心圆落点，删掉副标题</h1>
  <p class="lede">线的算法不变（SPX 21 个交易日，弧长归一 1.000 m）。落点用一个<b>空心圆</b>标住今天收在哪——描边同线色，中心镂空到卡片底色，不是实心点。粗细不再是固定数字，是按当天曲线的高度解出来的，保证不管哪天的形状多陡，线在版面上的分量看起来都一样。标题正下方那行副标题删掉。</p>

  <h2 class="sh">现在 vs 定稿 · 9/11</h2>
  <p class="note">同一份真实数据，唯一变量是线和落点。</p>
  <div class="duo">
    <figure><figcaption>现在</figcaption><div class="pg">__BEFORE__</div></figure>
    <figure><figcaption><b>定稿</b></figcaption><div class="pg">__AFTER__</div></figure>
  </div>

  <h2 class="sh">五期，同一套规矩</h2>
  <p class="note">粗细公式跟着每天的曲线高度走，落点位置就是当天收盘的位置——不额外编码任何行情数字。</p>
  <div class="strip">__DAYS__</div>

  <div class="foot">
    源头 · <b>Fluxus_Brand/visual/explorations/recap_ab_2026-09-04/build_recap.py</b> 与
    <b>recap_ab_2026-09-11/build_recap_0911.py</b> 的 <b>drop_svg()</b>／<b>bold_stroke()</b>，CSS 新增 <b>.dropdot</b>。分支 design/marketing-visual<br>
    落地 · pipeline 侧对应改 <b>recap_page.js</b> 的 dropSvg()（加 dot 参数 + 按 H 解粗细）与 <b>recap_visual.css</b>（加 .dropdot 规则）；模板里去掉 byline 段落
  </div>
</main>
"""

before = page("2026-09-11", True)
after = page("2026-09-11", False)
days = "".join(
    f'<div class="row">{drop_svg(WINDOWS[D], bold_stroke(WINDOWS[D]["H"]), "thin", dot=True, label=D)}'
    f'{reg(WINDOWS[D], D[5:].replace("-", ""))}</div>'
    for D in ["2026-09-04", "2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"]
)

html = (TEMPLATE.replace("__BEFORE__", before).replace("__AFTER__", after).replace("__DAYS__", days))
out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "final_form_preview.html"
out.write_text(html)
print(out, len(html))
