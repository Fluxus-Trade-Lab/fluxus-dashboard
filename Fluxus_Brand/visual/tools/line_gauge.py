#!/usr/bin/env python3
"""line_gauge — the Pantone card for the constitution's thick black line.
Five weights x three roughness levels, plus solid-black-mass ratio demos.
Each cell shows: straight rule / a real drop curve / a filled blob."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from dropmark import drop, path_d, PAPER, INK, ORANGE, GREY, DATES

W, H = 2200, 2350
s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">',
     '<defs>']
for i, (freq, scale) in enumerate([(0.0, 0), (0.012, 4), (0.02, 9)]):
    if scale:
        s.append(f'<filter id="rough{i}" x="-10%" y="-10%" width="120%" height="120%">'
                 f'<feTurbulence type="fractalNoise" baseFrequency="{freq}" numOctaves="3" seed="7" result="n"/>'
                 f'<feDisplacementMap in="SourceGraphic" in2="n" scale="{scale}"/></filter>')
s.append('</defs>')
s.append(f'<rect width="{W}" height="{H}" fill="{PAPER}"/>')
s.append(f'<text x="40" y="64" font-family="Courier New" font-size="30" letter-spacing="3" fill="{INK}">LINE GAUGE CARD &#183; PICK ONE WEIGHT + ONE ROUGHNESS</text>')

pts, L, d0, d1 = drop(DATES[-1], 21)
k = 0.32
small = [(x*k, y*k) for x, y in pts]

weights = [4, 7, 11, 16, 24]
rough = [("R0  clean", None), ("R1  hand", "rough1"), ("R2  zine", "rough2")]
CELLW, CELLH = 660, 400
for ri, (rlab, rid) in enumerate(rough):
    x0 = 60 + ri*(CELLW+50)
    s.append(f'<text x="{x0}" y="130" font-family="Courier New" font-size="24" letter-spacing="3" fill="{INK}">{rlab}</text>')
    for wi, w in enumerate(weights):
        y0 = 170 + wi*CELLH
        g = f'filter="url(#{rid})"' if rid else ''
        s.append(f'<g {g}>')
        s.append(f'<line x1="{x0}" y1="{y0+60}" x2="{x0+CELLW-120}" y2="{y0+60}" stroke="{INK}" stroke-width="{w}" stroke-linecap="round"/>')
        s.append(f'<path d="{path_d(small, x0+CELLW/2-60, y0+185)}" fill="none" stroke="{INK}" stroke-width="{w}" stroke-linecap="round"/>')
        s.append(f'<rect x="{x0+CELLW-100}" y="{y0+30}" width="72" height="60" fill="{INK}"/>')
        s.append('</g>')
        s.append(f'<text x="{x0}" y="{y0+320}" font-family="Courier New" font-size="19" letter-spacing="2" fill="{GREY}">L{wi+1} &#183; {w}px @2200w</text>')

s.append(f'<text x="60" y="{H-60}" font-family="Courier New" font-size="20" letter-spacing="2" fill="{GREY}">constitution: heavy blunt blacks &#183; scene03 used ~L3/R1 &#183; TE homepage sits ~L4/R1</text>')
s.append('</svg>')
out = sys.argv[1] if len(sys.argv)>1 else "."
open(f"{out}/line_gauge_card.svg","w").write("\n".join(s))
print("line gauge written")
