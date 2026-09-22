#!/usr/bin/env python3
"""Recap masthead, Andy 09-13 final: the drop line keeps its 2.5px weight and takes the centre of its band
(84% of the column, height follows the curve), a hollow dot marks today's close, the subtitle is gone.
Real SPX windows from origin/main (drop_windows.json, computed like recap_page.js dropLine()).

    python3 build_final_form.py [out.html]
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SP = Path("/private/tmp/claude-501/-Users-taolezhu-Documents-AI-Trading-System-Fluxus-Marketing-Visual-Design/ee3710aa-d552-414c-9357-4584bfc6459a/scratchpad")
WINDOWS = json.loads((SP / "drop_windows.json").read_text())
DAYS = ["2026-09-04", "2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"]
PAD = 6
COL = 704            # A4 print column, css px
WIDTH = 0.84         # share of the column the line takes
DOT = 4.5            # default hollow-dot radius, rendered px

TITLE = "A Hot Core Print Gets Bought — AI Hardware Runs, the Average Stock Doesn't"
SUB = "Four-day slide ends · HPE/DELL +12% · RSP and IWM still under the 50-day · Friday, September 11, 2026"
BIG = ("Four down days ended with a gap up that stuck: <b>SPY +0.85%, QQQ +0.87%, both back above the 50-day</b> — on a CPI "
       "print that ran hot, core +0.3% m/m against 0.2% expected. Bad data, higher prices: next week's hike was already "
       "priced near 90%, and once December odds slipped under 49% the uncertainty was gone.")


def drop_svg(w, cls, dot=0.0):
    ex, ey = w["d"].split()[-1].split(",")
    r = dot * (1000 + 2 * PAD) / (COL * WIDTH)
    mark = f'<circle class="dropdot" style="stroke-width:2.5" cx="{ex}" cy="{ey}" r="{r:.2f}"/>' if dot else ""
    return (f'<svg class="drop {cls}" viewBox="{-PAD} {-PAD} {1000 + 2 * PAD} {w["H"] + 2 * PAD:.1f}" role="img" '
            f'aria-label="SPX drop line, 21 sessions to {w["D"]}"><path style="stroke-width:2.5" d="{w["d"]}"/>{mark}</svg>')


def reg(w):
    tag = w["D"][5:].replace("-", "")
    return (f'<p class="reg">1m · drop <span class="m">#{tag}</span> · {w["D0"]} → {w["D"]} · SPX · '
            f'∫ = {w["arc"]:.3f} m</p>')


def page(before, dot=DOT, body=True):
    w = WINDOWS["2026-09-11"]
    line = drop_svg(w, "old") if before else drop_svg(w, "new", dot)
    sub = f'<p class="byline">{SUB}</p>' if before else ""
    big = f'<div class="sec"><h3>The Big Picture</h3><p>{BIG}</p></div>' if body else ""
    return (f'<div class="mast"><span class="brand">Fluxus Capital</span><span>Daily Market Recap · No. 0911</span></div>'
            f'{line}{reg(w)}<h2 class="hl-a">{TITLE}</h2>{sub}{big}')


TEMPLATE = r"""<title>掉落线定稿</title>
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
.wrap{max-width:1160px;margin:0 auto}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);margin:0 0 10px}
h1{font-family:var(--cond);font-weight:700;font-size:clamp(26px,4vw,38px);line-height:1.1;margin:0 0 10px;text-wrap:balance}
.lede{font-size:15px;color:var(--ink2);max-width:68ch;margin:0}
.lede b{color:var(--ink);font-weight:600}
h2.sh{font-family:var(--cond);font-weight:700;font-size:20px;margin:48px 0 4px}
.note{font-size:13.5px;color:var(--ink2);max-width:68ch;margin:0 0 14px}
figure{margin:0}
figcaption{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:0 0 8px}
figcaption b{color:var(--ink);font-weight:600}

/* the recap sheet at print scale: A4 794px, 45px margins → 704px column */
.pg{width:794px;background:var(--sheet);border:1px solid var(--rule);padding:38px 45px 30px}
.mast{display:flex;justify-content:space-between;font-family:var(--mono);font-size:11.7px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);padding-bottom:12px;border-bottom:1.5px solid var(--ink)}
.mast .brand{color:var(--ink);font-weight:600;letter-spacing:.26em}
.drop{display:block;overflow:visible}
.drop path{fill:none;stroke:var(--accent);stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}
.drop .dropdot{fill:var(--sheet);stroke:var(--accent);vector-effect:non-scaling-stroke}
.drop.old{width:100%;height:46px;margin-top:14px}
.drop.new{width:84%;height:auto;margin:22px auto 4px}
.reg{font-family:var(--mono);font-size:11.2px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:9px 0 0}
.reg .m{color:var(--ink);font-weight:600}
.hl-a{font-family:var(--cond);font-weight:700;font-size:29px;line-height:1.14;margin:22px 0 0;max-width:30ch}
.byline{font-family:var(--mono);font-size:12.3px;letter-spacing:.04em;color:var(--muted);margin:6px 0 0}
.sec{border-top:1.5px solid var(--ink);margin-top:20px;padding-top:12px}
.sec h3{font-family:var(--mono);font-size:12.3px;letter-spacing:.22em;text-transform:uppercase;margin:0 0 8px}
.sec p{font-size:14px;line-height:1.45;margin:0;color:var(--ink2)}
.sec p b{color:var(--ink)}

.duo{display:grid;grid-template-columns:1fr;gap:22px;margin-top:16px}
@media(min-width:1100px){.duo{grid-template-columns:1fr 1fr}}
.clip{overflow:hidden;max-width:100%}
.duo .pg{zoom:.7}
@media(max-width:1099px){.duo .pg{zoom:.85}}
@media(max-width:720px){.duo .pg{zoom:.42}}

.feed{display:flex;flex-wrap:wrap;gap:22px;margin-top:14px}
.phone{width:380px;max-width:100%;background:var(--sheet);border:1px solid var(--rule);padding:12px 10px 10px}
.phone .who{font:600 12.5px/1.3 var(--sans);margin:0 0 2px}
.phone .who span{color:var(--muted);font-weight:400}
.phone .txt{font-size:12.5px;color:var(--ink2);margin:0 0 8px;line-height:1.4}
.phone .shot{height:290px;overflow:hidden;border:1px solid var(--rule);border-radius:12px}
.phone .pg{zoom:.453;border:0}

.sizes{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px;margin-top:14px}
.card{background:var(--sheet);border:1px solid var(--rule);padding:14px 16px 12px}
.card.pick{border-color:var(--ink)}
.card .tag{font-family:var(--mono);font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:0 0 6px}
.card .tag b{color:var(--ink)}
.card .col{width:704px;zoom:.48}

.days{margin-top:14px;border-top:1.5px solid var(--ink)}
.day{display:grid;grid-template-columns:auto 1fr;gap:8px 28px;align-items:center;padding:12px 0;border-bottom:1px solid var(--rule)}
.day .col{width:704px;zoom:.62}
.day .drop.new{margin:6px auto}
.day .reg{margin:0}
@media(max-width:900px){.day{grid-template-columns:1fr}.day .col{zoom:.45}}

.foot{margin-top:52px;padding-top:14px;border-top:1px solid var(--rule);font-family:var(--mono);font-size:11px;line-height:1.85;color:var(--muted)}
.foot b{color:var(--ink);font-weight:500}
</style>

<main class="wrap">
  <p class="eyebrow">Fluxus Capital · 复盘视觉 · 掉落线</p>
  <h1>线还是那根细线，只是站到版面中间来</h1>
  <p class="lede">粗细不变（2.5px），算法不变（SPX 21 个交易日，弧长 1.000 m）。线从原来 46px 高的窄条里放出来：<b>水平居中，占版心宽度的 84%，高度跟着当天曲线的形状走</b>，不再撑满整栏。收盘那一点画一个空心圆。标题下的副标题删掉。</p>

  <h2 class="sh">现在 vs 定稿 · 9/11 日刊第 1 页</h2>
  <div class="duo">
    <figure><figcaption>现在</figcaption><div class="clip"><div class="pg">__BEFORE__</div></div></figure>
    <figure><figcaption><b>定稿</b></figcaption><div class="clip"><div class="pg">__AFTER__</div></div></figure>
  </div>

  <h2 class="sh">X 信息流里的实际大小</h2>
  <p class="note">产线发 X 的是第 1 页的 p1.png（1460px 宽），手机上约 380px 宽显示，按这个比例缩的。</p>
  <div class="feed">
    <figure><figcaption>现在</figcaption><div class="phone"><p class="who">Fluxus Capital <span>@Fluxus_Z</span></p><p class="txt">Four down days ended with a gap up that stuck…</p><div class="shot"><div class="pg">__FEED_BEFORE__</div></div></div></figure>
    <figure><figcaption><b>定稿</b></figcaption><div class="phone"><p class="who">Fluxus Capital <span>@Fluxus_Z</span></p><p class="txt">Four down days ended with a gap up that stuck…</p><div class="shot"><div class="pg">__FEED_AFTER__</div></div></div></figure>
  </div>

  <h2 class="sh">空心圆大小</h2>
  <p class="note">半径按打印版面的像素算，描边与线同为 2.5px。默认中间那档，换档只改一个数。</p>
  <div class="sizes">__SIZES__</div>

  <h2 class="sh">五期，同一套规矩</h2>
  <p class="note">宽度固定 84%，高度随形状：平的月份矮，陡的月份高。</p>
  <div class="days">__DAYS__</div>

  <div class="foot">
    源头 · <b>recap_ab_2026-09-04/build_recap.py</b> 与 <b>recap_ab_2026-09-11/build_recap_0911.py</b> 的 <b>drop_svg(…, dot=DOT_PX)</b>，CSS <b>.drop.thin</b> 改为 84% 宽居中、高度自适应，新增 <b>.drop .dropdot</b> · 分支 design/marketing-visual
  </div>
</main>
"""

sizes = "".join(
    f'<div class="card{" pick" if r == DOT else ""}"><p class="tag">半径 <b>{r}px</b>{" · 默认" if r == DOT else ""}</p>'
    f'<div class="col">{drop_svg(WINDOWS["2026-09-11"], "new", r)}{reg(WINDOWS["2026-09-11"])}</div></div>'
    for r in (3.5, DOT, 6.0))
days = "".join(
    f'<div class="day"><div class="col">{drop_svg(WINDOWS[D], "new", DOT)}</div>{reg(WINDOWS[D])}</div>' for D in DAYS)
html = (TEMPLATE.replace("__BEFORE__", page(True)).replace("__AFTER__", page(False))
        .replace("__FEED_BEFORE__", page(True)).replace("__FEED_AFTER__", page(False))
        .replace("__SIZES__", sizes).replace("__DAYS__", days))
out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "final_form_preview.html"
out.write_text(html)
print(out, len(html))
