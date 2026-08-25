"""WCAG contrast for every colour pair these four previews actually use.

No colour is invented in this round -- every hex below is copied out of
_shared.css, which was itself lifted verbatim from frontend/src/index.css.
So this is a check that the EXISTING palette carries the new sentence, not
a proposal for new ink.
"""
def lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def L(h):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return 0.2126*lin(r) + 0.7152*lin(g) + 0.0722*lin(b)

def ratio(a, b):
    la, lb = sorted((L(a), L(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

THEMES = {
    "light": dict(surface="#f2f0e9", muted="#655e55", secondary="#4b453e", bold="#292524", border="#dbd7cb"),
    "dark":  dict(surface="#1c1b19", muted="#979594", secondary="#c8c5c2", bold="#ffffff", border="#2a2827"),
}
# role -> which token that role uses in the four variants
USES = [("出处行本体 (.prov)",      "muted"),
        ("v1 的「落后 N 个交易日」 (.age)", "bold"),
        ("v2 第二行正文 (.second)", "muted"),
        ("v2 的两个日期 (<b>)",     "secondary"),
        ("v3 第二行斜体 (.second.it)", "muted")]

print(f"{'角色':<28}{'token':<11}{'light':>8}{'dark':>8}   AA(4.5) AA-large(3.0)")
for label, tok in USES:
    rl = ratio(THEMES['light'][tok], THEMES['light']['surface'])
    rd = ratio(THEMES['dark'][tok],  THEMES['dark']['surface'])
    aa  = "pass" if min(rl, rd) >= 4.5 else "FAIL"
    aal = "pass" if min(rl, rd) >= 3.0 else "FAIL"
    print(f"{label:<28}{tok:<11}{rl:>8.2f}{rd:>8.2f}   {aa:<8}{aal}")

print()
for th in THEMES:
    print(f"{th}: 卡片边框 border vs surface = {ratio(THEMES[th]['border'], THEMES[th]['surface']):.2f} "
          f"(非文字，1.5+ 即可辨)")
