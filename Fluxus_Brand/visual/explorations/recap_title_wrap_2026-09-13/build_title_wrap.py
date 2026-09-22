#!/usr/bin/env python3
"""Why the recap title breaks mid-column: text-wrap:balance vs normal wrap vs a break at the title's own dash.
Real titles from the local issue packs (never in git). Print column 704px, .hl-a at 21.84pt as in recap_local.css.

    python3 build_title_wrap.py <issues_root> <out.html>
"""
import html
import json
import re
import sys

ROOT, OUT = sys.argv[1], sys.argv[2]
ISSUES = [("2026-09-08", "09-08 日刊"), ("2026-09-09", "09-09 日刊"), ("2026-09-10", "09-10 日刊"),
          ("2026-09-11", "09-11 日刊"), ("2026-W37", "W37 周刊")]
DASH = re.compile(r"(——|\s?—\s?)")


def dash_break(t):
    m = DASH.search(t)
    if not m:
        return f'<span class="seg">{html.escape(t)}</span>'
    a, b = t[:m.start()].rstrip(), t[m.end():].lstrip()
    a += "——" if m.group(1) == "——" else "\u00a0—"   # the dash stays glued to the word before it
    gap = "<wbr>" if m.group(1) == "——" else " "   # no visible space after a Chinese dash
    return f'<span class="seg">{html.escape(a)}</span>{gap}<span class="seg">{html.escape(b)}</span>'


def cell(t, mode, lang):
    body = dash_break(t) if mode == "dash" else html.escape(t)
    return f'<div class="col"><h2 class="hl-a {mode}" lang="{"zh-Hans" if lang == "ZH" else "en"}">{body}</h2></div>'


rows = ""
for iss, label in ISSUES:
    for lang in ("EN", "ZH"):
        t = json.load(open(f"{ROOT}/{iss}/pack/content_{lang}.json", encoding="utf-8"))["title"]
        rows += (f'<div class="row"><p class="k">{label} · {"英文" if lang == "EN" else "中文"}</p>'
                 f'{cell(t, "balance", lang)}{cell(t, "pretty", lang)}{cell(t, "dash", lang)}</div>')

PAGE = """<title>标题折行</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@600;700&display=swap">
<style>
:root{
  --paper:#F2F1ED; --sheet:#FBFAF7; --ink:#1A1917; --ink2:#4A463F; --rule:#D9D6CD; --muted:#8A857A; --accent:#D1600F;
  --sans:"IBM Plex Sans",-apple-system,"PingFang SC",sans-serif;
  --cond:"IBM Plex Sans Condensed","IBM Plex Sans","Hiragino Sans GB","PingFang SC","Noto Sans SC",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;
}
@media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){
  --paper:#12110F; --sheet:#1A1917; --ink:#E9E7E2; --ink2:#B7B4AC; --rule:#35312B; --muted:#8E8A80; --accent:#E8843C;
}}
:root[data-theme="dark"]{
  --paper:#12110F; --sheet:#1A1917; --ink:#E9E7E2; --ink2:#B7B4AC; --rule:#35312B; --muted:#8E8A80; --accent:#E8843C;
}
*{box-sizing:border-box}
body{background:var(--paper);color:var(--ink);font-family:var(--sans);margin:0;padding:40px 20px 90px;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);margin:0 0 10px}
h1{font-family:var(--cond);font-weight:700;font-size:clamp(26px,4vw,38px);line-height:1.1;margin:0 0 12px;text-wrap:balance}
.lede{font-size:15px;color:var(--ink2);max-width:70ch;margin:0 0 8px}
.lede b{color:var(--ink);font-weight:600}
.head,.row{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px 18px}
.head{position:sticky;top:0;background:var(--paper);padding:14px 0 8px;margin-top:26px;border-bottom:1.5px solid var(--ink);z-index:1}
.head div{font-family:var(--mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.head b{display:block;color:var(--ink);font-weight:600;letter-spacing:.06em}
.row{padding:12px 0 14px;border-bottom:1px solid var(--rule)}
.k{grid-column:1/-1;font-family:var(--mono);font-size:11px;letter-spacing:.12em;color:var(--muted);margin:0}
.col{background:var(--sheet);border:1px solid var(--rule);overflow:hidden}
/* each cell is the real 704px print column, shown at half size */
.hl-a{width:704px;zoom:.5;font-family:var(--cond);font-weight:700;font-size:21.84pt;line-height:1.18;letter-spacing:-.01em;margin:0;padding:10px 0;color:var(--ink);box-shadow:inset -3px 0 0 var(--accent)}
.hl-a.balance{text-wrap:balance}
.hl-a.pretty{text-wrap:pretty}
.hl-a.pretty:lang(zh-Hans){word-break:keep-all}
.hl-a.dash .seg{display:inline-block;max-width:100%;text-wrap:pretty}
.hl-a.dash:lang(zh-Hans){word-break:keep-all}
@media(max-width:760px){.head,.row{grid-template-columns:1fr}.head div:not(:first-child){display:none}}
.foot{margin-top:40px;font-family:var(--mono);font-size:11px;line-height:1.85;color:var(--muted)}
.foot b{color:var(--ink);font-weight:500}
</style>
<main class="wrap">
  <p class="eyebrow">Fluxus Capital · 复盘视觉 · 主标题</p>
  <h1>标题为什么会在中间折行</h1>
  <p class="lede">标题样式开着<b>平衡折行</b>（<code>text-wrap: balance</code>）：一行放不下时，浏览器把两行排成差不多一样长，所以第一行排到版心一半多一点就折下来，右边空一块。</p>
  <p class="lede">中文不是没有这个问题，是<b>中文标题字少，多数一行就放得下</b>。9/11 的中文同样超了一行，一样在中间折，而且折在「硬｜件」两个字中间。英文同样意思要长出一大截，所以几乎每期都触发。</p>
  <p class="lede">右侧橙色竖线是版心右边界。每格都是打印版心原宽 704px，缩到一半显示。</p>
  <div class="head"><div><b>现在</b>平衡折行</div><div><b>排满 + 防孤字</b>一行排满再折，末行不留一两个词；中文不拆词</div><div><b>破折号处折行 · 推荐</b>放不下时破折号前后各一行；前半句自己超过一行，退回排满 + 防孤字</div></div>
  __ROWS__
  <script>
  /* the fallback: a first half that wraps by itself fills the column, so the dash break would cost a third line */
  (document.fonts ? document.fonts.ready : Promise.resolve()).then(function () {
    document.querySelectorAll(".hl-a.dash").forEach(function (h) {
      var s = h.querySelector(".seg");
      if (h.querySelectorAll(".seg").length > 1 && s.offsetWidth >= h.clientWidth - 2) {
        h.textContent = h.textContent;   /* flatten; the no-break space keeps the dash on its word */
        h.classList.replace("dash", "pretty");
      }
    });
  });
  </script>
  <p class="foot">产线位置 · <b>recap_visual.css</b> 的 <b>.hl-a{text-wrap:balance}</b> · 标题拼接在 <b>recap_page.js</b> sheet-1 模板（<b>&lt;h2 class="hl-a"&gt;</b>）· 字体栈同打印，浏览器里的中文字重可能与 PDF 略有出入</p>
</main>
"""
open(OUT, "w", encoding="utf-8").write(PAGE.replace("__ROWS__", rows))
print(OUT)
