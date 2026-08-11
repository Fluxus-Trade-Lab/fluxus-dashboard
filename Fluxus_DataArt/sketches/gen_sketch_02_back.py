#!/usr/bin/env python3
"""sketch 02 · 反面 — 手迹(立轴,镜像)。
同一座梯田山从布的背面看:走线穿层 · 呼吸的山路 · 墨温 · 九个结。单色。
"""
import math, datetime as dt, calendar
from pathlib import Path
from collections import defaultdict
from art_data import load
from craft import smooth_path, tapered

D = load()
PAPER, INK = "#f3eee1", "#2b2823"
W, H = 1600, 2400
XL, XR = 250, 1355
MARGIN = 72

month_eq = {}
cum = 0.0
by_exit = sorted(D["trades"], key=lambda z: z["exit"])
for m in range(1, 8):
    for t in by_exit:
        if t["exit"].month == m:
            cum += t["pnl"]
    month_eq[m] = 1_000_000 + cum

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
    x = XL + f * (XR - XL) if idx % 2 == 0 else XR - f * (XR - XL)
    return W - x          # 镜像:布翻过来

def terrain(x, idx):
    return ROWY[idx] + 5.5 * math.sin(((W - x) - XL) / 210 + idx * 1.7)

def pos(d):
    idx = row_of(d)
    x = x_in_row(d)
    return idx, x, terrain(x, idx)

def tension_at(day):
    best, bt = None, 0.35
    for d, v in D["tension"].items():
        if d <= day and (best is None or d > best):
            best, bt = d, v
    return bt

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Georgia, serif">',
       f'<rect width="{W}" height="{H}" fill="{PAPER}"/>']

def note(x, y, s, size=13, anchor="start", op=0.8, style="italic", weight="normal", color=INK):
    svg.append(f'<text x="{x:.0f}" y="{y:.0f}" font-style="{style}" font-weight="{weight}" font-size="{size}" fill="{color}" text-anchor="{anchor}" opacity="{op}" font-family="Georgia, \'Songti SC\', serif">{s}</text>')

# ---------- ink-temperature wash above each path + the path itself ----------
sess_by_m = defaultdict(list)
for d in D["sessions"]:
    if d.year == 2026 and d.month <= 7:
        sess_by_m[d.month].append(d)

sil_days = set()
for a, b in D["silences"]:
    d = a
    while d <= b:
        sil_days.add(d); d += dt.timedelta(days=1)

for idx in range(7):
    m = idx + 1
    days = sess_by_m[m]
    # per-day ink shadow: a soft under-stroke hugging the path, darkness = tension
    for d in days:
        x = x_in_row(d)
        wpx = (XR - XL) / max(len(days), 1) * 0.92
        tt = D["tension"][d]
        gy = terrain(x, idx)
        svg.append(f'<line x1="{x-wpx/2:.1f}" y1="{gy-9:.1f}" x2="{x+wpx/2:.1f}" y2="{gy-9:.1f}" stroke="{INK}" stroke-width="4.5" opacity="{0.02+0.20*tt:.2f}" stroke-linecap="round"/>')
    # breathing path along the terrace: amplitude/frequency = tension, silences straighten
    pts, phase = [], idx * 1.3
    for d in days:
        x = x_in_row(d)
        tt = D["tension"][d]
        quiet = d in sil_days
        amp = 1.0 if quiet else 2.2 + tt * 13
        phase += (0.5 if quiet else 0.95 + tt * 2.2)
        pts.append((x, terrain(x, idx) + math.sin(phase) * amp))
    pts.sort(key=lambda p: p[0], reverse=(idx % 2 == 0))   # 镜像后行进方向反转
    if len(pts) > 2:
        svg.append(f'<path d="{smooth_path(pts)}" fill="none" stroke="{INK}" stroke-width="1.25" opacity="0.8"/>')
    # month marker at (mirrored) end side
    endx = (W - (XR + 26)) if idx % 2 == 0 else (W - (XL - 26))
    anchor = "end" if idx % 2 == 0 else "start"
    note(endx, ROWY[idx] - 6, f"{'一二三四五六七'[idx]}月", 14, anchor, 0.6, "normal")

# ---------- thread floats: entry -> exit across the mountain ----------
for t in by_exit:
    i1, x1, y1 = pos(max(t["entry"], dt.date(2026, 1, 1)))
    i2, x2, y2 = pos(t["exit"])
    tt = tension_at(t["entry"])
    wgt = 0.5 + min(t["risk_pct"], 1.2) * 1.7
    op = 0.12 + 0.42 * tt
    if i1 == i2:
        sag = min(abs(x2 - x1) * 0.16, 34)
        svg.append(f'<path d="M {x1:.1f} {y1-4:.1f} Q {(x1+x2)/2:.1f} {y1-4+sag:.1f} {x2:.1f} {y2-4:.1f}" fill="none" stroke="{INK}" stroke-width="{wgt:.2f}" opacity="{op:.2f}" stroke-linecap="round"/>')
    else:
        mid = [(x2 + (i2 - rr - 1) * 4, terrain(x2, rr) - 5) for rr in range(i1, i2)]
        pts = [(x1, y1 - 4)] + mid + [(x2, y2 - 4)]
        svg.append(f'<path d="{smooth_path(pts)}" fill="none" stroke="{INK}" stroke-width="{wgt:.2f}" opacity="{op:.2f}" stroke-linecap="round"/>')
    svg.append(f'<circle cx="{x2:.1f}" cy="{y2-4:.1f}" r="1.5" fill="{INK}" opacity="{min(op*1.5,0.7):.2f}"/>')

# ---------- bursts: knot clusters on the path ----------
for d in D["bursts"]:
    idx, x, gy = pos(d)
    for k in range(6):
        a = k / 6 * 2 * math.pi
        svg.append(f'<circle cx="{x+math.cos(a)*4.6:.1f}" cy="{gy-2+math.sin(a)*3.4:.1f}" r="1.35" fill="{INK}" opacity="0.55"/>')

# ---------- nine knots + collage quotes ----------
for i, (ds, label, quote) in enumerate(D["keyframes"]):
    d = dt.date.fromisoformat(ds)
    idx, x, gy = pos(d)
    svg.append(f'<circle cx="{x:.1f}" cy="{gy-2:.1f}" r="4.2" fill="{INK}" opacity="0.9"/>')
    svg.append(f'<circle cx="{x:.1f}" cy="{gy-2:.1f}" r="7.8" fill="none" stroke="{INK}" stroke-width="0.9" opacity="0.5"/>')
    above = i % 2 == 0
    ty = gy - 64 - (i % 2) * 10 if above else gy + 58
    x = min(max(x, XL - 40), XR + 40)
    svg.append(f'<line x1="{x:.0f}" y1="{gy + (-11 if above else 7):.0f}" x2="{x:.0f}" y2="{ty + (8 if above else -14):.0f}" stroke="{INK}" stroke-width="0.55" opacity="0.4"/>')
    note(x, ty, f"{d.month}/{d.day} {label}", 13.5, "middle", 0.9, "normal")
    note(x, ty + 19, quote, 12.5, "middle", 0.6)

# the two symmetries
p423, p428 = pos(dt.date(2026, 4, 23)), pos(dt.date(2026, 4, 28))
note((p423[1] + p428[1]) / 2, ROWY[3] + 96, "认输与收获,同一周", 12.5, "middle", 0.6)
p602 = pos(dt.date(2026, 6, 2))
note(p602[1], ROWY[5] - 92, "峰值与暴雨,同一天", 12.5, "middle", 0.6)

# ---------- frame, title, ghost seal, footer ----------
svg.append(f'<rect x="{MARGIN}" y="{MARGIN}" width="{W-2*MARGIN}" height="{H-2*MARGIN}" fill="none" stroke="{INK}" stroke-width="1.5" opacity="0.5"/>')
svg.append(f'<rect x="{MARGIN+14}" y="{MARGIN+14}" width="{W-2*MARGIN-28}" height="{H-2*MARGIN-28}" fill="none" stroke="{INK}" stroke-width="0.55" opacity="0.35"/>')

tx = 118    # 镜像:题字在左
for i, ch in enumerate("反面手迹"):
    note(tx, 220 + i * 62, ch, 46, "middle", 0.9, "normal")
note(tx, 220 + 4 * 62 + 6, "the reverse", 13, "middle", 0.45)
sy = 220 + 4 * 62 + 34
svg.append(f'<rect x="{tx-23}" y="{sy}" width="46" height="46" rx="3.5" fill="none" stroke="{INK}" stroke-width="1.2" opacity="0.55"/>')
note(tx, sy + 20, "手", 17, "middle", 0.6, "normal")
note(tx, sy + 39, "迹", 17, "middle", 0.6, "normal")

note(W - XL, 200, "同一座山,从布的背面看。没有颜色:向内的博弈里没有结果,只有动作。", 14, "end", 0.6)
note(W - XL, 224, "走线 = 每笔从入场到离场 · 粗细 = 风险重量 · 浓淡 = 手的紧张度 · 山路的抖动 = 呼吸", 14, "end", 0.6)
note(W - XL, H - 116, "密结 = 爆发日(21 天) · 拉直的路 = 沉默期(15 段) · 九个结 = 拼贴的原句(句子是真的,位置是策展的)", 12, "end", 0.5)
note(W - XL, H - 96, "27/31 句为实录 · 4 句[重构] · 镜像时间轴:布翻过来,一月在右下", 12, "end", 0.5)

svg.append("</svg>")
out = Path(__file__).parent / "sketch_02_back.svg"
out.write_text("\n".join(svg))
print("wrote", out)
