#!/usr/bin/env python3
"""sketch 00 — glyph 语法 + 两条真实的线 (BE vs BABA)
从 sources/portfolio_2026-07-26.csv 直接取数，输出手绘感 SVG。
"""
import csv, math, random, datetime as dt
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE.parent / "sources" / "portfolio_2026-07-26.csv"
OUT = HERE / "sketch_00_glyph_grammar.svg"

rng = random.Random(20260722)

PAPER = "#f6f1e5"
INK = "#2f2b26"
RUST = "#a84b32"
LOSS_GREY = "#8d857a"
GREEN = "#4a6b52"
GOLD = "#b98c2c"

# ---------- data ----------
def load_trades():
    lines = list(csv.reader(open(SRC)))
    for i, l in enumerate(lines):
        if l and l[0] == "Ticker":
            header, start = l, i + 1
            break
    recs = [dict(zip(header, l)) for l in lines[start:] if l and l[0]]

    def d(s):
        if not s:
            return None
        return (dt.datetime.fromisoformat(s.replace("Z", "+00:00")).date()
                if "T" in s else dt.date.fromisoformat(s))

    out = []
    for x in recs:
        if x["Closed"] != "YES":
            continue
        e = float(x["Entry Price"]); q = float(x["Original Qty"])
        stop = float(x["Initial Stop"] or x["Stop Price"])
        sgn = 1 if x["Direction"] == "long" else -1
        pnl, last, trims = 0.0, None, 0
        for i in (1, 2, 3):
            if x.get(f"Trim{i} Date"):
                p = float(x[f"Trim{i} Price"]); tq = float(x[f"Trim{i} Qty"])
                pnl += sgn * (p - e) * tq
                last = d(x[f"Trim{i} Date"])
                trims += 1
        risk = abs(e - stop) * q
        r = pnl / risk if risk > 0 else 0.0
        out.append(dict(t=x["Ticker"], dir=x["Direction"], entry=d(x["Entry Date"]),
                        exit=last, pnl=pnl, r=r, trims=trims,
                        hold=(last - d(x["Entry Date"])).days))
    return out

# ---------- hand-feel primitives ----------
def jpath(pts, wobble=1.6):
    """jittered polyline -> smooth-ish path"""
    p = [(x + rng.uniform(-wobble, wobble), y + rng.uniform(-wobble, wobble)) for x, y in pts]
    dstr = f"M {p[0][0]:.1f} {p[0][1]:.1f}"
    for a, b in zip(p, p[1:]):
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        dstr += f" Q {a[0]:.1f} {a[1]:.1f} {mx:.1f} {my:.1f}"
    dstr += f" T {p[-1][0]:.1f} {p[-1][1]:.1f}"
    return dstr

def stem_pts(x, y0, y1, lean, n=6):
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((x + lean * t * 10 + 2.5 * math.sin(t * math.pi * 1.5), y0 + (y1 - y0) * t))
    return pts

def glyph(svg, x, base_y, tr, scale=1.0, gold=False):
    """one trade = one stitch-plant hanging from its thread"""
    hold_len = min(14 + tr["hold"] * 1.7, 190) * scale
    rad = max(3.0, min(3.0 + abs(tr["r"]) * 1.5, 24)) * scale
    lean = 1 if tr["dir"] == "long" else -1
    win = tr["pnl"] > 0
    color = GOLD if gold else (GREEN if win else (RUST if tr["r"] <= -1 else LOSS_GREY))
    tip_y = base_y + hold_len
    broken = tr["r"] <= -1

    if broken:  # stem with a break gap + bent tip
        gap = base_y + hold_len * 0.55
        svg.append(f'<path d="{jpath(stem_pts(x, base_y, gap, lean))}" fill="none" stroke="{color}" stroke-width="{1.6*scale:.1f}" stroke-linecap="round"/>')
        bend = [(x + lean * 6, gap + 6), (x + lean * 14, gap + hold_len * 0.25)]
        svg.append(f'<path d="{jpath([(x + lean*5, gap+5)] + bend)}" fill="none" stroke="{color}" stroke-width="{1.4*scale:.1f}" stroke-linecap="round" opacity="0.8"/>')
        tip_x, tip_y = x + lean * 14, gap + hold_len * 0.25
    else:
        svg.append(f'<path d="{jpath(stem_pts(x, base_y, tip_y, lean))}" fill="none" stroke="{color}" stroke-width="{1.7*scale:.1f}" stroke-linecap="round"/>')
        tip_x = x + lean * 10

    # bloom: two offset hand circles
    for k, (dx, dy, op) in enumerate([(0, 0, 0.9), (1.5, 1.2, 0.45)]):
        svg.append(f'<circle cx="{tip_x+dx:.1f}" cy="{tip_y+dy:.1f}" r="{rad:.1f}" fill="none" stroke="{color}" stroke-width="{1.5*scale:.1f}" opacity="{op}" transform="rotate({rng.uniform(-8,8):.0f} {tip_x:.1f} {tip_y:.1f})"/>')
    if win:
        svg.append(f'<circle cx="{tip_x:.1f}" cy="{tip_y:.1f}" r="{rad*0.45:.1f}" fill="{color}" opacity="{0.85 if gold else 0.55}"/>')
    # petals = trim legs
    for i in range(tr["trims"]):
        a = -math.pi / 2 + (i - 1) * 0.75 + rng.uniform(-0.1, 0.1)
        x1, y1 = tip_x + math.cos(a) * rad, tip_y + math.sin(a) * rad
        x2, y2 = tip_x + math.cos(a) * (rad + 10 * scale), tip_y + math.sin(a) * (rad + 10 * scale)
        svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{1.3*scale:.1f}" stroke-linecap="round"/>')
    return tip_x, tip_y

def note(svg, x, y, text, size=13, color=INK, anchor="start", op=0.85, style="italic"):
    svg.append(f'<text x="{x}" y="{y}" font-family="Georgia, \'Songti SC\', serif" font-style="{style}" font-size="{size}" fill="{color}" text-anchor="{anchor}" opacity="{op}">{text}</text>')

def arrow(svg, x1, y1, x2, y2):
    svg.append(f'<path d="{jpath([(x1,y1),((x1+x2)/2,(y1+y2)/2),(x2,y2)],0.8)}" fill="none" stroke="{INK}" stroke-width="0.8" opacity="0.55"/>')

# ---------- compose ----------
trades = load_trades()
be = sorted([t for t in trades if t["t"] == "BE"], key=lambda z: (z["entry"], z["exit"]))
baba = sorted([t for t in trades if t["t"] == "BABA"], key=lambda z: (z["entry"], z["exit"]))

W, H = 1500, 940
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Georgia, serif">',
       f'<rect width="{W}" height="{H}" fill="{PAPER}"/>']
# paper grain
for _ in range(240):
    gx, gy = rng.uniform(0, W), rng.uniform(0, H)
    svg.append(f'<circle cx="{gx:.0f}" cy="{gy:.0f}" r="{rng.uniform(0.3,0.9):.1f}" fill="{INK}" opacity="0.04"/>')

note(svg, 60, 70, "同一个动作 · The Same Gesture", 34, style="normal")
note(svg, 60, 100, "sketch 00 — glyph 语法，与两条真实的线 · data: 331 closed trades, 2025-12-31 → 2026-07-22", 15, op=0.6)
svg.append(f'<line x1="60" y1="118" x2="{W-60}" y2="118" stroke="{INK}" stroke-width="0.7" opacity="0.3"/>')

# ---- left: anatomy ----
ax, ay = 210, 240
note(svg, 60, 180, "一株 = 一笔交易", 20, style="normal")
demo = dict(t="DEMO", dir="long", pnl=30000, r=6.0, trims=3, hold=42, entry=None, exit=None)
svg.append(f'<line x1="{ax-90}" y1="{ay}" x2="{ax+90}" y2="{ay}" stroke="{INK}" stroke-width="1" opacity="0.35"/>')
tip = glyph(svg, ax, ay, demo, scale=2.2)
note(svg, ax + 105, ay + 8, "锚点 = 离场日（挂在时间线上）", 13)
arrow(svg, ax + 100, ay + 4, ax + 12, ay + 2)
note(svg, ax + 90, ay + 95, "茎长 = 持仓天数", 13)
arrow(svg, ax + 85, ay + 91, ax + 32, ay + 85)
note(svg, ax + 90, ay + 120, "茎的倾向 = long 右倾 / short 左倾", 13)
note(svg, tip[0] + 70, tip[1] - 20, "花冠半径 = |R|", 13)
arrow(svg, tip[0] + 65, tip[1] - 24, tip[0] + 30, tip[1] - 10)
note(svg, tip[0] + 70, tip[1] + 5, "花瓣 = 分批离场 1/2/3", 13)
note(svg, tip[0] + 70, tip[1] + 30, "实心 = 盈利 · 空心 = 亏损", 13)

# broken demo
bx, by = 210, 560
demo2 = dict(t="DEMO", dir="long", pnl=-8000, r=-1.0, trims=1, hold=6, entry=None, exit=None)
svg.append(f'<line x1="{bx-90}" y1="{by}" x2="{bx+90}" y2="{by}" stroke="{INK}" stroke-width="1" opacity="0.35"/>')
glyph(svg, bx, by, demo2, scale=2.2)
note(svg, bx + 80, by + 45, "断茎 = 被止损打出 (R ≤ −1)", 13, RUST)
note(svg, bx + 80, by + 68, "铁锈红 = 止损 · 灰 = 小亏", 13)

# color key
ky = 700
note(svg, 60, ky, "颜色", 20, style="normal")
for i, (c, label) in enumerate([(GREEN, "盈利 132 笔"), (LOSS_GREY, "小亏 (−1R…0)"), (RUST, "止损 (≤ −1R) 42 笔"), (GOLD, "扛起全部净利润的 31 笔 — 其余 300 笔加总 ≈ 0")]):
    yy = ky + 28 + i * 27
    svg.append(f'<circle cx="72" cy="{yy-5}" r="7" fill="none" stroke="{c}" stroke-width="2"/>')
    svg.append(f'<circle cx="72" cy="{yy-5}" r="3" fill="{c}" opacity="0.7"/>')
    note(svg, 92, yy, label, 14)

# ---- right: two real threads ----
rx0, rx1 = 620, W - 80
def xdate(day, d0, d1, x0=rx0, x1=rx1):
    return x0 + (day - d0).days / max((d1 - d0).days, 1) * (x1 - x0)

def spread(xs, min_gap=26):
    """nudge overlapping x positions apart, keep order"""
    out = []
    for x in sorted(xs):
        if out and x - out[-1] < min_gap:
            x = out[-1] + min_gap
        out.append(x)
    return out

# BE thread
ty = 260
d0, d1 = dt.date(2026, 1, 1), dt.date(2026, 7, 22)
note(svg, rx0, 180, "线 = 同一标的的重复进攻", 20, style="normal")
note(svg, rx0, 208, "BE — 16 次进攻。前 8 次：−$19,300。第 9 次：+$74,052。", 15, GREEN)
be = sorted(be, key=lambda z: z["exit"])
be_x = spread([xdate(t["exit"], d0, d1) for t in be])
pts = [(x, ty + rng.uniform(-4, 4)) for x in be_x]
svg.append(f'<path d="{jpath(pts, 1.2)}" fill="none" stroke="{INK}" stroke-width="0.9" opacity="0.4"/>')
big = max(be, key=lambda z: z["pnl"])
for t, x in zip(be, be_x):
    glyph(svg, x, ty, t, scale=0.95, gold=(t is big))
gx = be_x[be.index(big)]
note(svg, gx + 18, ty + 150, f"第 9 次 · +7.3R · ${big['pnl']:,.0f}", 13, GOLD)
note(svg, rx0, ty + 210, "同一个动作：被打出去，再打回来。趋势还在，所以它叫「坚持」。", 13, op=0.65)

# BABA thread
by2 = 600
note(svg, rx0, by2 - 60, "BABA — 5 次进攻，全败。−$54,418。持仓最长的三笔（102 / 99 / 93 天）都是它。", 15, RUST)
baba = sorted(baba, key=lambda z: z["exit"])
baba_x = spread([xdate(t["exit"], d0, d1) for t in baba], min_gap=42)
pts2 = [(x, by2 + rng.uniform(-4, 4)) for x in baba_x]
svg.append(f'<path d="{jpath(pts2, 1.2)}" fill="none" stroke="{RUST}" stroke-width="0.9" opacity="0.45"/>')
for t, x in zip(baba, baba_x):
    glyph(svg, x, by2, t, scale=0.95)
note(svg, rx0, by2 + 240, "同一个动作。论点已经坏了，所以它叫「固执」。入场那一刻，两者无法区分。", 13, op=0.65)

# month ticks
for m in range(1, 8):
    md = dt.date(2026, m, 1)
    mx = xdate(md, d0, d1)
    svg.append(f'<line x1="{mx:.0f}" y1="{H-90}" x2="{mx:.0f}" y2="{H-82}" stroke="{INK}" opacity="0.4"/>')
    note(svg, mx, H - 66, f"{m}月", 12, anchor="middle", op=0.5, style="normal")
svg.append(f'<line x1="{rx0}" y1="{H-90}" x2="{rx1}" y2="{H-90}" stroke="{INK}" stroke-width="0.7" opacity="0.35"/>')

note(svg, 60, H - 30, "Fluxus DataArt · sketch 00 · 数据：真实交易记录，无一虚构 · 胜率 39.9%，净利 +90.5%", 12, op=0.5)
svg.append("</svg>")
OUT.write_text("\n".join(svg))
print("wrote", OUT, len("\n".join(svg)), "bytes")
