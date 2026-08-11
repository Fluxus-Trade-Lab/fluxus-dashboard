#!/usr/bin/env python3
"""sketch 01 · 正面 — 园子:331 株全部种进七个月。
天气(天色带) + 品种(花形) + 生命周期(茎/花/落瓣入土) + 两段坏天气 + BE/BABA 两条线。
"""
import math, random, datetime as dt
from pathlib import Path
from collections import defaultdict
from art_data import load

rng = random.Random(331)
D = load()

PAPER, INK = "#f6f1e5", "#2f2b26"
GREEN, GOLD, RUST, GREY = "#4a6b52", "#b98c2c", "#a84b32", "#8d857a"
SOIL_C, COLD, WARM = "#6b5a44", "#6f8195", "#c9a227"

W, H = 2300, 1420
RX0, RX1 = 150, 2210
D0, D1 = dt.date(2025, 12, 29), dt.date(2026, 7, 24)
SKY0, SKY1 = 132, 540
GROUND = 1010
SOIL_MAX = 66

def X(day):
    return RX0 + (day - D0).days / (D1 - D0).days * (RX1 - RX0)

def lerp(a, b, t):
    return a + (b - a) * t

def mix(c1, c2, t):
    p = lambda c: (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16))
    a, b = p(c1), p(c2)
    return "#%02x%02x%02x" % tuple(int(lerp(a[i], b[i], t)) for i in range(3))

def jpath(pts, wob=1.5):
    p = [(x + rng.uniform(-wob, wob), y + rng.uniform(-wob, wob)) for x, y in pts]
    d = f"M {p[0][0]:.1f} {p[0][1]:.1f}"
    for a, b in zip(p, p[1:]):
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        d += f" Q {a[0]:.1f} {a[1]:.1f} {mx:.1f} {my:.1f}"
    return d + f" T {p[-1][0]:.1f} {p[-1][1]:.1f}"

def stem(x0, y0, y1, lean, n=6):
    return [(x0 + lean * (i / n) * 9 + 2.2 * math.sin(i / n * math.pi * 1.4),
             y0 + (y1 - y0) * i / n) for i in range(n + 1)]

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Georgia, serif">',
       f'<rect width="{W}" height="{H}" fill="{PAPER}"/>']
def note(x, y, s, size=14, color=INK, anchor="start", op=0.85, style="italic", weight="normal"):
    svg.append(f'<text x="{x:.0f}" y="{y:.0f}" font-style="{style}" font-weight="{weight}" font-size="{size}" fill="{color}" text-anchor="{anchor}" opacity="{op}" font-family="Georgia, \'Songti SC\', serif">{s}</text>')

# paper grain
for _ in range(420):
    svg.append(f'<circle cx="{rng.uniform(0,W):.0f}" cy="{rng.uniform(0,H):.0f}" r="{rng.uniform(0.3,0.9):.1f}" fill="{INK}" opacity="0.035"/>')

# ---------------- sky: regime score as daily color wash ----------------
sess = D["sessions"]
for i, d in enumerate(sess):
    if d < D0 or d > D1: continue
    x = X(d)
    nx = X(sess[i + 1]) if i + 1 < len(sess) and sess[i + 1] <= D1 else RX1
    sc = D["regime"][d] / 100
    svg.append(f'<rect x="{x:.1f}" y="{SKY0}" width="{max(nx-x,1):.1f}" height="{SKY1-SKY0}" fill="{mix("#5f7d99", WARM, sc)}" opacity="{0.08+0.30*sc:.2f}"/>')
note(RX0, SKY0 - 12, "天色 = market condition score(逐日重放,0–100 冷→暖)", 13, op=0.5)

# storm: short rain dashes filling the column between sky and ground
sx0, sx1 = X(D["storm"][0]), X(D["storm"][1])
for k in range(int((sx1 - sx0) / 5)):
    x = sx0 + k * 5 + rng.uniform(-1.5, 1.5)
    for _ in range(4):
        y = rng.uniform(SKY1 + 8, GROUND - 40)
        ln = rng.uniform(22, 42)
        svg.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x-7:.0f}" y2="{y+ln:.0f}" stroke="{COLD}" stroke-width="1" opacity="0.3"/>')
note((sx0 + sx1) / 2 - 60, SKY1 - 14, "暴雨 6/02–6/10 · −$223,100(峰值的 −11.1%)", 14, COLD, "middle", 0.8)

# frost: cold hatch band above ground
fx0, fx1 = X(D["frost"][0]), X(D["frost"][1])
for k in range(int((fx1 - fx0) / 5)):
    x = fx0 + k * 5
    svg.append(f'<line x1="{x:.0f}" y1="{GROUND-88+rng.uniform(-6,6):.0f}" x2="{x+6:.0f}" y2="{GROUND-4:.0f}" stroke="{COLD}" stroke-width="1" opacity="0.42"/>')
svg.append(f'<path d="{jpath([(fx0, GROUND-64),(lerp(fx0,fx1,.5), GROUND-72),(fx1, GROUND-64)],1)}" fill="none" stroke="{INK}" stroke-width="0.8" opacity="0.5"/>')
note((fx0 + fx1) / 2, GROUND - 82, "霜冻:十七连败 2/26–3/07 · −$43,833", 14, "middle" and INK, "middle", 0.75)

# ---------------- ground + soil (cumulative losses) ----------------
soil_pts, cum = [], 0
for d in sess:
    if d < D0 or d > D1: continue
    cum = max(cum, *(v for k, v in D["soil"].items() if k <= d)) if any(k <= d for k in D["soil"]) else 0
    soil_pts.append((X(d), GROUND + 6 + cum / D["soil_total"] * SOIL_MAX))
svg.append(f'<path d="M {RX0} {GROUND} ' + " ".join(f"L {x:.0f} {y:.0f}" for x, y in soil_pts) + f' L {RX1} {GROUND} Z" fill="{SOIL_C}" opacity="0.16"/>')
svg.append(f'<path d="{jpath([(RX0, GROUND)] + [(lerp(RX0,RX1,i/24), GROUND) for i in range(1,24)] + [(RX1, GROUND)], 1.2)}" fill="none" stroke="{INK}" stroke-width="1.4" opacity="0.6"/>')
svg.append(f'<path d="' + jpath(soil_pts, 1.2) + f'" fill="none" stroke="{SOIL_C}" stroke-width="1.2" opacity="0.55"/>')
note(RX1 + 6, GROUND + 6 + SOIL_MAX, "土壤 =", 13, SOIL_C, op=0.8)
note(RX1 + 6, GROUND + 6 + SOIL_MAX + 18, "累计凋落", 13, SOIL_C, op=0.8)

# ---------------- plants ----------------
by_day = defaultdict(list)
for t in D["trades"]:
    by_day[t["exit"]].append(t)

def bloom(x, y, rad, color, species, trims, filled, scale=1.0):
    rot = rng.uniform(-8, 8)
    for dx, dy, op in [(0, 0, 0.9), (1.4, 1.1, 0.4)]:
        svg.append(f'<circle cx="{x+dx:.1f}" cy="{y+dy:.1f}" r="{rad:.1f}" fill="none" stroke="{color}" stroke-width="{1.4*scale:.1f}" opacity="{op}" transform="rotate({rot:.0f} {x:.1f} {y:.1f})"/>')
    if filled:
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad*0.42:.1f}" fill="{color}" opacity="0.7"/>')
    if species == "ai":  # rayed corona — AI 链的花形
        for i in range(8):
            a = i / 8 * 2 * math.pi + rng.uniform(-0.06, 0.06)
            svg.append(f'<line x1="{x+math.cos(a)*(rad+2):.1f}" y1="{y+math.sin(a)*(rad+2):.1f}" x2="{x+math.cos(a)*(rad+6.5*scale):.1f}" y2="{y+math.sin(a)*(rad+6.5*scale):.1f}" stroke="{color}" stroke-width="{1.1*scale:.1f}" opacity="0.8"/>')
    for i in range(trims):  # 花瓣 = 分批落袋
        a = -math.pi / 2 + (i - 1) * 0.8 + rng.uniform(-0.1, 0.1)
        svg.append(f'<path d="M {x+math.cos(a)*rad:.1f} {y+math.sin(a)*rad:.1f} q {math.cos(a)*7:.1f} {math.sin(a)*7-3:.1f} {math.cos(a)*11:.1f} {math.sin(a)*11:.1f}" fill="none" stroke="{color}" stroke-width="{1.2*scale:.1f}" opacity="0.75"/>')

anchor = {}   # (ticker, attempt) -> (x, y) for chains
for day, ts in sorted(by_day.items()):
    n = len(ts)
    for i, t in enumerate(sorted(ts, key=lambda z: -z["pnl"])):
        x = X(day) + (i - (n - 1) / 2) * 9.5 + rng.uniform(-1.5, 1.5)
        lean = 1 if t["dir"] == "long" else -1
        if t["pnl"] > 0:
            h = min(30 + 42 * math.sqrt(t["hold"]), 470)
            h *= 0.78 + 0.5 * ((i * 37) % 7) / 6   # 同日错落,避免花冠成团
            rad = max(2.8, min(3 + abs(t["r"]) * 1.3, 22))
            color = GOLD if t["gold"] else GREEN
            base = GROUND if t["species"] != "rootless" else GROUND - 14
            if t["species"] == "rootless":  # 切花:茎不入土
                svg.append(f'<line x1="{x-4:.0f}" y1="{GROUND-7:.0f}" x2="{x+5:.0f}" y2="{GROUND-9:.0f}" stroke="{color}" stroke-width="1.2" opacity="0.6"/>')
            svg.append(f'<path d="{jpath(stem(x, base, GROUND-h, lean))}" fill="none" stroke="{color}" stroke-width="1.5" stroke-linecap="round" opacity="0.85"/>')
            bloom(x + lean * 8, GROUND - h, rad, color, t["species"], t["trims"], True,
                  1.15 if t["gold"] else 1.0)
            anchor[(t["t"], t["attempt"])] = (x, GROUND - h)
        else:
            depth = 10 + min(abs(t["r"]), 3.2) * 13
            color = RUST if t["r"] <= -1 else GREY
            if t["r"] <= -1:  # 断茎的残株
                svg.append(f'<path d="{jpath([(x, GROUND),(x+lean*3, GROUND-9),(x+lean*8, GROUND-13)],0.8)}" fill="none" stroke="{color}" stroke-width="1.3" stroke-linecap="round" opacity="0.7"/>')
            svg.append(f'<path d="{jpath([(x, GROUND+3),(x+lean*3, GROUND+depth*0.55),(x+lean*1.5, GROUND+depth)],0.9)}" fill="none" stroke="{color}" stroke-width="1.3" stroke-linecap="round" opacity="0.6"/>')
            svg.append(f'<circle cx="{x+lean*1.5:.1f}" cy="{GROUND+depth:.1f}" r="2.1" fill="{color}" opacity="0.55"/>')
            anchor[(t["t"], t["attempt"])] = (x, GROUND + depth)

# ---------------- two threads: BE / BABA ----------------
for name, color in [("BE", GREEN), ("BABA", RUST)]:
    pts = [anchor[k] for k in sorted(anchor) if k[0] == name]
    if len(pts) > 1:
        svg.append(f'<path d="{jpath(pts, 2)}" fill="none" stroke="{color}" stroke-width="0.9" opacity="0.4" stroke-dasharray="1 4"/>')

# annotations
x423 = X(dt.date(2026, 4, 23)); x428 = X(dt.date(2026, 4, 28)); x602 = X(dt.date(2026, 6, 2))
note(x423, GROUND + SOIL_MAX + 46, "4/23 三根 BABA 同日剪断 · −$49,939 · 102 天", 14, RUST, "middle", 0.85)
be9 = anchor.get(("BE", 9))
if be9:
    lx9, ly9 = be9[0] + 30, be9[1] - 60
    note(lx9, ly9, "4/28 BE 第九次 · +$74,052 · 距认输五天", 14, GOLD, "start", 0.9)
    svg.append(f'<path d="M {lx9-6:.0f} {ly9+4:.0f} Q {be9[0]+14:.0f} {ly9+20:.0f} {be9[0]+3:.0f} {be9[1]-8:.0f}" fill="none" stroke="{GOLD}" stroke-width="0.8" opacity="0.6"/>')
note(x602, SKY0 - 34, "6/02 峰值 $2,036,318(+104%)——与暴雨第一天是同一天", 14.5, INK, "middle", 0.85)
svg.append(f'<line x1="{x602:.0f}" y1="{SKY0-26:.0f}" x2="{x602:.0f}" y2="{SKY1:.0f}" stroke="{INK}" stroke-width="0.7" opacity="0.4" stroke-dasharray="2 3"/>')

# month ticks
for m in range(1, 8):
    md = dt.date(2026, m, 1); x = X(md)
    svg.append(f'<line x1="{x:.0f}" y1="{GROUND+SOIL_MAX+58:.0f}" x2="{x:.0f}" y2="{GROUND+SOIL_MAX+66:.0f}" stroke="{INK}" opacity="0.4"/>')
    note(x, GROUND + SOIL_MAX + 84, f"{m}月", 13, INK, "middle", 0.5, "normal")

# ---------------- title & legend & footer ----------------
note(RX0, 64, "同一个动作 · The Same Gesture — 正面:园子", 34, INK, "start", 0.95, "normal")
note(RX0, 96, "2026 上半年 · 331 笔真实交易 · sketch 01(构图小样)", 15, INK, "start", 0.55)

lx, ly = RX0, H - 150
note(lx, ly - 16, "图例", 15, INK, "start", 0.7, "normal")
def leg(dx, dy, s, c):
    note(lx + dx + 22, ly + dy + 5, s, 13, INK, "start", 0.75)
    return lx + dx, ly + dy
x0, y0 = leg(0, 10, "AI 链(169 株,净利 80%)——放射花形", GREEN); bloom(x0 + 8, y0, 6, GREEN, "ai", 0, True, 0.8)
x0, y0 = leg(0, 40, "其他品种(69 株,合计为负)", GREY); bloom(x0 + 8, y0, 6, GREY, "other", 0, True, 0.8)
x0, y0 = leg(0, 70, "无根(杠杆 ETF · 93 株)——切花,茎不入土", INK); bloom(x0 + 8, y0, 6, INK, "rootless", 0, False, 0.8)
x0, y0 = leg(420, 10, "扛起全部净利润的 31 株(其余 300 株加总 ≈ 0)", GOLD); bloom(x0 + 8, y0, 7, GOLD, "ai", 0, True, 0.9)
x0, y0 = leg(420, 40, "凋落入土:199 次亏损沉积成土壤层", SOIL_C)
svg.append(f'<path d="M {x0+4} {y0-4} q 3 6 1 12" fill="none" stroke="{GREY}" stroke-width="1.3"/><circle cx="{x0+5}" cy="{y0+9}" r="2" fill="{GREY}" opacity="0.6"/>')
x0, y0 = leg(420, 70, "断茎 = 止损(R ≤ −1,42 次)· 铁锈红", RUST)
svg.append(f'<path d="M {x0+2} {y0+6} L {x0+5} {y0-2} L {x0+11} {y0-6}" fill="none" stroke="{RUST}" stroke-width="1.3"/>')
note(lx + 900, ly + 15, "花冠 = |R| · 茎长 = 持仓天数 · 花瓣 = 分批落袋(盈亏在落瓣那一刻才实现)", 13, INK, "start", 0.6)
note(lx + 900, ly + 45, "先有凋落入土,后有满园盛开:31 朵金花里 26 朵开在 4 月之后", 13, INK, "start", 0.6)

note(RX0, H - 26, "Fluxus DataArt · sketch 01 正面 · 胜率 39.9% · +90.5% · 数据无一虚构 · 翻到反面:手迹", 13, INK, "start", 0.5)

svg.append("</svg>")
out = Path(__file__).parent / "sketch_01_front.svg"
out.write_text("\n".join(svg))
print("wrote", out)
