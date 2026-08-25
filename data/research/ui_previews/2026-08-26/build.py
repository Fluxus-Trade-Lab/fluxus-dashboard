"""Four takes on the Watchlist provenance line, rendered in the two states
that matter: current (must stay quiet) and the 2026-08-24 blackout
(data/output sat at 08-21 for three days while the page rendered normally).

Real values only: date/universe_gated/gate read from data/output/watchlist.json.
Tokens come from _shared.css, lifted verbatim from frontend/src/index.css.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
wl = json.load(open(ROOT / "data/output/watchlist.json"))
N = f"{wl['universe_gated']:,}"
GATE = "cap ≥ $1B · $vol ≥ $20M"

FRESH = dict(date="2026-08-24", today="2026-08-24", behind=0)
STALE = dict(date="2026-08-21", today="2026-08-25", behind=3)   # the 08-24 blackout

SWITCHES = ('<div class="switches">'
            '<span class="sw">3M pool</span><span class="sw">52w high only</span>'
            '<span class="sw">RS ≥ 70</span><span class="sw">exclude healthcare</span></div>')

def head(c):
    return f"""<!doctype html><meta charset="utf-8">
<title>Watchlist provenance · {c['name']}</title>
<link rel="stylesheet" href="_shared.css">
<h1>Watchlist → 出处行 · {c['name']}</h1>
<p class="sub">{c['blurb']}</p>"""

def case(label, body):
    return f'<div class="case"><h2>{label}</h2>{body}{SWITCHES}</div>'

# ---- v0: what ships today -------------------------------------------------
def v0(s):
    return f'<p class="prov">{s["date"]} 收盘 · {N} 只过闸（{GATE}）</p>'

# ---- v1: same line, one more clause, only when behind ---------------------
def v1(s):
    tail = "" if not s["behind"] else f' · <span class="age">落后 {s["behind"]} 个交易日</span>'
    return f'<p class="prov">{s["date"]} 收盘 · {N} 只过闸（{GATE}）{tail}</p>'

# ---- v2: the reader's question is the content ----------------------------
def v2(s):
    if not s["behind"]:
        return f'<p class="prov">{s["date"]} 收盘 · {N} 只过闸（{GATE}）</p>'
    return (f'<p class="prov">{s["date"]} 收盘 · {N} 只过闸（{GATE}）</p>'
            f'<p class="second">今天是 <b>{s["today"]}</b>，这张单子是 <b>{s["date"]}</b> 的'
            f'——中间 {s["behind"]} 个交易日没有落地。</p>')

# ---- v3: the site's existing sentence, borrowed verbatim in shape ---------
def v3(s):
    if not s["behind"]:
        return f'<p class="prov">{s["date"]} 收盘 · {N} 只过闸（{GATE}）</p>'
    return (f'<p class="prov">{s["date"]} 收盘 · {N} 只过闸（{GATE}）</p>'
            f'<p class="second it rule">Not measured today — watchlist.json 已 {s["behind"]} '
            f'个交易日没有更新（last {s["date"]}）。上面是那一场的名单，不是今天的。</p>')

VARIANTS = [
    (v0, dict(name="v0 · 现状（对照组）",
              blurb="现在站上就是这一行。它说的是「哪一场收盘」，从不说「这是几天前的」。"
                    "2026-08-22 到 08-25，schema 闸把整场 commit 拦下，data/output 在 main 上停在 08-21——"
                    "这一行三天都读作「2026-08-21 收盘」，而页面照常渲染。")),
    (v1, dict(name="v1 · 同一行加一个从句",
              blurb="最小改动：当且仅当落后时，行尾多一句「落后 N 个交易日」。当天数据时一个字都不多。")),
    (v2, dict(name="v2 · 把读者的问题当内容",
              blurb="读者真正要问的是「这是今天的吗」。第二行把两个日期并排放，差额自己说话。")),
    (v3, dict(name="v3 · 照抄本站已有的那句话",
              blurb="TickBand 已经有这条规矩（『Not measured — tick_cycle.json has not updated in N days』），"
                    "TickerProvenance 也有（ageDays ≥ 3）。这一稿只是把同一句话搬到 Watchlist。")),
]

for fn, meta in VARIANTS:
    html = head(meta)
    html += case("当天数据（2026-08-24 收盘，落后 0）", fn(FRESH))
    html += case("08-24 断更那三天（单子停在 08-21，今天 08-25）", fn(STALE))
    out = HERE / f"provenance_{meta['name'].split(' ')[0]}.html"
    out.write_text(html, encoding="utf-8")
    print("wrote", out.name)
