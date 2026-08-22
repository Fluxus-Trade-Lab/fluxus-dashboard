#!/usr/bin/env python3
"""poster_comp — the manifesto poster, composition blockout.
A huge orange drop (a real one: COVID, Feb-Mar 2020) crosses the sheet.
A tiny man on a stepladder holds a ruler to it. He measures; chance shapes."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from dropmark import drop, chaikin, raw_points, window, arclen, path_d, PAPER, INK, ORANGE, GREY

W, H = 1600, 2400
s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">',
     f'<rect width="{W}" height="{H}" fill="{PAPER}"/>']

# the great drop: COVID month, scaled big, rotated slightly so it falls across the sheet
pts, L, d0, d1 = drop("2020-03-20", 21)
th = math.radians(-28)
rot = [(x*math.cos(th)-y*math.sin(th), x*math.sin(th)+y*math.cos(th)) for x, y in pts]
big = [(x*1.85, y*1.85) for x, y in rot]
xs=[q[0] for q in big]; ys=[q[1] for q in big]
cx, cy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
big = [(x-cx+W*0.50, y-cy+H*0.40) for x, y in big]
s.append(f'<path d="{path_d(big,0,0)}" fill="none" stroke="{ORANGE}" stroke-width="26" stroke-linecap="round" stroke-linejoin="round"/>')

# the tiny man on a stepladder, lower right, ruler up against the line's tail
end = big[-1]
gx, gy = end[0]-212, end[1]+26   # so the ruler tip meets the thread's tail
gx = max(120, min(gx, W-360)); gy = max(300, min(gy, H-720))
s.append(f'<g transform="translate({gx},{gy})">')
# stepladder (A-frame)
s.append(f'<path d="M 0,300 L 60,60 L 120,300" fill="none" stroke="{INK}" stroke-width="10" stroke-linecap="round"/>')
for i in range(1,5):
    t=i/5; xA=60*t; xB=120-60*t
    s.append(f'<line x1="{60-60*(1-t):.0f}" y1="{60+240*t:.0f}" x2="{60+60*(1-t):.0f}" y2="{60+240*t:.0f}" stroke="{INK}" stroke-width="8"/>')
# the man, tiny: hat, head, body, on top step
s.append(f'<ellipse cx="60" cy="16" rx="30" ry="7" fill="{INK}"/>')
s.append(f'<path d="M 38,14 Q 39,-12 60,-14 Q 81,-12 82,14 Z" fill="{INK}"/>')
s.append(f'<circle cx="60" cy="26" r="16" fill="{PAPER}" stroke="{INK}" stroke-width="5"/>')
s.append(f'<path d="M 34,88 Q 60,72 86,88 L 92,150 L 28,150 Z" fill="{PAPER}" stroke="{INK}" stroke-width="6"/>')
s.append(f'<line x1="40" y1="150" x2="40" y2="176" stroke="{INK}" stroke-width="7"/>')
s.append(f'<line x1="80" y1="150" x2="80" y2="176" stroke="{INK}" stroke-width="7"/>')
# the raised arm + ruler reaching toward the orange line
s.append(f'<line x1="84" y1="96" x2="118" y2="52" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>')
s.append(f'<g transform="rotate(-38 118 52)"><rect x="118" y="44" width="120" height="16" fill="{PAPER}" stroke="{INK}" stroke-width="5"/>')
for i in range(1,8): s.append(f'<line x1="{118+i*15}" y1="44" x2="{118+i*15}" y2="{50 if i%2 else 54}" stroke="{INK}" stroke-width="3"/>')
s.append('</g></g>')

# hand caption + registry
s.append(f'<text x="90" y="{H-330}" font-family="Bradley Hand, Chalkboard SE" font-size="76" fill="{INK}">I don&#8217;t have opinions.</text>')
s.append(f'<text x="90" y="{H-230}" font-family="Bradley Hand, Chalkboard SE" font-size="76" fill="{INK}">I have measurements.</text>')
s.append(f'<text x="92" y="{H-150}" font-family="Courier New" font-size="26" letter-spacing="5" fill="{GREY}">SAME LENGTH, DIFFERENT SHAPES.</text>')
s.append(f'<text x="92" y="{H-84}" font-family="Courier New" font-size="22" letter-spacing="2" fill="{GREY}">1m &#183; drop #C19 &#183; {d0} &#8594; {d1} &#183; SPX &#183; &#8747;={L/1000.0:.3f}m</text>')
s.append(f'<text x="{W-90}" y="{H-84}" text-anchor="end" font-family="DIN Condensed" font-weight="bold" font-size="64" letter-spacing="3" fill="{INK}">FLUXUS</text>')
s.append('</svg>')
out = sys.argv[1] if len(sys.argv)>1 else "."
open(f"{out}/poster_manifesto_comp.svg","w").write("\n".join(s))
print("poster comp written")
