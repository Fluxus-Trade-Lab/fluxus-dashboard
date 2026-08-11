#!/usr/bin/env python3
"""配图系统 · crafty 版 — 同一个固定模板,手作的墨迹。
版式/网格/排印不动;数据标记全部手画:颤线 · 排线填充 · 双笔圆 · 红铅笔圈注。
确定性伪随机(固定种子),同一输入永远同一张图。
"""
import sys, math, random, datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "sketches"))
from art_data import load

D = load()
OUT = Path(__file__).parent
rng = random.Random(20260722)

W, H = 1600, 900
PAPER, INK = "#f6f2e8", "#2b2823"
GREEN, GOLD, RUST, GREY, SLATE = "#3f6b4d", "#b8892b", "#a04a30", "#8a8175", "#5b7a96"
PENCIL = "#b03a2e"
ML, MR = 96, 96
CH_TOP, CH_BOT = 250, 756
FONT = "Georgia, serif"


def wob(pts, amp=1.4):
    """给折线加克制的手绘颤:低频正弦+微量噪声,重采样为平滑 path。"""
    out = []
    ph = rng.uniform(0, 6.28)
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        t = i / max(n - 1, 1)
        dx = math.sin(t * 11 + ph) * amp * 0.4 + rng.uniform(-amp, amp) * 0.25
        dy = math.sin(t * 7 + ph * 1.7) * amp + rng.uniform(-amp, amp) * 0.3
        out.append((x + dx, y + dy))
    d = f"M {out[0][0]:.1f} {out[0][1]:.1f}"
    for a, b in zip(out, out[1:]):
        d += f" Q {a[0]:.1f} {a[1]:.1f} {(a[0]+b[0])/2:.1f} {(a[1]+b[1])/2:.1f}"
    return d


class Fig:
    def __init__(self, no, total, kicker, headline, sub):
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="{FONT}">',
                      f'<rect width="{W}" height="{H}" fill="{PAPER}"/>']
        for _ in range(150):     # paper grain
            self.parts.append(f'<circle cx="{rng.uniform(0,W):.0f}" cy="{rng.uniform(0,H):.0f}" '
                              f'r="{rng.uniform(0.3,0.8):.1f}" fill="{INK}" opacity="0.035"/>')
        self.no, self.total = no, total
        self.text(ML, 92, kicker, 15, GREY, spacing=3.2)
        self.text(ML, 148, headline, 46, INK)
        self.text(ML, 188, sub, 21, GREY, style="italic")
        self.hline(ML, W - MR, 212, 1.1, 0.45)

    def text(self, x, y, s, size, color=INK, anchor="start", style="normal",
             weight="normal", op=1.0, spacing=None):
        sp = f' letter-spacing="{spacing}"' if spacing else ''
        self.parts.append(
            f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" fill="{color}" text-anchor="{anchor}" '
            f'font-style="{style}" font-weight="{weight}" opacity="{op}"{sp} font-family="{FONT}">{s}</text>')

    def hline(self, x1, x2, y, wd=1.0, op=0.3, color=INK):
        self.parts.append(f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" '
                          f'stroke="{color}" stroke-width="{wd}" opacity="{op}"/>')

    def vline(self, x, y1, y2, wd=1.0, op=0.3, color=INK):
        self.parts.append(f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" '
                          f'stroke="{color}" stroke-width="{wd}" opacity="{op}"/>')

    def hand_line(self, x1, y1, x2, y2, wd=1.6, op=0.8, color=INK, amp=1.2, n=10):
        pts = [(x1 + (x2 - x1) * i / n, y1 + (y2 - y1) * i / n) for i in range(n + 1)]
        self.parts.append(f'<path d="{wob(pts, amp)}" fill="none" stroke="{color}" '
                          f'stroke-width="{wd}" opacity="{op}" stroke-linecap="round"/>')

    def hand_path(self, pts, wd=2.4, op=0.9, color=INK, amp=1.3):
        self.parts.append(f'<path d="{wob(pts, amp)}" fill="none" stroke="{color}" '
                          f'stroke-width="{wd}" opacity="{op}" stroke-linejoin="round" stroke-linecap="round"/>')

    def hand_circle(self, x, y, r, color, fill=False, op=0.9, sw=1.7):
        for k, (dr, o) in enumerate([(0, op), (rng.uniform(0.6, 1.1), op * 0.4)]):
            rot = rng.uniform(-20, 20)
            self.parts.append(f'<ellipse cx="{x+dr*0.6:.1f}" cy="{y+dr*0.4:.1f}" rx="{r+dr*0.3:.1f}" '
                              f'ry="{r*rng.uniform(0.93,1.0)+dr*0.3:.1f}" fill="none" stroke="{color}" '
                              f'stroke-width="{sw}" opacity="{o:.2f}" transform="rotate({rot:.0f} {x:.1f} {y:.1f})"/>')
        if fill:
            self.parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r*0.62:.1f}" fill="{color}" opacity="{op*0.85:.2f}"/>')

    def hatch_rect(self, x, y, w, h, color, spacing=7.5, op=0.6, outline=True, sw=1.7):
        cid = f"hc{len(self.parts)}"
        self.parts.append(f'<defs><clipPath id="{cid}"><rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"/></clipPath></defs>')
        k = 0
        xx = x - h
        while xx < x + w:
            j1, j2 = rng.uniform(-1.6, 1.6), rng.uniform(-1.6, 1.6)
            self.parts.append(f'<line x1="{xx+j1:.1f}" y1="{y+h+1:.1f}" x2="{xx+h+j2:.1f}" y2="{y-1:.1f}" '
                              f'stroke="{color}" stroke-width="1.5" opacity="{op}" clip-path="url(#{cid})"/>')
            xx += spacing; k += 1
        if outline:
            # 每条边取密点,让平滑保住直角——手的颤在边上,不在角上
            pts = []
            for (ax, ay), (bx2, by2) in [((x, y + h), (x, y)), ((x, y), (x + w, y)),
                                         ((x + w, y), (x + w, y + h))]:
                for k in range(7):
                    t = k / 7
                    pts.append((ax + (bx2 - ax) * t, ay + (by2 - ay) * t))
            pts.append((x + w, y + h))
            self.hand_path(pts, sw, 0.85, color, 0.7)

    def pencil_ring(self, x, y, rx, ry, color=PENCIL):
        """红铅笔圈注:一圈半,起收笔交叠。"""
        pts = []
        for k in range(30):
            a = -0.6 + k / 29 * (2 * math.pi * 1.18)
            rr1 = rx * (1 + 0.05 * math.sin(k * 1.7))
            rr2 = ry * (1 + 0.06 * math.cos(k * 2.1))
            pts.append((x + math.cos(a) * rr1, y + math.sin(a) * rr2))
        self.parts.append(f'<path d="{wob(pts, 1.0)}" fill="none" stroke="{color}" '
                          f'stroke-width="2.4" opacity="0.75" stroke-linecap="round"/>')

    def hand_bracket(self, x1, x2, y, color, op=0.6, drop=8):
        pts = [(x1, y - drop), (x1 + 3, y), ((x1 + x2) / 2, y + 3), (x2 - 3, y), (x2, y - drop)]
        self.hand_path(pts, 1.4, op, color, 0.9)

    def leader(self, x1, y1, x2, y2, color=GREY, op=0.6):
        mx, my = (x1 + x2) / 2 + rng.uniform(-6, 6), (y1 + y2) / 2 - 14
        self.parts.append(f'<path d="M {x1:.0f} {y1:.0f} Q {mx:.0f} {my:.0f} {x2:.0f} {y2:.0f}" '
                          f'fill="none" stroke="{color}" stroke-width="1.1" opacity="{op}"/>')

    def save(self, name):
        y = H - 64
        self.hline(ML, W - MR, y - 26, 1.1, 0.45)
        self.text(ML, y, "FLUXUS · THE SAME GESTURE — H1 2026 · REAL TRADE LOG, NOTHING SIMULATED",
                  13.5, GREY, spacing=2.2)
        self.text(W - MR - 56, y, f"{self.no:02d} / {self.total:02d}", 14, GREY, anchor="end")
        self.parts.append(f'<rect x="{W-MR-40}" y="{y-30}" width="40" height="40" rx="4" fill="#9e2b1f" opacity="0.92"/>')
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

# ============================================================ fig 01 crafty
f = Fig(1, 4, "EQUITY · DEC 31 2025 — JUL 22 2026",
        "Two storms on the way to +90.5%",
        "Realized equity, 331 closed trades. The high-water mark and the drawdown began on the same day.")

def eqy(v):
    return CH_BOT - (v - 950_000) / 1_150_000 * (CH_BOT - CH_TOP)

for v in [1_000_000, 1_250_000, 1_500_000, 1_750_000, 2_000_000]:
    f.hline(ML + 60, W - MR - 30, eqy(v), 0.8, 0.13)
    f.text(ML + 48, eqy(v) + 6, f"${v/1e6:.2f}M", 16, GREY, anchor="end")
for m in range(1, 8):
    x = XT(dt.date(2026, m, 1))
    f.vline(x, CH_BOT, CH_BOT + 8, 1, 0.4)
    f.text(x, CH_BOT + 30, ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL"][m - 1], 15, GREY, anchor="middle")

for (a, b), label, amt in [(D["frost"], "17 straight losses", "−$43,833"),
                           (D["storm"], "the drawdown window", "−$223,100 · −11.1%")]:
    xa, xb = XT(a), XT(b) + 8
    f.hatch_rect(xa, CH_TOP - 6, xb - xa, CH_BOT - CH_TOP + 6, SLATE, spacing=10, op=0.18, outline=False)
    f.hand_line(xa, CH_TOP - 6, xa, CH_BOT, 1.1, 0.45, SLATE, amp=0.9)
    f.text((xa + xb) / 2, CH_TOP + 22, label, 17, SLATE, anchor="middle", style="italic")
    f.text((xa + xb) / 2, CH_TOP + 46, amt, 16, SLATE, anchor="middle")

pts, cur = [], 1_000_000
for d in sess:
    cur = eq_by_day.get(d, cur)
    pts.append((XT(d), eqy(cur)))
f.hand_path(pts, 2.6, 0.9, INK, amp=1.6)

xp, yp = XT(dt.date(2026, 6, 2)), eqy(2_036_318)
f.hand_circle(xp, yp - 26, 8, GOLD, sw=2.2)
f.leader(xp - 8, yp - 32, xp - 120, yp - 52, GOLD)
f.text(xp - 130, yp - 58, "Jun 2 · mark-to-market peak $2,036,318 (+104%)", 18, INK, anchor="end")
f.text(xp - 130, yp - 34, "— the same day the storm began", 17, GREY, anchor="end", style="italic")
f.hand_circle(pts[-1][0], pts[-1][1], 5, INK, fill=True)
f.text(pts[-1][0] - 4, pts[-1][1] - 40, "$1,905,255", 20, INK, anchor="end")
f.text(pts[-1][0] - 4, pts[-1][1] - 18, "+90.5% realized", 16, GREY, anchor="end")
f.pencil_ring(pts[-1][0] - 68, pts[-1][1] - 33, 88, 26)
f.save("fig_01_equity_crafty.svg")

# ============================================================ fig 02 crafty
f = Fig(2, 4, "OUTCOME DISTRIBUTION · 331 CLOSED TRADES",
        "Losing six trades out of ten paid +90.5%",
        "Trades by R multiple. The average win is 3.40× the average loss — that is the entire trick.")

buckets = [("≤ −2R", 7, RUST), ("−2 … −1R", 35, RUST), ("−1 … 0", 139, GREY),
           ("0 … 1R", 53, GREEN), ("1 … 2R", 31, GREEN), ("2 … 3R", 19, GREEN), ("≥ 3R", 47, GOLD)]
bx0, bx1, base = ML + 30, 1030, CH_BOT - 40
bw = (bx1 - bx0) / len(buckets) - 26
for i, (lab, n, c) in enumerate(buckets):
    x = bx0 + i * (bw + 26)
    h = n / 139 * (base - CH_TOP - 30)
    f.hatch_rect(x, base - h, bw, h, c, spacing=8 if n > 20 else 6.5, op=0.55)
    f.text(x + bw / 2, base - h - 12, str(n), 19, INK, anchor="middle")
    f.text(x + bw / 2, base + 26, lab, 15.5, GREY, anchor="middle")
f.hand_line(bx0 - 10, base, bx1 + 6, base, 1.6, 0.6, INK, amp=0.8)
lx_end = bx0 + 2 * (bw + 26) + bw
f.hand_bracket(bx0, lx_end, base + 56, RUST)
f.text((bx0 + lx_end) / 2, base + 82, "199 trades lose — 60.1%", 16, RUST, anchor="middle", style="italic")
wx0 = bx0 + 3 * (bw + 26)
f.hand_bracket(wx0, bx1 - 26 + bw + 6, base + 56, GREEN)
f.text((wx0 + bx1) / 2, base + 82, "132 win — 39.9%", 16, GREEN, anchor="middle", style="italic")

px = 1130
f.text(px, CH_TOP + 30, "average loss", 17, GREY)
f.hatch_rect(px, CH_TOP + 44, 3378 / 11490 * 330, 26, RUST, spacing=6, op=0.6)
f.text(px + 3378 / 11490 * 330 + 12, CH_TOP + 63, "$3,378", 18, INK)
f.text(px, CH_TOP + 118, "average win", 17, GREY)
f.hatch_rect(px, CH_TOP + 132, 330, 26, GREEN, spacing=6, op=0.6)
f.text(px + 330 + 12, CH_TOP + 151, "$11,490", 18, INK)
f.text(px, CH_TOP + 272, "3.40×", 64, INK)
f.pencil_ring(px + 92, CH_TOP + 250, 120, 44)
f.text(px, CH_TOP + 310, "one average win pays for", 17, GREY, style="italic")
f.text(px, CH_TOP + 334, "3.4 average losses", 17, GREY, style="italic")
f.save("fig_02_distribution_crafty.svg")

# ============================================================ fig 03 crafty
ranked = sorted(D["trades"], key=lambda z: -z["pnl"])
top31 = sum(t["pnl"] for t in ranked[:31])
rest = sum(t["pnl"] for t in ranked[31:])
f = Fig(3, 4, "CONCENTRATION · ALL 331 TRADES, RANKED BY P&amp;L",
        "31 trades carried the whole year",
        f"The top 31 made ${top31/1000:,.0f}k. The other 300 add up to {'-' if rest<0 else ''}${abs(rest)/1000:.0f}k — roughly zero.")

cols, cell = 30, 30
gx0, gy0 = ML + 10, CH_TOP + 26
f.text(gx0, gy0 - 20, "each dot is one trade · gold = the 31 · ranked left-to-right, top-to-bottom", 15.5, GREY, style="italic")
for i, t in enumerate(ranked):
    r_, c_ = divmod(i, cols)
    x, y = gx0 + c_ * cell, gy0 + r_ * cell * 1.32
    if t["gold"]:
        f.hand_circle(x, y, 8.4, GOLD, fill=True, sw=1.6)
    elif t["pnl"] > 0:
        f.hand_circle(x, y, 6.2, GREEN, op=0.65, sw=1.3)
    else:
        f.hand_circle(x, y, 6.2, RUST if t["r"] <= -1 else GREY, op=0.5, sw=1.2)

px, pw = 1120, 330
f.text(px, CH_TOP + 40, "the 31 (9% of trades)", 17, GREY)
f.hatch_rect(px, CH_TOP + 54, pw, 30, GOLD, spacing=6.5, op=0.62)
f.text(px + pw + 12, CH_TOP + 75, f"+${top31/1e3:,.0f}k", 18, INK)
f.text(px, CH_TOP + 128, "the other 300 (91%)", 17, GREY)
rw = max(abs(rest) / top31 * pw, 4)
f.hatch_rect(px, CH_TOP + 142, rw, 30, RUST, spacing=5, op=0.6)
f.text(px + rw + 12, CH_TOP + 163, f"{'-' if rest<0 else ''}${abs(rest)/1e3:,.0f}k", 18, INK)
f.text(px, CH_TOP + 266, "100%", 64, INK)
f.pencil_ring(px + 88, CH_TOP + 244, 118, 44)
f.text(px, CH_TOP + 304, "of net P&amp;L came from trades", 17, GREY, style="italic")
f.text(px, CH_TOP + 328, "you could count on your hands", 17, GREY, style="italic")
f.save("fig_03_concentration_crafty.svg")

# ============================================================ fig 04 crafty
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
    f.vline(x, CH_TOP + 10, CH_BOT - 10, 0.7, 0.09)
    f.text(x, CH_BOT + 22, ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL"][m - 1], 14.5, GREY, anchor="middle")

yBE, yBB = CH_TOP + 105, CH_TOP + 330
f.text(ML + 10, yBE - 62, "BE — 16 attempts", 22, INK)
f.text(ML + 10, yBE - 36, "eight stops before it paid", 16, GREY, style="italic")
f.hand_line(ML + 150, yBE, W - MR - 60, yBE, 1.2, 0.35, INK, amp=1.0)
for t in be:
    x = xt(t["exit"])
    r_ = max(5.5, min(5 + abs(t["pnl"]) / 74052 * 17, 22))
    if t["pnl"] > 60000:
        f.hand_circle(x, yBE, r_, GOLD, fill=True, sw=2)
        f.leader(x, yBE - r_ - 4, x - 6, yBE - 52, GOLD)
        f.text(x, yBE - 88, "#9 · Apr 28", 18, INK, anchor="middle")
        f.text(x, yBE - 66, "+$74,052 · +7.3R", 17, GOLD, anchor="middle")
        f.pencil_ring(x, yBE, r_ + 12, r_ + 10)
    elif t["pnl"] > 0:
        f.hand_circle(x, yBE, r_, GREEN, sw=1.6)
    else:
        f.hand_circle(x, yBE, r_, RUST, sw=1.6)
x8a, x8b = xt(be[0]["exit"]) - 10, xt(be[7]["exit"]) + 10
f.hand_bracket(x8a, x8b, yBE + 40, RUST)
f.text((x8a + x8b) / 2, yBE + 66, "eight stops · −$19,300 total", 16, RUST, anchor="middle", style="italic")

f.text(ML + 10, yBB - 62, "BABA — 5 attempts", 22, INK)
f.text(ML + 10, yBB - 36, "the thesis died; the holding didn't", 16, GREY, style="italic")
f.hand_line(ML + 150, yBB, W - MR - 60, yBB, 1.2, 0.35, INK, amp=1.0)
for t in baba:
    xin, xout = xt(t["entry"]), xt(t["exit"])
    if t["hold"] > 30:
        f.hand_line(xin, yBB, xout, yBB, 5, 0.28, RUST, amp=1.2)
        f.hand_circle(xin, yBB, 4.5, RUST, sw=1.3)
    f.hand_circle(xout, yBB, max(5.5, min(5 + abs(t["pnl"]) / 74052 * 17, 22)), RUST, sw=1.8)
xcut = xt(dt.date(2026, 4, 23))
f.hand_line(xcut, yBB - 30, xcut, yBB + 30, 1.4, 0.7, RUST, amp=0.7)
f.text(xcut + 14, yBB - 44, "Apr 23 — all three cut the same day", 17, INK)
f.text(xcut + 14, yBB - 20, "held 102 / 99 / 93 days · five tries, −$54,418", 16, RUST)
f.text(ML + 150, CH_BOT - 6,
       "Five days apart: the surrender (Apr 23) and the harvest (Apr 28) settled in the same week.",
       17, GREY, style="italic")
f.save("fig_04_gesture_crafty.svg")
