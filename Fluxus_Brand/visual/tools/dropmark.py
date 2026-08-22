#!/usr/bin/env python3
"""dropmark — the daily drop mark generator.

Duchamp, made computable: a thread of CONSTANT ARC LENGTH (the "1 metre"),
its shape given by a real stretch of SPX closes. Calm tape stretches the
thread almost straight; wild tape crumples it. Same length, different shapes.

Usage: python3 dropmark.py  (writes SVG boards next to itself unless --out)
"""
import csv, math, os, sys, datetime as dt

DATA = "/Users/taolezhu/Documents/AI-Trading-System/SqueezeMetrics/DIX.csv"
PAPER, INK, ORANGE, GREY = "#F4F3F0", "#1F1D1B", "#D1600F", "#8F8B84"
K = 100.0          # vertical px per 100% log-return (1% move == 1 x-step)
TARGET_LEN = 1000.0  # the "metre"

def load():
    rows = list(csv.DictReader(open(DATA)))
    return [(r["date"], float(r["price"])) for r in rows]

SERIES = load()
DATES = [d for d, _ in SERIES]

def window(end_date, n):
    i = max(j for j, d in enumerate(DATES) if d <= end_date)
    seg = SERIES[i - n + 1 : i + 1]
    return seg

def raw_points(seg):
    p0 = seg[0][1]
    return [(float(i), -math.log(p[1] / p0) * K) for i, p in enumerate(seg)]

def chaikin(pts, iters=3):
    for _ in range(iters):
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            out.append((a[0]*0.75+b[0]*0.25, a[1]*0.75+b[1]*0.25))
            out.append((a[0]*0.25+b[0]*0.75, a[1]*0.25+b[1]*0.75))
        out.append(pts[-1])
        pts = out
    return pts

def arclen(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))

def normalise(pts, target=TARGET_LEN):
    L = arclen(pts)
    s = target / L
    pts = [(x*s, y*s) for x, y in pts]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    cx, cy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
    return [(x-cx, y-cy) for x, y in pts], arclen([( (x-cx), (y-cy)) for x, y in pts])

def drop(end_date, n=21):
    seg = window(end_date, n)
    pts, L = normalise(chaikin(raw_points(seg)))
    return pts, L, seg[0][0], seg[-1][0]

def path_d(pts, ox, oy):
    d = f"M {pts[0][0]+ox:.2f},{pts[0][1]+oy:.2f} "
    d += " ".join(f"L {x+ox:.2f},{y+oy:.2f}" for x, y in pts[1:])
    return d

def ribbon(pts, ox, oy, wmax):
    # tapered ink stroke: width swells mid-line, dies at the tips
    n = len(pts); left = []; right = []
    for i, (x, y) in enumerate(pts):
        if i == 0: dx, dy = pts[1][0]-x, pts[1][1]-y
        elif i == n-1: dx, dy = x-pts[-2][0], y-pts[-2][1]
        else: dx, dy = pts[i+1][0]-pts[i-1][0], pts[i+1][1]-pts[i-1][1]
        m = math.hypot(dx, dy) or 1
        nx, ny = -dy/m, dx/m
        t = i/(n-1)
        w = wmax * (0.18 + 0.82 * math.sin(math.pi * t) ** 0.7) / 2
        left.append((x+nx*w+ox, y+ny*w+oy)); right.append((x-nx*w+ox, y-ny*w+oy))
    poly = left + right[::-1]
    return "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in poly) + " Z"

def svg_open(w, h):
    return [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">',
            f'<rect width="{w}" height="{h}" fill="{PAPER}"/>']

def caption(x, y, num, d0, d1, L, extra="SPX", size=15):
    t = f'1m &#183; drop #{num:03d} &#183; {d0} &#8594; {d1} &#183; {extra} &#183; &#8747;={L/TARGET_LEN:.3f}m'
    return (f'<text x="{x}" y="{y}" font-family="Courier New, monospace" '
            f'font-size="{size}" letter-spacing="1" fill="{GREY}">{t}</text>')

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(__file__)
    os.makedirs(out, exist_ok=True)

    # ---- Board 1: twelve months, one drop each (grid 3 x 4), uniform black
    CW, CH = 1240, 420
    cols, rows_n = 3, 4
    W, H = CW*cols, CH*rows_n + 120
    s = svg_open(W, H)
    s.append(f'<text x="40" y="64" font-family="Courier New, monospace" font-size="30" letter-spacing="3" fill="{INK}">TWELVE DROPS &#183; 21 SESSIONS EACH &#183; SAME LENGTH, DIFFERENT SHAPES</text>')
    month_ends = []
    seen = set()
    for d, _ in reversed(SERIES):
        ym = d[:7]
        if ym not in seen:
            seen.add(ym); month_ends.append(d)
        if len(month_ends) == 12: break
    month_ends.reverse()
    for i, ed in enumerate(month_ends):
        pts, L, d0, d1 = drop(ed, 21)
        cx = (i % cols)*CW + CW/2
        cy = 110 + (i // cols)*CH + CH/2 - 30
        s.append(f'<path d="{path_d(pts, cx, cy)}" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>')
        s.append(caption(cx-520, 110+(i//cols)*CH+CH-46, i+1, d0, d1, L))
    s.append('</svg>')
    open(f"{out}/drops_board1_twelve_months.svg", "w").write("\n".join(s))

    # ---- Board 2: one drop, six treatments
    ed = DATES[-1]
    pts, L, d0, d1 = drop(ed, 21)
    CW2, CH2 = 1860, 400
    treatments = [
        ("T1  uniform ink 7px", lambda ox, oy: f'<path d="{path_d(pts,ox,oy)}" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>'),
        ("T2  uniform orange 7px", lambda ox, oy: f'<path d="{path_d(pts,ox,oy)}" fill="none" stroke="{ORANGE}" stroke-width="7" stroke-linecap="round"/>'),
        ("T3  taper ink 16px", lambda ox, oy: f'<path d="{ribbon(pts,ox,oy,16)}" fill="{INK}"/>'),
        ("T4  taper orange 16px", lambda ox, oy: f'<path d="{ribbon(pts,ox,oy,16)}" fill="{ORANGE}"/>'),
        ("T5  hairline ink 2.5px", lambda ox, oy: f'<path d="{path_d(pts,ox,oy)}" fill="none" stroke="{INK}" stroke-width="2.5"/>'),
        ("T6  marker ink 13px", lambda ox, oy: f'<path d="{path_d(pts,ox,oy)}" fill="none" stroke="{INK}" stroke-width="13" stroke-linecap="round"/>'),
    ]
    W2, H2 = CW2, CH2*len(treatments)//1 + 140
    s = svg_open(W2, H2)
    s.append(f'<text x="40" y="64" font-family="Courier New, monospace" font-size="30" letter-spacing="3" fill="{INK}">ONE DROP &#183; SIX TREATMENTS &#183; {d0} &#8594; {d1}</text>')
    for i, (label, fn) in enumerate(treatments):
        oy = 120 + i*CH2 + CH2/2 - 40
        s.append(fn(CW2/2, oy))
        s.append(f'<text x="60" y="{120+i*CH2+CH2-58}" font-family="Courier New, monospace" font-size="20" letter-spacing="2" fill="{GREY}">{label}</text>')
    s.append('</svg>')
    open(f"{out}/drops_board2_treatments.svg", "w").write("\n".join(s))

    # ---- Board 3: window variants (the metre absorbs a week / month / quarter / year)
    CW3, CH3 = 1860, 430
    wins = [(5, "ONE WEEK"), (21, "ONE MONTH"), (63, "ONE QUARTER"), (252, "ONE YEAR")]
    W3, H3 = CW3, CH3*len(wins) + 140
    s = svg_open(W3, H3)
    s.append(f'<text x="40" y="64" font-family="Courier New, monospace" font-size="30" letter-spacing="3" fill="{INK}">THE SAME METRE SWALLOWS A WEEK, A MONTH, A QUARTER, A YEAR</text>')
    for i, (n, lab) in enumerate(wins):
        pts, L, d0, d1 = drop(ed, n)
        oy = 120 + i*CH3 + CH3/2 - 40
        s.append(f'<path d="{path_d(pts, CW3/2, oy)}" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>')
        s.append(f'<text x="60" y="{120+i*CH3+CH3-58}" font-family="Courier New, monospace" font-size="20" letter-spacing="2" fill="{GREY}">{lab} &#183; {d0} &#8594; {d1} &#183; &#8747;={L/TARGET_LEN:.3f}m</text>')
    s.append('</svg>')
    open(f"{out}/drops_board3_windows.svg", "w").write("\n".join(s))

    # ---- Board 4: famous falls (history bends the thread)
    famous = [("2017-10-31", "THE CALM  (Oct 2017, vol at record lows)"),
              ("2020-03-20", "COVID  (the fastest bear in history)"),
              ("2018-12-24", "POWELL AUTOPILOT  (Christmas Eve massacre)"),
              ("2022-06-17", "THE 2022 GRIND  (rate-hike bear)"),
              ("2024-08-05", "YEN CARRY UNWIND  (VIX 65 morning)")]
    CW4 = 1860
    drops4 = []
    for ed4, lab in famous:
        pts, L, d0, d1 = drop(ed4, 21)
        ys = [q[1] for q in pts]
        drops4.append((pts, L, d0, d1, lab, max(ys)-min(ys)))
    PADV = 130
    H4 = 140 + sum(int(h)+PADV for *_, h in drops4)
    s = svg_open(CW4, H4)
    s.append(f'<text x="40" y="64" font-family="Courier New, monospace" font-size="30" letter-spacing="3" fill="{INK}">FAMOUS DROPS &#183; HISTORY BENDS THE THREAD, NEVER SHORTENS IT</text>')
    y = 130
    for pts, L, d0, d1, lab, h in drops4:
        cy = y + h/2 + 20
        s.append(f'<path d="{path_d(pts, CW4/2, cy)}" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>')
        s.append(f'<text x="60" y="{y + h + 90}" font-family="Courier New, monospace" font-size="20" letter-spacing="2" fill="{GREY}">{lab} &#183; {d0} &#8594; {d1} &#183; &#8747;={L/TARGET_LEN:.3f}m</text>')
        y += int(h) + PADV
    s.append('</svg>')
    open(f"{out}/drops_board4_famous.svg", "w").write("\n".join(s))
    print("boards written to", out)
