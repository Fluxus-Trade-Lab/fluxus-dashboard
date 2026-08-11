#!/usr/bin/env python3
"""sketch 04 — 反面·手迹的墙面版(5000×2000,镜像)。
同一面墙翻过来:素布,一根呼吸的山路,331 根悬线(垂深 = 持仓天数),
正面的湖、雨、太阳只剩透过布看到的影子。单色墨。
"""
import math, datetime as dt
from pathlib import Path
from collections import defaultdict
from art_data import load
from craft import smooth_path

D = load()
W, H = 5000, 2000
CLOTH, INK = "#f1ece0", "#2b2823"
D0, D1 = dt.date(2025, 12, 29), dt.date(2026, 7, 24)

def Xf(day):                      # 正面坐标
    return (day - D0).days / (D1 - D0).days * W
def RX(x):                        # 镜像
    return W - x

by_exit = sorted(D["trades"], key=lambda z: z["exit"])
eq_by_day, cum = {}, 0.0
for t in by_exit:
    cum += t["pnl"]
    eq_by_day[t["exit"]] = cum
days_sorted = sorted(eq_by_day)
def eq_at(d):
    v = 0.0
    for dd in days_sorted:
        if dd <= d:
            v = eq_by_day[dd]
        else:
            break
    return 1_000_000 + v

STORM0, STORM1 = D["storm"]
def ridge_y(x):
    d = D0 + dt.timedelta(days=x / W * (D1 - D0).days)
    y = 1450 - (eq_at(d) - 1_000_000) / 1_050_000 * 930
    sx0, sx1 = Xf(STORM0), Xf(STORM1)
    if sx0 - 60 < x < sx1 + 260:
        t = (x - (sx0 - 60)) / (sx1 + 260 - (sx0 - 60))
        y += 115 * math.sin(t * math.pi) ** 1.5
    return y

def tension_at(day):
    best, bt = None, 0.35
    for d, v in D["tension"].items():
        if d <= day and (best is None or d > best):
            best, bt = d, v
    return bt

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Georgia, serif">',
       f'<rect width="{W}" height="{H}" fill="{CLOTH}"/>']

def note(x, y, s, size=26, anchor="start", op=0.8, style="italic", weight="normal", color=INK, halo=None):
    common = (f'x="{x:.0f}" y="{y:.0f}" font-style="{style}" font-weight="{weight}" font-size="{size}" '
              f'text-anchor="{anchor}" font-family="Georgia, \'Songti SC\', serif"')
    if halo:
        svg.append(f'<text {common} fill="none" stroke="{halo}" stroke-width="{size*0.28:.0f}" stroke-linejoin="round" opacity="{min(op+0.1,1):.2f}">{s}</text>')
    svg.append(f'<text {common} fill="{color}" opacity="{op}">{s}</text>')

# ---------- cloth weave ----------
for k in range(0, W, 90):
    svg.append(f'<line x1="{k}" y1="0" x2="{k}" y2="{H}" stroke="{INK}" stroke-width="0.5" opacity="0.030"/>')
for k in range(0, H, 90):
    svg.append(f'<line x1="0" y1="{k}" x2="{W}" y2="{k}" stroke="{INK}" stroke-width="0.5" opacity="0.030"/>')

# ---------- ghosts of the front, seen through the cloth ----------
# ghost ridge fill
gpts = [(RX(x), ridge_y(x)) for x in range(0, W + 1, 60)]
svg.append(f'<path d="{smooth_path(gpts)} L 0 {H} L {W} {H} Z" fill="{INK}" opacity="0.035"/>')
# ghost month boundaries
for m in range(2, 8):
    x = RX(Xf(dt.date(2026, m, 1)))
    svg.append(f'<line x1="{x:.0f}" y1="{ridge_y(RX(x)):.0f}" x2="{x:.0f}" y2="{H}" stroke="{INK}" stroke-width="1.2" opacity="0.06" stroke-dasharray="3 14"/>')
# ghost lake (dashed)
lcx_f = Xf(dt.date(2026, 6, 7)) + 60
lcy = ridge_y(lcx_f) + 265
svg.append(f'<ellipse cx="{RX(lcx_f):.0f}" cy="{lcy:.0f}" rx="385" ry="104" fill="none" stroke="{INK}" stroke-width="1.6" opacity="0.16" stroke-dasharray="7 9"/>')
note(RX(lcx_f), lcy + 6, "湖的影子", 22, "middle", 0.18)
# ghost rain (faint hatch) + ghost sun
gx0, gx1 = RX(Xf(STORM1) + 560), RX(Xf(STORM0) - 260)
for k in range(int(gx0), int(gx1), 60):
    svg.append(f'<line x1="{k}" y1="{140+(k%5)*30}" x2="{k-40}" y2="{ridge_y(RX(k))-40:.0f}" stroke="{INK}" stroke-width="0.9" opacity="0.05"/>')
sun_x = RX(Xf(dt.date(2026, 7, 14)))
svg.append(f'<circle cx="{sun_x:.0f}" cy="300" r="90" fill="none" stroke="{INK}" stroke-width="1.4" opacity="0.12" stroke-dasharray="4 8"/>')

# ---------- hanging threads: one per trade, depth = days held ----------
sess = [d for d in D["sessions"] if D0 <= d <= D1]
for t in by_exit:
    e = max(t["entry"], dt.date(2026, 1, 1))
    x1, x2 = RX(Xf(e)), RX(Xf(t["exit"]))
    y1, y2 = ridge_y(Xf(e)), ridge_y(Xf(t["exit"]))
    tt = tension_at(t["entry"])
    wgt = 0.6 + min(t["risk_pct"], 1.2) * 2.0
    op = 0.10 + 0.40 * tt
    sag = 40 + min(t["hold"], 110) * 4.6          # 持仓越久,线垂得越深
    mx, my = (x1 + x2) / 2, max(y1, y2) + sag
    svg.append(f'<path d="M {x1:.1f} {y1:.1f} Q {mx:.1f} {my:.1f} {x2:.1f} {y2:.1f}" fill="none" stroke="{INK}" stroke-width="{wgt:.2f}" opacity="{op:.2f}" stroke-linecap="round"/>')
    svg.append(f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="2.2" fill="{INK}" opacity="{min(op*1.6,0.75):.2f}"/>')

# BABA 的三根最深的线,点名
deep = sorted([t for t in by_exit if t["t"] == "BABA"], key=lambda z: -z["hold"])[:3]
if deep:
    t0 = deep[0]
    mx = (RX(Xf(t0["entry"])) + RX(Xf(t0["exit"]))) / 2
    my = max(ridge_y(Xf(t0["entry"])), ridge_y(Xf(t0["exit"]))) + 40 + min(t0["hold"], 110) * 4.6
    mx = min(max(mx, 460), W - 460)
    my = min(my + 46, H - 220)
    note(mx, my, "垂得最深的三根线,都是 BABA · 102 / 99 / 93 天", 24, "middle", 0.7, halo=CLOTH)

# ---------- the breathing path (the mountain road itself) ----------
sil_days = set()
for a, b in D["silences"]:
    d = a
    while d <= b:
        sil_days.add(d); d += dt.timedelta(days=1)
pts, phase = [], 0.0
for d in sess:
    x = RX(Xf(d))
    tt = D["tension"][d]
    quiet = d in sil_days
    amp = 1.4 if quiet else 3.2 + tt * 21
    phase += (0.5 if quiet else 0.95 + tt * 2.3)
    pts.append((x, ridge_y(Xf(d)) + math.sin(phase) * amp))
    # ink temperature: shadow dash under the path
    svg.append(f'<line x1="{x-13:.0f}" y1="{ridge_y(Xf(d))+26:.0f}" x2="{x+13:.0f}" y2="{ridge_y(Xf(d))+26:.0f}" stroke="{INK}" stroke-width="7" opacity="{0.02+0.16*tt:.2f}" stroke-linecap="round"/>')
pts.sort(key=lambda p: p[0])
svg.append(f'<path d="{smooth_path(pts)}" fill="none" stroke="{INK}" stroke-width="2.6" opacity="0.85"/>')

# bursts: knot clusters on the path
for d in D["bursts"]:
    x = RX(Xf(d))
    gy = ridge_y(Xf(d))
    for k in range(6):
        a = k / 6 * 2 * math.pi
        svg.append(f'<circle cx="{x+math.cos(a)*7:.1f}" cy="{gy+math.sin(a)*5:.1f}" r="2.4" fill="{INK}" opacity="0.6"/>')

# ---------- nine knots + collage quotes ----------
for i, (ds, label, quote) in enumerate(D["keyframes"]):
    d = dt.date.fromisoformat(ds)
    x = RX(Xf(d))
    gy = ridge_y(Xf(d))
    svg.append(f'<circle cx="{x:.1f}" cy="{gy:.1f}" r="7.5" fill="{INK}" opacity="0.9"/>')
    svg.append(f'<circle cx="{x:.1f}" cy="{gy:.1f}" r="14" fill="none" stroke="{INK}" stroke-width="1.6" opacity="0.5"/>')
    above = i % 2 == 0
    ty = gy - 120 - (i % 3) * 46 if above else gy + 150 + (i % 3) * 46
    ty = max(150, min(ty, H - 90))
    svg.append(f'<line x1="{x:.0f}" y1="{gy + (-18 if above else 14):.0f}" x2="{x:.0f}" y2="{ty + (12 if above else -26):.0f}" stroke="{INK}" stroke-width="1" opacity="0.4"/>')
    note(x, ty, f"{d.month}/{d.day} {label}", 30, "middle", 0.9, "normal", halo=CLOTH)
    note(x, ty + 34, quote, 26, "middle", 0.65, halo=CLOTH)

# the two symmetries
x423, x428 = RX(Xf(dt.date(2026, 4, 23))), RX(Xf(dt.date(2026, 4, 28)))
y423 = ridge_y(Xf(dt.date(2026, 4, 25)))
svg.append(f'<path d="M {x423:.0f} {y423+300:.0f} Q {(x423+x428)/2:.0f} {y423+340:.0f} {x428:.0f} {y423+300:.0f}" fill="none" stroke="{INK}" stroke-width="1.2" opacity="0.5"/>')
note((x423 + x428) / 2, y423 + 376, "认输与收获,同一周", 24, "middle", 0.65)

# ---------- title, outline seal, footer ----------
note(W - 150, 190, "同一个动作 · 反面", 88, "end", 0.9, "normal")
note(W - 154, 248, "the reverse — 同一批针脚,从布的背面看。没有颜色:向内的博弈里没有结果,只有动作。", 28, "end", 0.55)
svg.append(f'<rect x="{W-224}" y="282" width="70" height="70" rx="6" fill="none" stroke="{INK}" stroke-width="2" opacity="0.55"/>')
note(W - 189, 315, "手", 28, "middle", 0.6, "normal")
note(W - 189, 344, "迹", 28, "middle", 0.6, "normal")
note(150, H - 60, "悬线 = 每一笔,垂深 = 持仓天数 · 粗细 = 风险重量 · 浓淡 = 手的紧张度 · 山路的抖动 = 呼吸 · 密结 = 爆发日 · 拉直 = 沉默", 24, "start", 0.55)
note(150, H - 100, "九个结 = 拼贴的原句(27/31 为实录,句子是真的,位置是策展的) · 镜像:一月在右", 24, "start", 0.55)

svg.append("</svg>")
out = Path(__file__).parent / "sketch_04_back_wall.svg"
out.write_text("\n".join(svg))
print("wrote", out)
