#!/usr/bin/env python3
"""sketch 01 · 反面 — 手迹:同一批针脚从背面看。
镜像时间轴(翻布) · 线迹 = 每笔的 entry→exit 走线 · 呼吸线 + 墨温 + 九个结。单色。
"""
import math, random, datetime as dt
from pathlib import Path
from art_data import load

rng = random.Random(1017)
D = load()

PAPER, INK = "#f3efe4", "#2f2b26"
W, H = 2300, 1420
RX0, RX1 = 150, 2210
D0, D1 = dt.date(2025, 12, 29), dt.date(2026, 7, 24)
BAND0, BAND1 = 300, 860      # thread float band
BREATH_Y = 1020

def X(day):  # 镜像:翻过布来,时间从右往左
    x = RX0 + (day - D0).days / (D1 - D0).days * (RX1 - RX0)
    return RX0 + RX1 - x

def tension_at(day):
    best, bt = None, 0.35
    for d, v in D["tension"].items():
        if d <= day and (best is None or d > best):
            best, bt = d, v
    return bt

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Georgia, serif">',
       f'<rect width="{W}" height="{H}" fill="{PAPER}"/>']
def note(x, y, s, size=14, anchor="start", op=0.8, style="italic", weight="normal", color=INK):
    svg.append(f'<text x="{x:.0f}" y="{y:.0f}" font-style="{style}" font-weight="{weight}" font-size="{size}" fill="{color}" text-anchor="{anchor}" opacity="{op}" font-family="Georgia, \'Songti SC\', serif">{s}</text>')
def jpath(pts, wob=1.5):
    p = [(x + rng.uniform(-wob, wob), y + rng.uniform(-wob, wob)) for x, y in pts]
    d = f"M {p[0][0]:.1f} {p[0][1]:.1f}"
    for a, b in zip(p, p[1:]):
        d += f" Q {a[0]:.1f} {a[1]:.1f} {(a[0]+b[0])/2:.1f} {(a[1]+b[1])/2:.1f}"
    return d + f" T {p[-1][0]:.1f} {p[-1][1]:.1f}"

for _ in range(420):
    svg.append(f'<circle cx="{rng.uniform(0,W):.0f}" cy="{rng.uniform(0,H):.0f}" r="{rng.uniform(0.3,0.9):.1f}" fill="{INK}" opacity="0.03"/>')

# ---------------- thread floats: entry -> exit, one per trade ----------------
# 反面看到的是走线:从入场日到离场日的一根浮线。粗细 = 风险重量,浓淡 = 当日手的紧张度。
lanes = 40
for i, t in enumerate(sorted(D["trades"], key=lambda z: z["entry"])):
    x1, x2 = X(t["entry"]), X(t["exit"])
    lane = i % lanes
    y = BAND0 + (BAND1 - BAND0) * lane / lanes + rng.uniform(-4, 4)
    tt = tension_at(t["entry"])
    wgt = 0.6 + min(t["risk_pct"], 1.2) * 2.1
    op = 0.16 + 0.5 * tt
    sag = min(abs(x2 - x1) * 0.10, 46) * (1 if lane % 2 == 0 else -0.6)
    mx = (x1 + x2) / 2
    svg.append(f'<path d="M {x1:.1f} {y:.1f} Q {mx:.1f} {y+sag:.1f} {x2:.1f} {y:.1f}" fill="none" stroke="{INK}" stroke-width="{wgt:.2f}" opacity="{op:.2f}" stroke-linecap="round"/>')
    # 线尾的小结 = 离场
    svg.append(f'<circle cx="{x2:.1f}" cy="{y:.1f}" r="1.6" fill="{INK}" opacity="{op*0.9:.2f}"/>')
note(RX0, BAND0 - 46, "走线 = 每一笔从入场到离场的线程(粗细 = 风险重量,浓淡 = 当日手的紧张度)", 13, "start", 0.55)
note(RX0, BAND0 - 26, "镜像时间轴——布翻过来,七月在左", 13, "start", 0.45)

# burst days: knot clusters just under the band
for d in D["bursts"]:
    x = X(d)
    for k in range(6):
        svg.append(f'<circle cx="{x+rng.uniform(-7,7):.1f}" cy="{BAND1+16+rng.uniform(-5,5):.1f}" r="{rng.uniform(1.2,2.4):.1f}" fill="{INK}" opacity="0.5"/>')
note(RX0, BAND1 + 22, "密结 = 爆发日(≥5 笔,共 21 天)", 13, "start", 0.55)

# ---------------- ink-temperature strip (墨温) ----------------
sess = [d for d in D["sessions"] if D0 <= d <= D1]
for i, d in enumerate(sess):
    x = X(d)
    nx = X(sess[i + 1]) if i + 1 < len(sess) else RX0
    tt = D["tension"][d]
    x0, x1 = min(x, nx), max(x, nx)
    svg.append(f'<rect x="{x0:.1f}" y="{H-104}" width="{max(x1-x0,1):.1f}" height="26" fill="{INK}" opacity="{0.05+0.5*tt:.2f}"/>')
note(RX0, H - 116, "墨温 = 手的紧张度(连败深度 + sizing 离散 + 开仓密度的合成)——画的不是情绪,是情绪的脚印", 13, "start", 0.55)

# ---------------- breathing line (园丁的呼吸线) ----------------
sil_days = set()
for a, b in D["silences"]:
    d = a
    while d <= b:
        sil_days.add(d); d += dt.timedelta(days=1)
pts = []
phase = 0.0
for d in sess:
    x = X(d)
    tt = D["tension"][d]
    quiet = d in sil_days
    amp = 1.2 if quiet else 3 + tt * 24
    phase += (0.6 if quiet else 1.1 + tt * 2.6)
    pts.append((x, BREATH_Y + math.sin(phase) * amp))
pts.sort(key=lambda p: p[0])
svg.append(f'<path d="{jpath(pts, 0.8)}" fill="none" stroke="{INK}" stroke-width="1.3" opacity="0.75"/>')
note(RX1, BREATH_Y - 58, "园丁的呼吸线:连败时抖,爆发时急,沉默期拉直", 13, "end", 0.55)

# silences: label the longest one
a, b = max(D["silences"], key=lambda ab: (ab[1] - ab[0]).days)
xm = (X(a) + X(b)) / 2
svg.append(f'<line x1="{X(a):.0f}" y1="{BREATH_Y+40:.0f}" x2="{X(b):.0f}" y2="{BREATH_Y+40:.0f}" stroke="{INK}" stroke-width="0.7" opacity="0.4"/>')
note(xm, BREATH_Y + 58, "最长的沉默:6/28–7/05,七天", 13, "middle", 0.55)

# ---------------- nine knots + collage lines ----------------
for i, (ds, label, quote) in enumerate(D["keyframes"]):
    d = dt.date.fromisoformat(ds)
    x = X(d)
    yy = BREATH_Y
    svg.append(f'<circle cx="{x:.1f}" cy="{yy:.1f}" r="4.6" fill="{INK}" opacity="0.85"/>')
    svg.append(f'<circle cx="{x:.1f}" cy="{yy:.1f}" r="8.5" fill="none" stroke="{INK}" stroke-width="1" opacity="0.45"/>')
    above = i % 2 == 0
    ty = yy - 118 - (i % 3) * 30 if above else yy + 108 + (i % 3) * 30
    svg.append(f'<line x1="{x:.0f}" y1="{yy + (-10 if above else 10):.0f}" x2="{x:.0f}" y2="{ty + (8 if above else -14):.0f}" stroke="{INK}" stroke-width="0.6" opacity="0.35"/>')
    note(x, ty, f"{d.month}/{d.day} {label}", 14.5, "middle", 0.85, "normal")
    note(x, ty + 20, quote, 13.5, "middle", 0.6)

# the two cruel symmetries
x423, x428 = X(dt.date(2026, 4, 23)), X(dt.date(2026, 4, 28))
svg.append(f'<path d="M {x423:.0f} {BREATH_Y+176:.0f} Q {(x423+x428)/2:.0f} {BREATH_Y+200:.0f} {x428:.0f} {BREATH_Y+176:.0f}" fill="none" stroke="{INK}" stroke-width="0.8" opacity="0.5"/>')
note((x423 + x428) / 2, BREATH_Y + 222, "认输与收获,同一周", 13.5, "middle", 0.65)

# ---------------- title & footer ----------------
note(RX0, 64, "同一个动作 — 反面:手迹", 34, "start", 0.95, "normal")
note(RX0, 96, "同一批针脚,从背面看。没有颜色:向内的博弈里没有结果,只有动作。", 15, "start", 0.55)
note(RX0, H - 26, "Fluxus DataArt · sketch 01 反面 · 27/31 句为实录原句(句子是真的,位置是策展的)· 4 句 [重构]", 13, "start", 0.5)

svg.append("</svg>")
out = Path(__file__).parent / "sketch_01_back.svg"
out.write_text("\n".join(svg))
print("wrote", out)
