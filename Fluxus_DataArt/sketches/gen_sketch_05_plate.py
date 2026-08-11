#!/usr/bin/env python3
"""sketch 05 — the plate · 数据版画(5000×2100)。
方向修正:回到 data humanism 本源。不画画:精确的线条与几何形状,专业信息设计。
一条时间脊柱,盈利向上/亏损向下,每一笔是一个多维 glyph;
所有尺度都有标尺,所有事件都有精确边界。La Lettura 版式。
"""
import math, datetime as dt, calendar
from pathlib import Path
from collections import defaultdict
from art_data import load

D = load()

W, H = 5000, 2100
PAPER, INK = "#f6f2e8", "#2b2823"
GREEN, GOLD, RUST, GREY, SLATE = "#3f6b4d", "#b8892b", "#a04a30", "#8a8175", "#5b7a96"

X0, X1 = 300, 4260          # time span
SPINE = 1270                 # the axis
WIN_MAX, LOSS_MAX = 790, 350 # zone heights (sqrt scales)
R_WIN_CAP, R_LOSS_CAP = 28.0, 6.0
LEG_X = 4390                 # legend column

D0, D1 = dt.date(2025, 12, 29), dt.date(2026, 7, 24)

def X(day):
    return X0 + (day - D0).days / (D1 - D0).days * (X1 - X0)

def y_win(r):
    return SPINE - math.sqrt(min(r, R_WIN_CAP) / R_WIN_CAP) * WIN_MAX

def y_loss(r):
    return SPINE + math.sqrt(min(abs(r), R_LOSS_CAP) / R_LOSS_CAP) * LOSS_MAX

def rad(risk):
    return 3.5 + math.sqrt(risk / 115_000) * 30

def mix(c1, c2, t):
    p = lambda c: (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16))
    a, b = p(c1), p(c2)
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Georgia, serif">',
       f'<rect width="{W}" height="{H}" fill="{PAPER}"/>']

def note(x, y, s, size=22, color=INK, anchor="start", op=0.8, style="italic", weight="normal"):
    svg.append(f'<text x="{x:.0f}" y="{y:.0f}" font-style="{style}" font-weight="{weight}" font-size="{size}" fill="{color}" text-anchor="{anchor}" opacity="{op}" font-family="Georgia, \'Songti SC\', serif">{s}</text>')

def hline(x1, x2, y, wd=0.8, op=0.3, color=INK, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    svg.append(f'<line x1="{x1:.0f}" y1="{y:.1f}" x2="{x2:.0f}" y2="{y:.1f}" stroke="{color}" stroke-width="{wd}" opacity="{op}"{d}/>')

def vline(x, y1, y2, wd=0.8, op=0.3, color=INK, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    svg.append(f'<line x1="{x:.1f}" y1="{y1:.0f}" x2="{x:.1f}" y2="{y2:.0f}" stroke="{color}" stroke-width="{wd}" opacity="{op}"{d}/>')

# ================= event bands (precise, full-height) =================
for (a, b), color, label in [(D["frost"], SLATE, "霜冻期 2/26–3/07 · 十七连败 · −$43,833"),
                             (D["storm"], SLATE, "回撤窗口 6/02–6/10 · 盯市 −$223,100(−11.1%)")]:
    xa, xb = X(a), X(b) + 12
    svg.append(f'<rect x="{xa:.0f}" y="330" width="{xb-xa:.0f}" height="{1690}" fill="{color}" opacity="0.07"/>')
    vline(xa, 330, 2020, 0.8, 0.35, color); vline(xb, 330, 2020, 0.8, 0.35, color, "2 4")
    note(xa, 316, label, 21, mix(SLATE, INK, 0.3), "start", 0.85)

# ================= month grid + axis =================
for m in range(1, 8):
    x = X(dt.date(2026, m, 1))
    vline(x, 360, 1980, 0.7, 0.14)
    note(x + 10, 1998, f"{m} 月", 24, INK, "start", 0.6, "normal")
hline(X0 - 20, X1 + 20, SPINE, 2.2, 0.85)

# week ticks on the spine
d = D0
while d <= D1:
    if d.weekday() == 0:
        vline(X(d), SPINE - 5, SPINE + 5, 0.9, 0.5)
    d += dt.timedelta(days=1)

# ================= R scales with gridlines =================
for r in [1, 2, 5, 10, 20]:
    y = y_win(r)
    hline(X0 - 20, X1 + 20, y, 0.6, 0.10)
    note(X0 - 34, y + 7, f"+{r}R", 20, INK, "end", 0.5)
for r in [1, 3, 5.7]:
    y = y_loss(-r)
    hline(X0 - 20, X1 + 20, y, 0.6, 0.10)
    note(X0 - 34, y + 7, f"−{r:g}R", 20, INK, "end", 0.5)
note(X0 - 130, y_win(20) - 26, "离场结果(R 倍数,√ 标尺)", 21, INK, "start", 0.6)

# ================= regime strip (daily, precise) =================
sess = [d for d in D["sessions"] if D0 <= d <= D1]
RS_Y, RS_H = SPINE + 8, 26
for i, d in enumerate(sess):
    x = X(d)
    nx = X(sess[i + 1]) if i + 1 < len(sess) else X1
    sc = D["regime"][d] / 100
    svg.append(f'<rect x="{x:.1f}" y="{RS_Y}" width="{max(nx-x,1.5):.1f}" height="{RS_H}" fill="{mix(SLATE, GOLD, sc)}" opacity="{0.25+0.55*sc:.2f}"/>')
svg.append(f'<rect x="{X0:.0f}" y="{RS_Y}" width="{X1-X0:.0f}" height="{RS_H}" fill="none" stroke="{INK}" stroke-width="0.7" opacity="0.4"/>')
note(X1 + 26, RS_Y + 20, "score 冷→暖", 18, INK, "start", 0.55)

# ================= entry rhythm rows =================
RH_Y = RS_Y + RS_H + 14
entries_by_day = defaultdict(int)
for t in D["trades"]:
    entries_by_day[t["entry"]] += 1
for d, n in entries_by_day.items():
    if d < D0:
        continue
    x = X(d)
    for k in range(n):
        vline(x, RH_Y + k * 9, RH_Y + k * 9 + 6, 1.5, 0.65)
note(X1 + 26, RH_Y + 22, "每格一次开仓", 18, INK, "start", 0.55)
# burst callout: the nine-entry day
xb9 = X(dt.date(2026, 5, 7))
note(xb9 + 10, RH_Y + 92, "5/07 单日 9 仓", 19, INK, "start", 0.65)
# silences: dedicated row at the bottom of the loss zone
SIL_Y = y_loss(-R_LOSS_CAP) + 96
for a, b in D["silences"]:
    if (b - a).days >= 5:
        xa, xb = X(a) + 6, X(b) - 6
        svg.append(f'<path d="M {xa:.0f} {SIL_Y-8} L {xa:.0f} {SIL_Y} L {xb:.0f} {SIL_Y} L {xb:.0f} {SIL_Y-8}" fill="none" stroke="{INK}" stroke-width="0.9" opacity="0.5"/>')
        note((xa + xb) / 2, SIL_Y + 24, f"沉默 {(b-a).days} 天", 19, INK, "middle", 0.6)
note(X1 + 26, SIL_Y + 6, "≥5 天不开仓", 18, INK, "start", 0.5)

# ================= equity line (top, precise) =================
by_exit = sorted(D["trades"], key=lambda z: z["exit"])
eq_by_day, cum = {}, 0.0
for t in by_exit:
    cum += t["pnl"]
    eq_by_day[t["exit"]] = 1_000_000 + cum
EQ_Y0, EQ_Y1 = 430, 200      # $1.0M .. $2.1M
def eq_y(v):
    return EQ_Y0 - (v - 1_000_000) / 1_100_000 * (EQ_Y0 - EQ_Y1)
for v, lab in [(1_000_000, "$1.0M"), (1_500_000, "$1.5M"), (2_000_000, "$2.0M")]:
    hline(X0, X1, eq_y(v), 0.6, 0.14)
    note(X0 - 34, eq_y(v) + 7, lab, 20, INK, "end", 0.5)
pts, last = [], 1_000_000
for d in sess:
    last = eq_by_day.get(d, last)
    for dd, vv in eq_by_day.items():
        if dd <= d and vv != last and dd > max([k for k in eq_by_day if k <= d], default=d):
            pass
    cur = max([v for k, v in eq_by_day.items() if k <= d], default=1_000_000, key=lambda z: 0)
# simpler: step through sessions
pts, cur = [], 1_000_000
for d in sess:
    if d in eq_by_day:
        cur = eq_by_day[d]
    pts.append((X(d), eq_y(cur)))
svg.append('<path d="M ' + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts) + f'" fill="none" stroke="{INK}" stroke-width="2" opacity="0.8"/>')
note(X0, EQ_Y1 - 16, "已实现净值(逐日) · 期末 $1,905,255(+90.5%)", 21, INK, "start", 0.6)
# MTM peak marker
xp = X(dt.date(2026, 6, 2))
svg.append(f'<circle cx="{xp:.0f}" cy="{eq_y(2_036_318):.0f}" r="6" fill="none" stroke="{GOLD}" stroke-width="2"/>')
note(xp + 14, eq_y(2_036_318) - 8, "6/02 盯市峰值 $2,036,318(+104%)——与回撤窗口首日同日", 21, mix(GOLD, INK, 0.3), "start", 0.9)

# ================= trade glyphs =================
by_day_w, by_day_l = defaultdict(list), defaultdict(list)
for t in D["trades"]:
    (by_day_w if t["pnl"] > 0 else by_day_l)[t["exit"]].append(t)

def glyph_shape(x, y, r_, species, color, gold, filled):
    if species == "ai":            # 圆 = AI 链
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r_:.1f}" fill="{color if filled else "none"}" fill-opacity="{0.85 if gold else 0.55}" stroke="{color}" stroke-width="1.6"/>')
    elif species == "other":       # 菱形 = 其他品种
        svg.append(f'<path d="M {x:.1f} {y-r_:.1f} L {x+r_:.1f} {y:.1f} L {x:.1f} {y+r_:.1f} L {x-r_:.1f} {y:.1f} Z" fill="{color if filled else "none"}" fill-opacity="{0.85 if gold else 0.5}" stroke="{color}" stroke-width="1.6"/>')
    else:                          # 空方 = 无根工具(杠杆 ETF)
        s = r_ * 0.85
        svg.append(f'<rect x="{x-s:.1f}" y="{y-s:.1f}" width="{2*s:.1f}" height="{2*s:.1f}" fill="none" stroke="{color}" stroke-width="1.6"/>')

anchors = {}
for day_map, is_win in [(by_day_w, True), (by_day_l, False)]:
    for day, ts in sorted(day_map.items()):
        n = len(ts)
        for i, t in enumerate(sorted(ts, key=lambda z: -abs(z["r"]))):
            x = X(day) + (i - (n - 1) / 2) * 11
            y = y_win(t["r"]) if is_win else y_loss(t["r"])
            color = (GOLD if t["gold"] else GREEN) if is_win else (RUST if t["r"] <= -1 else GREY)
            dash = ' stroke-dasharray="5 4"' if t["dir"] == "short" else ''
            # hold whisker: 从入场日到离场日的水平细线(在 glyph 高度)
            xe = X(max(t["entry"], D0))
            if x - xe > 3:
                svg.append(f'<line x1="{xe:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y:.1f}" stroke="{color}" stroke-width="0.9" opacity="0.4"/>')
            # stem: 从脊柱到 glyph
            svg.append(f'<line x1="{x:.1f}" y1="{SPINE + (0 if is_win else RS_H + 8):.1f}" y2="{y:.1f}" x2="{x:.1f}" stroke="{color}" stroke-width="1.1" opacity="0.55"{dash}/>')
            # trims: 分批离场的横刻
            for k in range(t["trims"] - 1):
                ty = y + (14 + k * 9) * (1 if is_win else -1)
                svg.append(f'<line x1="{x-5:.1f}" y1="{ty:.1f}" x2="{x+5:.1f}" y2="{ty:.1f}" stroke="{color}" stroke-width="1.2" opacity="0.6"/>')
            glyph_shape(x, y, rad(t["risk"]), t["species"], color, t["gold"], is_win)
            anchors[(t["t"], t["attempt"])] = (x, y)

# ================= narrative threads: BE / BABA =================
def thread(name, color):
    ks = sorted(k for k in anchors if k[0] == name)
    pts = [anchors[k] for k in ks]
    if len(pts) < 2:
        return
    d_ = f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"
    for a, b in zip(pts, pts[1:]):
        mx = (a[0] + b[0]) / 2
        d_ += f" C {mx:.1f} {a[1]:.1f} {mx:.1f} {b[1]:.1f} {b[0]:.1f} {b[1]:.1f}"
    svg.append(f'<path d="{d_}" fill="none" stroke="{color}" stroke-width="1.2" opacity="0.55"/>')
    for p in pts:
        svg.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="2.4" fill="{color}" opacity="0.8"/>')

thread("BE", mix(GREEN, INK, 0.15))
thread("BABA", RUST)
p9 = anchors.get(("BE", 9))
if p9:
    note(p9[0] + 20, p9[1] - 16, "BE 第九次 · +7.3R · +$74,052 · 前八次合计 −$19,300", 22, mix(GOLD, INK, 0.25), "start", 0.95)
baba_last = max([t for t in D["trades"] if t["t"] == "BABA"], key=lambda z: z["exit"])
p5 = anchors.get(("BABA", baba_last["attempt"]))
if p5:
    tx_, ty_ = X(dt.date(2026, 2, 16)), y_loss(-3.4)
    note(tx_, ty_, "BABA 五次全败 · −$54,418", 22, RUST, "start", 0.95)
    note(tx_, ty_ + 30, "持仓最长的三笔(102/99/93 天)都是它,4/23 同日剪断", 21, RUST, "start", 0.8)
    note(tx_, ty_ + 60, "同一个动作:被打出去再打回来。BE 的趋势还在,BABA 的论点已死。", 21, INK, "start", 0.6)
    svg.append(f'<path d="M {tx_+560:.0f} {ty_+76:.0f} Q {(tx_+560+p5[0])/2:.0f} {ty_+150:.0f} {p5[0]:.0f} {p5[1]+14:.0f}" fill="none" stroke="{RUST}" stroke-width="0.8" opacity="0.5"/>')

# 4/23 -> 4/28 the week
x423, x428 = X(dt.date(2026, 4, 23)), X(dt.date(2026, 4, 28))
yb = y_loss(-5.7) + 60
svg.append(f'<path d="M {x423:.0f} {yb} L {x423:.0f} {yb+10} L {x428:.0f} {yb+10} L {x428:.0f} {yb}" fill="none" stroke="{INK}" stroke-width="0.9" opacity="0.5"/>')
note((x423 + x428) / 2, yb + 36, "认输与收获,同一周", 21, INK, "middle", 0.65)

# ================= legend column (structured) =================
lx = LEG_X
note(lx, 250, "同一个动作", 64, INK, "start", 0.92, "normal")
note(lx, 296, "The Same Gesture", 24, INK, "start", 0.55)
note(lx, 330, "2026 上半年 · 331 笔真实交易", 22, INK, "start", 0.55)
svg.append(f'<rect x="{lx+430}" y="200" width="60" height="60" rx="5" fill="#9e2b1f" opacity="0.9"/>')
note(lx + 460, 228, "测", 24, "#f6f2e8", "middle", 0.95, "normal")
note(lx + 460, 252, "量", 24, "#f6f2e8", "middle", 0.95, "normal")

ly = 420
hline(lx, W - 90, ly - 24, 1.2, 0.5)
note(lx, ly, "读法", 26, INK, "start", 0.8, "normal")
rows = [
    ("shape", "ai", GREEN, "圆 = AI 链(169 笔,净利 80%)"),
    ("shape", "other", GREY, "菱 = 其他品种(69 笔,合计为负)"),
    ("shape", "rootless", INK, "空方 = 杠杆工具(93 笔)"),
    ("fill", None, GOLD, "金实心 = 扛起全部净利的 31 笔"),
    ("color", None, RUST, "锈红 = 止损(R ≤ −1,42 笔)"),
    ("text", None, INK, "向上 = 盈利 · 向下 = 亏损(√R 标尺)"),
    ("text", None, INK, "面积 = 该笔风险 $(种子大小)"),
    ("text", None, INK, "水平细线 = 持仓天数(入场→离场)"),
    ("text", None, INK, "横刻 = 分批离场 · 虚线茎 = 做空"),
    ("text", None, INK, "细曲线 = 同一标的的重复进攻(BE ×16 · BABA ×5)"),
]
for i, (kind, sp, c, label) in enumerate(rows):
    yy = ly + 40 + i * 46
    if kind == "shape":
        glyph_shape(lx + 16, yy - 7, 11, sp, c, False, sp != "rootless")
    elif kind == "fill":
        glyph_shape(lx + 16, yy - 7, 11, "ai", c, True, True)
    elif kind == "color":
        svg.append(f'<line x1="{lx+6}" y1="{yy-7}" x2="{lx+26}" y2="{yy-7}" stroke="{c}" stroke-width="2.4"/>')
    note(lx + 44, yy, label, 21, INK, "start", 0.75)

ly2 = ly + 40 + len(rows) * 46 + 30
hline(lx, W - 90, ly2 - 26, 0.8, 0.3)
note(lx, ly2, "数字", 26, INK, "start", 0.8, "normal")
stats = ["胜率 39.9% · 盈亏比 3.40× · 期望 +0.88R/笔",
         "最长连败 17 · 最长连胜 6 · 沉默期 15 段",
         "31 笔 = 100% 净利润;其余 300 笔加总 ≈ 0",
         "Caution 天气盈亏比 6.91× · Neutral 只有 1.85×",
         "连亏后 48h 种下的 73 笔:胜率 49% vs 平常 37%"]
for i, s in enumerate(stats):
    note(lx, ly2 + 40 + i * 40, s, 21, INK, "start", 0.7)

note(lx, H - 80, "数据:交易 log 2025-12-31 → 2026-07-22,无一虚构", 20, INK, "start", 0.5)
note(lx, H - 50, "Fluxus DataArt · sketch 05 · the plate", 20, INK, "start", 0.5)

svg.append("</svg>")
out = Path(__file__).parent / "sketch_05_plate.svg"
out.write_text("\n".join(svg))
print("wrote", out)
