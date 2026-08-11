#!/usr/bin/env python3
"""sketch 09 — the weeks · 周历版(2000×2800,竖幅)。
论点:「不动,也是一个仓位」——等待是判断力唯一可见的形态。
Lupi《My 2020 in Data》式周历:30 个交易周,每周一行。
主角是空白:15 段沉默期被斜纹标出并标注天数;Caution 雪花日;
6/28–7/05 那一行几乎全空。先看没做什么,再看做了什么。
零随机数,所有尺度有标尺。
"""
import math, datetime as dt
from pathlib import Path
from collections import defaultdict
from art_data import load

D = load()

W, H = 2000, 2800
PAPER, INK = "#f6f2e8", "#2b2823"
GREEN, GOLD, RUST, GREY, SLATE = "#3f6b4d", "#b8892b", "#a04a30", "#8a8175", "#5b7a96"
SEAL = "#9e2b1f"

D0 = dt.date(2025, 12, 29)          # Monday of week 0
NW = 30                              # 30 trading weeks -> rows

# ---- columns ----
LBL_X = 142                          # week label, end-anchored
SNOW_X = 160                         # caution snowflake
REG0, REG_CW = 176, 27               # regime microstrip, 5 cells
MAIN0, MAIN1 = 335, 1147             # exit-glyph field, Mon..Sun
SLOTW = (MAIN1 - MAIN0) / 7
PL0, PL1 = 1185, 1555                # weekly P&L axis, -50k..+150k linear
PK = (PL1 - PL0) / 200_000           # px per $
ZX = PL0 + 50_000 * PK               # zero
EN0, EN_DX = 1592, 15                # entry-rhythm day slots
NOTE_BX, NOTE_X = 1742, 1756         # margin notes

# ---- rows ----
Y0, RH, BASE = 560, 70, 44
def yb(w):  return Y0 + w * RH + BASE
def week_i(d): return (d - D0).days // 7
def monday(w): return D0 + dt.timedelta(days=7 * w)
def dayx(d):  return MAIN0 + (d.weekday() + 0.5) * SLOTW

# ---- value scales (documented in row 0 ruler) ----
WCAP, LCAP = 90_000, 25_000
def off_w(p): return math.sqrt(min(p, WCAP) / WCAP) * 28
def off_l(p): return math.sqrt(min(-p, LCAP) / LCAP) * 18
RMAX = max(t["risk"] for t in D["trades"])
def rad(risk): return 2.0 + math.sqrt(risk / RMAX) * 11

def mix(c1, c2, t):
    p = lambda c: (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16))
    a, b = p(c1), p(c2)
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Georgia, serif">',
       f'<rect width="{W}" height="{H}" fill="{PAPER}"/>']

def note(x, y, s, size=16, color=INK, anchor="start", op=0.8, style="italic", weight="normal", spacing=None):
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    sp = f' letter-spacing="{spacing}"' if spacing else ''
    svg.append(f'<text x="{x:.0f}" y="{y:.0f}" font-style="{style}" font-weight="{weight}" font-size="{size}" fill="{color}" text-anchor="{anchor}" opacity="{op}" font-family="Georgia, \'Songti SC\', serif"{sp}>{s}</text>')

def hline(x1, x2, y, wd=0.8, op=0.3, color=INK, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    svg.append(f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" stroke="{color}" stroke-width="{wd}" opacity="{op}"{d}/>')

def vline(x, y1, y2, wd=0.8, op=0.3, color=INK, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    svg.append(f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{wd}" opacity="{op}"{d}/>')

def glyph_shape(x, y, r_, species, color, gold, filled, short=False):
    dash = ' stroke-dasharray="4 3"' if short else ''
    if species == "ai":
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r_:.1f}" fill="{color if filled else "none"}" fill-opacity="{0.9 if gold else 0.6}" stroke="{color}" stroke-width="{1.6 if gold else 1.3}"{dash}/>')
    elif species == "other":
        svg.append(f'<path d="M {x:.1f} {y-r_:.1f} L {x+r_:.1f} {y:.1f} L {x:.1f} {y+r_:.1f} L {x-r_:.1f} {y:.1f} Z" fill="{color if filled else "none"}" fill-opacity="{0.9 if gold else 0.55}" stroke="{color}" stroke-width="1.3"{dash}/>')
    else:
        s = r_ * 0.85
        svg.append(f'<rect x="{x-s:.1f}" y="{y-s:.1f}" width="{2*s:.1f}" height="{2*s:.1f}" fill="{color if (filled and gold) else "none"}" fill-opacity="0.9" stroke="{color}" stroke-width="1.3"{dash}/>')

def snowflake(x, y, r=5.2, color=SLATE, op=0.85, wd=1.1):
    for ang in (90, 30, 150):
        a = math.radians(ang)
        dx, dy = math.cos(a) * r, math.sin(a) * r
        svg.append(f'<line x1="{x-dx:.1f}" y1="{y-dy:.1f}" x2="{x+dx:.1f}" y2="{y+dy:.1f}" stroke="{color}" stroke-width="{wd}" opacity="{op}"/>')

def hatch_rect(x, y, w, h, color=SLATE, op=0.30, step=7.0, wd=0.9):
    """manual 45° hatch, no <pattern> (QuickLook-safe)."""
    s = x - h
    while s < x + w:
        x1, y1 = s, y + h
        x2, y2 = s + h, y
        if x1 < x:
            y1 = y + h - (x - x1); x1 = x
        if x2 > x + w:
            y2 = y + (x2 - (x + w)); x2 = x + w
        if x2 > x and x1 < x + w and y1 > y2:
            svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{wd}" opacity="{op}"/>')
        s += step

# ======================================================================
# data prep
# ======================================================================
wpnl, went_days = defaultdict(float), defaultdict(lambda: defaultdict(int))
by_exit_day = defaultdict(list)
for t in D["trades"]:
    wpnl[week_i(t["exit"])] += t["pnl"]
    went_days[week_i(t["entry"])][t["entry"].weekday()] += 1
    by_exit_day[t["exit"]].append(t)

caution_days = [d for d in D["sessions"] if D0 <= d and D["regime"][d] < 34]
caution_w = defaultdict(int)
for d in caution_days:
    caution_w[week_i(d)] += 1

ROWS_TOP, ROWS_BOT = Y0 - 12, Y0 + NW * RH + 4

# ======================================================================
# rows region furniture
# ======================================================================
# faint day-slot boundaries through the whole field
for k in range(8):
    x = MAIN0 + k * SLOTW
    vline(x, ROWS_TOP + 4, ROWS_BOT, 0.6, 0.05 if k not in (0, 7) else 0.10)
vline(MAIN0 + 5 * SLOTW, ROWS_TOP + 4, ROWS_BOT, 0.6, 0.09, INK, "1 5")  # weekend divider
# P&L axis verticals
for v in (-50_000, 0, 50_000, 100_000, 150_000):
    x = ZX + v * PK
    vline(x, ROWS_TOP + 4, ROWS_BOT, 0.7, 0.14 if v == 0 else 0.045)

# month separators
for w in range(1, NW):
    if monday(w).month != monday(w - 1).month:
        y = Y0 + w * RH - 6
        hline(70, 1985, y, 0.7, 0.10)
        note(74, y - 6, f"{monday(w).month} 月", 14, INK, "start", 0.42, "normal")
note(74, Y0 - 18, "2025 · 12 月", 14, INK, "start", 0.42, "normal")

# frost / storm tints (slate, quiet)
for (a, b) in (D["frost"], D["storm"]):
    d = a
    per_week = defaultdict(list)
    while d <= b:
        per_week[week_i(d)].append(d)
        d += dt.timedelta(days=1)
    for w, ds in per_week.items():
        s0, s1 = min(x.weekday() for x in ds), max(x.weekday() for x in ds)
        xa, xb = MAIN0 + s0 * SLOTW + 1, MAIN0 + (s1 + 1) * SLOTW - 1
        svg.append(f'<rect x="{xa:.1f}" y="{yb(w)-33:.1f}" width="{xb-xa:.1f}" height="40" fill="{SLATE}" opacity="0.055"/>')

# per-row baseline + label + regime + snowflakes
for w in range(NW):
    y = yb(w)
    hline(MAIN0, MAIN1, y, 0.7, 0.13)
    for k in range(7):  # day ticks
        vline(MAIN0 + (k + 0.5) * SLOTW, y - 2, y + 2, 0.7, 0.22)
    m = monday(w)
    note(LBL_X, y + 5, f"{m.month}/{m.day:02d}", 15, INK, "end", 0.55, "normal")
    # regime microstrip (Mon..Fri sessions)
    for wd in range(5):
        d = m + dt.timedelta(days=wd)
        cx = REG0 + wd * REG_CW
        if d in D["regime"]:
            sc = D["regime"][d] / 100
            svg.append(f'<rect x="{cx}" y="{y-13}" width="{REG_CW-2}" height="11" fill="{mix(SLATE, GOLD, sc)}" opacity="{0.25+0.55*sc:.2f}"/>')
        else:
            svg.append(f'<rect x="{cx}" y="{y-13}" width="{REG_CW-2}" height="11" fill="none" stroke="{INK}" stroke-width="0.5" opacity="0.13"/>')
    if caution_w.get(w):
        snowflake(SNOW_X, y - 8)
        if caution_w[w] > 1:
            note(SNOW_X + 8, y - 3, f"×{caution_w[w]}", 11, SLATE, "start", 0.8, "normal")

# ======================================================================
# silences — the protagonist
# ======================================================================
sil_label_pts = []
for (a, b) in D["silences"]:
    days = [a + dt.timedelta(days=k) for k in range(1, (b - a).days)]
    per_week = defaultdict(list)
    for d in days:
        if 0 <= week_i(d) < NW:
            per_week[week_i(d)].append(d)
    widest = max(per_week, key=lambda w: len(per_week[w]))
    for w, ds in per_week.items():
        s0, s1 = min(x.weekday() for x in ds), max(x.weekday() for x in ds)
        xa, xb = MAIN0 + s0 * SLOTW + 2, MAIN0 + (s1 + 1) * SLOTW - 2
        y = yb(w)
        hatch_rect(xa, y - 29, xb - xa, 35)
        hline(xa, xb, y - 29, 0.7, 0.22, SLATE)
        hline(xa, xb, y + 6, 0.7, 0.22, SLATE)
        if w == widest:
            note(xa + 5, y + 1, f"{(b-a).days} 天", 13, mix(SLATE, INK, 0.25), "start", 0.85)
            sil_label_pts.append((xa, y))

# ======================================================================
# threads: BE ×16 · BABA ×5 (quiet noise under glyphs)
# ======================================================================
# glyph layout first
placed = []          # (trade, x, y, color, filled)
anchors = {}
for day, ts in sorted(by_exit_day.items()):
    w = week_i(day)
    if not (0 <= w < NW):
        continue
    n = len(ts)
    for i, t in enumerate(sorted(ts, key=lambda z: -z["risk"])):
        x = dayx(day) + (i - (n - 1) / 2) * 8.5
        y = yb(w) - off_w(t["pnl"]) if t["pnl"] > 0 else yb(w) + off_l(t["pnl"])
        if t["pnl"] > 0:
            color = GOLD if t["gold"] else GREEN
        else:
            color = RUST if t["r"] <= -1 else GREY
        placed.append((t, x, y, color, t["pnl"] > 0))
        anchors[(t["t"], t["attempt"])] = (x, y)

def thread(name, color):
    ks = sorted(k for k in anchors if k[0] == name)
    pts = [anchors[k] for k in ks]
    if len(pts) < 2:
        return
    d_ = f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"
    for p, q in zip(pts, pts[1:]):
        my = (p[1] + q[1]) / 2
        d_ += f" C {p[0]:.1f} {my:.1f} {q[0]:.1f} {my:.1f} {q[0]:.1f} {q[1]:.1f}"
    svg.append(f'<path d="{d_}" fill="none" stroke="{color}" stroke-width="1.0" opacity="0.30"/>')
    for p in pts:
        svg.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="1.7" fill="{color}" opacity="0.55"/>')

thread("BE", mix(GREEN, INK, 0.25))
thread("BABA", RUST)
be1 = anchors.get(("BE", 1))
if be1:
    note(be1[0] - 4, be1[1] + 18, "BE ×16", 12, mix(GREEN, INK, 0.25), "middle", 0.7)
ba2 = anchors.get(("BABA", 2))
if ba2:
    note(ba2[0] - 12, ba2[1] + 14, "BABA ×5", 12, RUST, "end", 0.75)

# glyphs on top
for t, x, y, color, win in placed:
    glyph_shape(x, y, rad(t["risk"]), t["species"], color, t["gold"], win or t["gold"], t["dir"] == "short")
assert len(placed) == len(D["trades"]) == 331, len(placed)

# ======================================================================
# weekly P&L bars + numbers · entry-rhythm stacks
# ======================================================================
def fmt_k(v):
    a = abs(v) / 1000
    s = f"{a:.1f}" if a < 9.95 else f"{a:.0f}"
    return ("+$" if v > 0 else "−$") + s + "k"

for w in range(NW):
    y = yb(w)
    v = wpnl.get(w, 0.0)
    if abs(v) > 1:
        xv = ZX + v * PK
        x0_, x1_ = (ZX, xv) if v > 0 else (xv, ZX)
        c = GREEN if v > 0 else RUST
        svg.append(f'<rect x="{x0_:.1f}" y="{y-8:.1f}" width="{max(x1_-x0_,0.8):.1f}" height="7" fill="{c}" opacity="0.72"/>')
        if v > 0:
            note(xv + 7, y - 1, fmt_k(v), 13, mix(c, INK, 0.2), "start", 0.75, "normal")
        else:
            note(xv - 7, y - 1, fmt_k(v), 13, mix(c, INK, 0.2), "end", 0.75, "normal")
    # entry rhythm: one dot per entry, stacked per weekday
    for wd, n in sorted(went_days.get(w, {}).items()):
        for k in range(n):
            svg.append(f'<circle cx="{EN0 + wd*EN_DX:.1f}" cy="{y + 1 - k*6.5:.1f}" r="2.0" fill="{INK}" opacity="0.5"/>')

# ======================================================================
# row 0: the ruler sample (scales, documented)
# ======================================================================
y0r = yb(0)
rx = 420
vline(rx, y0r - 28, y0r + 18, 0.9, 0.5)
for p, lab in ((10_000, "+$10k"), (40_000, "+$40k"), (90_000, "+$90k")):
    yy = y0r - off_w(p)
    hline(rx - 4, rx + 4, yy, 0.9, 0.5)
    note(rx - 8, yy + 4, lab, 11.5, INK, "end", 0.55)
for p, lab in ((-5_000, "−$5k"), (-25_000, "−$25k")):
    yy = y0r + off_l(p)
    hline(rx - 4, rx + 4, yy, 0.9, 0.5)
    note(rx - 8, yy + 4, lab, 11.5, INK, "end", 0.55)
note(rx + 10, y0r - 32, "纵向偏移 = 该笔 P&L(√ 标尺)", 12.5, INK, "start", 0.6)
# risk-area samples
sx = 560
for i, rk in enumerate((2_000, 10_000, 30_000)):
    cx = sx + i * 48
    svg.append(f'<circle cx="{cx}" cy="{y0r-6}" r="{rad(rk):.1f}" fill="none" stroke="{INK}" stroke-width="1.1" opacity="0.55"/>')
    note(cx, y0r + 14, f"${rk//1000}k", 11.5, INK, "middle", 0.55)
note(sx - 12, y0r + 32, "面积 = 该笔风险(种子大小)", 12.5, INK, "start", 0.6)

# ======================================================================
# margin notes(italic + 引线)
# ======================================================================
def margin_note(w0_, w1_, lines, leader_to=None, leader_color=INK, y_off=-28, flake=False):
    ytop = yb(w0_) + y_off
    ybot = yb(w1_) + 22
    vline(NOTE_BX, ytop, ybot, 1.0, 0.4)
    hline(NOTE_BX, NOTE_BX + 6, ytop, 1.0, 0.4)
    hline(NOTE_BX, NOTE_BX + 6, ybot, 1.0, 0.4)
    yy = ytop + 14
    for k, ln in enumerate(lines):
        size, color, txt = ln
        dx0 = 18 if (flake and k == 0) else 0
        note(NOTE_X + dx0, yy, txt, size, color, "start", 0.85)
        if flake and k == 0:
            snowflake(NOTE_X + 6, yy - 5)
        yy += size + 6
    if leader_to:
        tx, ty = leader_to
        svg.append(f'<path d="M {NOTE_BX-4:.0f} {ytop+10:.0f} Q {(NOTE_BX+tx)/2:.0f} {min(ytop+10, ty)-16:.0f} {tx:.0f} {ty:.0f}" fill="none" stroke="{leader_color}" stroke-width="0.8" opacity="0.32"/>')

margin_note(8, 9, [
    (17, INK, "十七连败,跨这两周"),
    (15, RUST, "2/26–3/07 · −$43,833"),
    (15, INK, "无一笔超出预算风险"),
], leader_to=(ZX - 32_214 * PK - 2, yb(9) - 11), leader_color=RUST)

margin_note(10, 11, [
    (17, mix(SLATE, INK, 0.2), "Caution 天气"),
    (15, INK, "半年只出手 8 次"),
    (15, mix(SLATE, INK, 0.2), "盈亏比 6.91× · 期望 +1.93R"),
    (15, INK, "全场最高;Neutral 87 次"),
    (15, INK, "盈亏比只有 1.85×"),
], flake=True)

margin_note(16, 17, [
    (17, INK, "认输与收获,同一周"),
    (15, RUST, "4/23 剪 BABA · −$54,418"),
    (15, mix(GOLD, INK, 0.2), "4/28 收 BE 第九次 +$74,052"),
    (15, INK, "此前八次合计 −$19,300"),
], leader_to=(ZX + 89_995 * PK + 3, yb(17) - 11), leader_color=GOLD)

margin_note(18, 19, [
    (17, INK, "5/07 单日 9 仓"),
    (15, INK, "——等待的反面。此后"),
    (15, RUST, "sizing 散度 CV 1.82"),
    (15, INK, "全年最乱的一段手"),
], leader_to=(EN0 + 3 * EN_DX + 4, yb(18) - 56), leader_color=INK)

margin_note(22, 23, [
    (17, INK, "6/02:峰值与暴雨"),
    (15, mix(GOLD, INK, 0.2), "盯市 $2,036,318(+104%)"),
    (15, INK, "与回撤窗口首日,同一天"),
    (15, RUST, "八日 −$223,100(−11.1%)"),
], leader_to=(ZX + 135_363 * PK + 3, yb(22) - 11), leader_color=SLATE)

margin_note(26, 26, [
    (19, INK, "七天。"),
    (16, INK, "YTD 一分没少。"),
    (13, INK, "最长的沉默 6/28–7/05"),
], leader_to=(MAIN0 + 2.5 * SLOTW, yb(26) - 14), leader_color=SLATE, y_off=-24)

# ======================================================================
# column headers
# ======================================================================
hy = Y0 - 46
note(LBL_X, hy, "周(周一)", 14, INK, "end", 0.55, "normal")
note(REG0 + 2.5 * REG_CW - 1, hy, "天气 冷→暖", 14, INK, "middle", 0.55, "normal")
note(MAIN0, hy, "离场交易 · 上=盈利 下=亏损(√$ 标尺见首行)", 14, INK, "start", 0.55, "normal")
note((PL0 + PL1) / 2, hy, "周已实现 P&L(线性)", 14, INK, "middle", 0.55, "normal")
note(EN0 - 4, hy, "开仓节拍 · 每点一次", 14, INK, "start", 0.55, "normal")
note(NOTE_X, hy, "边注", 14, INK, "start", 0.55, "normal")
# day letters
for k, ch in enumerate("一二三四五六日"):
    op_ = 0.5 if k < 5 else 0.38
    note(MAIN0 + (k + 0.5) * SLOTW, hy + 22, ch, 14, INK if k < 5 else SLATE, "middle", op_, "normal")
    note(EN0 + k * EN_DX, hy + 22, ch, 10.5, INK if k < 5 else SLATE, "middle", op_ - 0.08, "normal")
# P&L axis ticks
for v, lab in ((-50_000, "−$50k"), (0, "0"), (50_000, "+$50k"), (100_000, "+$100k"), (150_000, "+$150k")):
    x = ZX + v * PK
    vline(x, hy + 14, hy + 22, 0.9, 0.45)
    note(x, hy + 36, lab, 12.5, INK, "middle", 0.5, "normal")

# ======================================================================
# header: title · legend · numbers · seal
# ======================================================================
note(90, 160, "不动,也是一个仓位", 64, INK, "start", 0.92, "normal")
note(94, 208, "等待是判断力唯一可见的形态 —— 2026 上半年,331 笔交易散落在 30 个交易周里。先看空白,再看交易。", 21, INK, "start", 0.6)
svg.append(f'<rect x="1900" y="100" width="60" height="60" rx="5" fill="{SEAL}" opacity="0.9"/>')
note(1930, 128, "测", 24, PAPER, "middle", 0.95, "normal")
note(1930, 152, "量", 24, PAPER, "middle", 0.95, "normal")

hline(90, 1960, 248, 1.1, 0.45)

# col A · 每一笔
ax = 90
note(ax, 278, "读法 · 每一笔", 18, INK, "start", 0.75, "normal")
rows_a = [
    ("ai", GREEN, False, "圆 = AI 链(169 笔,净利 80%,payoff 4.46×)"),
    ("other", GREY, False, "菱 = 其他品种(69 笔,合计 −$30,668)"),
    ("rootless", INK, False, "空方 = 杠杆工具(93 笔,$214k)"),
    ("ai", GOLD, True, "金实心 = 扛起 100% 净利的 31 笔;其余 300 笔 ≈ 0"),
    ("short", None, False, "虚线描边 = 做空"),
    ("swatch", None, False, "锈红 = 止损 R ≤ −1(42 笔) · 灰 = 小亏"),
]
for i, (kind, c, filled, lab) in enumerate(rows_a):
    yy = 306 + i * 30
    if kind == "short":
        glyph_shape(ax + 12, yy - 5, 8, "ai", GREEN, False, False, True)
    elif kind == "swatch":
        svg.append(f'<line x1="{ax+3}" y1="{yy-5}" x2="{ax+13}" y2="{yy-5}" stroke="{RUST}" stroke-width="3"/>')
        svg.append(f'<line x1="{ax+15}" y1="{yy-5}" x2="{ax+25}" y2="{yy-5}" stroke="{GREY}" stroke-width="3"/>')
    else:
        glyph_shape(ax + 12, yy - 5, 8, kind, c, filled, filled or kind == "ai")
    note(ax + 34, yy, lab, 15.5, INK, "start", 0.72)

# col B · 每一行
bx = 610
note(bx, 278, "读法 · 每一行(一个交易周)", 18, INK, "start", 0.75, "normal")
hatch_rect(bx, 294, 28, 14)
note(bx + 46, 306, "斜纹 = 无开仓的空白,标注间隔天数(15 段)", 15.5, INK, "start", 0.72)
snowflake(bx + 13, 331)
note(bx + 46, 336, "雪花 = Caution 天气日(score<34)", 15.5, INK, "start", 0.72)
for k in range(5):
    svg.append(f'<rect x="{bx+k*7}" y="{354}" width="6" height="11" fill="{mix(SLATE, GOLD, k/4)}" opacity="{0.25+0.55*k/4:.2f}"/>')
note(bx + 46, 366, "微条 = 每日天气 score(冷→暖)", 15.5, INK, "start", 0.72)
svg.append(f'<path d="M {bx} 390 C {bx+11} 382 {bx+17} 398 {bx+28} 390" fill="none" stroke="{mix(GREEN, INK, 0.25)}" stroke-width="1.0" opacity="0.5"/>')
note(bx + 46, 396, "细曲线 = 同一标的的重复进攻(BE ×16 · BABA ×5)", 15.5, INK, "start", 0.72)
svg.append(f'<rect x="{bx}" y="410" width="28" height="12" fill="{SLATE}" opacity="0.1"/>')
note(bx + 46, 426, "蓝灰底 = 霜冻(2/26–3/07)与回撤窗口(6/02–6/10)", 15.5, INK, "start", 0.72)
note(bx + 46, 456, "周 P&L:绿=正 · 锈红=负,线性 −$50k..+$150k", 15.5, INK, "start", 0.72)

# col C · the argument numbers
cx = 1190
vline(cx - 20, 262, 470, 2.0, 0.5, SEAL)
note(cx, 296, "沉默 15 段", 34, INK, "start", 0.9, "normal")
note(cx, 324, "两次开仓之间 ≥4 天的空白;最长 7 天。", 15.5, INK, "start", 0.65)
note(cx, 346, "空白不是没有仓位 —— 空白就是仓位。", 15.5, mix(SLATE, INK, 0.2), "start", 0.8)
note(cx, 396, "连亏后 48h 内的 73 笔:胜率 49%", 22, INK, "start", 0.88, "normal")
note(cx, 420, "平常只有 37%;期望 +1.14R vs +0.80R。", 15.5, INK, "start", 0.65)
note(cx, 442, "被打疼之后先退半步,更准。", 15.5, mix(SLATE, INK, 0.2), "start", 0.8)

# col D · 数字
dx_ = 1640
note(dx_, 278, "数字", 18, INK, "start", 0.75, "normal")
for i, s in enumerate(["331 笔 · 胜率 39.9% · 盈亏比 3.40×",
                       "净 +90.5%($1.0M → $1,905,255)",
                       "均盈 $11,490 · 均亏 $3,378",
                       "最长连败 17 · 最长连胜只有 6",
                       "种子中位数随天气单调:",
                       "$1.8k → $3.3k → $4.1k → $4.6k"]):
    note(dx_, 306 + i * 27, s, 15.5, INK, "start", 0.7)

hline(90, 1960, 492, 1.1, 0.45)

# ======================================================================
# footer
# ======================================================================
fy = ROWS_BOT + 26
hline(70, 1985, fy, 1.0, 0.4)
note(70, fy + 30, "数据:交易 log 2025-12-31 → 2026-07-22,331 笔全部在场,无一虚构 · 时间全域 2025-12-29 → 2026-07-24", 15, INK, "start", 0.55)
note(70, fy + 54, "标尺:主区纵向偏移 √|P&L|(样例见首行) · 周 P&L 线性 −$50k..+$150k · 面积 = 风险$", 15, INK, "start", 0.55)
note(1985, fy + 30, "同一个动作 · The Same Gesture 系列", 16, INK, "end", 0.6, "normal")
note(1985, fy + 54, "Fluxus DataArt · sketch 09 · the weeks · 周历", 14, INK, "end", 0.5)

svg.append("</svg>")
out = Path(__file__).parent / "sketch_09_weeks.svg"
out.write_text("\n".join(svg))
print("wrote", out, "| glyphs:", len(placed))
