#!/usr/bin/env python3
"""sketch 03 — 美术馆墙(全出血横幅,5000×2000 ≈ 10m×4m)。
远看:一座山的 landscape,山脊 = 净值曲线,拼布田野,巨雨,一面湖。
近看:331 株真实交易,月份、品种、生命周期全部可读。
Hockney:饱和拼布色块 · 果断轮廓 · 巨大的雨 · 湖面倒影。
"""
import math, datetime as dt, calendar
from pathlib import Path
from collections import defaultdict
from art_data import load
from craft import smooth_path, tapered, stem_curve, umbel, five_petal

D = load()

W, H = 5000, 2000
INK = "#2b2823"
GREEN, GOLD, RUST = "#3e6e49", "#c1912a", "#a04a30"
UMBER = "#4a3f33"
SKY_TOP, SKY_HOR = "#a9c7d8", "#f0e2bd"
SLATE = "#5b7a96"
FIELD = {1: "#8fa98f", 2: "#a9a2c0", 3: "#8ba3b5", 4: "#7fae5c",
         5: "#b9c356", 6: "#d9b84a", 7: "#5d8f57"}

D0, D1 = dt.date(2025, 12, 29), dt.date(2026, 7, 24)

def X(day):
    return (day - D0).days / (D1 - D0).days * W

def mix(c1, c2, t):
    p = lambda c: (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16))
    a, b = p(c1), p(c2)
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def shade(c, t):
    return mix(c, "#2b2823", t) if t >= 0 else mix(c, "#f7f3e6", -t)

# ---------- ridge = equity curve (with the June notch) ----------
by_exit = sorted(D["trades"], key=lambda z: z["exit"])
eq_by_day, cum = {}, 0.0
for t in by_exit:
    cum += t["pnl"]
    eq_by_day[t["exit"]] = cum
days = sorted(eq_by_day)
def eq_at(d):
    v = 0.0
    for dd in days:
        if dd <= d:
            v = eq_by_day[dd]
        else:
            break
    return 1_000_000 + v

STORM0, STORM1 = D["storm"]
SX0 = X(STORM0) - 260
SX1 = X(STORM1) + 560
def wind(x, scale=1.0):
    """暴雨区的风:压弯花茎的力度,区间内正弦包络。"""
    if SX0 < x < SX1:
        return 85 * scale * math.sin((x - SX0) / (SX1 - SX0) * math.pi)
    return 0.0

def ridge_y(x):
    d = D0 + dt.timedelta(days=x / W * (D1 - D0).days)
    y = 1450 - (eq_at(d) - 1_000_000) / 1_050_000 * 930
    sx0, sx1 = X(STORM0), X(STORM1)
    if sx0 - 60 < x < sx1 + 260:            # 暴雨的缺口(盯市回撤的形状,-11.1%)
        t = (x - (sx0 - 60)) / (sx1 + 260 - (sx0 - 60))
        y += 115 * math.sin(t * math.pi) ** 1.5
    return y

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Georgia, serif">']

def note(x, y, s, size=26, color=INK, anchor="start", op=0.8, style="italic", weight="normal", halo=None):
    common = (f'x="{x:.0f}" y="{y:.0f}" font-style="{style}" font-weight="{weight}" font-size="{size}" '
              f'text-anchor="{anchor}" font-family="Georgia, \'Songti SC\', serif"')
    if halo:
        svg.append(f'<text {common} fill="none" stroke="{halo}" stroke-width="{size*0.28:.0f}" stroke-linejoin="round" opacity="{min(op+0.1,1):.2f}">{s}</text>')
    svg.append(f'<text {common} fill="{color}" opacity="{op}">{s}</text>')

# ---------- sky ----------
svg.append(f'<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
           f'<stop offset="0" stop-color="{SKY_TOP}"/><stop offset="0.72" stop-color="{mix(SKY_TOP, SKY_HOR, 0.6)}"/>'
           f'<stop offset="1" stop-color="{SKY_HOR}"/></linearGradient></defs>')
svg.append(f'<defs><clipPath id="page"><rect width="{W}" height="{H}"/></clipPath></defs>')
svg.append(f'<g clip-path="url(#page)">')
svg.append(f'<rect width="{W}" height="{H}" fill="url(#sky)"/>')
# regime tint: broad translucent bands over the sky, day by day
sess = [d for d in D["sessions"] if D0 <= d <= D1]
for i, d in enumerate(sess):
    x = X(d); nx = X(sess[i + 1]) if i + 1 < len(sess) else W
    sc = D["regime"][d] / 100
    svg.append(f'<rect x="{x:.0f}" y="0" width="{max(nx-x,2):.0f}" height="{H}" fill="{mix(SLATE, "#e8c95f", sc)}" opacity="{0.05+0.13*sc:.2f}"/>')
# clouds: long confident ellipses
for cx, cy, rx, opac in [(700, 260, 420, 0.5), (1500, 170, 520, 0.4), (2500, 300, 380, 0.45),
                         (3900, 200, 600, 0.35), (4500, 330, 300, 0.4), (1100, 380, 260, 0.3)]:
    svg.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{rx*0.16:.0f}" fill="#f7f3e6" opacity="{opac}"/>')
# July sun, pale gold
svg.append(f'<circle cx="{X(dt.date(2026,7,14)):.0f}" cy="300" r="98" fill="{GOLD}" opacity="0.35"/>')
svg.append(f'<circle cx="{X(dt.date(2026,7,14)):.0f}" cy="300" r="80" fill="#e8cf7a" opacity="0.5"/>')

# ---------- distant hills ----------
for off, col, op in [(300, mix(SLATE, "#ffffff", 0.45), 0.5), (170, mix(GREEN, SKY_TOP, 0.55), 0.55)]:
    pts = [(x, ridge_y(x) - off - 60 * math.sin(x / 900 + off)) for x in range(0, W + 1, 100)]
    svg.append(f'<path d="{smooth_path(pts)} L {W} {H} L 0 {H} Z" fill="{col}" opacity="{op}"/>')

# ---------- patchwork fields (weekly quilt, Hockney) ----------
for m in range(1, 8):
    m0 = dt.date(2026, m, 1) if m > 1 else D0
    dim = calendar.monthrange(2026, m)[1]
    m1 = min(dt.date(2026, m, dim), D1)
    weeks = []
    d = m0
    while d <= m1:
        e = min(d + dt.timedelta(days=6), m1)
        weeks.append((d, e)); d = e + dt.timedelta(days=1)
    for wi, (a, b) in enumerate(weeks):
        x0, x1 = X(a), X(b) + (X(b) - X(a)) / max((b - a).days, 1)
        base = FIELD[m]
        col = shade(base, -0.18 if wi % 2 == 0 else 0.13)
        top = [(x, ridge_y(x) + 2) for x in range(int(x0), int(x1) + 1, 40)] or [(x0, ridge_y(x0))]
        svg.append(f'<path d="{smooth_path(top)} L {x1:.0f} {H} L {x0:.0f} {H} Z" fill="{col}" opacity="0.97"/>')
    # hedgerow between months: dark studded band
    hx = X(m1) + (X(m1) - X(m0)) / max((m1 - m0).days, 1)
    if m < 7:
        pts = [(hx + 14 * math.sin(y / 130), y) for y in range(int(ridge_y(hx)), H, 60)]
        svg.append(f'<path d="{smooth_path(pts)}" fill="none" stroke="{shade(GREEN, 0.35)}" stroke-width="10" opacity="0.5" stroke-linecap="round"/>')
        for px, py in pts[::2]:
            svg.append(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="13" fill="{shade(GREEN, 0.2)}" opacity="0.45"/>')

# field furrows: contour strokes following each month's slope
for m in range(1, 8):
    m0 = dt.date(2026, m, 1) if m > 1 else D0
    dim = calendar.monthrange(2026, m)[1]
    m1 = min(dt.date(2026, m, dim), D1)
    x0, x1 = X(m0), X(m1)
    for k in range(1, 6):
        yoff = 90 + k * 150
        pts = [(x, min(ridge_y(x) + yoff + 12 * math.sin(x / 300 + k), H - 16)) for x in range(int(x0), int(x1) + 1, 60)]
        if len(pts) > 2:
            svg.append(f'<path d="{smooth_path(pts)}" fill="none" stroke="{shade(FIELD[m], 0.28)}" stroke-width="3.2" opacity="0.35"/>')

# frost over Feb–Mar fields
fx0, fx1 = X(dt.date(2026, 2, 1)), X(dt.date(2026, 3, 20))
k = 0
for rx in range(int(fx0), int(fx1), 46):
    for j in range(6):
        ry = ridge_y(rx) + 60 + ((k * 97 + j * 173) % 900)
        if ry < H - 40:
            svg.append(f'<line x1="{rx:.0f}" y1="{ry:.0f}" x2="{rx+30:.0f}" y2="{ry-12:.0f}" stroke="#eef4f8" stroke-width="5" opacity="0.5" stroke-linecap="round"/>')
    k += 1
# snow drifting in the winter air (Jan–Mar)
snx0, snx1 = X(dt.date(2026, 1, 6)), X(dt.date(2026, 3, 18))
for k in range(70):
    px = snx0 + (k * 191) % int(snx1 - snx0)
    py = ridge_y(px) - 60 - (k * 137) % 480
    r = 2.6 + (k % 3) * 1.4
    svg.append(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="{r:.1f}" fill="#f7f3e6" opacity="{0.28+(k%3)*0.09:.2f}"/>')
# snow patches on the field shoulder
for k in range(9):
    px = fx0 + (k * 233) % int(fx1 - fx0)
    py = ridge_y(px) + 26 + (k * 71) % 50
    svg.append(f'<ellipse cx="{px:.0f}" cy="{py:.0f}" rx="{46+(k%4)*16}" ry="{9+(k%3)*3}" fill="#f2f4f0" opacity="0.55"/>')

# the seventeen bare twigs: 连败的枯枝立在霜冻里
streak_losses = sorted([t for t in D["trades"] if t["pnl"] <= 0 and D["frost"][0] <= t["exit"] <= D["frost"][1]],
                       key=lambda z: z["exit"])[:17]
for i, t in enumerate(streak_losses):
    x = X(t["exit"]) + (i % 5 - 2) * 34
    gy = ridge_y(x)
    hh = 62 + (i * 29) % 58
    lean = 8 if i % 2 == 0 else -8
    svg.append(f'<path d="M {x:.0f} {gy:.0f} q {lean*0.4:.0f} {-hh*0.6:.0f} {lean:.0f} {-hh:.0f}" fill="none" stroke="{UMBER}" stroke-width="3.4" opacity="0.7" stroke-linecap="round"/>')
    for b in range(2):
        by = gy - hh * (0.45 + b * 0.28)
        sgn = 1 if (i + b) % 2 == 0 else -1
        svg.append(f'<path d="M {x+lean*0.5:.0f} {by:.0f} q {sgn*14:.0f} -6 {sgn*24:.0f} {-16-b*4:.0f}" fill="none" stroke="{UMBER}" stroke-width="2.2" opacity="0.6" stroke-linecap="round"/>')

# ---------- the lake (the drawdown, collected) ----------
lcx, lcy = X(dt.date(2026, 6, 7)) + 60, 0
lcy = ridge_y(lcx) + 265
lrx, lry = 385, 104
svg.append(f'<defs><linearGradient id="lake" x1="0" y1="0" x2="0" y2="1">'
           f'<stop offset="0" stop-color="{mix(SLATE, "#ffffff", 0.25)}"/>'
           f'<stop offset="1" stop-color="{shade(SLATE, 0.25)}"/></linearGradient></defs>')
svg.append(f'<ellipse cx="{lcx:.0f}" cy="{lcy:.0f}" rx="{lrx}" ry="{lry}" fill="url(#lake)" opacity="0.92"/>')
svg.append(f'<ellipse cx="{lcx:.0f}" cy="{lcy:.0f}" rx="{lrx}" ry="{lry}" fill="none" stroke="{shade(SLATE, 0.4)}" stroke-width="3" opacity="0.5"/>')
for k in range(7):   # Hockney ripples
    ry_ = lcy - lry * 0.5 + k * lry * 0.16
    wamp = 6 + (k % 3) * 3
    pts = [(lcx - lrx * 0.9 + i * lrx * 0.12, ry_ + wamp * math.sin(i * 1.1 + k)) for i in range(16)]
    svg.append(f'<path d="{smooth_path(pts)}" fill="none" stroke="#dce8f0" stroke-width="3.5" opacity="{0.5-k*0.04:.2f}"/>')
note(lcx, lcy + lry + 54, "湖 = 那场暴雨留下的水位 · −$223,100", 24, INK, "middle", 0.8, halo="#f5f0e3")

# ---------- losses: dark seeds sown in the fields ----------
by_day = defaultdict(list)
for t in D["trades"]:
    by_day[t["exit"]].append(t)
for day, ts in sorted(by_day.items()):
    losses = [t for t in ts if t["pnl"] <= 0]
    for i, t in enumerate(losses):
        x = X(day) + (i - len(losses) / 2) * 26
        depth = 70 + ((i * 137 + day.day * 61) % 780)
        y = ridge_y(x) + depth
        if abs(x - lcx) < lrx and abs(y - lcy) < lry * 1.3:
            y = lcy + lry + 60
        if y > H - 30:
            y = H - 30 - (i * 37) % 120
        col = RUST if t["r"] <= -1 else UMBER
        sc = 0.7 + depth / 900 * 0.8
        svg.append(f'<path d="M {x:.0f} {y:.0f} q {5*sc:.1f} {8*sc:.1f} {1.5*sc:.1f} {16*sc:.1f}" fill="none" stroke="{col}" stroke-width="{3*sc:.1f}" opacity="0.55" stroke-linecap="round"/>')
        svg.append(f'<circle cx="{x+1.5*sc:.0f}" cy="{y+16*sc:.0f}" r="{3.4*sc:.1f}" fill="{col}" opacity="0.5"/>')

# ---------- winners: the meadow, scale variance amplified ----------
plants = []
for day, ts in sorted(by_day.items()):
    wins = [t for t in ts if t["pnl"] > 0]
    n = len(wins)
    for i, t in enumerate(sorted(wins, key=lambda z: -z["pnl"])):
        x = X(day) + (i - (n - 1) / 2) * 30
        drow = (i * 53 + day.day * 31) % 4
        base = ridge_y(x) + (26 if drow == 0 else 90 + drow * 130 + ((i * 97) % 90))
        if abs(x - lcx) < lrx * 1.05 and abs(base - lcy) < lry * 1.4:
            base = lcy - lry - 20
        scale = 0.62 + drow * 0.24 + (0.35 if t["gold"] else 0)
        plants.append((base, x, scale, t))
plants.sort(key=lambda p: p[0])

for base, x, scale, t in plants:
    h = (40 + 46 * math.sqrt(t["hold"])) * scale
    h = min(h, 640)
    rad = (7 + abs(t["r"]) * 2.1) * scale
    rad = min(rad, 52)
    color = GOLD if t["gold"] else (GREEN if t["species"] != "rootless" else shade(GREEN, 0.3))
    lean = (16 if t["dir"] == "long" else -16) * scale
    wp = wind(x, scale)
    tip = (x + lean - wp, base - h + wp * 0.18)
    pts = stem_curve(x, base, tip[0], tip[1], sway=0.13 + (0.17 if wp else 0), phase=(int(x) % 3) * 0.8)
    svg.append(f'<path d="{tapered(pts, 6.5*scale, 2.2*scale, 22)}" fill="{shade(color, 0.12)}" opacity="0.92"/>')
    if h > 150:      # leaves on tall stems
        for lf in (0.35, 0.6):
            lx_, ly_ = x + lean * lf, base - h * lf
            sgn = 1 if (int(x) + int(lf * 10)) % 2 == 0 else -1
            svg.append(f'<path d="M {lx_:.0f} {ly_:.0f} q {sgn*34*scale:.0f} {-10*scale:.0f} {sgn*52*scale:.0f} {6*scale:.0f} q {-sgn*30*scale:.0f} {14*scale:.0f} {-sgn*52*scale:.0f} {-6*scale:.0f} Z" fill="{shade(color, -0.05)}" opacity="0.75"/>')
    if t["species"] == "ai":
        svg += umbel(tip[0], tip[1] - rad * 0.15, rad, max(10, int(rad * 0.85)), shade(color, 0.05),
                     sw=2.2 * scale, dot=3.4 * scale, op=0.95 if t["gold"] else 0.85)
    elif t["species"] == "other":
        svg += five_petal(tip[0], tip[1], rad * 1.05, shade(color, 0.05), 0.85)
    else:
        svg.append(f'<ellipse cx="{tip[0]:.0f}" cy="{tip[1]-rad*0.4:.0f}" rx="{rad*0.5:.0f}" ry="{rad*0.75:.0f}" fill="{color}" fill-opacity="0.25" stroke="{shade(color,0.15)}" stroke-width="{2.4*scale:.1f}" opacity="0.85"/>')

# lake reflections: inverted flower shadows, clipped to the water
svg.append(f'<defs><clipPath id="lakeclip"><ellipse cx="{lcx:.0f}" cy="{lcy:.0f}" rx="{lrx}" ry="{lry}"/></clipPath></defs>')
svg.append(f'<g clip-path="url(#lakeclip)">')
svg.append(f'<ellipse cx="{lcx:.0f}" cy="{lcy-lry*0.55:.0f}" rx="{lrx*0.9:.0f}" ry="{lry*0.35:.0f}" fill="#dce8f0" opacity="0.35"/>')
refl = 0
for base, x, scale, t in sorted(plants, key=lambda p: -p[2]):
    if abs(x - lcx) < lrx * 1.6 and base < lcy and refl < 7:
        color = GOLD if t["gold"] else GREEN
        h = min((40 + 46 * math.sqrt(t["hold"])) * scale, 640) * 0.5
        rx_ = lcx + (x - lcx) * 0.85
        segs = int(h / 26) + 2
        pts = [(rx_ + 10 * math.sin(k * 1.6 + refl), lcy - lry * 0.6 + k * 24) for k in range(segs)]
        svg.append(f'<path d="{smooth_path(pts)}" fill="none" stroke="{color}" stroke-width="{7*scale:.1f}" opacity="0.34"/>')
        rad_r = min((7 + abs(t["r"]) * 2.1) * scale, 52) * 0.7
        svg.append(f'<circle cx="{pts[-1][0]:.0f}" cy="{pts[-1][1]:.0f}" r="{rad_r:.0f}" fill="{color}" opacity="0.22"/>')
        refl += 1
svg.append('</g>')

# ---------- THE RAIN (Hockney weather series, huge) ----------
sx0, sx1 = SX0, SX1
svg.append(f'<defs><linearGradient id="stormsky" x1="{sx0:.0f}" y1="0" x2="{sx1:.0f}" y2="0" gradientUnits="userSpaceOnUse">'
           f'<stop offset="0" stop-color="{shade(SLATE, 0.25)}" stop-opacity="0"/>'
           f'<stop offset="0.25" stop-color="{shade(SLATE, 0.25)}" stop-opacity="0.4"/>'
           f'<stop offset="0.75" stop-color="{shade(SLATE, 0.25)}" stop-opacity="0.4"/>'
           f'<stop offset="1" stop-color="{shade(SLATE, 0.25)}" stop-opacity="0"/></linearGradient></defs>')
svg.append(f'<rect x="{sx0:.0f}" y="0" width="{sx1-sx0:.0f}" height="{H*0.78:.0f}" fill="url(#stormsky)"/>')
# heavy storm clouds pressing down
for cx_, cy_, rx_, op_ in [(lcx - 300, 120, 620, 0.6), (lcx + 200, 80, 520, 0.55), (lcx - 40, 190, 720, 0.45)]:
    svg.append(f'<ellipse cx="{cx_:.0f}" cy="{cy_:.0f}" rx="{rx_}" ry="{rx_*0.2:.0f}" fill="{shade(SLATE, 0.35)}" opacity="{op_}"/>')
k = 0
for rx in range(int(sx0) + 40, int(sx1) - 20, 21):
    ln = 420 + (k * 173) % 720
    ry0 = 20 + (k * 97) % 340
    drop_end = min(ry0 + ln, ridge_y(rx + 60) + 220, lcy + 60)
    drift = 120 + (k % 5) * 26          # 斜扫:风向左
    op = 0.30 + (k % 3) * 0.12
    svg.append(f'<path d="M {rx:.0f} {ry0:.0f} q {-drift*0.32:.0f} {(drop_end-ry0)*0.55:.0f} {-drift:.0f} {drop_end-ry0:.0f}" fill="none" stroke="{shade(SLATE, 0.12)}" stroke-width="3.8" opacity="{op:.2f}" stroke-linecap="round"/>')
    if k % 2 == 0:
        svg.append(f'<path d="M {rx+9:.0f} {ry0+70:.0f} q {-drift*0.3:.0f} {(drop_end-ry0-90)*0.5:.0f} {-drift*0.9:.0f} {drop_end-ry0-90:.0f}" fill="none" stroke="#dce8f0" stroke-width="2.1" opacity="{op+0.16:.2f}" stroke-linecap="round"/>')
    k += 1
# wind streaks racing through the rain
for k in range(7):
    wy = 260 + k * 130
    wx0 = sx0 + 60 + (k * 211) % 300
    svg.append(f'<path d="M {wx0+620:.0f} {wy:.0f} q -260 {26+(k%3)*10:.0f} -620 {14+(k%4)*8:.0f}" fill="none" stroke="#dce8f0" stroke-width="2.4" opacity="0.4" stroke-linecap="round"/>')
# rain striking the ridge: splashes along the ground
for k in range(int((sx1 - sx0) / 60)):
    px = sx0 + 30 + k * 60
    py = ridge_y(px) - 4
    svg.append(f'<path d="M {px:.0f} {py:.0f} l -9 -14 M {px:.0f} {py:.0f} l 9 -14 M {px:.0f} {py:.0f} l 0 -18" stroke="#dce8f0" stroke-width="2.2" opacity="0.55" fill="none"/>')
for k in range(26):   # splashes on the lake
    px = lcx - lrx * 0.85 + k * lrx * 0.07
    py = lcy - lry * 0.3 + (k * 61 % int(lry * 0.9))
    svg.append(f'<path d="M {px:.0f} {py:.0f} l -8 -12 M {px:.0f} {py:.0f} l 8 -12" stroke="#eef4f8" stroke-width="2.6" opacity="0.7" fill="none"/>')

# ---------- vines ----------
anchors = {}
for base, x, scale, t in plants:
    h = min((40 + 46 * math.sqrt(t["hold"])) * scale, 640)
    anchors[(t["t"], t["attempt"])] = (x + (16 if t["dir"] == "long" else -16) * scale, base - h)
for day, ts in sorted(by_day.items()):
    for i, t in enumerate([q for q in ts if q["pnl"] <= 0]):
        if (t["t"], t["attempt"]) not in anchors:
            anchors[(t["t"], t["attempt"])] = (X(day) + (i - 1) * 26, ridge_y(X(day)) + 120)
for name, color in [("BE", shade(GREEN, 0.2)), ("BABA", RUST)]:
    ks = sorted(k for k in anchors if k[0] == name)
    raw = [anchors[k] for k in ks]
    pts = []
    for a, b in zip(raw, raw[1:]):        # 悬链垂坠:两锚之间下垂,像真的藤
        pts.append(a)
        sag = min(abs(b[0] - a[0]) * 0.22, 130)
        pts.append(((a[0] + b[0]) / 2, max(a[1], b[1]) + sag))
    if raw:
        pts.append(raw[-1])
    if len(pts) > 2:
        svg.append(f'<path d="{smooth_path(pts)}" fill="none" stroke="{color}" stroke-width="2.6" opacity="0.42"/>')
        for p in raw:
            svg.append(f'<circle cx="{p[0]:.0f}" cy="{p[1]:.0f}" r="4" fill="none" stroke="{color}" stroke-width="1.6" opacity="0.6"/>')

# ---------- the walker's footprints: one step per session, weight = entries ----------
entries_by_day = defaultdict(int)
for t in D["trades"]:
    entries_by_day[t["entry"]] += 1
step = 0
for d in sess:
    x = X(d)
    n = entries_by_day.get(d, 0)
    y = ridge_y(x) + 15 + 4 * (step % 2)      # 左右脚交替
    r = 2.2 + min(n, 9) * 0.55
    op = 0.18 + min(n, 9) * 0.05
    svg.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{r:.1f}" ry="{r*1.7:.1f}" fill="{INK}" opacity="{op:.2f}" transform="rotate(12 {x:.0f} {y:.0f})"/>')
    step += 1

# rain-wet blooms: drops falling from flowers inside the storm
for base, x, scale, t in plants:
    wp = wind(x, scale)
    if wp > 20 and t["pnl"] > 0:
        h = min((40 + 46 * math.sqrt(t["hold"])) * scale, 640)
        tipx, tipy = x + (16 if t["dir"] == "long" else -16) * scale - wp, base - h + wp * 0.18
        for k in range(2):
            dy = 26 + k * 30 + (int(x) % 20)
            svg.append(f'<line x1="{tipx+6-k*9:.0f}" y1="{tipy+12+dy:.0f}" x2="{tipx+6-k*9:.0f}" y2="{tipy+24+dy:.0f}" stroke="#dce8f0" stroke-width="2.6" opacity="0.6" stroke-linecap="round"/>')

# ---------- ridge contour + month stones ----------
rpts = [(x, ridge_y(x)) for x in range(0, W + 1, 40)]
svg.append(f'<path d="{tapered(rpts, 9, 4, 80)}" fill="{INK}" opacity="0.78"/>')
for m in range(1, 8):
    md = dt.date(2026, m, 1)
    x = X(md)
    y = ridge_y(x)
    svg.append(f'<rect x="{x-5:.0f}" y="{y-34:.0f}" width="10" height="26" rx="4" fill="{INK}" opacity="0.55"/>')
    eqv = eq_at(dt.date(2026, m, calendar.monthrange(2026, m)[1]) if m < 7 else D1)
    note(x + 14, y - 40, f"{'一二三四五六七'[m-1]}月", 27, INK, "start", 0.85, "normal", halo="#f5f0e3")
    note(x + 14, y - 12, f"${eqv/1e6:.2f}M", 21, INK, "start", 0.6, halo="#f5f0e3")

# key spots (close-viewing rewards)
if ("BE", 9) in anchors:
    p = anchors[("BE", 9)]
    note(p[0] + 20, p[1] - 26, "BE 第九次 · +$74,052 · 前八次全败", 23, shade(GOLD, 0.35), "start", 0.95, halo="#f5f0e3")
b = anchors.get(("BABA", 5))
if b:
    note(b[0], b[1] + 56, "BABA · 5 次 · 102 天 · 始终没有开花", 23, RUST, "middle", 0.95, halo="#f5f0e3")
fx = X(dt.date(2026, 3, 2))
note(fx, ridge_y(fx) + 950, "霜冻 · 十七连败 · −$43,833", 24, INK, "middle", 0.9, halo="#eef4f8")
note((sx0 + sx1) / 2, 96, "暴雨 6/02–6/10 · 峰值与暴雨同日", 26, "#eef4f8", "middle", 0.95, halo=shade(SLATE, 0.5))

# ---------- title & seal & footer ----------
note(150, 190, "同一个动作", 100, INK, "start", 0.9, "normal")
note(154, 250, "The Same Gesture — 2026 上半年,331 笔真实交易织成的一座山", 30, INK, "start", 0.6)
svg.append(f'<rect x="760" y="130" width="74" height="74" rx="6" fill="#9e2b1f" opacity="0.9"/>')
note(797, 165, "测", 30, "#f5f0e3", "middle", 0.95, "normal")
note(797, 196, "量", 30, "#f5f0e3", "middle", 0.95, "normal")
note(W - 60, H - 72, "山脊 = 净值曲线 · 田野 = 月份 · 伞形花 = AI 链 · 五瓣花 = 其他品种 · 金 = 扛起全部净利的 31 株", 22, INK, "end", 0.8, halo="#f5f0e3")
note(W - 60, H - 38, "枯枝 = 十七连败 · 脚印 = 交易日 · 湖 = 回撤 −$223,100 · 胜率 39.9% · +90.5% · 数据无一虚构", 22, INK, "end", 0.8, halo="#f5f0e3")

svg.append("</g></svg>")
out = Path(__file__).parent / "sketch_03_wall.svg"
out.write_text("\n".join(svg))
print("wrote", out)
