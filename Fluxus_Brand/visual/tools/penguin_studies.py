#!/usr/bin/env python3
"""penguin_studies — First Penguin geometry studies, constitution-compliant:
big black masses, paper negative space, no orange (reserved), deadpan."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dropmark import PAPER, INK, GREY, ORANGE

W, H = 2200, 1350
s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">',
     f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
     f'<text x="40" y="64" font-family="Courier New" font-size="30" letter-spacing="3" fill="{INK}">FIRST PENGUIN &#183; GEOMETRY STUDIES P1&#8211;P4 &#183; (final art: image model; these fix proportion &amp; attitude)</text>']

def penguin_front(cx, cy, sc=1.0):
    g = [f'<g transform="translate({cx},{cy}) scale({sc})">']
    g.append(f'<ellipse cx="0" cy="40" rx="95" ry="135" fill="{INK}"/>')          # body
    g.append(f'<circle cx="0" cy="-115" r="62" fill="{INK}"/>')                    # head
    g.append(f'<ellipse cx="0" cy="52" rx="60" ry="100" fill="{PAPER}"/>')         # belly
    g.append(f'<circle cx="-22" cy="-122" r="9" fill="{PAPER}"/>')                 # eyes
    g.append(f'<circle cx="22" cy="-122" r="9" fill="{PAPER}"/>')
    g.append(f'<path d="M -12,-98 L 12,-98 L 0,-78 Z" fill="{ORANGE}"/>')          # beak: allowed? NO — keep ink
    g[-1] = f'<path d="M -12,-98 L 12,-98 L 0,-78 Z" fill="{INK}" stroke="{PAPER}" stroke-width="4"/>'
    g.append(f'<ellipse cx="-98" cy="20" rx="22" ry="88" fill="{INK}" transform="rotate(14 -98 20)"/>')  # flippers
    g.append(f'<ellipse cx="98" cy="20" rx="22" ry="88" fill="{INK}" transform="rotate(-14 98 20)"/>')
    g.append(f'<path d="M -52,172 L -12,172 L -32,190 Z" fill="{INK}"/>')          # feet
    g.append(f'<path d="M 12,172 L 52,172 L 32,190 Z" fill="{INK}"/>')
    g.append('</g>')
    return g

def penguin_profile(cx, cy, sc=1.0):
    g = [f'<g transform="translate({cx},{cy}) scale({sc})">']
    g.append(f'<path d="M -20,-180 C 60,-175 85,-95 78,10 C 72,95 55,150 20,172 L -70,172 C -108,120 -118,20 -100,-70 C -88,-135 -60,-178 -20,-180 Z" fill="{INK}"/>')
    g.append(f'<path d="M -35,-40 C 5,-45 30,0 28,60 C 26,110 12,150 -12,164 L -58,164 C -80,120 -84,40 -70,-10 C -62,-32 -50,-38 -35,-40 Z" fill="{PAPER}"/>')
    g.append(f'<circle cx="-8" cy="-128" r="10" fill="{PAPER}"/>')
    g.append(f'<path d="M -95,-118 L -150,-104 L -95,-92 Z" fill="{INK}"/>')       # beak wedge left
    g.append(f'<ellipse cx="46" cy="30" rx="20" ry="85" fill="{INK}" transform="rotate(-8 46 30)"/>')  # near flipper over belly
    g.append(f'<path d="M -60,172 L -16,172 L -38,192 Z" fill="{INK}"/>')
    g.append('</g>')
    return g

def penguin_dive(cx, cy, sc=1.0):
    # streamlined head-first dive, 45 degrees down-right; drawn axis-aligned then rotated
    g = [f'<g transform="translate({cx},{cy}) scale({sc}) rotate(135)">']
    # torpedo body, nose at top (-y), tail at bottom
    g.append(f'<path d="M 0,-190 C 55,-180 78,-90 70,20 C 64,110 40,168 0,180 C -40,168 -64,110 -70,20 C -78,-90 -55,-180 0,-190 Z" fill="{INK}"/>')
    # belly stripe (paper), on the leading side
    g.append(f'<path d="M 8,-150 C 45,-135 58,-60 52,30 C 47,100 30,150 4,162 C -8,150 -14,100 -12,20 C -10,-70 -4,-135 8,-150 Z" fill="{PAPER}"/>')
    # eye + beak at the nose
    g.append(f'<circle cx="-18" cy="-142" r="9" fill="{PAPER}"/>')
    g.append(f'<path d="M -14,-186 L 14,-186 L 0,-226 Z" fill="{INK}"/>')
    # flippers swept back along body
    g.append(f'<ellipse cx="-62" cy="30" rx="16" ry="78" fill="{INK}" transform="rotate(16 -62 30)"/>')
    g.append(f'<ellipse cx="62" cy="30" rx="16" ry="78" fill="{INK}" transform="rotate(-16 62 30)"/>')
    g.append('</g>')
    return g

def penguin_tvbuddha(cx, cy, sc=1.0):
    g = [f'<g transform="translate({cx},{cy}) scale({sc})">']
    # penguin from behind (solid back) on a low plinth, facing a CRT
    g.append(f'<rect x="-260" y="150" width="220" height="26" fill="{INK}"/>')     # penguin plinth
    g.append(f'<ellipse cx="-150" cy="30" rx="88" ry="122" fill="{INK}"/>')        # back
    g.append(f'<circle cx="-150" cy="-110" r="56" fill="{INK}"/>')
    g.append(f'<ellipse cx="-238" cy="20" rx="18" ry="76" fill="{INK}" transform="rotate(12 -238 20)"/>')
    # CRT on plinth
    g.append(f'<rect x="60" y="-60" width="240" height="200" rx="18" fill="{INK}"/>')
    g.append(f'<rect x="82" y="-38" width="172" height="132" rx="10" fill="{PAPER}"/>')
    g.append(f'<circle cx="272" cy="120" r="7" fill="{PAPER}"/>')
    # on screen: the penguin itself, tiny
    g.append(f'<ellipse cx="168" cy="40" rx="26" ry="36" fill="{INK}"/>')
    g.append(f'<circle cx="168" cy="-2" r="16" fill="{INK}"/>')
    g.append(f'<ellipse cx="168" cy="44" rx="15" ry="25" fill="{PAPER}"/>')
    g.append(f'<rect x="40" y="150" width="290" height="26" fill="{INK}"/>')       # tv plinth
    g.append('</g>')
    return g

cells = [(560, 420, "P1  FRONT &#183; deadpan, flippers down", penguin_front),
         (1650, 420, "P2  PROFILE &#183; the measurer's stance", penguin_profile),
         (560, 1060, "P3  THE DIVE &#183; head-first, no hesitation", penguin_dive),
         (1650, 1060, "P4  TV BUDDHA &#183; the review seat (Paik)", penguin_tvbuddha)]
for cx, cy, lab, fn in cells:
    s += fn(cx, cy, 0.85 if fn is not penguin_tvbuddha else 0.9)
    s.append(f'<text x="{cx-330}" y="{cy+270}" font-family="Courier New" font-size="20" letter-spacing="2" fill="{GREY}">{lab}</text>')
s.append('</svg>')
out = sys.argv[1] if len(sys.argv)>1 else "."
open(f"{out}/penguin_studies.svg","w").write("\n".join(s))
print("penguin studies written")
