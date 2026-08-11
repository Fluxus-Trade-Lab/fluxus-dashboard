#!/usr/bin/env python3
"""sketch 07 — rings 年轮(螺旋时间)· 论点 = 重复。
「每一次亏损都在教你,每一次盈利都在强化」——重复是这份工作里唯一的复利。
时间从中心向外螺旋,每月一圈(1 号在 12 点方向,顺时针);半径逐日线性增长。
每笔 = 径向刻线(盈利向外 √R,亏损向内)+ 品种 glyph(面积 = 风险 $)。
论点主角 = 同名重复进攻的缠绕线(≥5 次,19 个名字,142 笔 = 43%)。
零随机数 · 精确几何 · 所有尺度带标尺。
"""
import math, datetime as dt, calendar
from pathlib import Path
from collections import defaultdict
from art_data import load

D = load()

W = H = 2600
CX, CY = 1300, 1360
R0, GAP = 150, 108
PAPER, INK = "#f6f2e8", "#2b2823"
GREEN, GOLD, RUST, GREY, SLATE = "#3f6b4d", "#b8892b", "#a04a30", "#8a8175", "#5b7a96"
SEAL = "#9e2b1f"

D_START, D_END = dt.date(2025, 12, 29), dt.date(2026, 7, 24)

LW, LL = 62.0, 36.0          # win/loss radial tick max length
RCW, RCL = 28.0, 6.0         # R caps (data max +27.4 / −5.7)

def dim_of(d):
    return calendar.monthrange(d.year, d.month)[1]

def uof(d):
    """连续月坐标:Dec2025 = 0..1, Jan = 1..2, … Jul = 7..8。"""
    m = (d.year - 2025) * 12 + d.month - 12
    return m + (d.day - 1) / dim_of(d)

def rad_of(u):
    return R0 + u * GAP

def pt(u, r):
    a = 2 * math.pi * u
    return CX + r * math.sin(a), CY - r * math.cos(a)

def lwin(r):
    return math.sqrt(min(r, RCW) / RCW) * LW

def lloss(r):
    return math.sqrt(min(abs(r), RCL) / RCL) * LL

def grad(risk):
    return 2.0 + math.sqrt(risk / 115_000) * 12

def mix(c1, c2, t):
    p = lambda c: (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16))
    a, b = p(c1), p(c2)
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Georgia, serif">',
       f'<rect width="{W}" height="{H}" fill="{PAPER}"/>']

def note(x, y, s, size=22, color=INK, anchor="start", op=0.8, style="italic", weight="normal"):
    svg.append(f'<text x="{x:.0f}" y="{y:.0f}" font-style="{style}" font-weight="{weight}" '
               f'font-size="{size}" fill="{color}" text-anchor="{anchor}" opacity="{op}" '
               f'font-family="Georgia, \'Songti SC\', serif">{s}</text>')

def halo(x, y, w, h, op=0.82):
    svg.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="6" fill="{PAPER}" opacity="{op}"/>')

def poly(pts, color, wd, op, dash=None, cap="butt"):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    p = " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    svg.append(f'<path d="M {p}" fill="none" stroke="{color}" stroke-width="{wd}" opacity="{op}" stroke-linecap="{cap}"{d}/>')

def spiral_pts(u0, u1, roff=0.0, step=0.01):
    pts, u = [], u0
    while u < u1:
        pts.append(pt(u, rad_of(u) + roff)); u += step
    pts.append(pt(u1, rad_of(u1) + roff))
    return pts

U0, U1 = uof(D_START), uof(D_END) + 1 / 31

# ================= ① 事件扇区(浅色,先铺底) =================
for (a, b), label in [(D["frost"], "frost"), (D["storm"], "storm")]:
    ua, ub = uof(a), uof(b) + 1 / dim_of(b)
    # 用 13px 外偏、宽 132 的描边沿螺旋铺出扇区(覆盖 −53..+79 的刻线域)
    p = " L ".join(f"{x:.1f} {y:.1f}" for x, y in spiral_pts(ua, ub, 13))
    svg.append(f'<path d="M {p}" fill="none" stroke="{SLATE}" stroke-width="132" opacity="0.08" stroke-linecap="butt"/>')
    for uu, dash in [(ua, None), (ub, "3 4")]:
        r = rad_of(uu)
        (x1, y1), (x2, y2) = pt(uu, r - 53), pt(uu, r + 79)
        dd = f' stroke-dasharray="{dash}"' if dash else ''
        svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{SLATE}" stroke-width="1.2" opacity="0.5"{dd}/>')

# ================= ① 螺旋基线:整域淡线 + 交易日按地气上色 =================
poly(spiral_pts(U0, U1), INK, 1.0, 0.32)
for d in D["sessions"]:
    if not (D_START <= d <= D_END):
        continue
    u0 = uof(d); u1 = u0 + 1 / dim_of(d)
    sc = D["regime"][d] / 100
    poly(spiral_pts(u0, u1, 0, 0.004), mix(SLATE, GOLD, sc), 4.5, 0.25 + 0.55 * sc)

# 起点 / 终点端帽
xs, ys = pt(U0, rad_of(U0))
svg.append(f'<circle cx="{xs:.1f}" cy="{ys:.1f}" r="4" fill="{INK}" opacity="0.7"/>')
ue = uof(D_END) + 1 / 31
xe, ye = pt(ue, rad_of(ue))
(bx1, by1), (bx2, by2) = pt(ue, rad_of(ue) - 14), pt(ue, rad_of(ue) + 14)
svg.append(f'<line x1="{bx1:.1f}" y1="{by1:.1f}" x2="{bx2:.1f}" y2="{by2:.1f}" stroke="{INK}" stroke-width="2.4" opacity="0.8"/>')

# 终点注记:沿七月圈未走完的空弧(textPath)
arc = spiral_pts(ue + 0.015, ue + 0.16, 8, 0.004)
pth = " L ".join(f"{x:.1f} {y:.1f}" for x, y in arc)
svg.append(f'<defs><path id="endArc" d="M {pth}"/></defs>')
svg.append(f'<text font-size="26" font-style="italic" fill="{INK}" opacity="0.8" '
           f'font-family="Georgia, \'Songti SC\', serif"><textPath href="#endArc" startOffset="8">'
           f'7/24 收官 · $1,905,255 · +90.5%</textPath></text>')
# 起点小注
note(1128, 1146, "12/29 起步", 18, INK, "end", 0.6)

# ================= ① 12 点月轴:月份标签 + 月末权益,随年轮向外生长 =================
month_eq = {1: "$1.00M 起", 2: "$1.03M", 3: "$1.05M", 4: "$1.07M",
            5: "$1.21M", 6: "$1.44M", 7: "$1.76M"}   # 边界时刻 = 上月末已实现权益
svg.append(f'<line x1="{CX}" y1="436" x2="{CX}" y2="{CY-R0-56:.0f}" stroke="{INK}" stroke-width="0.9" opacity="0.35"/>')
for m in range(1, 8):
    r = R0 + m * GAP
    y = CY - r
    svg.append(f'<line x1="{CX-9}" y1="{y:.0f}" x2="{CX+9}" y2="{y:.0f}" stroke="{INK}" stroke-width="1.6" opacity="0.6"/>')
    fs = 15 + m * 1.4
    # 月名在界痕上方、权益在界痕下方,都压在轴线上居中(轴两侧 ±2.5° 无数据的楔形带)
    halo(CX - fs * 1.35, y - 8 - fs, fs * 2.7, fs + 6, 0.78)
    note(CX, y - 11, f"{m} 月", fs, INK, "middle", 0.78, "normal")
    ew = len(month_eq[m]) * fs * 0.42 + 10
    halo(CX - ew / 2, y + 12, ew, fs + 6, 0.78)
    note(CX, y + 13 + fs, month_eq[m], fs - 1, mix(GOLD, INK, 0.45), "middle", 0.92, "normal")
note(CX, 398, "1 号在 12 点 · 顺时针一圈 = 一个月", 20, INK, "middle", 0.55)

# ================= ③ 论点主角:同名重复进攻的缠绕线 =================
groups = defaultdict(list)
for t in D["trades"]:
    if t["attempts_total"] >= 5:
        groups[t["t"]].append(t)
for g in groups.values():
    g.sort(key=lambda z: (z["exit"], z["entry"]))

def anchor(t):
    return t["_pos"]

# 先计算所有 glyph 位置(离场日 + 同日错位)
by_exit_day = defaultdict(list)
for t in D["trades"]:
    by_exit_day[t["exit"]].append(t)
for day, ts in by_exit_day.items():
    ts.sort(key=lambda z: -abs(z["r"]))
    n = len(ts)
    uc = uof(day) + 0.5 / dim_of(day)
    rb = rad_of(uc)
    du = 13 / (2 * math.pi * rb)
    for i, t in enumerate(ts):
        uu = uc + (i - (n - 1) / 2) * du
        rr = rad_of(uu)
        L = lwin(t["r"]) if t["pnl"] > 0 else -lloss(t["r"])
        g = grad(t["risk"])
        t["_u"], t["_rb"] = uu, rr
        t["_tip"] = rr + L + (g if t["pnl"] > 0 else -g) * (1 if abs(L) > 0.5 else 0)
        t["_pos"] = pt(uu, t["_tip"])

def link_path(t1, t2):
    (x1, y1), (x2, y2) = anchor(t1), anchor(t2)
    r1 = math.hypot(x1 - CX, y1 - CY); r2 = math.hypot(x2 - CX, y2 - CY)
    chord = math.hypot(x2 - x1, y2 - y1)
    df = 0.22 + 0.78 * min((t2["exit"] - t1["exit"]).days / 100, 1)
    # 内弯深度同时受时间间隔与弦长约束:近的链结贴着走,远的才绕进中心
    c1r = r1 - min(df * (r1 - 268), 0.55 * chord + 6)
    c2r = r2 - min(df * (r2 - 268), 0.55 * chord + 6)
    c1 = (CX + (x1 - CX) / r1 * c1r, CY + (y1 - CY) / r1 * c1r)
    c2 = (CX + (x2 - CX) / r2 * c2r, CY + (y2 - CY) / r2 * c2r)
    return (f'M {x1:.1f} {y1:.1f} C {c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {x2:.1f} {y2:.1f}')

# 安静的底噪线(17 个名字)
for name, g in sorted(groups.items()):
    if name in ("BE", "BABA"):
        continue
    for a, b in zip(g, g[1:]):
        svg.append(f'<path d="{link_path(a, b)}" fill="none" stroke="{INK}" stroke-width="0.9" opacity="0.20"/>')

# BE ×16:加重的结线
be = groups["BE"]
BE_C = mix(GREEN, INK, 0.25)
for a, b in zip(be, be[1:]):
    svg.append(f'<path d="{link_path(a, b)}" fill="none" stroke="{BE_C}" stroke-width="2.3" opacity="0.75"/>')

# BABA ×5:锈红线,4/23 戛然而止
ba = groups["BABA"]
for a, b in zip(ba, ba[1:]):
    svg.append(f'<path d="{link_path(a, b)}" fill="none" stroke="{RUST}" stroke-width="2.0" opacity="0.8"/>')

# ================= ② 每笔交易:径向刻线 + 品种 glyph =================
def glyph(x, y, g, species, color, gold, filled, short):
    dash = ' stroke-dasharray="4 3"' if short else ''
    if species == "ai":
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{g:.1f}" '
                   f'fill="{color if filled else "none"}" fill-opacity="{0.9 if gold else 0.5}" '
                   f'stroke="{color}" stroke-width="1.4"{dash}/>')
    elif species == "other":
        svg.append(f'<path d="M {x:.1f} {y-g:.1f} L {x+g:.1f} {y:.1f} L {x:.1f} {y+g:.1f} L {x-g:.1f} {y:.1f} Z" '
                   f'fill="{color if filled else "none"}" fill-opacity="{0.9 if gold else 0.45}" '
                   f'stroke="{color}" stroke-width="1.4"{dash}/>')
    else:
        s = g * 0.85
        svg.append(f'<rect x="{x-s:.1f}" y="{y-s:.1f}" width="{2*s:.1f}" height="{2*s:.1f}" '
                   f'fill="{color if gold else "none"}" fill-opacity="{0.9 if gold else 0}" '
                   f'stroke="{color}" stroke-width="1.4"{dash}/>')

for t in sorted(D["trades"], key=lambda z: z["exit"]):
    uu, rb = t["_u"], t["_rb"]
    win = t["pnl"] > 0
    color = (GOLD if t["gold"] else GREEN) if win else (RUST if t["r"] <= -1 else GREY)
    L = lwin(t["r"]) if win else lloss(t["r"])
    g = grad(t["risk"])
    (x1, y1) = pt(uu, rb)
    (x2, y2) = pt(uu, rb + L if win else rb - L)
    if L > 0.5:
        svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                   f'stroke="{color}" stroke-width="{1.6 if t["gold"] else 1.1}" opacity="{0.9 if t["gold"] else 0.55}"/>')
    gx, gy = t["_pos"]
    glyph(gx, gy, g, t["species"], color, t["gold"], win, t["dir"] == "short")

# BE 结点 + 第九结注记
for i, t in enumerate(be):
    x, y = anchor(t)
    svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.0" fill="{BE_C}" opacity="0.9"/>')
p9 = next(t for t in be if t["attempt"] == 9)
x9, y9 = anchor(p9)
svg.append(f'<circle cx="{x9:.1f}" cy="{y9:.1f}" r="{grad(p9["risk"])+5:.1f}" fill="none" stroke="{GOLD}" stroke-width="1.6" opacity="0.9"/>')

# BABA 剪断记号:末端双短杠
last3 = [t for t in ba if t["exit"] == dt.date(2026, 4, 23)]
tcut = max(last3, key=lambda z: math.hypot(anchor(z)[0] - CX, anchor(z)[1] - CY))
xc, yc = anchor(tcut)
rr = math.hypot(xc - CX, yc - CY)
nx, ny = (xc - CX) / rr, (yc - CY) / rr          # 径向
txv, tyv = -ny, nx                               # 切向
for off in (-14, -22):
    ax, ay = xc + nx * off, yc + ny * off
    svg.append(f'<line x1="{ax-txv*9:.1f}" y1="{ay-tyv*9:.1f}" x2="{ax+txv*9:.1f}" y2="{ay+tyv*9:.1f}" '
               f'stroke="{RUST}" stroke-width="2.2" opacity="0.9"/>')

# ================= ④ 十七连败 / 第九次 / 扇区注记 =================
# 霜冻标签:沿 3 月 1–7 的盈利域空弧走 textPath(那 17 笔全是亏损,外侧是空的)
frost_arc = spiral_pts(3.045, 3.23, 56, 0.004)
fpth = " L ".join(f"{x:.1f} {y:.1f}" for x, y in frost_arc)
svg.append(f'<defs><path id="frostArc" d="M {fpth}"/></defs>')
svg.append(f'<text font-size="22" font-style="italic" fill="{mix(SLATE, INK, 0.45)}" opacity="0.9" '
           f'font-family="Georgia, \'Songti SC\', serif"><textPath href="#frostArc" startOffset="4">'
           f'教的那一面 —— 十七连败 · −$43,833</textPath></text>')

# 第九次(4/28)——强化的那一面。七月圈在此角度尚未存在,注记放空弧,引线径向进来
nax, nay = 709, 596
note(nax, nay, "第九次 —— 强化的那一面", 24, mix(GOLD, INK, 0.3), "end", 0.95)
note(nax, nay + 32, "+$74,052 · 前八次合计 −$19,300", 20, mix(GOLD, INK, 0.3), "end", 0.8)
svg.append(f'<path d="M {nax+8:.0f} {nay+10:.0f} L {x9-8:.1f} {y9-8:.1f}" fill="none" '
           f'stroke="{mix(GOLD, INK, 0.3)}" stroke-width="0.9" opacity="0.55" stroke-dasharray="2 4"/>')

# 回撤窗口注记:盘面右侧空白,引线进扇区
note(2352, 1168, "回撤窗口 6/02–6/10", 21, mix(SLATE, INK, 0.35), "start", 0.85)
note(2352, 1198, "盯市 −$223,100(−11.1%)", 19, mix(SLATE, INK, 0.35), "start", 0.75)
sx, sy = pt(6 + 5.5 / 30, rad_of(6 + 5.5 / 30) + 92)
svg.append(f'<path d="M 2344 1178 L {sx:.1f} {sy:.1f}" fill="none" stroke="{SLATE}" '
           f'stroke-width="0.9" opacity="0.5" stroke-dasharray="2 4"/>')

# BABA 注记:中心孔下缘,锈红引线到剪断处
halo(1078, 1448, 444, 96, 0.86)
note(CX, 1478, "BABA ×5 · 全败 −$54,418", 21, RUST, "middle", 0.95)
note(CX, 1510, "102 / 99 / 93 天 · 4/23 同日剪断", 19, RUST, "middle", 0.8)
svg.append(f'<path d="M 1082 1480 Q 900 1470 {xc+18:.0f} {yc+6:.0f}" fill="none" stroke="{RUST}" '
           f'stroke-width="0.9" opacity="0.5" stroke-dasharray="2 4"/>')

# ================= 中心:论点本体 =================
halo(1078, 1242, 444, 160, 0.88)
note(CX, 1316, "×331", 78, INK, "middle", 0.92, "normal")
note(CX, 1354, "同一个动作,重复三百三十一次", 22, INK, "middle", 0.75)
note(CX, 1388, "19 个名字被打了 5 次以上 · 142 笔 · 43%", 19, INK, "middle", 0.6)

# ================= 标题(TL) =================
note(110, 168, "每一次亏损都在教你,每一次盈利都在强化", 56, INK, "start", 0.92, "normal")
note(112, 218, "重复,是这份工作里唯一的复利 —— 年轮就是重复的形状", 26, INK, "start", 0.6)
note(112, 256, "Growth Rings · 2025-12-29 → 2026-07-24 · 331 笔真实交易,一圈一月", 20, INK, "start", 0.5)

# ================= 标尺(TL 下,贴着圆盘左上空区) =================
note(110, 336, "标尺", 26, INK, "start", 0.8, "normal")
svg.append('<line x1="110" y1="348" x2="560" y2="348" stroke="#2b2823" stroke-width="1.1" opacity="0.4"/>')
# R 刻线标尺
bx, by = 140, 452
svg.append(f'<line x1="{bx}" y1="{by}" x2="{bx+330}" y2="{by}" stroke="{INK}" stroke-width="1.4" opacity="0.6"/>')
for i, r in enumerate([1, 5, 10, 20]):
    x = bx + 30 + i * 80
    svg.append(f'<line x1="{x}" y1="{by}" x2="{x}" y2="{by-lwin(r):.1f}" stroke="{GREEN}" stroke-width="1.3" opacity="0.8"/>')
    note(x, by - lwin(r) - 8, f"+{r}R", 17, INK, "middle", 0.6)
for i, r in enumerate([1, 3, 6]):
    x = bx + 380 + i * 46
    svg.append(f'<line x1="{x}" y1="{by}" x2="{x}" y2="{by+lloss(r):.1f}" stroke="{RUST}" stroke-width="1.3" opacity="0.8"/>')
    note(x, by + lloss(r) + 18, f"−{r}R", 17, INK, "middle", 0.6)
note(110, 530, "径向刻线长 = √R · 向外 = 盈利 · 向内 = 亏损", 20, INK, "start", 0.65)
# 风险面积标尺
cy2 = 580
for x, v, lab in [(158, 2_000, "$2k"), (238, 20_000, "$20k"), (330, 80_000, "$80k")]:
    svg.append(f'<circle cx="{x}" cy="{cy2}" r="{grad(v):.1f}" fill="none" stroke="{INK}" stroke-width="1.2" opacity="0.6"/>')
    note(x, cy2 + 38, lab, 17, INK, "middle", 0.55)
note(110, 648, "glyph 面积 = 该笔风险 $(种子大小)", 20, INK, "start", 0.65)
# 地气色带
ry = 678
for i in range(40):
    svg.append(f'<rect x="{130+i*6.5:.1f}" y="{ry}" width="6.6" height="14" fill="{mix(SLATE, GOLD, i/39)}" opacity="{0.25+0.55*i/39:.2f}"/>')
note(122, ry + 12, "0", 16, INK, "end", 0.5)
note(398, ry + 12, "100", 16, INK, "start", 0.5)
note(110, ry + 44, "基线逐日按地气 score 上色 · 冷 → 暖", 20, INK, "start", 0.6)
note(110, ry + 76, "每笔刻在离场日", 19, INK, "start", 0.5)

# ================= 读法(TR) =================
lx = 2058
note(lx, 178, "读法", 26, INK, "start", 0.8, "normal")
svg.append(f'<line x1="{lx}" y1="190" x2="2542" y2="190" stroke="{INK}" stroke-width="1.1" opacity="0.4"/>')
rows = [
    ("ai", GREEN, False, False, "圆 = AI 链 · 169 笔 · 净利 80%"),
    ("other", GREY, False, False, "菱 = 其他品种 · 69 笔 · 合计 −$30,668"),
    ("rootless", INK, False, False, "空方 = 杠杆工具 · 93 笔"),
    ("ai", GOLD, True, False, "金实心 = 那 31 笔 = 100% 净利"),
    (None, RUST, False, False, "锈红 = 止损 R ≤ −1 · 42 次"),
    ("ai", GREEN, False, True, "虚线描边 = 做空 · 33 笔"),
    ("thin", INK, False, False, "细线 = 同名重复进攻(≥5 次)"),
    ("knot", BE_C, False, False, "结线 = BE ×16 · 锈红结线 = BABA ×5"),
]
for i, (sp, c, gd, sh, label) in enumerate(rows):
    yy = 232 + i * 44
    if sp in ("ai", "other", "rootless"):
        glyph(lx + 14, yy - 7, 10, sp, c, gd, True, sh)
    elif sp == "thin":
        svg.append(f'<path d="M {lx+2} {yy-4} C {lx+10} {yy-18} {lx+18} {yy+6} {lx+27} {yy-10}" fill="none" stroke="{c}" stroke-width="0.9" opacity="0.5"/>')
    elif sp == "knot":
        svg.append(f'<path d="M {lx+2} {yy-4} C {lx+10} {yy-18} {lx+18} {yy+6} {lx+27} {yy-10}" fill="none" stroke="{c}" stroke-width="2.3" opacity="0.8"/>')
        svg.append(f'<circle cx="{lx+2}" cy="{yy-4}" r="3" fill="{c}"/><circle cx="{lx+27}" cy="{yy-10}" r="3" fill="{c}"/>')
    else:
        svg.append(f'<line x1="{lx+4}" y1="{yy-7}" x2="{lx+24}" y2="{yy-7}" stroke="{c}" stroke-width="2.4"/>')
    note(lx + 40, yy, label, 20, INK, "start", 0.75)

# ================= 数字(BL) =================
ny0 = 2200
note(110, ny0, "数字", 26, INK, "start", 0.8, "normal")
svg.append(f'<line x1="110" y1="{ny0+12}" x2="600" y2="{ny0+12}" stroke="{INK}" stroke-width="1.1" opacity="0.4"/>')
stats = [
    ("最长连败 17 · 最长连胜 6", 0.85),
    ("十七连败共 −$43,833 · 无一笔超预算风险", 0.7),
    ("止损 42 次 = 学费", 0.85),
    ("31 笔金 = 复利 · 其余 300 笔加总 ≈ 0", 0.85),
    ("胜率 39.9% · 盈亏比 3.40× · 半年 +90.5%", 0.7),
    ("均盈 $11,490 · 均亏 $3,378", 0.7),
]
for i, (s, op) in enumerate(stats):
    note(110, ny0 + 52 + i * 42, s, 21, INK, "start", op)

# ================= 重复名单 + 落款(BR) =================
rx = 1950
note(rx, 2246, "重复进攻 · 同名 ≥5 次", 26, INK, "start", 0.8, "normal")
svg.append(f'<line x1="{rx}" y1="2258" x2="2436" y2="2258" stroke="{INK}" stroke-width="1.1" opacity="0.4"/>')
rep = ["BE ×16 · PL ×14 · NBIS ×11 · PLTR ×8",
       "ARKK ×8 · AXTI ×8 · DOCN ×8 · ONDS ×7 · SOXS ×7",
       "ALAB · SNDK · GLW · TSLL · SLV ×6",
       "BABA · ARM · FSLY · CAR · CRDO ×5",
       "19 个名字 · 142 笔 = 全部 331 笔的 43%"]
for i, s in enumerate(rep):
    note(rx, 2296 + i * 36, s, 19, INK, "start", 0.7)
note(rx, 2470, "数据:交易 log 2025-12-31 → 2026-07-22 · 无一虚构", 18, INK, "start", 0.5)
note(rx, 2502, "同一个动作 · The Same Gesture 系列 · sketch 07 · rings", 20, INK, "start", 0.6)
svg.append(f'<rect x="2482" y="2426" width="60" height="60" rx="5" fill="{SEAL}" opacity="0.9"/>')
note(2512, 2452, "测", 24, PAPER, "middle", 0.95, "normal")
note(2512, 2478, "量", 24, PAPER, "middle", 0.95, "normal")

svg.append("</svg>")
out = Path(__file__).parent / "sketch_07_rings.svg"
out.write_text("\n".join(svg))
print("wrote", out)

# ---- 诊断 ----
for t in D["trades"]:
    f = (t["_u"]) % 1
    a = min(f, 1 - f) * 360
    if a < 12:
        print("near-axis:", t["t"], t["exit"], f"angle={f*360:.0f}", "base=", round(t["_rb"]),
              "tip=", round(t["_tip"]), "WIN" if t["pnl"] > 0 else "loss")
# 霜冻窗口内唯一的赢家(它的外向刻线会不会撞 frost textPath)
for t in D["trades"]:
    if D["frost"][0] <= t["exit"] <= D["frost"][1] and t["pnl"] > 0:
        print("frost-win:", t["t"], t["exit"], f"angle={(t['_u']%1)*360:.0f}", "tip=", round(t["_tip"]))
# 第九次注记区(angle 312-332, r>930)是否真空
for t in D["trades"]:
    f = (t["_u"] % 1) * 360
    if 306 <= f <= 336 and max(t["_rb"], t["_tip"]) > 920:
        print("ninth-zone occupied:", t["t"], t["exit"], f"angle={f:.0f}", "tip=", round(t["_tip"]))
