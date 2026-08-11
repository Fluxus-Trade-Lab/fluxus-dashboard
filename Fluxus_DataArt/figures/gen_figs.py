#!/usr/bin/env python3
"""配图系统 — the fixed frame. 1600×900,纯英文,纸墨浅色。
一图一论点:01 净值+事件窗 · 02 R 分布 · 03 31/300 集中度 · 04 BE vs BABA。
美观工整:严格网格 · 大留白 · 大字号 · 同一模板。
"""
import sys, math, datetime as dt
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parents[1] / "sketches"))
from art_data import load

D = load()
OUT = Path(__file__).parent

W, H = 1600, 900
PAPER, INK = "#f6f2e8", "#2b2823"
GREEN, GOLD, RUST, GREY, SLATE = "#3f6b4d", "#b8892b", "#a04a30", "#8a8175", "#5b7a96"
ML, MR = 96, 96                      # margins
CH_TOP, CH_BOT = 250, 756            # chart zone

FONT = "Georgia, serif"


class Fig:
    def __init__(self, no, total, kicker, headline, sub):
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="{FONT}">',
                      f'<rect width="{W}" height="{H}" fill="{PAPER}"/>']
        self.no, self.total = no, total
        self.text(ML, 92, kicker, 15, GREY, weight="normal", spacing=3.2)
        self.text(ML, 148, headline, 46, INK, weight="normal")
        self.text(ML, 188, sub, 21, GREY, style="italic")
        self.line(ML, W - MR, 212, 1.1, 0.45)

    def text(self, x, y, s, size, color=INK, anchor="start", style="normal",
             weight="normal", op=1.0, spacing=None):
        sp = f' letter-spacing="{spacing}"' if spacing else ''
        self.parts.append(
            f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" fill="{color}" text-anchor="{anchor}" '
            f'font-style="{style}" font-weight="{weight}" opacity="{op}"{sp} font-family="{FONT}">{s}</text>')

    def line(self, x1, x2, y, wd=1.0, op=0.3, color=INK, dash=None, y2=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        yy2 = y if y2 is None else y2
        self.parts.append(f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{yy2:.1f}" '
                          f'stroke="{color}" stroke-width="{wd}" opacity="{op}"{d}/>')

    def vline(self, x, y1, y2, wd=1.0, op=0.3, color=INK, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.parts.append(f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" '
                          f'stroke="{color}" stroke-width="{wd}" opacity="{op}"{d}/>')

    def rect(self, x, y, w, h, color, op=1.0, rx=0, stroke=None, sw=1.0):
        s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
        self.parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                          f'fill="{color}" opacity="{op}" rx="{rx}"{s}/>')

    def circle(self, x, y, r, color, fill=True, op=1.0, sw=1.6):
        f = color if fill else "none"
        self.parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{f}" '
                          f'stroke="{color}" stroke-width="{sw}" opacity="{op}"/>')

    def path(self, d, color, wd=2.0, op=1.0, fill="none", dash=None):
        dd = f' stroke-dasharray="{dash}"' if dash else ''
        self.parts.append(f'<path d="{d}" fill="{fill}" stroke="{color}" stroke-width="{wd}" '
                          f'opacity="{op}" stroke-linejoin="round" stroke-linecap="round"{dd}/>')

    def save(self, name):
        y = H - 64
        self.line(ML, W - MR, y - 26, 1.1, 0.45)
        self.text(ML, y, "FLUXUS · THE SAME GESTURE — H1 2026 · REAL TRADE LOG, NOTHING SIMULATED",
                  13.5, GREY, spacing=2.2)
        self.text(W - MR - 56, y, f"{self.no:02d} / {self.total:02d}", 14, GREY, anchor="end")
        self.rect(W - MR - 40, y - 30, 40, 40, "#9e2b1f", 0.92, rx=4)
        self.text(W - MR - 20, y - 13, "测", 15, "#f6f2e8", anchor="middle")
        self.text(W - MR - 20, y + 3, "量", 15, "#f6f2e8", anchor="middle")
        self.parts.append("</svg>")
        (OUT / name).write_text("\n".join(self.parts))
        print("wrote", OUT / name)


D0, D1 = dt.date(2025, 12, 29), dt.date(2026, 7, 24)
def XT(day, x0=ML + 60, x1=W - MR - 30):
    return x0 + (day - D0).days / (D1 - D0).days * (x1 - x0)

sess = [d for d in D["sessions"] if D0 <= d <= D1]
by_exit = sorted(D["trades"], key=lambda z: z["exit"])
eq_by_day, cum = {}, 0.0
for t in by_exit:
    cum += t["pnl"]
    eq_by_day[t["exit"]] = 1_000_000 + cum

# ================================================================= fig 01
f = Fig(1, 4, "EQUITY · DEC 31 2025 — JUL 22 2026",
        "Two storms on the way to +90.5%",
        "Realized equity, 331 closed trades. The high-water mark and the drawdown began on the same day.")

def eqy(v):
    return CH_BOT - (v - 950_000) / 1_150_000 * (CH_BOT - CH_TOP)

for v in [1_000_000, 1_250_000, 1_500_000, 1_750_000, 2_000_000]:
    f.line(ML + 60, W - MR - 30, eqy(v), 0.8, 0.14)
    f.text(ML + 48, eqy(v) + 6, f"${v/1e6:.2f}M", 16, GREY, anchor="end")
for m in range(1, 8):
    x = XT(dt.date(2026, m, 1))
    f.vline(x, CH_BOT, CH_BOT + 8, 1, 0.4)
    f.text(x, CH_BOT + 30, ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL"][m - 1], 15, GREY, anchor="middle")

for (a, b), label, amt in [(D["frost"], "17 straight losses", "−$43,833"),
                           (D["storm"], "the drawdown window", "−$223,100 · −11.1%")]:
    xa, xb = XT(a), XT(b) + 8
    f.rect(xa, CH_TOP - 6, xb - xa, CH_BOT - CH_TOP + 6, SLATE, 0.10)
    f.vline(xa, CH_TOP - 6, CH_BOT, 0.9, 0.4, SLATE)
    f.text((xa + xb) / 2, CH_TOP + 22, label, 17, SLATE, anchor="middle", style="italic")
    f.text((xa + xb) / 2, CH_TOP + 46, amt, 16, SLATE, anchor="middle")

pts, cur = [], 1_000_000
for d in sess:
    cur = eq_by_day.get(d, cur)
    pts.append((XT(d), eqy(cur)))
f.path("M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts), INK, 2.6, 0.9)

xp, yp = XT(dt.date(2026, 6, 2)), eqy(2_036_318)
f.circle(xp, yp - 26, 7, GOLD, fill=False, sw=2.2)
f.line(xp, W is None or xp, yp - 19, 0)  # no-op guard
f.vline(xp, yp - 19, eqy(eq_by_day.get(dt.date(2026, 6, 2), cur)) - 6, 0.9, 0.5, GOLD)
f.text(xp - 12, yp - 58, "Jun 2 · mark-to-market peak $2,036,318 (+104%)", 18, INK, anchor="end")
f.text(xp - 12, yp - 34, "— the same day the storm began", 17, GREY, anchor="end", style="italic")
f.circle(pts[-1][0], pts[-1][1], 4.5, INK)
f.text(pts[-1][0] - 4, pts[-1][1] - 38, "$1,905,255", 20, INK, anchor="end")
f.text(pts[-1][0] - 4, pts[-1][1] - 16, "+90.5% realized", 16, GREY, anchor="end")
f.save("fig_01_equity.svg")

# ================================================================= fig 02
f = Fig(2, 4, "OUTCOME DISTRIBUTION · 331 CLOSED TRADES",
        "Losing six trades out of ten paid +90.5%",
        "Trades by R multiple. The average win is 3.40× the average loss — that is the entire trick.")

buckets = [("≤ −2R", 7, RUST), ("−2 … −1R", 35, RUST), ("−1 … 0", 139, GREY),
           ("0 … 1R", 53, GREEN), ("1 … 2R", 31, GREEN), ("2 … 3R", 19, GREEN), ("≥ 3R", 47, GOLD)]
bx0, bx1, base = ML + 30, 1030, CH_BOT - 40
bw = (bx1 - bx0) / len(buckets) - 26
maxn = 139
for i, (lab, n, c) in enumerate(buckets):
    x = bx0 + i * (bw + 26)
    h = n / maxn * (base - CH_TOP - 30)
    f.rect(x, base - h, bw, h, c, 0.82 if c != GREY else 0.55)
    f.text(x + bw / 2, base - h - 12, str(n), 19, INK, anchor="middle")
    f.text(x + bw / 2, base + 26, lab, 15.5, GREY, anchor="middle")
f.line(bx0 - 10, bx1 + 6, base, 1.4, 0.6)
lx_end = bx0 + 2 * (bw + 26) + bw
f.line(bx0, lx_end, base + 52, 0.9, 0.5, RUST)
f.text((bx0 + lx_end) / 2, base + 76, "199 trades lose — 60.1%", 16, RUST, anchor="middle", style="italic")
wx0 = bx0 + 3 * (bw + 26)
f.line(wx0, bx1 - 26 + bw + 6, base + 52, 0.9, 0.5, GREEN)
f.text((wx0 + bx1) / 2, base + 76, "132 win — 39.9%", 16, GREEN, anchor="middle", style="italic")

px = 1130
f.text(px, CH_TOP + 30, "average loss", 17, GREY)
f.rect(px, CH_TOP + 44, 3378 / 11490 * 330, 26, RUST, 0.8)
f.text(px + 3378 / 11490 * 330 + 12, CH_TOP + 63, "$3,378", 18, INK)
f.text(px, CH_TOP + 118, "average win", 17, GREY)
f.rect(px, CH_TOP + 132, 330, 26, GREEN, 0.8)
f.text(px + 330 - 4, CH_TOP + 151, "$11,490", 18, "#f6f2e8", anchor="end")
f.text(px, CH_TOP + 268, "3.40×", 64, INK)
f.text(px, CH_TOP + 302, "one average win pays for", 17, GREY, style="italic")
f.text(px, CH_TOP + 326, "3.4 average losses", 17, GREY, style="italic")
f.save("fig_02_distribution.svg")

# ================================================================= fig 03
ranked = sorted(D["trades"], key=lambda z: -z["pnl"])
top31 = sum(t["pnl"] for t in ranked[:31])
rest = sum(t["pnl"] for t in ranked[31:])
f = Fig(3, 4, "CONCENTRATION · ALL 331 TRADES, RANKED BY P&amp;L",
        "31 trades carried the whole year",
        f"The top 31 made ${top31/1000:,.0f}k. The other 300 add up to {'-' if rest<0 else ''}${abs(rest)/1000:.0f}k — roughly zero.")

cols, cell = 30, 30
gx0, gy0 = ML + 10, CH_TOP + 26
for i, t in enumerate(ranked):
    r_, c_ = divmod(i, cols)
    x, y = gx0 + c_ * cell, gy0 + r_ * cell * 1.32
    if t["gold"]:
        f.circle(x, y, 8.6, GOLD)
    elif t["pnl"] > 0:
        f.circle(x, y, 6.4, GREEN, fill=False, sw=1.4, op=0.75)
    else:
        f.circle(x, y, 6.4, RUST if t["r"] <= -1 else GREY, fill=False, sw=1.3, op=0.55)
bracket_x = gx0 + 30 * cell + 4
f.text(gx0, gy0 - 20, "each dot is one trade · gold = the 31 · ranked left-to-right, top-to-bottom", 15.5, GREY, style="italic")

px, pw = 1120, 330
f.text(px, CH_TOP + 40, "the 31 (9% of trades)", 17, GREY)
f.rect(px, CH_TOP + 54, pw, 30, GOLD, 0.9)
f.text(px + pw - 8, CH_TOP + 75, f"+${top31/1e3:,.0f}k", 18, "#f6f2e8", anchor="end")
f.text(px, CH_TOP + 128, "the other 300 (91%)", 17, GREY)
rw = max(abs(rest) / top31 * pw, 3)
f.rect(px, CH_TOP + 142, rw, 30, RUST if rest < 0 else GREY, 0.8)
f.text(px + rw + 12, CH_TOP + 163, f"{'-' if rest<0 else ''}${abs(rest)/1e3:,.0f}k", 18, INK)
f.text(px, CH_TOP + 262, "100%", 64, INK)
f.text(px, CH_TOP + 296, "of net P&amp;L came from trades", 17, GREY, style="italic")
f.text(px, CH_TOP + 320, "you could count on your hands", 17, GREY, style="italic")
f.save("fig_03_concentration.svg")

# ================================================================= fig 04
f = Fig(4, 4, "RE-ENTRY · TWO NAMES, ONE GESTURE",
        "The same gesture, two verdicts",
        "Stopped out, go back in. With the trend intact it is persistence; against a dead thesis it is stubbornness.")

be = sorted([t for t in D["trades"] if t["t"] == "BE"], key=lambda z: z["exit"])
baba = sorted([t for t in D["trades"] if t["t"] == "BABA"], key=lambda z: z["exit"])
T0, T1 = dt.date(2026, 1, 1), dt.date(2026, 7, 1)
def xt(day, x0=ML + 150, x1=W - MR - 60):
    return x0 + (day - T0).days / (T1 - T0).days * (x1 - x0)

for m in range(1, 8):
    x = xt(dt.date(2026, m, 1))
    f.vline(x, CH_TOP + 10, CH_BOT - 10, 0.7, 0.10)
    f.text(x, CH_BOT + 22, ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL"][m - 1], 14.5, GREY, anchor="middle")

yBE, yBB = CH_TOP + 105, CH_TOP + 330
f.text(ML + 10, yBE - 62, "BE — 16 attempts", 22, INK)
f.text(ML + 10, yBE - 36, "eight stops before it paid", 16, GREY, style="italic")
f.line(ML + 150, W - MR - 60, yBE, 1.1, 0.35)
for i, t in enumerate(be):
    x = xt(t["exit"])
    r_ = max(5, min(5 + abs(t["pnl"]) / 74052 * 17, 22))
    if t["pnl"] > 60000:
        f.circle(x, yBE, r_, GOLD)
        f.vline(x, yBE - r_ - 6, yBE - 56, 0.9, 0.5, GOLD)
        f.text(x, yBE - 88, "#9 · Apr 28", 18, INK, anchor="middle")
        f.text(x, yBE - 66, "+$74,052 · +7.3R", 17, GOLD, anchor="middle")
    elif t["pnl"] > 0:
        f.circle(x, yBE, max(r_, 5.5), GREEN, fill=False, sw=1.6)
    else:
        f.circle(x, yBE, max(r_, 5.5), RUST, fill=False, sw=1.6)
x8a, x8b = xt(be[0]["exit"]) - 10, xt(be[7]["exit"]) + 10
f.line(x8a, x8b, yBE + 34, 0.9, 0.5, RUST)
f.vline(x8a, yBE + 28, yBE + 34, 0.9, 0.5, RUST)
f.vline(x8b, yBE + 28, yBE + 34, 0.9, 0.5, RUST)
f.text((x8a + x8b) / 2, yBE + 58, "eight stops · −$19,300 total", 16, RUST, anchor="middle", style="italic")

f.text(ML + 10, yBB - 62, "BABA — 5 attempts", 22, INK)
f.text(ML + 10, yBB - 36, "the thesis died; the holding didn't", 16, GREY, style="italic")
f.line(ML + 150, W - MR - 60, yBB, 1.1, 0.35)
for t in baba:
    xin, xout = xt(t["entry"]), xt(t["exit"])
    if t["hold"] > 30:
        f.line(xin, xout, yBB, 5, 0.30, RUST)
        f.circle(xin, yBB, 4, RUST, fill=False, sw=1.4)
    f.circle(xout, yBB, max(5.5, min(5 + abs(t["pnl"]) / 74052 * 17, 22)), RUST, fill=False, sw=1.8)
xcut = xt(dt.date(2026, 4, 23))
f.vline(xcut, yBB - 30, yBB + 30, 1.2, 0.7, RUST)
f.text(xcut + 14, yBB - 44, "Apr 23 — all three cut the same day", 17, INK)
f.text(xcut + 14, yBB - 20, "held 102 / 99 / 93 days · five tries, −$54,418", 16, RUST)
f.text(ML + 150, CH_BOT - 6,
       "Five days apart: the surrender (Apr 23) and the harvest (Apr 28) settled in the same week.",
       17, GREY, style="italic")
f.save("fig_04_gesture.svg")
