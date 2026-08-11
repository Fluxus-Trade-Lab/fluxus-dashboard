#!/usr/bin/env python3
"""sketch 02 · 正面 — 梯田山(立轴)。
七个月叠成一座山:海拔 = 当月权益,亏损垒成托住下一层的墙,时间在层内蛇行。
细活版:tapered 笔画 · 伞形花序 · 渐变天光 · 装裱框 · 竖排题字 · 红印。
"""
import math, datetime as dt, calendar
from pathlib import Path
from collections import defaultdict
from art_data import load
from craft import smooth_path, tapered, stem_curve, umbel, five_petal, falling_petals

D = load()

PAPER, INK = "#f5f0e3", "#2b2823"
GREEN, GOLD, RUST, GREY = "#3e6e49", "#c1912a", "#a04a30", "#8a8175"
SOIL, COLD, WARM, SEAL = "#5f5140", "#5b7a96", "#d3a92f", "#9e2b1f"

W, H = 1600, 2400
XL, XR = 250, 1355
MARGIN = 72

# ---------- monthly aggregates ----------
eq = 1_000_000.0
month_eq, month_loss = {}, defaultdict(float)
by_exit = sorted(D["trades"], key=lambda z: z["exit"])
cum = 0.0
for m in range(1, 8):
    for t in by_exit:
        if t["exit"].month == m and t["exit"].year == 2026:
            cum += t["pnl"]
            if t["pnl"] < 0:
                month_loss[m] += -t["pnl"]
    month_eq[m] = 1_000_000 + cum

# ---------- terrace geometry ----------
def y_row(idx):
    gain = (month_eq[idx + 1] - 1_000_000) / 950_000
    return 2135 - idx * 182 - gain * 430

ROWY = [y_row(i) for i in range(7)]

def row_of(d):
    return (d.month - 1) if d.year == 2026 else 0

def x_in_row(d):
    m = d.month if d.year == 2026 else 1
    dim = calendar.monthrange(2026, m)[1]
    day = d.day if d.year == 2026 else 1
    f = (day - 1) / (dim - 1)
    idx = m - 1
    return XL + f * (XR - XL) if idx % 2 == 0 else XR - f * (XR - XL)

def terrain(x, idx):
    return ROWY[idx] + 5.5 * math.sin((x - XL) / 210 + idx * 1.7)

def pos(d):
    idx = row_of(d)
    x = x_in_row(d)
    return idx, x, terrain(x, idx)

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Georgia, serif">']
defs = ['<defs>']
svg.append(f'<rect width="{W}" height="{H}" fill="{PAPER}"/>')

def note(x, y, s, size=13, color=INK, anchor="start", op=0.8, style="italic", weight="normal"):
    svg.append(f'<text x="{x:.0f}" y="{y:.0f}" font-style="{style}" font-weight="{weight}" font-size="{size}" fill="{color}" text-anchor="{anchor}" opacity="{op}" font-family="Georgia, \'Songti SC\', serif">{s}</text>')

def mix(c1, c2, t):
    p = lambda c: (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16))
    a, b = p(c1), p(c2)
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

# ---------- sky gradients + terraces ----------
sess_by_m = defaultdict(list)
for d in D["sessions"]:
    if d.year == 2026 and d.month <= 7:
        sess_by_m[d.month].append(d)

for idx in range(7):
    m = idx + 1
    gy = ROWY[idx]
    gap = (ROWY[idx - 1] - gy) if idx > 0 else 230
    sky_h = min(150, gap * 0.62)
    # gradient stops from daily scores (weekly samples)
    days = sess_by_m[m]
    stops = []
    for k in range(0, len(days), max(len(days) // 5, 1)):
        d = days[k]
        f = (d.day - 1) / (calendar.monthrange(2026, m)[1] - 1)
        if idx % 2 == 1:
            f = 1 - f
        stops.append((f, D["regime"][d] / 100))
    stops.sort()
    gid = f"sky{m}"
    defs.append(f'<linearGradient id="{gid}" x1="{XL}" y1="0" x2="{XR}" y2="0" gradientUnits="userSpaceOnUse">')
    for f, sc in stops:
        defs.append(f'<stop offset="{f:.2f}" stop-color="{mix(COLD, WARM, sc)}" stop-opacity="{0.09+0.30*sc:.2f}"/>')
    defs.append('</linearGradient>')
    svg.append(f'<rect x="{XL}" y="{gy-sky_h:.0f}" width="{XR-XL}" height="{sky_h:.0f}" fill="url(#{gid})"/>')

    # terrace wall (this month's losses hold up the next terrace)
    wall_h = 8 + min(month_loss[m] / 95_000, 1.0) * 52
    top = [(x, terrain(x, idx)) for x in range(XL, XR + 1, 24)]
    bot = [(x, y + wall_h) for x, y in reversed(top)]
    wall_path = smooth_path(top) + " L " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in bot) + " Z"
    cid = f"wall{m}"
    defs.append(f'<clipPath id="{cid}"><path d="{wall_path}"/></clipPath>')
    svg.append(f'<path d="{wall_path}" fill="{SOIL}" fill-opacity="0.17"/>')
    for hx in range(XL - 20, XR + 20, 5):   # fine 60° hatch inside the wall
        svg.append(f'<line x1="{hx}" y1="{gy-6:.0f}" x2="{hx+wall_h*0.6:.0f}" y2="{gy+wall_h+6:.0f}" stroke="{SOIL}" stroke-width="0.55" opacity="0.28" clip-path="url(#{cid})"/>')
    svg.append(f'<path d="{smooth_path([(x, y + wall_h) for x, y in top])}" fill="none" stroke="{SOIL}" stroke-width="0.8" opacity="0.5"/>')
    # ground line: calligraphic tapered stroke in direction of travel
    line = top if idx % 2 == 0 else list(reversed(top))
    svg.append(f'<path d="{tapered(line, 4.2, 1.3, 40)}" fill="{INK}" opacity="0.8"/>')
    # switchback chevron at the turn end of this row
    ex = XR + 8 if idx % 2 == 0 else XL - 8
    sgn_c = 1 if idx % 2 == 0 else -1
    if idx < 6:
        svg.append(f'<path d="M {ex:.0f} {gy:.0f} q {sgn_c*26} -14 {sgn_c*20} -46" fill="none" stroke="{INK}" stroke-width="1.1" opacity="0.45"/>')
        svg.append(f'<path d="M {ex+sgn_c*16:.0f} {gy-40:.0f} l {sgn_c*4} -8 l {-sgn_c*9} -1" fill="none" stroke="{INK}" stroke-width="1" opacity="0.45"/>')

    # elevation marker at the row's end side
    endx = XR + 26 if idx % 2 == 0 else XL - 26
    anchor = "start" if idx % 2 == 0 else "end"
    cn = "一二三四五六七"[idx]
    note(endx, gy - 6, f"{cn}月", 15, INK, anchor, 0.75, "normal")
    note(endx, gy + 14, f"${month_eq[m]/1e6:.2f}M", 12.5, INK, anchor, 0.5)
    note(endx, gy + 32, f"墙 −${month_loss[m]/1000:.0f}k", 11.5, SOIL, anchor, 0.55)

svg.append("".join(defs) + "</defs>")

# ---------- weather events ----------
# frost 2/26–3/07: fine vertical ticks above ground
d = D["frost"][0]
while d <= D["frost"][1]:
    idx, x, gy = pos(d)
    for k in range(4):
        fx = x + (k - 1.5) * 4.6
        svg.append(f'<line x1="{fx:.1f}" y1="{gy-24 - 6*math.sin(k*2.1):.1f}" x2="{fx:.1f}" y2="{gy-3:.1f}" stroke="{COLD}" stroke-width="0.8" opacity="0.5"/>')
    d += dt.timedelta(days=1)
i3, x3, y3 = pos(dt.date(2026, 3, 3))
note(x3, y3 - 44, "霜冻 · 十七连败 2/26–3/07 · −$43,833", 12.5, COLD, "middle", 0.8)

# storm 6/02–6/10 on the June terrace
s0, s1 = D["storm"]
xs = sorted([x_in_row(s0), x_in_row(s1)])
gy6 = ROWY[5]
gap6 = ROWY[4] - ROWY[5]
defs2 = f'<linearGradient id="stormg" x1="0" y1="{gy6-gap6*0.58:.0f}" x2="0" y2="{gy6:.0f}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{COLD}" stop-opacity="0.30"/><stop offset="1" stop-color="{COLD}" stop-opacity="0.05"/></linearGradient>'
svg.append(f'<defs>{defs2}</defs>')
svg.append(f'<rect x="{xs[0]-8:.0f}" y="{gy6-gap6*0.58:.0f}" width="{xs[1]-xs[0]+16:.0f}" height="{gap6*0.58:.0f}" fill="url(#stormg)"/>')
k = 0
for rx in range(int(xs[0]), int(xs[1]), 6):
    for j in range(3):
        ry = gy6 - gap6 * 0.55 + ((k * 53 + j * 71) % int(gap6 * 0.48))
        ln = 20 + (k * 7 + j * 11) % 22
        svg.append(f'<line x1="{rx:.0f}" y1="{ry:.0f}" x2="{rx-5:.0f}" y2="{ry+ln:.0f}" stroke="{COLD}" stroke-width="0.8" opacity="0.45"/>')
    k += 1
note((xs[0] + xs[1]) / 2, gy6 - gap6 * 0.58 - 10, "暴雨 6/02–6/10 · −$223,100 · 峰值与暴雨同日", 12.5, COLD, "middle", 0.85)

# ---------- plants ----------
by_day = defaultdict(list)
for t in D["trades"]:
    by_day[t["exit"]].append(t)

anchors = {}
for day, ts in sorted(by_day.items()):
    n = len(ts)
    idx, x0, _ = pos(day)
    sgn = 1 if idx % 2 == 0 else -1
    for i, t in enumerate(sorted(ts, key=lambda z: -z["pnl"])):
        x = x0 + (i - (n - 1) / 2) * 8.5 * sgn
        gy = terrain(x, idx)
        if t["pnl"] > 0:
            h = (22 + 17.5 * math.sqrt(t["hold"])) * (0.82 + 0.42 * ((i * 37) % 5) / 4)
            h = min(h, 180 if not t["gold"] else 215)
            rad = max(4.0, min(4.2 + abs(t["r"]) * 1.1, 21)) * (1.12 if t["gold"] else 1)
            color = GOLD if t["gold"] else (GREEN if t["species"] != "rootless" else INK)
            base_y = gy if t["species"] != "rootless" else gy - 9
            lean = 10 if t["dir"] == "long" else -10
            tip = (x + lean * 0.7, base_y - h)
            pts = stem_curve(x, base_y, tip[0], tip[1], sway=0.12, phase=(i % 3) * 0.9)
            svg.append(f'<path d="{tapered(pts, 2.5 if t["gold"] else 2.1, 0.9, 22)}" fill="{color}" opacity="0.88"/>')
            if t["species"] == "rootless":
                svg.append(f'<line x1="{x-5:.1f}" y1="{gy-6:.1f}" x2="{x+5:.1f}" y2="{gy-8:.1f}" stroke="{INK}" stroke-width="1.1" opacity="0.55"/>')
                svg.append(f'<ellipse cx="{tip[0]:.1f}" cy="{tip[1]-rad*0.5:.1f}" rx="{rad*0.42:.1f}" ry="{rad*0.66:.1f}" fill="none" stroke="{INK}" stroke-width="1.1" opacity="0.75"/>')
            elif t["species"] == "ai":
                svg += umbel(tip[0], tip[1] - rad * 0.2, rad, max(9, int(rad * 0.95)), color,
                             sw=1.0 + (0.25 if t["gold"] else 0), op=0.92 if t["gold"] else 0.82)
            else:
                svg += five_petal(tip[0], tip[1], rad * 0.95, color, 0.8)
            if t["trims"] > 1:
                svg += falling_petals(tip[0] + rad * 0.4 * sgn, tip[1] + rad, t["trims"] - 1, color, drift=sgn)
            anchors[(t["t"], t["attempt"])] = (tip[0], tip[1])
        else:
            depth = 9 + min(abs(t["r"]), 3.0) * 12
            color = RUST if t["r"] <= -1 else GREY
            pts = [(x, gy + 1.5), (x + 3 * sgn, gy + depth * 0.6), (x + 1.4 * sgn, gy + depth)]
            svg.append(f'<path d="{tapered(pts, 2.3, 0.6, 12)}" fill="{color}" opacity="0.78"/>')
            svg.append(f'<circle cx="{x+1.4*sgn:.1f}" cy="{gy+depth:.1f}" r="1.9" fill="{color}" opacity="0.7"/>')
            anchors[(t["t"], t["attempt"])] = (x, gy + depth)

# ---------- vines: BE / BABA climb the switchbacks, not the void ----------
row_of_anchor = {}
for t in D["trades"]:
    row_of_anchor[(t["t"], t["attempt"])] = row_of(t["exit"])

def vine_route(keys):
    """藤沿地面爬到目标横坐标,再垂直穿层向上——贴着墙根攀爬。"""
    pts = []
    prev = None
    for k in keys:
        p, r = anchors[k], row_of_anchor[k]
        if prev is not None and r > prev[1]:
            x2 = p[0]
            for rr in range(prev[1], r):      # 在每一层的地面处经过目标横坐标
                pts.append((x2 + (rr - r) * 3, terrain(x2, rr) - 4))
        pts.append(p)
        prev = (p, r)
    return pts

for name, color, label in [("BE", GREEN, "BE — 打了 16 次,第 9 次开花"),
                           ("BABA", RUST, "BABA — 5 次,始终没有开花")]:
    ks = sorted(k for k in anchors if k[0] == name)
    pts = vine_route(ks)
    if len(pts) > 1:
        svg.append(f'<path d="{smooth_path(pts)}" fill="none" stroke="{color}" stroke-width="1.05" opacity="0.45"/>')
        for k in ks:
            p = anchors[k]
            svg.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="1.7" fill="none" stroke="{color}" stroke-width="0.8" opacity="0.65"/>')
        lx, ly = anchors[ks[0]]
        note(lx + 12, ly + 28, label, 12, color, "start", 0.8)

# key annotations (few, precise)
b423 = anchors.get(("BABA", 5))
if b423:
    note(b423[0] - 14, b423[1] + 30, "4/23 三根同日剪断 · 102 天", 12, RUST, "end", 0.85)
be9 = anchors.get(("BE", 9))
if be9:
    note(be9[0] + 16, be9[1] - 14, "4/28 第九次 · +$74,052", 12, GOLD, "start", 0.9)

# ---------- mounting frame, vertical title, seal, footer ----------
svg.append(f'<rect x="{MARGIN}" y="{MARGIN}" width="{W-2*MARGIN}" height="{H-2*MARGIN}" fill="none" stroke="{INK}" stroke-width="1.5" opacity="0.55"/>')
svg.append(f'<rect x="{MARGIN+14}" y="{MARGIN+14}" width="{W-2*MARGIN-28}" height="{H-2*MARGIN-28}" fill="none" stroke="{INK}" stroke-width="0.55" opacity="0.4"/>')

tx = W - 118
for i, ch in enumerate("同一个动作"):
    note(tx, 220 + i * 62, ch, 46, INK, "middle", 0.92, "normal")
note(tx, 220 + 5 * 62 + 6, "The Same Gesture", 13, INK, "middle", 0.5)
note(tx, 220 + 5 * 62 + 26, "二〇二六 · 上半年", 13, INK, "middle", 0.5)
sy = 220 + 5 * 62 + 52
svg.append(f'<rect x="{tx-23}" y="{sy}" width="46" height="46" rx="3.5" fill="{SEAL}" opacity="0.9"/>')
note(tx, sy + 20, "测", 17, "#f5f0e3", "middle", 0.95, "normal")
note(tx, sy + 39, "量", 17, "#f5f0e3", "middle", 0.95, "normal")

note(XL, 200, "山 = 二〇二六上半年的权益;每一层梯田是一个月,海拔是月末的账户。", 14, INK, "start", 0.62)
note(XL, 224, "亏损不是失败——一百九十九次凋落,垒成托住下一层梯田的墙。", 14, INK, "start", 0.62)
note(XL, H - 116, "花冠 = |R| · 茎长 = 持仓天数 · 伞形花 = AI 链 · 五瓣花 = 其他品种 · 无根芽 = 杠杆工具 · 金 = 扛起全部净利的 31 株", 12, INK, "start", 0.5)
note(XL, H - 96, "胜率 39.9% · +90.5% · 331 笔真实交易,无一虚构 · 翻到反面:手迹", 12, INK, "start", 0.5)

svg.append("</svg>")
out = Path(__file__).parent / "sketch_02_front.svg"
out.write_text("\n".join(svg))
print("wrote", out)
