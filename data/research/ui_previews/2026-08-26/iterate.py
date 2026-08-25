"""Two more rounds on v1, the 11/12 winner. It lost its point on
「让推理被看懂」: it says how far behind, never what today is, so the reader
still has to hold a date in their head to use it.
"""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
wl = json.load(open(ROOT / "data/output/watchlist.json"))
N = f"{wl['universe_gated']:,}"
GATE = "cap ≥ $1B · $vol ≥ $20M"
FRESH = dict(date="2026-08-24", today="2026-08-24", behind=0)
STALE = dict(date="2026-08-21", today="2026-08-25", behind=3)
SW = ('<div class="switches"><span class="sw">3M pool</span>'
      '<span class="sw">52w high only</span><span class="sw">RS ≥ 70</span>'
      '<span class="sw">exclude healthcare</span></div>')

# round 1 -- name today as well, still one line
def v1a(s):
    t = "" if not s["behind"] else (f' · <span class="age">落后 {s["behind"]} 个交易日</span>'
                                    f'（今天 {s["today"]}）')
    return f'<p class="prov">{s["date"]} 收盘 · {N} 只过闸（{GATE}）{t}</p>'

# round 2 -- the age leads, because it changes how everything below is read
def v1b(s):
    if not s["behind"]:
        return f'<p class="prov">{s["date"]} 收盘 · {N} 只过闸（{GATE}）</p>'
    return (f'<p class="prov"><span class="age">落后 {s["behind"]} 个交易日</span> · '
            f'{s["date"]} 收盘（今天 {s["today"]}） · {N} 只过闸（{GATE}）</p>')

for fn, name, blurb in [
    (v1a, "v1a", "第 1 轮：把「今天」也写出来，读者不必自己记日期。仍是一行，静默时仍是零字。"),
    (v1b, "v1b", "第 2 轮：落后天数**移到行首**。一张三天前的单子会改变下面每一格的读法，"
                 "所以它该在名单之前被读到，而不是在出处的末尾。仍是一行、仍无新颜色、仍在当天数据时完全消失。"),
]:
    h = (f'<!doctype html><meta charset="utf-8"><title>Watchlist provenance · {name}</title>'
         f'<link rel="stylesheet" href="_shared.css">'
         f'<h1>Watchlist → 出处行 · {name}（v1 的迭代）</h1><p class="sub">{blurb}</p>')
    h += f'<div class="case"><h2>当天数据（落后 0）</h2>{fn(FRESH)}{SW}</div>'
    h += f'<div class="case"><h2>08-24 断更那三天</h2>{fn(STALE)}{SW}</div>'
    (HERE / f"provenance_{name}.html").write_text(h, encoding="utf-8")
    print("wrote", f"provenance_{name}.html")
