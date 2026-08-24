"""Four takes on ONE thing: the Percent-Volatility lesson card in Journal -> Sizing.

The live card (v0) states Tharp's principle, then hands the reader a number that
does not test it -- "ATR 8-21%" plus a counterfactual ("would have equalized").
Nothing on the card says the volatility dial actually predicts anything forward.

As of 2026-08-25 it does, measured on our own archive out of sample:
data/research/amplitude_2026-08/results.md. So the question this preview asks is
narrow: what is the smallest change that puts the evidence on the card?

frontend/ is not touched. These are static files.
Build: python3 build.py
"""
import pathlib

HEAD = """<!doctype html><meta charset=utf-8><title>{t}</title>
<link rel=stylesheet href=_shared.css>
<div class=pagewrap><p class=plabel>{label}</p>
"""
TAIL = "</div>\n"

TITLE = "The Percent-Volatility Model"
SUB = "Size by ATR so every position breathes the same"
PRINCIPLE = (
    "Instead of stop distance, divide the risk budget by the ATR: "
    "shares = (equity &times; vol%) &divide; ATR. Every position then contributes equal "
    "daily volatility to the book. Useful when stops vary in quality or when names "
    "differ wildly in volatility &mdash; a 2% ATR mega-cap and a 15% ATR small-cap stop "
    "being sized the same notional is a hidden bet on the wilder one."
)

# holdout arm, data/research/amplitude_2026-08/results.md
QUINTILES = [
    ("Q1  quietest", 3.44, 3.60, -1.34),
    ("Q2",           6.77, 3.90, +0.65),
    ("Q3",          10.21, 4.83, -0.17),
    ("Q4",          14.59, 6.23, +0.98),
    ("Q5  wildest", 17.50, 8.47, -2.51),
]


def card(body, src):
    return (f'<div class=lesson><h3>{TITLE}</h3><p class=sub>{SUB}</p>'
            f'<p class=principle>{PRINCIPLE}</p>{body}'
            f'<p class=src>{src}</p></div>')


def v0():
    body = ('<div class=ournum><div class=stat>This book’s pick profile</div>'
            '<div class=val>ATR 8&ndash;21%</div>'
            '<p class=read>ALAB, DOCN and peers ran 8&ndash;21% ATR at entry &mdash; '
            'high-volatility names. Percent-volatility sizing would have equalized what '
            'each position could do to the equity curve in a day.</p></div>')
    return card(body, 'Tharp, DGPS · percent-volatility model')


def v1():
    """Smallest possible edit: same slot, a measured number instead of a counterfactual."""
    body = ('<div class=ournum><div class=stat>Measured on our own archive</div>'
            '<div class=val>2.4&times;</div>'
            '<p class=read>Across 10,913 breakout events, the wildest fifth of names moved '
            '2.4&times; as far in the next five sessions as the quietest fifth '
            '(8.5% vs 3.6% median absolute move vs SPY). Same dollars in a Q5 name is '
            '2.4&times; the risk &mdash; a size you did not choose.</p></div>')
    return card(body, 'Tharp, DGPS · measured: amplitude_2026-08 (holdout)')


def v2():
    """The contrast IS the finding: it predicts size, not direction."""
    body = ('<div class=cols>'
            '<div><div class=stat>Predicts the size of the move</div>'
            '<div class="val on">ρ = +0.30</div>'
            '<p>Prior volatility ranks the next five sessions’ move size, out of sample. '
            'Right-tail odds run 3.4% in the quietest fifth to 17.5% in the wildest.</p></div>'
            '<div><div class=stat>Predicts the direction</div>'
            '<div class="val off">ρ = −0.03</div>'
            '<p>Nothing (p = 0.15). The same variable that ranks magnitude cleanly says '
            'nothing about which way. That is why it sets share count, not whether to buy.</p>'
            '</div></div>')
    return card(body, 'Tharp, DGPS · measured: amplitude_2026-08 (holdout, n=3,149)')


def v3():
    """The whole ladder. Most information; the test is whether it is still calm."""
    w = 92.0
    rows = []
    for name, tail, absmove, med in QUINTILES:
        bar = f'<span class=bar style="width:{tail / 17.5 * w:.0f}px"></span>'
        flat = f'<span class="bar flat" style="width:{abs(med) / 2.51 * 34:.0f}px"></span>'
        rows.append(
            f'<tr><td>{name}</td><td style="text-align:right">{tail:.1f}%&nbsp;{bar}</td>'
            f'<td style="text-align:right">{absmove:.1f}%</td>'
            f'<td style="text-align:right">{med:+.2f}%&nbsp;{flat}</td></tr>')
    body = ('<div class=ournum><div class=stat>Next 5 sessions, by prior-volatility fifth'
            '</div><table class=q><tr><th>&nbsp;</th><th>odds of +10%</th>'
            '<th>typical move</th><th>direction</th></tr>' + "".join(rows) + '</table>'
            '<p class=read style="margin-top:11px">The first two columns climb together and '
            'the third does not move &mdash; volatility ranks how far, never which way. '
            'Read it as a divisor on share count, not as a reason to take the trade.</p></div>')
    return card(body, 'Tharp, DGPS · measured: amplitude_2026-08 (holdout, n=3,149)')


LABELS = {
    "v0": "v0 · 现状（对照组）",
    "v1": "v1 · 同一个槽位，换成量过的数字",
    "v2": "v2 · 把对比本身当成内容（管幅度 / 不管方向）",
    "v3": "v3 · 整道梯子",
}
for k, fn in (("v0", v0), ("v1", v1), ("v2", v2), ("v3", v3)):
    p = pathlib.Path(f"sizing_volatility_{k}.html")
    p.write_text(HEAD.format(t=f"Percent-Volatility {k}", label=LABELS[k]) + fn() + TAIL)
    print("wrote", p)
