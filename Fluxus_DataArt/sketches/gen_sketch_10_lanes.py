#!/usr/bin/env python3
"""sketch 10 — lanes · 品种泳道版(5000×2100)。
论点:「只有龙头有养分」。三条水平泳道共享一条时间轴:
上 = AI 链(169 笔,净利 80%)· 中 = 杠杆工具(93 笔,24%)· 下 = 其他品种(69 笔,加总为负)。
每道右端一根真实比例的净利汇总条 —— 那三根条是全图的结论。
远看 = 三道的疏密与三根条;近看 = 每一笔的个体档案。331 笔,一笔不少。
"""
import math, datetime as dt
from pathlib import Path
from collections import defaultdict
from art_data import load

D = load()

W, H = 5000, 2100
PAPER, INK = "#f6f2e8", "#2b2823"
GREEN, GOLD, RUST, GREY, SLATE = "#3f6b4d", "#b8892b", "#a04a30", "#8a8175", "#5b7a96"
SEAL = "#9e2b1f"

X0, X1 = 290, 4020          # 时间跨度
ZX = 4130                    # 汇总条零线
BAR_RATE = 300 / 750_000     # 汇总条 $→px(真实比例,三道共用)
LEG_X = 4520                 # 图例列
CUM_RATE = 0.00086           # 累计净利阶梯线 $→px(三道同一比例尺)

D0, D1 = dt.date(2025, 12, 29), dt.date(2026, 7, 24)

def X(day):
    day = max(day, D0)
    return X0 + (day - D0).days / (D1 - D0).days * (X1 - X0)

def rad(risk):
    return 3.5 + math.sqrt(risk / 115_000) * 30

def mix(c1, c2, t):
    p = lambda c: (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16))
    a, b = p(c1), p(c2)
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Georgia, \'Songti SC\', serif">',
       f'<rect width="{W}" height="{H}" fill="{PAPER}"/>']

def note(x, y, s, size=22, color=INK, anchor="start", op=0.8, style="italic", weight="normal", halo=False):
    common = f'font-style="{style}" font-weight="{weight}" font-size="{size}" text-anchor="{anchor}" font-family="Georgia, \'Songti SC\', serif"'
    if halo:
        svg.append(f'<text x="{x:.0f}" y="{y:.0f}" {common} fill="{PAPER}" stroke="{PAPER}" stroke-width="9" stroke-linejoin="round" opacity="0.85">{s}</text>')
    svg.append(f'<text x="{x:.0f}" y="{y:.0f}" {common} fill="{color}" opacity="{op}">{s}</text>')

def hline(x1, x2, y, wd=0.8, op=0.3, color=INK, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    svg.append(f'<line x1="{x1:.0f}" y1="{y:.1f}" x2="{x2:.0f}" y2="{y:.1f}" stroke="{color}" stroke-width="{wd}" opacity="{op}"{d}/>')

def vline(x, y1, y2, wd=0.8, op=0.3, color=INK, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    svg.append(f'<line x1="{x:.1f}" y1="{y1:.0f}" x2="{x:.1f}" y2="{y2:.0f}" stroke="{color}" stroke-width="{wd}" opacity="{op}"{d}/>')

def glyph_shape(x, y, r_, species, color, gold, filled, short=False):
    dash = ' stroke-dasharray="4 3"' if short else ''
    if species == "ai":            # 圆 = AI 链
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r_:.1f}" fill="{color if filled else "none"}" fill-opacity="{0.85 if gold else 0.55}" stroke="{color}" stroke-width="1.6"{dash}/>')
    elif species == "other":       # 菱形 = 其他品种
        svg.append(f'<path d="M {x:.1f} {y-r_:.1f} L {x+r_:.1f} {y:.1f} L {x:.1f} {y+r_:.1f} L {x-r_:.1f} {y:.1f} Z" fill="{color if filled else "none"}" fill-opacity="{0.85 if gold else 0.5}" stroke="{color}" stroke-width="1.6"{dash}/>')
    else:                          # 空心方 = 杠杆工具
        s = r_ * 0.85
        svg.append(f'<rect x="{x-s:.1f}" y="{y-s:.1f}" width="{2*s:.1f}" height="{2*s:.1f}" fill="none" stroke="{color}" stroke-width="1.6"{dash}/>')

# ================= 三条泳道的几何 =================
LANES = [
    dict(sp="ai",       name="AI 链",  shape_cn="圆",   top=95,   header=140, win_top=185,  base=830,  loss_bot=985,
         wcap=28.0, lcap=3.0, wticks=[1, 5, 10, 20], lticks=[1, 2]),
    dict(sp="rootless", name="杠杆工具", shape_cn="空心方", top=1035, header=1080, win_top=1112, base=1388, loss_bot=1458,
         wcap=10.0, lcap=1.6, wticks=[1, 3, 9], lticks=[1]),
    dict(sp="other",    name="其他品种", shape_cn="菱",   top=1505, header=1550, win_top=1580, base=1785, loss_bot=1912,
         wcap=7.0, lcap=6.0, wticks=[1, 3, 7], lticks=[1, 3, 5.7]),
]
LN = {l["sp"]: l for l in LANES}

def y_of(lane, r):
    if r >= 0:
        return lane["base"] - math.sqrt(min(r, lane["wcap"]) / lane["wcap"]) * (lane["base"] - lane["win_top"])
    return lane["base"] + math.sqrt(min(abs(r), lane["lcap"]) / lane["lcap"]) * (lane["loss_bot"] - lane["base"])

# 每道统计
STATS = {}
for l in LANES:
    ts = [t for t in D["trades"] if t["species"] == l["sp"]]
    wins = [t for t in ts if t["pnl"] > 0]
    losses = [t for t in ts if t["pnl"] < 0]
    aw = sum(t["pnl"] for t in wins) / len(wins)
    al = -sum(t["pnl"] for t in losses) / len(losses)
    STATS[l["sp"]] = dict(n=len(ts), net=sum(t["pnl"] for t in ts),
                          wr=100 * len(wins) / len(ts), pf=aw / al,
                          gold=sum(1 for t in ts if t["gold"]), ts=ts)
NET_ALL = sum(s["net"] for s in STATS.values())

# ================= 月份网格(贯穿三道) =================
for m in range(1, 8):
    x = X(dt.date(2026, m, 1))
    vline(x, 95, 1944, 0.7, 0.12)
    note(x + 8, 2022, f"{m} 月", 24, INK, "start", 0.6, "normal")

# ================= 道与道之间的细规则线 =================
hline(X0 - 50, ZX + 330, 1022, 0.9, 0.32)
hline(X0 - 50, ZX + 330, 1492, 0.9, 0.32)

# ================= 汇总条零线 + 底部时间轴 =================
vline(ZX, 150, 1938, 0.7, 0.4)
note(ZX, 138, "净利汇总 · 真实比例", 22, INK, "start", 0.75, "normal")
hline(X0 - 20, X1 + 20, 1948, 1.4, 0.6)
d = D0
while d <= D1:
    if d.weekday() == 0:
        vline(X(d), 1944, 1952, 0.9, 0.5)
    d += dt.timedelta(days=1)

# 汇总条标尺
RY = 1930
hline(ZX - 20, ZX + 310, RY, 0.8, 0.4)
for v, lab in [(0, "0"), (250_000, "+$250k"), (500_000, "+$500k"), (750_000, "+$750k")]:
    x = ZX + v * BAR_RATE
    vline(x, RY - 4, RY + 4, 0.9, 0.5)
    note(x, RY - 12, lab, 16, INK, "middle", 0.5)

# ================= regime 色带(底部时间轴上) =================
sess = [dd for dd in D["sessions"] if D0 <= dd <= D1]
RS_Y, RS_H = 1956, 24
for i, dd in enumerate(sess):
    x = X(dd)
    nx = X(sess[i + 1]) if i + 1 < len(sess) else X1
    sc = D["regime"][dd] / 100
    svg.append(f'<rect x="{x:.1f}" y="{RS_Y}" width="{max(nx-x,1.5):.1f}" height="{RS_H}" fill="{mix(SLATE, GOLD, sc)}" opacity="{0.25+0.55*sc:.2f}"/>')
svg.append(f'<rect x="{X0:.0f}" y="{RS_Y}" width="{X1-X0:.0f}" height="{RS_H}" fill="none" stroke="{INK}" stroke-width="0.7" opacity="0.4"/>')
note(X1 + 22, RS_Y + 18, "市场天气 score 冷→暖", 17, INK, "start", 0.55)

# ================= 每道:R 标尺 + 基线 + 道标 =================
for l in LANES:
    s = STATS[l["sp"]]
    # R 网格线与刻度
    for r in l["wticks"]:
        y = y_of(l, r)
        hline(X0 - 20, X1 + 20, y, 0.6, 0.10)
        note(X0 - 32, y + 6, f"+{r}R", 18, INK, "end", 0.5)
    for r in l["lticks"]:
        y = y_of(l, -r)
        hline(X0 - 20, X1 + 20, y, 0.6, 0.10)
        note(X0 - 32, y + 6, f"−{r:g}R", 18, INK, "end", 0.5)
    # 基线(R = 0)
    hline(X0 - 20, X1 + 20, l["base"], 1.8, 0.75)
    hline(X1 + 20, ZX, l["base"], 0.6, 0.15, INK, "2 6")
    note(X0 - 32, l["base"] + 6, "0", 18, INK, "end", 0.5)
    # 道标
    glyph_shape(X0 + 12, l["header"] - 9, 11, l["sp"], INK, False, l["sp"] != "rootless")
    sign = "+" if s["net"] >= 0 else "−"
    note(X0 + 36, l["header"], f'{l["name"]}({l["shape_cn"]})· {s["n"]} 笔', 30, INK, "start", 0.9, "normal")
    note(X0 + 620, l["header"], f'胜率 {s["wr"]:.1f}% · 盈亏比 {s["pf"]:.2f}× · 净利 {sign}${abs(s["net"]):,.0f} · 占净利 {s["net"]/NET_ALL*100:+.0f}%', 22, INK, "start", 0.6)

# 道标下的一句话
note(X0 + 36, LN["ai"]["header"] + 34, "大种子全种在这条道:最大单笔风险 $113,146。", 20, mix(GREEN, INK, 0.3), "start", 0.7)
note(X0 + 36, LN["rootless"]["header"] + 32, "顺风时的放大器,不是根:最大单笔风险只有 $15,907。", 20, INK, "start", 0.55)
note(X0 + 36, LN["other"]["header"] + 32, "做别的板块不是「长得慢」,是在消耗养分:69 笔加总,−$30,668。", 20, RUST, "start", 0.75)

# ================= 累计净利阶梯线(三道同一 $ 比例尺) =================
for l in LANES:
    ts = sorted(STATS[l["sp"]]["ts"], key=lambda z: z["exit"])
    cum_by_day, cum = {}, 0.0
    for t in ts:
        cum += t["pnl"]
        cum_by_day[t["exit"]] = cum
    pts, cur = [], 0.0
    for dd in sess:
        if dd in cum_by_day:
            cur = cum_by_day[dd]
        pts.append((X(dd), l["base"] - cur * CUM_RATE))
    path = f'M {X0} {l["base"]:.1f} L ' + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    svg.append(f'<path d="{path}" fill="none" stroke="{INK}" stroke-width="1.7" opacity="0.26"/>')
    svg.append(f'<circle cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="3" fill="{INK}" opacity="0.45"/>')
    # 右缘 $ 刻度
    lo = min(0, min(y for _, y in [(0, l["base"] - min(cum_by_day.values(), default=0) * CUM_RATE)]))
    ticks = ([0, 250_000, 500_000] if l["sp"] == "ai" else
             [0, 100_000, 200_000] if l["sp"] == "rootless" else [0, -40_000])
    for v in ticks:
        y = l["base"] - v * CUM_RATE
        hline(X1 + 2, X1 + 12, y, 0.8, 0.4)
        lab = "0" if v == 0 else (f"+${v//1000}k" if v > 0 else f"−${-v//1000}k")
        note(X1 + 16, y + 5, lab, 15, INK, "start", 0.45)
note(X1 + 16, LN["ai"]["base"] - 500_000 * CUM_RATE - 24, "累计净利(三道同尺)", 16, INK, "start", 0.5, halo=True)

# ================= 净利汇总条(全图的结论) =================
for l, color in [(LN["ai"], GREEN), (LN["rootless"], mix(INK, GREY, 0.25)), (LN["other"], RUST)]:
    net = STATS[l["sp"]]["net"]
    w = abs(net) * BAR_RATE
    if net >= 0:
        svg.append(f'<rect x="{ZX}" y="{l["base"]-35:.1f}" width="{w:.1f}" height="34" fill="{color}" opacity="0.78"/>')
    else:
        svg.append(f'<rect x="{ZX-w:.1f}" y="{l["base"]+1:.1f}" width="{w:.1f}" height="34" fill="{color}" opacity="0.85"/>')

aw_ = ZX + STATS["ai"]["net"] * BAR_RATE
note(aw_, LN["ai"]["base"] - 46, "+$721,529", 30, mix(GREEN, INK, 0.25), "end", 0.95, "normal")
note(aw_, LN["ai"]["base"] + 26, "= 净利的 80%", 20, INK, "end", 0.65, halo=True)
note(ZX + STATS["rootless"]["net"] * BAR_RATE + 16, LN["rootless"]["base"] - 10, "+$214,394", 26, INK, "start", 0.85, "normal")
note(ZX + STATS["rootless"]["net"] * BAR_RATE + 16, LN["rootless"]["base"] + 18, "= 24%", 20, INK, "start", 0.55)
bw = abs(STATS["other"]["net"]) * BAR_RATE
note(ZX + 14, LN["other"]["base"] + 30, "−$30,668", 26, RUST, "start", 0.95, "normal")
note(ZX + 14, LN["other"]["base"] + 56, "= −3% · 69 笔的总和", 19, RUST, "start", 0.7)

# ================= glyphs(每道内,按离场日) =================
anchors = {}
for l in LANES:
    by_day = defaultdict(list)
    for t in STATS[l["sp"]]["ts"]:
        by_day[t["exit"]].append(t)
    for day, ts in sorted(by_day.items()):
        n = len(ts)
        for i, t in enumerate(sorted(ts, key=lambda z: -abs(z["r"]))):
            x = X(day) + (i - (n - 1) / 2) * 10
            y = y_of(l, t["r"])
            win = t["pnl"] > 0
            color = (GOLD if t["gold"] else GREEN) if win else (RUST if t["r"] <= -1 else GREY)
            # 持仓细线:入场→离场
            xe = X(t["entry"])
            if x - xe > 3:
                svg.append(f'<line x1="{xe:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y:.1f}" stroke="{color}" stroke-width="0.9" opacity="0.38"/>')
            # 茎:基线→glyph
            dash = ' stroke-dasharray="5 4"' if t["dir"] == "short" else ''
            svg.append(f'<line x1="{x:.1f}" y1="{l["base"]:.1f}" x2="{x:.1f}" y2="{y:.1f}" stroke="{color}" stroke-width="1.0" opacity="0.5"{dash}/>')
            # 分批离场横刻
            for k in range(t["trims"] - 1):
                ty = y + (13 + k * 8) * (1 if win else -1)
                svg.append(f'<line x1="{x-5:.1f}" y1="{ty:.1f}" x2="{x+5:.1f}" y2="{ty:.1f}" stroke="{color}" stroke-width="1.1" opacity="0.55"/>')
            glyph_shape(x, y, rad(t["risk"]), t["species"], color, t["gold"], win, t["dir"] == "short")
            anchors[(t["t"], t["attempt"])] = (x, y)

# ================= 叙事线:BE ×16(AI 道)· BABA ×5(其他道) =================
def thread(name, color):
    ks = sorted(k for k in anchors if k[0] == name)
    pts = sorted([anchors[k] for k in ks])   # 按 x 排序,避免曲线回折
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
    note(p9[0] + 22, p9[1] - 30, "BE 第九次 · +7.3R · +$74,052", 24, mix(GOLD, INK, 0.25), "start", 0.95, halo=True)
    note(p9[0] + 22, p9[1] - 4, "前八次合计 −$19,300 —— 细线缠绕的就是那八次", 20, INK, "start", 0.65, halo=True)

# AI 道:两笔值得点名的收成
pd_ = anchors.get(("DOCN", 2))
if pd_:
    note(pd_[0] - 20, pd_[1] - 26, "DOCN · +17.4R · +$85,364(全年最大单笔)", 22, mix(GREEN, INK, 0.2), "end", 0.9, halo=True)
pa = anchors.get(("AXTI", 6))
if pa:
    note(pa[0] + 18, pa[1] - 12, "AXTI · +27.4R —— 种子只有 $475", 21, INK, "start", 0.7, halo=True)

# 其他道:BABA 档案
l_o = LN["other"]
p2 = anchors.get(("BABA", 2))
if p2:
    tx, ty = X(dt.date(2026, 1, 12)), l_o["base"] - 150
    note(tx, ty, "BABA ×5 全败 · −$54,418", 26, RUST, "start", 0.95, "normal", halo=True)
    note(tx, ty + 30, "Consumer Retail —— H1 最差品种", 21, RUST, "start", 0.8, halo=True)
    note(tx, ty + 58, "三笔各持 102 / 99 / 93 天,4/23 同日剪断;同一周,上面那条道:BE 第九次 +$74,052。", 20, INK, "start", 0.6, halo=True)
    # 注记直接压在 102 天持仓线上
    note(1400, p2[1] + 6, "最长的持仓给了最差的品种 —— 102 天", 19, RUST, "middle", 0.85, halo=True)
# 4/23 三笔同日:小括线
x423 = X(dt.date(2026, 4, 23))
yb = l_o["loss_bot"] + 6
svg.append(f'<path d="M {x423-16:.0f} {yb-6} L {x423-16:.0f} {yb} L {x423+16:.0f} {yb} L {x423+16:.0f} {yb-6}" fill="none" stroke="{RUST}" stroke-width="0.9" opacity="0.6"/>')
note(x423 + 24, yb + 4, "4/23 同日剪断", 17, RUST, "start", 0.75, halo=True)

# ================= 图例列 =================
lx = LEG_X
note(lx, 245, "只有龙头有养分", 52, INK, "start", 0.92, "normal")
note(lx, 292, "2026 上半年 · 331 笔真实交易,一笔不少", 22, INK, "start", 0.55)
note(lx, 324, "三条泳道 · 同一条时间轴 · 同一双手", 20, INK, "start", 0.45)

ly = 400
hline(lx, W - 80, ly - 26, 1.2, 0.5)
note(lx, ly, "读法", 26, INK, "start", 0.8, "normal")
rows = [
    ("shape", "ai", GREEN, "圆 = AI 链(上道,169 笔)"),
    ("shape", "other", GREY, "菱 = 其他品种(下道,69 笔)"),
    ("shape", "rootless", INK, "空心方 = 杠杆工具(中道,93 笔)"),
    ("fill", None, GOLD, "金实心 = 扛起全部净利的 31 笔(20/7/4)"),
    ("color", None, RUST, "锈红 = 止损(R ≤ −1)· 灰 = 小亏"),
    ("dash", None, INK, "虚线描边 = 做空"),
    ("text", None, INK, "上 = 盈利 · 下 = 亏损(√R 标尺,刻度在左)"),
    ("text", None, INK, "面积 = 风险 $(种子大小,三道同尺)"),
    ("text", None, INK, "水平细线 = 持仓天数(入场→离场)"),
    ("text", None, INK, "淡阶梯线 = 累计净利(三道同尺,右缘刻度)"),
    ("text", None, INK, "右端横条 = 各道净利(真实比例,下有标尺)"),
    ("text", None, INK, "细曲线 = 同一标的的重复进攻(BE·BABA)"),
]
for i, (kind, sp, c, label) in enumerate(rows):
    yy = ly + 40 + i * 42
    if kind == "shape":
        glyph_shape(lx + 16, yy - 7, 10, sp, c, False, sp != "rootless")
    elif kind == "fill":
        glyph_shape(lx + 16, yy - 7, 10, "ai", c, True, True)
    elif kind == "color":
        svg.append(f'<line x1="{lx+6}" y1="{yy-7}" x2="{lx+26}" y2="{yy-7}" stroke="{c}" stroke-width="2.4"/>')
    elif kind == "dash":
        svg.append(f'<circle cx="{lx+16}" cy="{yy-7}" r="10" fill="none" stroke="{c}" stroke-width="1.6" stroke-dasharray="4 3"/>')
    note(lx + 44, yy, label, 20, INK, "start", 0.75)

# ---- 数字块:80 / 24 / −3 ----
ny = ly + 40 + len(rows) * 42 + 44
hline(lx, W - 80, ny - 30, 0.8, 0.3)
note(lx, ny, "净利的分配", 26, INK, "start", 0.8, "normal")
trio = [("80%", GREEN, "AI 链 · 169 笔"), ("24%", mix(INK, GREY, 0.2), "杠杆工具 · 93 笔"), ("−3%", RUST, "其他品种 · 69 笔")]
for i, (big, c, lab) in enumerate(trio):
    bx = lx + i * 155
    note(bx, ny + 74, big, 58, c, "start", 0.95, "normal")
    note(bx, ny + 104, lab, 17, INK, "start", 0.6)
sy = ny + 150
for i, s in enumerate([
        "+$721,529 / +$214,394 / −$30,668(合计 +$905,255)",
        "胜率相近:41.4% / 40.9% / 34.8% —— 手是同一双",
        "盈亏比悬殊:4.46× / 3.21× / 1.44× —— 土不是同一片",
        "全账户:胜率 39.9% · 盈亏比 3.40× · +90.5%"]):
    note(lx, sy + i * 36, s, 20, INK, "start", 0.7)

# ---- 读 ----
ry2 = sy + 4 * 36 + 48
hline(lx, W - 80, ry2 - 28, 0.8, 0.3)
note(lx, ry2, "读", 26, INK, "start", 0.8, "normal")
for i, s in enumerate([
        "同一双手,同一套规则,三片不同的土。",
        "胜率几乎没有差别;差别全在赢的时候能长多大。",
        "龙头主题让 41% 的胜率长成 80% 的净利;",
        "其他品种用 69 笔换回一个负号。",
        "做别的板块不是「长得慢」——是在消耗养分。"]):
    note(lx, ry2 + 38 + i * 34, s, 21, INK, "start", 0.72)

# ---- 落款 + 印 ----
svg.append(f'<rect x="{W-80-60}" y="1706" width="60" height="60" rx="5" fill="{SEAL}" opacity="0.9"/>')
note(W - 80 - 30, 1734, "测", 24, PAPER, "middle", 0.95, "normal")
note(W - 80 - 30, 1758, "量", 24, PAPER, "middle", 0.95, "normal")
note(lx, 1860, "同一个动作 · The Same Gesture 系列", 22, INK, "start", 0.6, "normal")
note(lx, 1930, "数据:交易 log 2025-12-31 → 2026-07-22,无一虚构", 20, INK, "start", 0.5)
note(lx, 1962, "Fluxus DataArt · sketch 10 · lanes", 20, INK, "start", 0.5)

svg.append("</svg>")
out = Path(__file__).parent / "sketch_10_lanes.svg"
out.write_text("\n".join(svg))
print("wrote", out, len("\n".join(svg)) // 1024, "KB")
