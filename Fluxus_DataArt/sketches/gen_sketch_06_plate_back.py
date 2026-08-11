#!/usr/bin/env python3
"""sketch 06 — the reverse · 已批准版画(sketch 05)的反面(5000×2100)。
布翻过来:同一几何,水平镜像,一月在右。
论点:盈亏是给世界看的,挣扎是自己的。
单色墨于素布——向内没有结果,只有动作。
① 呼吸线:逐日振幅/频率 = tension,沉默期拉直
② 331 根悬线:入场挂到离场,垂深 = 持仓天数,粗细 = risk%,浓淡 = 入场日 tension
③ 九个实心结 = keyframes(句子是真的,位置是策展的)
④ 爆发日密结 + 墨温影线
⑤ 正面结构的虚影(事件带边界 · 净值幽灵线)
⑥ 两个对句:认输与收获同一周 · 峰值与暴雨同一天
"""
import math, datetime as dt
from pathlib import Path
from collections import defaultdict
from art_data import load

D = load()

W, H = 5000, 2100
CLOTH, INK = "#f1ece0", "#2b2823"
SEAL = "#9e2b1f"

# ---- mirrored geometry (front: X0=300..X1=4260; back = W - x) ----
D0, D1 = dt.date(2025, 12, 29), dt.date(2026, 7, 24)
XR, XL = 4700, 740            # D0 at right, D1 at left
SPAN_D = (D1 - D0).days       # 207

def X(day):
    return XR - (day - D0).days / SPAN_D * (XR - XL)

SPINE = 1270                  # same axis height as the front
AMP_MAX = 44                  # breathing amplitude at tension = 1.0
DEPTH_MAX = 620               # catenary depth at hold = 102 days
HOLD_MAX = 102

def depth_of(hold):
    return max(10.0, hold / HOLD_MAX * DEPTH_MAX)

def w_of(risk_pct):           # stroke width, sqrt scale capped at 4%
    return 0.5 + math.sqrt(min(risk_pct, 4.0) / 4.0) * 3.0

def op_of(tension):           # ink darkness by entry-day tension
    return 0.15 + 0.62 * tension

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Georgia, serif">',
       f'<rect width="{W}" height="{H}" fill="{CLOTH}"/>']

def note(x, y, s, size=22, color=INK, anchor="start", op=0.8, style="italic", weight="normal"):
    svg.append(f'<text x="{x:.0f}" y="{y:.0f}" font-style="{style}" font-weight="{weight}" font-size="{size}" fill="{color}" text-anchor="{anchor}" opacity="{op}" font-family="Georgia, \'Songti SC\', serif">{s}</text>')

def hline(x1, x2, y, wd=0.8, op=0.3, color=INK, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    svg.append(f'<line x1="{x1:.0f}" y1="{y:.1f}" x2="{x2:.0f}" y2="{y:.1f}" stroke="{color}" stroke-width="{wd}" opacity="{op}"{d}/>')

def vline(x, y1, y2, wd=0.8, op=0.3, color=INK, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    svg.append(f'<line x1="{x:.1f}" y1="{y1:.0f}" x2="{x:.1f}" y2="{y2:.0f}" stroke="{color}" stroke-width="{wd}" opacity="{op}"{d}/>')

sess = [d for d in D["sessions"] if D0 <= d <= D1]
tension = D["tension"]

# ================= ⑤ ghosts of the front: event bands (dashed boundaries) =================
for (a, b), label in [(D["frost"], "霜冻期的虚影 2/26–3/07(盈亏留在正面)"),
                      (D["storm"], "回撤窗口的虚影 6/02–6/10")]:
    xa, xb = X(b) - 12, X(a)          # mirrored: later date is further left
    svg.append(f'<rect x="{xa:.0f}" y="330" width="{xb-xa:.0f}" height="1690" fill="{INK}" opacity="0.035"/>')
    vline(xa, 330, 2020, 0.8, 0.30, INK, "2 5")
    vline(xb, 330, 2020, 0.8, 0.30, INK, "2 5")
    note(xb, 316, label, 21, INK, "end", 0.55)

# ================= month grid (mirrored) =================
month_edges = [dt.date(2026, m, 1) for m in range(1, 8)] + [D1]
for m in range(1, 8):
    x = X(dt.date(2026, m, 1))
    vline(x, 460, 2016, 0.7, 0.14)
    nxt = month_edges[m] if m < 7 else D1
    cx = (X(dt.date(2026, m, 1)) + X(nxt)) / 2
    note(cx, 2046, f"{m} 月", 24, INK, "middle", 0.55, "normal")
note(XR, 150, "布翻了过来:时间从右向左读,一月在右 ←", 22, INK, "end", 0.6)

# ================= depth ruler (hold days, linear) =================
for h in [30, 60, 90]:
    y = SPINE + depth_of(h)
    hline(XL, XR, y, 0.6, 0.09)
    note(XR + 26, y + 7, f"{h} 天", 20, INK, "start", 0.5)
y102 = SPINE + DEPTH_MAX
hline(XL, XR, y102, 0.6, 0.09, INK, "6 6")
note(XR + 26, y102 + 7, "102 天(最深)", 20, INK, "start", 0.5)
note(XR + 26, SPINE + 96, "垂深 = 持仓天数", 20, INK, "start", 0.55)
note(XR + 26, SPINE + 124, "(线性标尺)", 18, INK, "start", 0.45)

# ================= ④ ink-temperature band (tension per session) =================
TB_Y0, TB_Y1 = SPINE - 56, SPINE - 32
for i, d in enumerate(sess):
    x2 = X(d)
    x1 = X(sess[i + 1]) if i + 1 < len(sess) else XL
    t = tension[d]
    svg.append(f'<rect x="{x1:.1f}" y="{TB_Y0}" width="{max(x2-x1,1.5):.1f}" height="{TB_Y1-TB_Y0}" fill="{INK}" opacity="{0.03+0.55*t:.3f}"/>')
svg.append(f'<rect x="{XL:.0f}" y="{TB_Y0}" width="{XR-XL:.0f}" height="{TB_Y1-TB_Y0}" fill="none" stroke="{INK}" stroke-width="0.7" opacity="0.35"/>')
note(XR + 26, TB_Y0 + 4, "墨温 = 紧张度(浓 = 紧)", 20, INK, "start", 0.55)

# ================= ① the breathing line =================
in_silence = {}
for d in sess:
    in_silence[d] = any(a < d < b for a, b in D["silences"])

amp = {d: (0.0 if in_silence[d] else AMP_MAX * tension[d]) for d in sess}
freq = {d: 0.8 + 3.4 * tension[d] for d in sess}   # rad / day

breath_y = {}
pts = []
phase = 0.0
for i, d in enumerate(sess):
    if i == 0:
        breath_y[d] = SPINE - amp[d] * math.sin(phase)
        pts.append((X(d), breath_y[d]))
        continue
    d0 = sess[i - 1]
    gap = (d - d0).days
    n = max(4, gap * 5)
    for k in range(1, n + 1):
        t_ = k / n
        a_ = amp[d0] + (amp[d] - amp[d0]) * t_
        f_ = freq[d0] + (freq[d] - freq[d0]) * t_
        phase += f_ * (gap / n)
        day_frac = (d0 - D0).days + gap * t_
        x = XR - day_frac / SPAN_D * (XR - XL)
        y = SPINE - a_ * math.sin(phase)
        pts.append((x, y))
    breath_y[d] = pts[-1][1]

def by(day):
    """breathing-line y at a date (nearest session <= date)."""
    if day in breath_y:
        return breath_y[day]
    prev = [s for s in sess if s <= day]
    return breath_y[prev[-1]] if prev else breath_y[sess[0]]

# rest baseline (dotted) + amplitude ruler at right end
hline(XL, XR, SPINE, 0.7, 0.12, INK, "1 6")
rx = XR + 8
vline(rx, SPINE - AMP_MAX, SPINE + AMP_MAX, 0.8, 0.4)
for yy in (SPINE - AMP_MAX, SPINE, SPINE + AMP_MAX):
    hline(rx - 4, rx + 4, yy, 0.8, 0.4)
note(XR + 26, SPINE - 6, "满幅 = 紧张度 1.0", 18, INK, "start", 0.5)
note(XR + 26, SPINE + AMP_MAX + 4, "基线 = 0", 18, INK, "start", 0.45)

# ================= ② 331 hanging threads =================
threads = sorted(D["trades"], key=lambda z: z["hold"])   # deep ones drawn last
for t in threads:
    xe, xx = X(t["entry"]), X(t["exit"])                 # entry right, exit left
    ye, yx = by(t["entry"]), by(t["exit"])
    dep = depth_of(t["hold"])
    wd = w_of(t["risk_pct"])
    op = op_of(tension.get(t["entry"], 0.0))
    if abs(xe - xx) < 2.5:                               # 1-day hold: a short drop
        vline(xe, ye, ye + dep, wd, op, INK)
    else:
        cx_, cy_ = (xe + xx) / 2, (ye + yx) / 2 + 2 * dep
        svg.append(f'<path d="M {xe:.1f} {ye:.1f} Q {cx_:.1f} {cy_:.1f} {xx:.1f} {yx:.1f}" fill="none" stroke="{INK}" stroke-width="{wd:.2f}" opacity="{op:.3f}" stroke-linecap="round"/>')

# the breathing line drawn over the threads
path = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
svg.append(f'<path d="{path}" fill="none" stroke="{INK}" stroke-width="1.9" opacity="0.9"/>')

# ================= ④ burst-day knots (one wrap per entry) =================
entries_by_day = defaultdict(int)
for t in D["trades"]:
    entries_by_day[t["entry"]] += 1
for d in D["bursts"]:
    n = entries_by_day[d]
    x = X(d)
    yb_ = by(d)
    for k in range(n):
        xx_ = x + (k - (n - 1) / 2) * 3.0
        vline(xx_, yb_ - 11, yb_ + 11, 1.2, 0.65)
note(X(dt.date(2026, 5, 14)), TB_Y0 - 12, "5/14 · 9 仓", 18, INK, "middle", 0.5)

# ================= silences: straightened + overline for the long ones =================
long_sil = [s for s in D["silences"] if (s[1] - s[0]).days >= 5]
for i, (a, b) in enumerate(long_sil):
    days = (b - a).days
    xa, xb = X(b) + 5, X(a) - 5        # mirrored
    yb_ = TB_Y0 - 26 - (26 if i % 2 else 0)   # two tiers against neighbours
    svg.append(f'<path d="M {xa:.0f} {yb_+8} L {xa:.0f} {yb_} L {xb:.0f} {yb_} L {xb:.0f} {yb_+8}" fill="none" stroke="{INK}" stroke-width="0.9" opacity="0.45"/>')
    lab = f"沉默 {days} 天" + (",线拉直" if days == 7 else "")
    note((xa + xb) / 2, yb_ - 10, lab, 18, INK, "middle", 0.5)

# ================= ⑤ ghost equity line (dashed, mirrored) =================
by_exit = sorted(D["trades"], key=lambda z: z["exit"])
eq_by_day, cum = {}, 0.0
for t in by_exit:
    cum += t["pnl"]
    eq_by_day[t["exit"]] = 1_000_000 + cum
EQ_Y0, EQ_Y1 = 430, 200
def eq_y(v):
    return EQ_Y0 - (v - 1_000_000) / 1_100_000 * (EQ_Y0 - EQ_Y1)
for v, lab in [(1_000_000, "$1.0M"), (1_500_000, "$1.5M"), (2_000_000, "$2.0M")]:
    hline(XL, XR, eq_y(v), 0.6, 0.08)
    note(XR + 26, eq_y(v) + 7, lab, 20, INK, "start", 0.4)
epts, cur = [], 1_000_000
for d in sess:
    if d in eq_by_day:
        cur = eq_by_day[d]
    epts.append((X(d), eq_y(cur)))
svg.append('<path d="M ' + " L ".join(f"{x:.1f} {y:.1f}" for x, y in epts) +
           f'" fill="none" stroke="{INK}" stroke-width="1.5" opacity="0.22" stroke-dasharray="7 5"/>')
note(X(dt.date(2026, 1, 10)), EQ_Y1 - 14, "正面的净值线,在背面只留虚影", 21, INK, "end", 0.5)

# ================= ⑥ couplet II: peak & storm, same day =================
x602 = X(dt.date(2026, 6, 2))
yp = eq_y(2_036_318)
svg.append(f'<circle cx="{x602:.0f}" cy="{yp:.0f}" r="7" fill="none" stroke="{INK}" stroke-width="1.4" opacity="0.5" stroke-dasharray="3 3"/>')
vline(x602, yp + 10, by(dt.date(2026, 6, 2)) - 14, 0.8, 0.35, INK, "2 5")
note(x602 + 16, yp + 6, "「峰值与暴雨,同一天」· 6/02", 22, INK, "start", 0.8)

# ================= ③ nine knots (keyframes) =================
KF_LAYOUT = {   # date -> (label_y, anchor)
    "2026-03-03": (950, "start"),
    "2026-03-07": (730, "end"),
    "2026-03-30": (800, "middle"),
    "2026-04-23": (950, "start"),
    "2026-04-28": (730, "middle"),
    "2026-05-07": (860, "middle"),
    "2026-06-02": (950, "start"),
    "2026-06-10": (760, "middle"),
    "2026-07-05": (980, "middle"),
}
for iso, tag, quote in D["keyframes"]:
    day = dt.date.fromisoformat(iso)
    x = X(day)
    yk = by(day)
    ly, anc = KF_LAYOUT[iso]
    svg.append(f'<circle cx="{x:.1f}" cy="{yk:.1f}" r="6.2" fill="{INK}" opacity="0.9"/>')
    svg.append(f'<circle cx="{x:.1f}" cy="{yk:.1f}" r="10.5" fill="none" stroke="{INK}" stroke-width="1" opacity="0.5"/>')
    vline(x, ly + 44, yk - 13, 0.7, 0.3)
    tx = x + (10 if anc == "start" else (-10 if anc == "end" else 0))
    mmdd = f"{day.month}/{day.day:02d}"
    note(tx, ly, f"{mmdd} · {tag}", 22, INK, anc, 0.85, "normal")
    note(tx, ly + 30, quote, 20, INK, anc, 0.6)
    if iso == "2026-05-07":
        note(tx, ly + 58, "(这天开了 9 仓;5/14 又一次)", 17, INK, anc, 0.5)

# ================= BABA: the three deepest threads =================
baba = sorted([t for t in D["trades"] if t["t"] == "BABA" and t["hold"] > 30],
              key=lambda z: -z["hold"])
mx = sum((X(t["entry"]) + X(t["exit"])) / 2 for t in baba) / len(baba)
ybot = SPINE + depth_of(baba[0]["hold"])
note(mx, ybot + 44, "BABA · 垂得最深的三根线:102 / 99 / 93 天", 22, INK, "middle", 0.8)
note(mx, ybot + 74, "挂了一季,4/23 同日剪断", 20, INK, "middle", 0.6)

# ================= ⑥ couplet I: surrender & harvest, same week =================
x423, x428 = X(dt.date(2026, 4, 23)), X(dt.date(2026, 4, 28))
yb2 = 1958
svg.append(f'<path d="M {x428:.0f} {yb2-10} L {x428:.0f} {yb2} L {x423:.0f} {yb2} L {x423:.0f} {yb2-10}" fill="none" stroke="{INK}" stroke-width="0.9" opacity="0.5"/>')
note((x423 + x428) / 2, yb2 + 28, "「认输与收获,同一周」", 22, INK, "middle", 0.8)
note((x423 + x428) / 2, yb2 + 56, "4/23 剪断 BABA · 4/28 收 BE 第九次", 18, INK, "middle", 0.55)

# ================= legend column (mirrored to the LEFT) =================
lx = 90
# seal — hollow outline (the back of the stamp)
sx, sy = 548, 88
svg.append(f'<rect x="{sx}" y="{sy}" width="62" height="62" rx="5" fill="none" stroke="{SEAL}" stroke-width="2.2" opacity="0.9"/>')
note(sx + 31, sy + 27, "手", 24, SEAL, "middle", 0.9, "normal")
note(sx + 31, sy + 53, "迹", 24, SEAL, "middle", 0.9, "normal")

note(lx, 220, "同一个动作 · 反面", 56, INK, "start", 0.92, "normal")
note(lx, 262, "the reverse", 24, INK, "start", 0.5)
note(lx, 312, "盈亏是给世界看的,挣扎是自己的。", 24, INK, "start", 0.85)
note(lx, 346, "2026 上半年 · 331 笔 · 单色墨于素布", 20, INK, "start", 0.5)

ly = 420
hline(lx, 640, ly - 24, 1.2, 0.5)
note(lx, ly, "读法", 26, INK, "start", 0.8, "normal")

# breathing line samples
yw = ly + 46
note(lx, yw, "呼吸线 = 逐日的手:振幅与频率 = 紧张度", 20, INK, "start", 0.75)
for j, tt in enumerate([0.2, 0.45, 0.73]):
    x0_ = lx + 6 + j * 130
    a_, f_ = AMP_MAX * tt * 0.55, 0.8 + 3.4 * tt
    sp = []
    for k in range(41):
        u = k / 40
        sp.append((x0_ + u * 100, yw + 34 - a_ * math.sin(u * f_ * 6)))
    svg.append('<path d="M ' + " L ".join(f"{x:.1f} {y:.1f}" for x, y in sp) +
               f'" fill="none" stroke="{INK}" stroke-width="1.4" opacity="0.8"/>')
    note(x0_ + 50, yw + 62, f"{tt:g}", 16, INK, "middle", 0.5)
note(lx, yw + 92, "拉直 = ≥4 天没有开仓(15 段沉默)", 20, INK, "start", 0.75)

# thread rows
y2 = yw + 140
svg.append(f'<path d="M {lx+6} {y2-8} Q {lx+34} {y2+30} {lx+62} {y2-8}" fill="none" stroke="{INK}" stroke-width="1.4" opacity="0.7"/>')
note(lx + 80, y2, "悬线 = 一笔交易:入场挂到离场(331 根,一根不少)", 20, INK, "start", 0.75)
note(lx, y2 + 40, "垂深 = 持仓天数 · 右缘刻 30/60/90/102 天", 20, INK, "start", 0.75)

y3 = y2 + 84
note(lx, y3, "粗细 = 风险 ÷ 当时净值(0.25% → 4%,封顶)", 20, INK, "start", 0.75)
for j, pp in enumerate([0.25, 0.5, 1.0, 4.0]):
    x0_ = lx + 6 + j * 100
    hline(x0_, x0_ + 60, y3 + 26, w_of(pp), 0.8)
    note(x0_ + 30, y3 + 52, f"{pp:g}%", 16, INK, "middle", 0.5)

y4 = y3 + 92
note(lx, y4, "浓淡 = 入场那天的紧张度", 20, INK, "start", 0.75)
for j, tt in enumerate([0.1, 0.4, 0.73]):
    x0_ = lx + 6 + j * 100
    hline(x0_, x0_ + 60, y4 + 24, 2.2, op_of(tt))
    note(x0_ + 30, y4 + 50, f"{tt:g}", 16, INK, "middle", 0.5)

y5 = y4 + 92
for k in range(5):
    vline(lx + 10 + k * 4, y5 - 14, y5 + 2, 1.1, 0.6)
note(lx + 46, y5, "密结 = 单日 ≥5 仓,一圈一仓(21 天)", 20, INK, "start", 0.75)
svg.append(f'<circle cx="{lx+18}" cy="{y5+34}" r="5.5" fill="{INK}" opacity="0.9"/>')
svg.append(f'<circle cx="{lx+18}" cy="{y5+34}" r="9" fill="none" stroke="{INK}" stroke-width="1" opacity="0.5"/>')
note(lx + 46, y5 + 40, "实心结 = 九个被记住的日子", 20, INK, "start", 0.75)
hline(lx + 6, lx + 36, y5 + 74, 1.4, 0.4, INK, "6 5")
note(lx + 46, y5 + 80, "虚线 = 正面的虚影(净值线 · 霜冻 · 回撤带)", 20, INK, "start", 0.75)
note(lx, y5 + 118, "颜色与盈亏,都留在正面。", 20, INK, "start", 0.55)

# numbers
ly2 = y5 + 176
hline(lx, 640, ly2 - 26, 0.8, 0.3)
note(lx, ly2, "数字", 26, INK, "start", 0.8, "normal")
tmax_d = max(sess, key=lambda d: tension[d])
stats = [
    "最长连败 17(2/26–3/07),无一笔超预算风险",
    "最长的沉默 7 天(6/28–7/05)· 单日最多 9 仓",
    "持仓最长 102 天 · 中位 3 天 · 331 笔合计 2,466 天",
    f"紧张度峰值 {tension[tmax_d]:.2f} · {tmax_d.month}/{tmax_d.day:02d},两天后单日 9 仓",
    "九句拼贴皆真:31 句语料中 27 句为逐字实录,",
    "句子是真的,位置是策展的。",
]
for i, s in enumerate(stats):
    note(lx, ly2 + 40 + i * 38, s, 20, INK, "start", 0.7)

note(lx, H - 118, "同一个动作 · The Same Gesture 系列", 21, INK, "start", 0.6)
note(lx, H - 86, "Fluxus DataArt · sketch 06 · the reverse(反面)", 20, INK, "start", 0.5)
note(lx, H - 54, "数据:交易 log 2025-12-31 → 2026-07-22,无一虚构", 20, INK, "start", 0.5)

svg.append("</svg>")
out = Path(__file__).parent / "sketch_06_plate_back.svg"
out.write_text("\n".join(svg))
print("wrote", out)
print("threads:", len(threads), "| max tension:", round(tension[tmax_d], 3), tmax_d)
