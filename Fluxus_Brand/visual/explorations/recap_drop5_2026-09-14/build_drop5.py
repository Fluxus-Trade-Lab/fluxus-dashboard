#!/usr/bin/env python3
"""The 5-session drop line (Andy 09-14) — what OPS shipped vs the two calls handed to Visual Vera:
① height: the x span drops from 20 to 10 so the line keeps its old presence, capped at 160px tall;
② which closes: one trading day = one segment — daily draws 6 closes (5 moves, the last in accent),
   weekly draws last week's final close + this week's sessions, so the line matches its date label.
Geometry mirrors recap_page.js dropLine()/tailPaths(); real SPX closes from origin/main.

    python3 build_drop5.py <issues_root> <out.html>
"""
import datetime as dt
import html
import json
import math
import subprocess
import sys

ROOT, OUT = sys.argv[1], sys.argv[2]
REPO = "/Users/taolezhu/Documents/AI-Trading-System"
raw = subprocess.run(["git", "-C", REPO, "show", "origin/main:data/output/breadth.json"], capture_output=True, check=True).stdout
ROWS = [(r["date"], r["spx_close"]) for r in json.loads(raw)["history"]["rows"] if r.get("spx_close")]
IDX = {d: i for i, (d, _) in enumerate(ROWS)}
PAD, DOT, CAP = 6, 4.5, 160
NOW_SPAN, NEW_SPAN = 20.0, 10.0


def geometry(closes, span):
    p0 = closes[0]
    step = span / (len(closes) - 1)
    P = [(k * step, -math.log(p / p0) * 100) for k, p in enumerate(closes)]
    for _ in range(3):
        o = [P[0]]
        for a, c in zip(P, P[1:]):
            o.append((a[0] * .75 + c[0] * .25, a[1] * .75 + c[1] * .25))
            o.append((a[0] * .25 + c[0] * .75, a[1] * .25 + c[1] * .75))
        o.append(P[-1])
        P = o
    xs = [q[0] for q in P]
    ys = [q[1] for q in P]
    k = 1000 / (max(xs) - min(xs))
    pts = [((x - min(xs)) * k, (y - min(ys)) * k) for x, y in P]
    return pts, (max(ys) - min(ys)) * k, len(closes)


def path(pts):
    return "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def rendered_px(h):
    return 704 * 0.84 * (h + 2 * PAD) / (1000 + 2 * PAD)


SEQ = [0]


def svg(closes, span, tail, cap):
    pts, h, n = geometry(closes, span)
    if tail and n > 2:
        cut = 1000 * (n - 2) / (n - 1)
        old, last = [], []
        for i, q in enumerate(pts):
            if q[0] <= cut:
                old.append(q)
            if q[0] >= cut:
                last.append(q)
            if i + 1 < len(pts) and q[0] < cut < pts[i + 1][0]:
                r = pts[i + 1]
                m = (cut, q[1] + (r[1] - q[1]) * (cut - q[0]) / (r[0] - q[0]))
                old.append(m)
                last.append(m)
        SEQ[0] += 1
        gid = f"tail{SEQ[0]}"
        line = (f'<defs><linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{cut:.1f}" y2="0">'
                f'<stop offset="0" style="stop-color:var(--muted);stop-opacity:.12"/><stop offset="1" style="stop-color:var(--muted);stop-opacity:1"/></linearGradient></defs>'
                f'<path style="stroke-width:2.5;stroke:url(#{gid})" d="{path(old)}"/><path style="stroke-width:2.5" d="{path(last)}"/>')
    else:
        line = f'<path style="stroke-width:2.5" d="{path(pts)}"/>'
    ex, ey = pts[-1]
    r = DOT * (1000 + 2 * PAD) / (704 * 0.84)
    style = f' style="max-height:{CAP}px"' if cap else ""
    return (f'<svg class="drop thin" viewBox="{-PAD} {-PAD} {1000 + 2 * PAD} {h + 2 * PAD:.1f}"{style} role="img" aria-label="SPX drop line">'
            f'{line}<circle class="dropdot" style="stroke-width:2.5" cx="{ex:.1f}" cy="{ey:.1f}" r="{r:.2f}"/></svg>'), h


def week_sessions(D):
    y, w, _ = dt.date.fromisoformat(D).isocalendar()
    return [d for d, _ in ROWS if dt.date.fromisoformat(d).isocalendar()[:2] == (y, w) and d <= D]


def closes_for(kind, D, scheme):
    i = IDX[D]
    if scheme == "now":
        return [c for _, c in ROWS[i - 4:i + 1]]
    if kind == "daily":
        return [c for _, c in ROWS[i - 5:i + 1]]
    first = IDX[week_sessions(D)[0]]
    return [c for _, c in ROWS[first - 1:i + 1]]


def title(iss):
    try:
        return json.load(open(f"{ROOT}/{iss}/pack/content_EN.json", encoding="utf-8"))["title"]
    except OSError:
        return None


CASES = [("daily", "2026-09-08", "2026-09-08", "09-08 日刊"), ("daily", "2026-09-09", "2026-09-09", "09-09 日刊"),
         ("daily", "2026-09-10", "2026-09-10", "09-10 日刊"), ("daily", "2026-09-11", "2026-09-11", "09-11 日刊"),
         ("weekly", "2026-09-11", "2026-W37", "W37 周刊 · 劳动节周，4 个交易日"),
         ("weekly", "2026-09-04", None, "W36 · 普通周示意（这周没出周刊，只为看 5 个交易日的周）")]


def sheet(kind, D, iss, scheme):
    cl = closes_for(kind, D, scheme)
    s, h = svg(cl, NOW_SPAN if scheme == "now" else NEW_SPAN, kind == "daily", scheme == "new")
    if kind == "daily":
        reg = f'1m · drop <span class="m">#{D[5:]}</span> · SPX · ∫ = 1.000 m'
        mast = f"Daily Market Recap · No. {D[5:].replace('-', '')}"
    else:
        ws = week_sessions(D)
        wk = dt.date.fromisoformat(D).isocalendar()[1]
        reg = f'1m · drop <span class="m">Week{wk}</span> · {ws[0]} → {ws[-1]} · SPX · ∫ = 1.000 m'
        mast = f"Weekly Market Recap · No. W{wk}"
    t = title(iss) if iss else None
    hl = f'<h2 class="hl">{html.escape(t)}</h2>' if t else ""
    px = min(rendered_px(h), CAP) if scheme == "new" else rendered_px(h)
    capped = scheme == "new" and rendered_px(h) > CAP
    meta = f'{len(cl)} 个收盘 · 线高约 {px:.0f}px{" · 已封顶" if capped else ""}'
    return (f'<figure><div class="clip"><div class="pg"><div class="mast"><span class="brand">Fluxus Capital</span><span>{mast}</span></div>'
            f'{s}<p class="reg">{reg}</p>{hl}</div></div><figcaption>{meta}</figcaption></figure>')


def stats(n, span, cap=None):
    hs = sorted(rendered_px(geometry([c for _, c in ROWS[i - n + 1:i + 1]], span)[1]) for i in range(n - 1, len(ROWS)))
    q = lambda f: hs[min(len(hs) - 1, int(f * len(hs)))]
    shown = [min(x, cap) for x in hs] if cap else hs
    sq = lambda f: shown[min(len(shown) - 1, int(f * len(shown)))]
    over = sum(x > cap for x in hs) / len(hs) if cap else 0
    return sq(.5), sq(.9), max(shown), over


rows = "".join(f'<div class="case"><p class="k">{html.escape(lab)}</p>{sheet(kind, D, iss, "now")}{sheet(kind, D, iss, "new")}</div>'
               for kind, D, iss, lab in CASES)
s21, s5, s6 = stats(21, NOW_SPAN), stats(5, NOW_SPAN), stats(6, NEW_SPAN, CAP)
table = (f'<table class="st"><thead><tr><th></th><th>线高中位</th><th>线高 P90</th><th>最高</th><th>触顶比例</th></tr></thead><tbody>'
         f'<tr><td>原来 · 21 个收盘</td><td>{s21[0]:.0f}px</td><td>{s21[1]:.0f}px</td><td>{s21[2]:.0f}px</td><td>—</td></tr>'
         f'<tr><td>现在 · 5 个收盘 · 跨度 20</td><td>{s5[0]:.0f}px</td><td>{s5[1]:.0f}px</td><td>{s5[2]:.0f}px</td><td>—</td></tr>'
         f'<tr class="pick"><td>建议 · 6 个收盘 · 跨度 10 · 封顶 {CAP}px</td><td>{s6[0]:.0f}px</td><td>{s6[1]:.0f}px</td><td>{s6[2]:.0f}px</td><td>{s6[3]:.0%}</td></tr>'
         f'</tbody></table>')

PAGE = """<title>五日掉落线</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@600;700&display=swap">
<style>
:root{
  --paper:#F2F1ED; --sheet:#FBFAF7; --ink:#1A1917; --ink2:#4A463F; --rule:#D9D6CD; --muted:#8A857A; --accent:#D1600F;
  --sans:"IBM Plex Sans",-apple-system,"PingFang SC",sans-serif;
  --cond:"IBM Plex Sans Condensed","IBM Plex Sans",sans-serif;
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
.wrap{max-width:1100px;margin:0 auto}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);margin:0 0 10px}
h1{font-family:var(--cond);font-weight:700;font-size:clamp(26px,4vw,38px);line-height:1.1;margin:0 0 12px;text-wrap:pretty}
.lede{font-size:15px;color:var(--ink2);max-width:72ch;margin:0 0 8px}
.lede b{color:var(--ink);font-weight:600}
.calls{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:14px;margin:22px 0 8px}
.call{background:var(--sheet);border:1px solid var(--rule);padding:14px 16px}
.call h3{font-family:var(--cond);font-size:17px;margin:0 0 4px}
.call p{font-size:13.5px;color:var(--ink2);margin:0}
.call p b{color:var(--ink)}
.st{border-collapse:collapse;font-family:var(--mono);font-size:12px;font-variant-numeric:tabular-nums;margin:18px 0 4px;width:100%;max-width:720px}
.st th,.st td{text-align:right;padding:6px 10px;border-bottom:1px solid var(--rule)}
.st th:first-child,.st td:first-child{text-align:left}
.st th{color:var(--muted);font-weight:500;letter-spacing:.08em}
.st tr.pick td{color:var(--ink);font-weight:600}
.src{font-family:var(--mono);font-size:11px;color:var(--muted);margin:0 0 20px}
.head{display:grid;grid-template-columns:1fr 1fr;gap:18px;border-bottom:1.5px solid var(--ink);padding:10px 0 6px;position:sticky;top:0;background:var(--paper);z-index:1}
.head div{font-family:var(--mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.head b{color:var(--ink);font-weight:600}
.case{display:grid;grid-template-columns:1fr 1fr;gap:6px 18px;padding:12px 0 16px;border-bottom:1px solid var(--rule)}
.k{grid-column:1/-1;font-family:var(--mono);font-size:11px;letter-spacing:.1em;color:var(--muted);margin:0}
figure{margin:0}
figcaption{font-family:var(--mono);font-size:10.5px;color:var(--muted);margin-top:4px}
.clip{overflow:hidden;border:1px solid var(--rule);background:var(--sheet)}
.pg{width:794px;padding:28px 45px 22px;zoom:.66}
.mast{display:flex;justify-content:space-between;font-family:var(--mono);font-size:11.7px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);padding-bottom:12px;border-bottom:1.5px solid var(--ink)}
.mast .brand{color:var(--ink);font-weight:600;letter-spacing:.26em}
.drop{display:block;overflow:visible}
.drop path{fill:none;stroke:var(--accent);stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}
.drop .dropdot{fill:var(--sheet);stroke:var(--accent);vector-effect:non-scaling-stroke}
.drop.thin{margin:18px auto 0;width:84%;height:auto}
.reg{font-family:var(--mono);font-size:11.2px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:9px 0 0}
.reg .m{color:var(--ink);font-weight:600}
.hl{font-family:var(--cond);font-weight:700;font-size:29px;line-height:1.12;margin:18px 0 0;text-wrap:pretty}
@media(max-width:760px){.head,.case{grid-template-columns:1fr}.pg{zoom:.45}}
</style>
<main class="wrap">
  <p class="eyebrow">Fluxus Capital · 复盘视觉 · 掉落线 5 个交易日</p>
  <h1>五日线：留给视觉线判的两件事</h1>
  <p class="lede">Andy 定了「最近 5 个交易日；日报最后一天橙、前面渐变灰；周报全橙；标签写日期或周」，产线已落地。下面两件他没说，OPS 交给我判。左栏是产线现在的样子，右栏是建议。</p>
  <div class="calls">
    <div class="call"><h3>① 线变平了，要加高</h3><p>5 个点沿用 21 个点的横向跨度，线高中位只剩 21 日版的三分之一左右。<b>跨度从 20 改成 10</b>，常见的周回到原来那种分量；<b>高度封顶 160px</b>，剧烈的周形状照画、整体缩小，不会把标题挤下去。比例每期都一样，平的周就是平的。</p></div>
    <div class="call"><h3>② 一天 = 一段，线才对得上标签</h3><p>5 个收盘只连出 4 段涨跌。<b>日报画 6 个收盘</b>（5 段，橙色正好是最后一天那段）；<b>周报画「上周最后一个收盘 + 本周每个交易日」</b>——普通周 6 个点，W37 劳动节周 5 个点（09-04 是起点，不是一个交易日），和 <code>09-08 → 09-11</code> 的标签完全一致。</p></div>
  </div>
  __TABLE__
  <p class="src">线高 = 打印版心 704px × 84% 下的渲染高度 · 样本：origin/main breadth.json 全部 SPX 收盘（2026-04-21 → 09-11，100 个交易日，偏平静，剧烈周的真实触顶比例会更高）</p>
  <div class="head"><div><b>现在</b> · 5 个收盘 · 跨度 20</div><div><b>建议</b> · 一天一段 · 跨度 10 · 封顶 160px</div></div>
  __ROWS__
</main>
"""
open(OUT, "w", encoding="utf-8").write(PAGE.replace("__TABLE__", table).replace("__ROWS__", rows))
print(OUT, "| stats n21", [round(x) for x in s21[:3]], "n5", [round(x) for x in s5[:3]], "n6/10 cap", [round(x) for x in s6[:3]], f"{s6[3]:.0%}")
