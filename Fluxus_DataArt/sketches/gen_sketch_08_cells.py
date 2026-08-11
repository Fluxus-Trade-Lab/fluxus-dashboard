#!/usr/bin/env python3
"""sketch 08 — the receipts · 331 张存根(卡矩阵)。
论点:止损是营业成本。这不是一本盈利的画册,是一本收据簿。
199 张没赚钱的存根是主角:每一张都小(均亏 $3,378 vs 均盈 $11,490),
十七连败无一张超预算,于是 39.9% 的胜率撑得起 +90.5%。
布局:331 张 100×150 卡按离场日装订,每行 24 张,月份换行;
远看=色温(离场日天气)+金点+红疤;近看=每张卡一笔档案。
"""
import math, datetime as dt
from pathlib import Path
from collections import defaultdict
from art_data import load

D = load()
T = D["trades"]                      # already sorted by (exit, entry)

PAPER, INK = "#f6f2e8", "#2b2823"
GREEN, GOLD, RUST, GREY, SLATE = "#3f6b4d", "#b8892b", "#a04a30", "#8a8175", "#5b7a96"
SEAL = "#9e2b1f"

W = 3120
CW, CH = 100, 150                    # card size
GAPX, GAPY = 8, 14
COLS = 24
X0 = 150                             # matrix left
XR = X0 + COLS * (CW + GAPX) - GAPX  # matrix right = 2734
XN = XR + 30                         # margin-note column
MAT_Y0 = 500
SEP_H = 66                           # month separator band
MAX_RISK = max(t["risk"] for t in T)

# ---------- helpers ----------
svg = []

def note(x, y, s, size=22, color=INK, anchor="start", op=0.8, style="italic", weight="normal"):
    svg.append(f'<text x="{x:.0f}" y="{y:.0f}" font-style="{style}" font-weight="{weight}" '
               f'font-size="{size}" fill="{color}" text-anchor="{anchor}" opacity="{op}" '
               f'font-family="Georgia, \'Songti SC\', serif">{s}</text>')

def hline(x1, x2, y, wd=0.8, op=0.3, color=INK, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    svg.append(f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" stroke="{color}" stroke-width="{wd}" opacity="{op}"{d}/>')

def vline(x, y1, y2, wd=0.8, op=0.3, color=INK, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    svg.append(f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{wd}" opacity="{op}"{d}/>')

def mix(c1, c2, t):
    p = lambda c: (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16))
    a, b = p(c1), p(c2)
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def money(v):
    s = f"{abs(v):,.0f}"
    return ("+$" if v >= 0 else "−$") + s

SESS = D["sessions"]
def score_at(d):
    """离场日 regime score;非交易日回看最近一个交易日。"""
    for k in range(6):
        dd = d - dt.timedelta(days=k)
        if dd in D["regime"]:
            return D["regime"][dd]
    return 50.0

def rad(risk, s=1.0):
    return (3.2 + math.sqrt(risk / MAX_RISK) * 17.0) * s

R_WCAP, R_LCAP = 28.0, 6.0
WIN_H, LOSS_H = 56.0, 42.0           # bar zone heights inside card (from baseline y=86)
def bar_dy(r):
    """R 条端点相对基线的位移(上负下正,√ 标尺)。"""
    if r > 0:
        return -math.sqrt(min(r, R_WCAP) / R_WCAP) * WIN_H
    if r < 0:
        return math.sqrt(min(-r, R_LCAP) / R_LCAP) * LOSS_H
    return 0.0

def glyph(x, y, r_, species, color, gold, filled, short, s=1.0):
    dash = f' stroke-dasharray="{4*s:.1f} {3*s:.1f}"' if short else ''
    sw = (2.0 if gold else 1.5) * s
    if species == "ai":
        fill = color if (filled or gold) else "none"
        fo = 0.9 if gold else 0.45
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r_:.1f}" fill="{fill}" fill-opacity="{fo}" stroke="{color}" stroke-width="{sw}"{dash}/>')
    elif species == "other":
        fill = color if (filled or gold) else "none"
        fo = 0.9 if gold else 0.4
        svg.append(f'<path d="M {x:.1f} {y-r_:.1f} L {x+r_:.1f} {y:.1f} L {x:.1f} {y+r_:.1f} L {x-r_:.1f} {y:.1f} Z" fill="{fill}" fill-opacity="{fo}" stroke="{color}" stroke-width="{sw}"{dash}/>')
    else:                             # 空心方 = 杠杆工具;金卡例外:金实心
        a = r_ * 0.86
        fill = color if gold else "none"
        fo = 0.9
        svg.append(f'<rect x="{x-a:.1f}" y="{y-a:.1f}" width="{2*a:.1f}" height="{2*a:.1f}" fill="{fill}" fill-opacity="{fo}" stroke="{color}" stroke-width="{sw}"{dash}/>')

BE_SET = {(t["t"], t["attempt"]) for t in T if t["t"] == "BE"}

def draw_card(t, x0, y0, s=1.0, show_riskpct=False):
    """一张存根。局部坐标 100×150,基线 y=86。"""
    sc = score_at(t["exit"]) / 100.0
    stop = t["pnl"] < 0 and t["r"] <= -1
    win = t["pnl"] > 0
    color = (GOLD if t["gold"] else GREEN) if win else (RUST if stop else GREY)
    # ① 底色 = 离场日天气(冷→暖)
    svg.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{CW*s:.1f}" height="{CH*s:.1f}" rx="{3*s:.1f}" '
               f'fill="{mix(SLATE, GOLD, sc)}" opacity="{0.12 + 0.08*sc:.3f}"/>')
    # 卡框:止损卡锈红加重,其余安静
    if stop:
        svg.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{CW*s:.1f}" height="{CH*s:.1f}" rx="{3*s:.1f}" '
                   f'fill="none" stroke="{RUST}" stroke-width="{2.4*s:.1f}" opacity="0.9"/>')
    else:
        svg.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{CW*s:.1f}" height="{CH*s:.1f}" rx="{3*s:.1f}" '
                   f'fill="none" stroke="{INK}" stroke-width="{0.7*s:.1f}" opacity="0.25"/>')
    # 抬头:ticker · 第几次 | 离场日
    tk = t["t"] + (f" ×{t['attempt']}" if t["attempt"] > 1 else "")
    note(x0 + 7*s, y0 + 17*s, tk, 12*s, INK, "start", 0.6, "normal")
    note(x0 + 93*s, y0 + 16*s, f"{t['exit'].month}/{t['exit'].day:02d}", 9.5*s, INK, "end", 0.42)
    # BE 链金环
    if (t["t"], t["attempt"]) in BE_SET:
        svg.append(f'<circle cx="{x0+88*s:.1f}" cy="{y0+29*s:.1f}" r="{3.4*s:.1f}" fill="none" stroke="{GOLD}" stroke-width="{1.3*s:.1f}" opacity="0.9"/>')
    # 基线 + 卡内 ±1R 预算线(条区)
    yb = y0 + 86*s
    hline(x0 + 6*s, x0 + 94*s, yb, 0.7*s, 0.20)
    y1u, y1d = yb + bar_dy(1)*s, yb + bar_dy(-1)*s
    hline(x0 + 58*s, x0 + 93*s, y1u, 0.7*s, 0.30, INK, f"{2*s:.0f} {3*s:.0f}")
    hline(x0 + 58*s, x0 + 93*s, y1d, 0.8*s, 0.42, RUST, f"{2*s:.0f} {3*s:.0f}")
    # ③ R 条(√ 标尺)+ 分批刻痕
    bx = x0 + 75*s
    dy = bar_dy(t["r"]) * s
    if abs(dy) > 0.5:
        yt = yb + dy
        bo = (0.9 if t["gold"] else 0.5) if win else (0.85 if stop else 0.5)
        svg.append(f'<rect x="{bx-5.5*s:.1f}" y="{min(yb, yt):.1f}" width="{11*s:.1f}" height="{abs(dy):.1f}" fill="{color}" opacity="{bo}"/>')
        if abs(dy) >= 13*s:
            for k in range(1, t["trims"]):
                ny = yb + dy * k / t["trims"]
                svg.append(f'<rect x="{bx-6.5*s:.1f}" y="{ny-1.1*s:.1f}" width="{13*s:.1f}" height="{2.2*s:.1f}" fill="{PAPER}"/>')
    else:                             # 打平:基线上一枚灰刻
        svg.append(f'<rect x="{bx-5.5*s:.1f}" y="{yb-1.2*s:.1f}" width="{11*s:.1f}" height="{2.4*s:.1f}" fill="{GREY}" opacity="0.6"/>')
    # ② 品种 glyph,面积 = 风险 $
    glyph(x0 + 31*s, yb, rad(t["risk"], s), t["species"], color, t["gold"], win, t["dir"] == "short", s)
    # 霜冻卡:印上当笔风险占比
    if show_riskpct:
        note(x0 + 6*s, y0 + 133*s, f"{t['risk_pct']:.2f}%", 10*s, RUST, "start", 0.85, "normal")
    # ④ 持仓天数条(0–102 线性)
    ty = y0 + 140*s
    hline(x0 + 6*s, x0 + 94*s, ty, 3.4*s, 0.10)
    wl = t["hold"] / 102 * 88*s
    svg.append(f'<rect x="{x0+6*s:.1f}" y="{ty-1.7*s:.1f}" width="{max(wl,1.2*s):.1f}" height="{3.4*s:.1f}" fill="{INK}" opacity="0.4"/>')

# ---------- 版面骨架:先算出每张卡的位置 ----------
months = []                          # [(ym, [trade,...])]
for t in T:
    ym = (t["exit"].year, t["exit"].month)
    if not months or months[-1][0] != ym:
        months.append((ym, []))
    months[-1][1].append(t)

CN = {1: "一月", 2: "二月", 3: "三月", 4: "四月", 5: "五月", 6: "六月", 7: "七月"}
EN = {1: "JAN", 2: "FEB", 3: "MAR", 4: "APR", 5: "MAY", 6: "JUN", 7: "JUL"}

pos = {}                             # id(trade) -> (x, y)
y = MAT_Y0
sep_rows = []                        # (y_band, ym, trades)
for ym, ts in months:
    sep_rows.append((y, ym, ts))
    y += SEP_H
    for j, t in enumerate(ts):
        r_, c_ = divmod(j, COLS)
        pos[id(t)] = (X0 + c_ * (CW + GAPX), y + r_ * (CH + GAPY))
    y += ((len(ts) - 1) // COLS + 1) * (CH + GAPY) - GAPY + 26
MAT_Y1 = y - 26
H = MAT_Y1 + 210

svg.insert(0, f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Georgia, serif">')
svg.append(f'<rect width="{W}" height="{H}" fill="{PAPER}"/>')
# (背景矩形要垫底:重排一下)
bg = svg.pop()
svg.insert(1, bg)

# ================= 页眉 =================
note(150, 122, "止损是营业成本", 82, INK, "start", 0.92, "normal")
note(150, 168, "Stops Are the Cost of Doing Business · 一本收据簿:331 张存根按离场日装订", 26, INK, "start", 0.55)
para = [
    "这不是一本盈利的画册,而是一本收据簿。199 张没赚钱的存根是主角(181 张亏损 · 18 张打平):",
    "每一张都小,小得起 —— 均亏只有均盈的 29%;十七连败连成一道疤,却无一张超预算。",
    "39.9% 的胜率,就这样撑起了 +90.5%。",
]
for i, s in enumerate(para):
    note(150, 226 + i * 34, s, 23, INK, "start", 0.75)
# ⑨ 均亏 / 均盈 等比例对比条
BX, BY = 150, 352
PX = 760 / 12000.0                  # $12k → 760px
note(BX, BY - 8, "两根等比例的条 —— 整本账的原理", 20, INK, "start", 0.6)
svg.append(f'<rect x="{BX}" y="{BY+6}" width="{3378*PX:.1f}" height="16" fill="{RUST}" opacity="0.85"/>')
note(BX + 3378 * PX + 14, BY + 20, "均亏 −$3,378 · 181 张收据", 21, RUST, "start", 0.85)
svg.append(f'<rect x="{BX}" y="{BY+40}" width="{11490*PX:.1f}" height="16" fill="{GREEN}" opacity="0.8"/>')
for k in (1, 2, 3):                  # 均盈条里装得下 3.40 段均亏
    vline(BX + k * 3378 * PX, BY + 40, BY + 56, 1.6, 0.9, PAPER)
note(BX + 11490 * PX + 14, BY + 54, "均盈 +$11,490 · 132 张", 21, GREEN, "start", 0.85)
ax = BY + 74
hline(BX, BX + 12000 * PX, ax, 0.9, 0.4)
for v in (0, 4000, 8000, 12000):
    vline(BX + v * PX, ax - 4, ax + 4, 0.9, 0.45)
    note(BX + v * PX, ax + 22, f"${v//1000}k" if v else "$0", 16, INK, "middle", 0.5)
note(BX, ax + 52, "一张均盈,付得起 3.40 张均亏。", 24, INK, "start", 0.8, "normal")

# ---- 样张(读一张存根):选一张锈红止损卡放大 ----
spec = None
for t in T:
    if t["pnl"] < 0 and t["r"] <= -1 and t["trims"] >= 2 and t["species"] == "ai" and 3 <= t["hold"] <= 40:
        spec = t; break
if spec is None:
    for t in T:
        if t["pnl"] < 0 and t["r"] <= -1 and t["species"] == "ai":
            spec = t; break
SX, SY, SS = 1358, 156, 1.9
note(SX, SY - 14, "读一张存根", 24, INK, "start", 0.8, "normal")
draw_card(spec, SX, SY, SS)
# 样张右缘:R 标尺刻度(√)
rx = SX + CW * SS + 10
ybase = SY + 86 * SS
note(rx + 6, ybase + bar_dy(20) * SS - 26, "离场结果(R,√ 标尺)", 15, INK, "start", 0.6)
for rr in (1, 5, 10, 20):
    yy = ybase + bar_dy(rr) * SS
    hline(rx - 6, rx, yy, 0.8, 0.5)
    note(rx + 6, yy + 5, f"+{rr}R", 14, INK, "start", 0.55)
for rr in (3, 6):
    yy = ybase + bar_dy(-rr) * SS
    hline(rx - 6, rx, yy, 0.8, 0.5)
    note(rx + 6, yy + 5, f"−{rr}R", 14, INK, "start", 0.55)
yy1 = ybase + bar_dy(-1) * SS
hline(rx - 6, rx, yy1, 0.9, 0.6, RUST)
note(rx + 6, yy1 + 5, "← −1R 预算线", 15, RUST, "start", 0.85)
# 样张左缘 callouts
lx = SX - 14
note(lx, SY + 22, "标的 · 第几次尝试 →", 16, INK, "end", 0.6)
note(lx, SY + 40, "底色 = 离场日天气 →", 16, INK, "end", 0.6)
note(lx, ybase + 2, "品种 glyph,面积 = 风险$ →", 16, INK, "end", 0.6)
note(lx, ybase + 24, "锈红 = 止损离场 →", 16, RUST, "end", 0.7)
note(lx, SY + 140 * SS + 4, "持仓天数 0–102 天(线性)→", 16, INK, "end", 0.6)
note(SX, SY + CH * SS + 34, f"样张:{spec['t']} ×{spec['attempt']} · {spec['exit'].month}/{spec['exit'].day} 止损 −{abs(spec['r']):.1f}R · {money(spec['pnl'])}", 17, INK, "start", 0.55)

# ---- 读法(两列)----
LGX = 1980
note(LGX, 142, "读法", 24, INK, "start", 0.8, "normal")
hline(LGX, LGX + 640, 156, 1.0, 0.4)
rows1 = [("ai", GREEN, False, False, "圆 = AI 链(169 张)"),
         ("other", GREY, False, False, "菱 = 其他品种(69 张)"),
         ("rootless", INK, False, False, "空方 = 杠杆工具(93 张)"),
         ("ai", GOLD, True, False, "金实心 = 扛起全部净利的 31 张")]
for i, (sp, c, gd, sh, lab) in enumerate(rows1):
    yy = 190 + i * 44
    glyph(LGX + 14, yy - 6, 10, sp, c, gd, not gd, sh)
    note(LGX + 40, yy, lab, 19, INK, "start", 0.72)
rows2 = [("card", RUST, "锈红重框 = 止损存根(R ≤ −1,42 张)"),
         ("dash", INK, "虚线描边 = 做空(33 张)"),
         ("ring", GOLD, "金环 = BE 的 16 次尝试"),
         ("notch", INK, "刻痕 = 分批离场(2–3 批)")]
for i, (kind, c, lab) in enumerate(rows2):
    yy = 190 + i * 44
    x = LGX + 330
    if kind == "card":
        svg.append(f'<rect x="{x+4}" y="{yy-16}" width="16" height="22" rx="2" fill="none" stroke="{RUST}" stroke-width="2.2" opacity="0.9"/>')
    elif kind == "dash":
        svg.append(f'<circle cx="{x+12}" cy="{yy-6}" r="9" fill="none" stroke="{INK}" stroke-width="1.5" stroke-dasharray="4 3" opacity="0.8"/>')
    elif kind == "ring":
        svg.append(f'<circle cx="{x+12}" cy="{yy-6}" r="4.5" fill="none" stroke="{GOLD}" stroke-width="1.6" opacity="0.9"/>')
    else:
        svg.append(f'<rect x="{x+7}" y="{yy-16}" width="10" height="22" fill="{GREY}" opacity="0.6"/>')
        svg.append(f'<rect x="{x+5}" y="{yy-8}" width="14" height="2.4" fill="{PAPER}"/>')
    note(x + 32, yy, lab, 19, INK, "start", 0.72)

# ---- 标尺块:底色色温 + 风险面积 ----
SCX = 1980
note(SCX, 398, "底色 = 离场日天气 score(冷→暖)", 18, INK, "start", 0.6)
for i in range(60):
    sc = i / 59
    svg.append(f'<rect x="{SCX + i*4:.1f}" y="406" width="4.4" height="16" fill="{mix(SLATE, GOLD, sc)}" opacity="{0.12+0.08*sc+0.22:.2f}"/>')
for v in (20, 50, 80):
    xx = SCX + v / 100 * 236
    vline(xx, 422, 428, 0.9, 0.5)
    note(xx, 444, str(v), 14, INK, "middle", 0.5)
ACX = 2470
note(ACX, 398, "面积 = 该笔风险 $", 18, INK, "start", 0.6)
for i, v in enumerate((5_000, 30_000, 110_000)):
    xx = ACX + 20 + i * 82
    svg.append(f'<circle cx="{xx}" cy="418" r="{rad(v):.1f}" fill="none" stroke="{INK}" stroke-width="1.2" opacity="0.6"/>')
    note(xx, 452, f"${v//1000}k", 14, INK, "middle", 0.5)

# ---- 印章 ----
svg.append(f'<rect x="2988" y="58" width="62" height="62" rx="5" fill="{SEAL}" opacity="0.9"/>')
note(3019, 86, "测", 24, PAPER, "middle", 0.95, "normal")
note(3019, 111, "量", 24, PAPER, "middle", 0.95, "normal")

# ================= 矩阵:月份分隔行 + 331 张卡 =================
frost_ids = set()
byx = T
s_, run, best = 0, [], []
for t in byx:                        # 找 17 连败(按离场顺序)
    if t["pnl"] < 0:
        run.append(t)
        if len(run) > len(best):
            best = list(run)
    else:
        run = []
frost_ids = {id(t) for t in best}
assert len(best) == 17

for band_y, ym, ts in sep_rows:
    pl = sum(t["pnl"] for t in ts)
    wr = sum(1 for t in ts if t["pnl"] > 0) / len(ts) * 100
    lsum = sum(t["pnl"] for t in ts if t["pnl"] < 0)
    lcnt = sum(1 for t in ts if t["pnl"] < 0)
    note(X0, band_y + 34, f"{CN[ym[1]]} · {EN[ym[1]]} {ym[0]}", 27, INK, "start", 0.8, "normal")
    note(X0 + 330, band_y + 34, f"{len(ts)} 张", 20, INK, "start", 0.5)
    note(XR, band_y + 34, f"月 P&amp;L {money(pl)} · 胜率 {wr:.1f}% · 亏损存根 {lcnt} 张,合计 {money(lsum)}", 19, INK, "end", 0.6)
    hline(X0, XR, band_y + 48, 1.1, 0.4)
    if ym == (2026, 3):               # 疤跨页:在三月页眉接上二月末的连败
        note(X0 + 620, band_y + 34, "↓ 二月末的连败延续到本页,至 3/07 —— 共十七张", 18, RUST, "start", 0.75)

assert len(pos) == len(T) == 331     # 一笔不少
for t in T:
    x, yy = pos[id(t)]
    draw_card(t, x, yy, 1.0, show_riskpct=(id(t) in frost_ids))

# ================= ⑥ 十七连败:疤 =================
def runs_of(ids_list):
    """把一串卡(已按顺序)切成同一行的连续段,返回 [(x,y,w,h)] 包住整段。"""
    out, cur = [], []
    for t in ids_list:
        x, yy = pos[id(t)]
        if cur and abs(cur[-1][1] - yy) < 1 and abs(cur[-1][0] + CW + GAPX - x) < 1:
            cur.append((x, yy))
        else:
            if cur:
                out.append(cur)
            cur = [(x, yy)]
    if cur:
        out.append(cur)
    return [(c[0][0], c[0][1], c[-1][0] + CW - c[0][0], CH) for c in out]

PAD = 6
SPAD = 8                              # 疤框外扩得比止损卡框更多,一眼分出「群」与「张」
scar_rects = runs_of(best)
for (x, yy, w, h) in scar_rects:
    svg.append(f'<rect x="{x-SPAD}" y="{yy-SPAD}" width="{w+2*SPAD}" height="{h+2*SPAD}" rx="7" fill="{RUST}" opacity="0.05"/>')
    svg.append(f'<rect x="{x-SPAD}" y="{yy-SPAD}" width="{w+2*SPAD}" height="{h+2*SPAD}" rx="7" fill="none" stroke="{RUST}" stroke-width="3.6" opacity="0.85"/>')
fx, fy, fw, fh = scar_rects[0]
frost_note_y = fy + 8
lines = [("十七连败 2/26 – 3/07", 23, RUST, "normal", 0.9),
         ("十七张收据,无一超预算:", 21, RUST, "italic", 0.85),
         ("单笔风险 0.12% – 1.13%,", 19, INK, "italic", 0.65),
         ("逐张印在卡上。", 19, INK, "italic", 0.65),
         ("合计 −$43,833", 20, INK, "italic", 0.7)]
yy = frost_note_y
for s, sz, c, st, op in lines:
    note(XN, yy, s, sz, c, "start", op, st)
    yy += 32
# leader:疤在二月段的右缘离页边最近,从那里短接到边注
runs_sorted = sorted(scar_rects, key=lambda r_: -(r_[0] + r_[2]))
lr = runs_sorted[0]
svg.append(f'<path d="M {lr[0]+lr[2]+PAD+4:.0f} {lr[1]+CH/2:.0f} Q {XN-40:.0f} {lr[1]+CH/2:.0f} {XN-8:.0f} {frost_note_y+16:.0f}" '
           f'fill="none" stroke="{RUST}" stroke-width="0.9" opacity="0.5"/>')

# ================= ⑦ BABA 最后三张 · ⑧ BE 第九张 =================
baba3 = [t for t in T if t["t"] == "BABA" and t["exit"] == dt.date(2026, 4, 23)]
baba3.sort(key=lambda z: pos[id(z)])
for (x, yy, w, h) in runs_of(baba3):
    svg.append(f'<rect x="{x-PAD}" y="{yy-PAD}" width="{w+2*PAD}" height="{h+2*PAD}" rx="6" fill="none" stroke="{INK}" stroke-width="3.4" opacity="0.9"/>')
be9 = next(t for t in T if t["t"] == "BE" and t["attempt"] == 9)
bx9, by9 = pos[id(be9)]
svg.append(f'<rect x="{bx9-PAD}" y="{by9-PAD}" width="{CW+2*PAD}" height="{CH+2*PAD}" rx="6" fill="none" stroke="{GOLD}" stroke-width="3" opacity="0.95"/>')

bnote_y = runs_of(baba3)[0][1] + 4
blines = [("BABA · 最后三张 · 4/23", 23, INK, "normal", 0.9),
          ("同日剪断:102 / 99 / 93 天,", 19, INK, "italic", 0.7),
          ("全簿最长的三根持仓条。", 19, INK, "italic", 0.7),
          ("五次尝试全败 −$54,418。", 20, RUST, "italic", 0.8),
          ("全簿唯一「该止没止」的反例:", 19, INK, "italic", 0.7),
          ("判断亏,不是探针亏。", 21, INK, "italic", 0.85)]
yy = bnote_y
for s, sz, c, st, op in blines:
    note(XN, yy, s, sz, c, "start", op, st)
    yy += 31
glines = [("BE · 第九张 · 金 · +7.3R", 23, mix(GOLD, INK, 0.25), "normal", 0.95),
          ("+$74,052。前八张学费收据", 19, INK, "italic", 0.7),
          ("散在此前(2/11 – 4/06),", 19, INK, "italic", 0.7),
          ("合计 −$19,300。", 20, INK, "italic", 0.7),
          ("4/23 认输,4/28 收获,", 20, INK, "italic", 0.75),
          ("—— 同一周。", 21, INK, "italic", 0.85)]
gy = max(yy + 26, by9 + 4)
yy = gy
for s, sz, c, st, op in glines:
    note(XN, yy, s, sz, c, "start", op, st)
    yy += 31
# leaders:走行间空隙,不横穿卡面
def leader_gutter(rect, note_y, color, op=0.5):
    x_, y_, w_, h_ = rect
    gy_ = y_ + CH + PAD + 3.5           # 行与行之间的空隙
    svg.append(f'<path d="M {x_+w_+PAD:.0f} {y_+h_+PAD-8:.0f} Q {x_+w_+PAD+8:.0f} {gy_:.0f} {x_+w_+PAD+22:.0f} {gy_:.0f} '
               f'L {XN-26:.0f} {gy_:.0f} Q {XN-10:.0f} {gy_:.0f} {XN-8:.0f} {note_y:.0f}" '
               f'fill="none" stroke="{color}" stroke-width="0.9" opacity="{op}"/>')

leader_gutter(runs_of(baba3)[0], bnote_y + 16, INK, 0.45)
leader_gutter((bx9, by9, CW, CH), gy + 16, GOLD, 0.6)

# ================= 页脚 =================
FY = MAT_Y1 + 44
hline(X0, XR, FY, 1.2, 0.5)
note(X0, FY + 42, f"本簿亏损收据 181 张,合计 −$611,377 —— 每一张都按价目表付清;盈利 132 张,合计 +$1,516,632;净 +$905,255(+90.5%)。", 24, INK, "start", 0.85, "normal")
note(X0, FY + 80, "胜率 39.9% · 盈亏比 3.40× · 止损(R ≤ −1)42 张 · 最长连败 17 · 最长连胜仅 6 · 31 张金卡 = 100% 净利润,其余 300 张加总 ≈ 0", 20, INK, "start", 0.62)
note(X0, FY + 116, "数据:交易 log 2025-12-31 → 2026-07-22,无一虚构 · 存根按离场日排序装订", 19, INK, "start", 0.5)
note(XR, FY + 116, "同一个动作 · The Same Gesture 系列 · Fluxus DataArt · sketch 08 · the receipts", 19, INK, "end", 0.5)

svg.append("</svg>")
out = Path(__file__).parent / "sketch_08_cells.svg"
out.write_text("\n".join(svg))
print("wrote", out, f"{W}x{H}", "cards:", len(T))
