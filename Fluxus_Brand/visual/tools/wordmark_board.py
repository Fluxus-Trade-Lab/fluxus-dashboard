#!/usr/bin/env python3
"""wordmark_board — FLUXUS wordmark candidates.
W1-W6 typographic directions (system fonts, rendered by WebKit via qlmanage).
W7-W9 the unique experiments: a real drop living inside/under the mark.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from dropmark import drop, path_d, PAPER, INK, ORANGE, GREY, DATES

W, ROWH = 2000, 340
FONTS = [
    ("W1  DIN CONDENSED BOLD (TE industrial)", "DIN Condensed", "bold", 200, 6),
    ("W2  DIN ALTERNATE BOLD (rounder industrial)", "DIN Alternate", "bold", 150, 4),
    ("W3  FUTURA BOLD (bauhaus geometry)", "Futura", "bold", 150, 10),
    ("W4  AMERICAN TYPEWRITER BOLD (the archive)", "American Typewriter", "bold", 140, 6),
    ("W5  COURIER BOLD (pure registry)", "Courier New", "bold", 150, 2),
    ("W6  HELVETICA NEUE BLACK (swiss punch)", "Helvetica Neue", "900", 150, 2),
]
SPECIAL_ROWS = 3
H = 120 + ROWH*len(FONTS) + 430*SPECIAL_ROWS + 80

s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">',
     f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
     f'<text x="40" y="64" font-family="Courier New" font-size="30" letter-spacing="3" fill="{INK}">FLUXUS WORDMARK &#183; NINE CANDIDATES</text>']

y = 120
for label, fam, weight, size, ls in FONTS:
    s.append(f'<text x="90" y="{y+size*0.9:.0f}" font-family="{fam}" font-weight="{weight}" font-size="{size}" letter-spacing="{ls}" fill="{INK}">FLUXUS</text>')
    s.append(f'<text x="94" y="{y+size*0.9+44:.0f}" font-family="Courier New" font-size="19" letter-spacing="6" fill="{GREY}">CAPITAL &#183; MEASUREMENTS SINCE 2019 &#183; TOKYO</text>')
    s.append(f'<text x="1420" y="{y+60}" font-family="Courier New" font-size="18" letter-spacing="1" fill="{GREY}">{label}</text>')
    y += ROWH

# --- helpers for specials -----------------------------------------------
def scaled_drop(end, n, target_w, max_h):
    pts, L, d0, d1 = drop(end, n)
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    w=max(xs)-min(xs); h=max(ys)-min(ys) or 1
    k=min(target_w/w, max_h/h)
    return [(p[0]*k, p[1]*k) for p in pts], d0, d1

ed = DATES[-1]

# W7: underline drop — mark stays typographic, the drop lives beneath, changes daily
s.append(f'<text x="90" y="{y+150}" font-family="DIN Condensed" font-weight="bold" font-size="200" letter-spacing="6" fill="{INK}">FLUXUS</text>')
pts, d0, d1 = scaled_drop(ed, 21, 470, 80)
s.append(f'<path d="{path_d(pts, 90+239, y+215)}" fill="none" stroke="{ORANGE}" stroke-width="7" stroke-linecap="round"/>')
s.append(f'<text x="94" y="{y+300}" font-family="Courier New" font-size="19" letter-spacing="4" fill="{GREY}">1m &#183; drop #012 &#183; {d0} &#8594; {d1}</text>')
s.append(f'<text x="1420" y="{y+60}" font-family="Courier New" font-size="18" fill="{GREY}">W7  UNDERLINE DROP (the mark signs itself daily)</text>')
y += 430

# W8: the U is a hanging thread (catenary pinned at the two stems' tops)
s.append(f'<text x="90" y="{y+150}" font-family="DIN Condensed" font-weight="bold" font-size="200" letter-spacing="6" fill="{INK}">FL</text>')
ux0, ux1 = 90+148+12, 90+148+12+85   # the U slot, measured
cat = []
a = 2.6
for i in range(41):
    t = i/40
    x = ux0 + (ux1-ux0)*t
    sag = (math.cosh(a/2) - math.cosh(a*(t-0.5))) / (math.cosh(a/2) - 1)
    cat.append((x, (y+12) + 132*sag))
s.append(f'<path d="{path_d(cat, 0, 0)}" fill="none" stroke="{ORANGE}" stroke-width="15" stroke-linecap="round"/>')
s.append(f'<circle cx="{ux0}" cy="{y+12}" r="9" fill="{INK}"/>')
s.append(f'<circle cx="{ux1}" cy="{y+12}" r="9" fill="{INK}"/>')
s.append(f'<text x="{ux1+12}" y="{y+150}" font-family="DIN Condensed" font-weight="bold" font-size="200" letter-spacing="6" fill="{INK}">XUS</text>')
s.append(f'<text x="1420" y="{y+60}" font-family="Courier New" font-size="18" fill="{GREY}">W8  THE U HANGS (a thread pinned at two nails)</text>')
y += 430

# W9: the X is two crossed threads (one ink, one orange), measured slot
s.append(f'<text x="90" y="{y+150}" font-family="DIN Condensed" font-weight="bold" font-size="200" letter-spacing="6" fill="{INK}">FLU</text>')
xa, xb = 90+233+14, 90+233+14+88
th1=[]; th2=[]
for i in range(41):
    t=i/40
    wob1 = math.sin(t*6.1)+0.6*math.sin(t*11+1.2)
    wob2 = math.sin(t*5.2+2.0)+0.55*math.sin(t*9.7)
    th1.append((xa+(xb-xa)*t + wob1*6, (y+8) + 142*t))
    th2.append((xb+(xa-xb)*t + wob2*6, (y+8) + 142*t))
s.append(f'<path d="{path_d(th1,0,0)}" fill="none" stroke="{INK}" stroke-width="15" stroke-linecap="round"/>')
s.append(f'<path d="{path_d(th2,0,0)}" fill="none" stroke="{ORANGE}" stroke-width="15" stroke-linecap="round"/>')
s.append(f'<text x="{xb+14}" y="{y+150}" font-family="DIN Condensed" font-weight="bold" font-size="200" letter-spacing="6" fill="{INK}">US</text>')
s.append(f'<text x="1420" y="{y+60}" font-family="Courier New" font-size="18" fill="{GREY}">W9  THE X IS TWO CROSSED THREADS (ink meets orange)</text>')

s.append('</svg>')
out = sys.argv[1] if len(sys.argv)>1 else "."
open(f"{out}/wordmark_board.svg","w").write("\n".join(s))
print("wordmark board written")
