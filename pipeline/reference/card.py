"""Render the daily brief to a single PNG card.

Why an image and not text: a Discord message is capped at 2000 characters and a
forwarded wall of text loses its structure on a phone. A card survives being
forwarded, reads at a glance, and carries its own provenance — the date, the
window it was pulled in, and the honest track record — so a screenshot two weeks
from now still says what it is.

The card is deliberately not the whole brief. It carries the day's ONE question,
the levels that two independent frameworks agree on, what disagrees, and how
often our published levels have actually held. Everything else stays in the HTML.

Matplotlib rather than a headless browser on purpose: this runs from launchd at
07:30 and 16:30 with no display, and a browser dependency is one more thing to
go stale at exactly the moment nobody is watching.
"""
from __future__ import annotations

from pathlib import Path

BG = "#0A0D13"
LINE = "#1E2633"
TXT = "#C7CDD8"
MUT = "#79828F"
DIM = "#525b69"
ACCENT = "#5AA9FF"
GOOD = "#42B96A"
BAD = "#EF5E6B"
WARN = "#D6A34C"

MONO = ["DejaVu Sans Mono", "Menlo", "monospace"]
SANS = ["DejaVu Sans", "Helvetica", "sans-serif"]

W = 1080                    # portrait: the shape a phone actually shows well
PAD = 56
DPI = 100
MAX_H = 2400                # scratch canvas for the measuring pass


def _fig(height: float):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(W / DPI, height / DPI), dpi=DPI, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, height)
    ax.axis("off")
    ax.set_facecolor(BG)
    return fig, ax


def _wrap_lines(ax, s: str, size: float, family, weight: str,
                width: float) -> list[str]:
    """Wrap by MEASURING the rendered text, not by guessing an em width.

    Two guesses at characters-per-line both overflowed the right margin —
    0.55 em and then 0.63 em — because the ratio depends on the glyphs actually
    in the string. Asking the renderer removes the guess entirely.
    """
    fig = ax.figure
    renderer = fig.canvas.get_renderer()

    def w(t):
        probe = ax.text(0, 0, t, fontsize=size, family=family, fontweight=weight)
        ext = probe.get_window_extent(renderer=renderer)
        probe.remove()
        return ext.width

    if w(s) <= width:
        return [s]
    lines, cur = [], ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        if cur and w(trial) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


class _Cursor:
    """Top-down text placement.

    Every draw advances y, so a section that grows pushes what follows instead of
    overlapping it. `at()` places something on the CURRENT line without advancing
    — the first version reused `self.y` after it had already moved, which is what
    collided the header, the spot and the regime into one another.
    """

    def __init__(self, ax, y: float, x: float = PAD):
        self.ax, self.y, self.x = ax, y, x

    def at(self, s, size, color=TXT, family=SANS, weight="normal",
           dx=0.0, dy=0.0, ha="left"):
        """Draw relative to the current line WITHOUT advancing the cursor.

        `dy` is DOWNWARD, matching every other offset in this class. In
        matplotlib's data coordinates larger y is higher, so the first version's
        `self.y + dy` pushed the sub-labels UP into the line above — which is how
        "net +10.93B" landed on top of the date and "52.2%" under its own header.
        """
        self.ax.text(self.x + dx if ha != "right" else W - self.x, self.y - dy, s,
                     fontsize=size, color=color, family=family,
                     fontweight=weight, va="top", ha=ha)

    def text(self, s, size=20, color=TXT, family=SANS, weight="normal",
             dy=0.0, wrap=True):
        lines = (_wrap_lines(self.ax, s, size, family, weight, W - 2 * PAD)
                 if wrap else [s])
        for ln in lines:
            self.ax.text(self.x, self.y, ln, fontsize=size, color=color,
                         family=family, fontweight=weight, va="top")
            self.y -= size * 1.45
        self.y -= dy
        return self.y

    def rule(self, pad=16, color=LINE):
        self.y -= pad
        self.ax.plot([self.x, W - self.x], [self.y, self.y], color=color, lw=1)
        self.y -= pad
        return self.y


def _fmt(x, spec=",.0f"):
    return format(x, spec) if isinstance(x, (int, float)) else "—"


def _draw(ax, data: dict, top: float, window: str) -> float:
    """Draw the whole card from `top` downward; return the y it finished at.

    Split out so the height can be MEASURED on a scratch canvas and the real
    figure sized to fit. The first card left 500px of dead space at the bottom
    because the height was a guess.
    """
    g = data.get("gex") or {}
    c = _Cursor(ax, top)

    # ---- header ----
    c.at("FLUXUS CAPITAL", 17, ACCENT, MONO, "bold")
    c.at(f"{g.get('symbol', 'SPX')} · DAILY BRIEF", 15, MUT, MONO, ha="right")
    c.y -= 34
    head = data.get("date", "")
    if window:
        head += f"   ·   {window}"
    c.text(head, size=32, weight="bold")
    c.rule()

    # ---- the state ----
    c.at(_fmt(g.get("spot")), 50, TXT, MONO, "bold")
    regime = (g.get("regime") or "?").upper()
    c.at(f"{regime} GAMMA", 19, GOOD if regime == "POSITIVE" else BAD,
         MONO, "bold", dx=310, dy=6)
    tg = g.get("total_gex")
    if tg is not None:
        c.at(f"net {tg/1e9:+.2f}B per 1%", 17, MUT, MONO, dx=310, dy=36)
    c.y -= 78
    c.rule()

    # ---- today's business: the fork ----
    q = data.get("todays_business")
    if q:
        c.text("TODAY'S BUSINESS", size=14, color=MUT, family=MONO, dy=8)
        c.text(q["question"], size=22, weight="bold", dy=14)
        for label, key, col in (("HOLDS", "holds", GOOD), ("FAILS", "fails", BAD)):
            c.text(label, size=14, color=col, family=MONO, weight="bold", dy=2)
            c.text(q.get(key, ""), size=17, color=MUT, dy=12)
        c.rule()

    # ---- the ladder ----
    rows = (data.get("reference_map") or [])[:7]
    if rows:
        c.text("LEVELS", size=14, color=MUT, family=MONO, dy=10)
        for r in rows:
            conf = r.get("confluence")
            c.at(f"{r['price']:,.0f}", 21, ACCENT if conf else TXT, MONO,
                 "bold" if conf else "normal")
            c.at(" + ".join(m["name"] for m in r["members"]), 17,
                 TXT if conf else MUT, dx=160, dy=3)
            if conf:
                c.at("BOTH", 14, ACCENT, MONO, "bold", dy=3, ha="right")
            c.y -= 34
        c.rule()

    # ---- what conflicts ----
    cons = data.get("conflicts") or []
    if cons:
        c.text("WHAT CONFLICTS", size=14, color=BAD, family=MONO, dy=8)
        for x in cons[:3]:
            c.text(f"· {x['issue']}", size=17, color=MUT, dy=6)
        c.rule()

    # ---- the track record, printed whether or not it flatters ----
    sc = (data.get("scorecard") or {}).get("total") or {}
    if sc:
        c.text("OUR OWN LEVELS, FORWARD-SCORED", size=14, color=MUT,
               family=MONO, dy=12)
        pct = sc.get("held_pct")
        col = MUT if pct is None else (GOOD if pct >= 60 else BAD if pct <= 50 else WARN)
        c.at("n/a" if pct is None else f"{pct:.1f}%", 32, col, MONO, "bold")
        c.at(f"{sc.get('held', 0)} held / {sc.get('broke', 0)} broke / "
             f"{sc.get('untested', 0)} untested", 17, MUT, MONO, dx=170, dy=12)
        c.y -= 48

    return c.y


def render_card(data: dict, out_path: str | Path, window: str = "") -> Path:
    """Draw the card and save it as a PNG, sized to its own content."""
    import matplotlib.pyplot as plt

    # pass 1 — measure on a scratch canvas
    fig, ax = _fig(MAX_H)
    used = MAX_H - 52 - _draw(ax, data, MAX_H - 52, window)
    plt.close(fig)

    footer = 108
    height = used + 52 + footer

    # pass 2 — the real thing
    fig, ax = _fig(height)
    _draw(ax, data, height - 52, window)
    ax.plot([PAD, W - PAD], [footer - 22, footer - 22], color=LINE, lw=1)
    ax.text(PAD, 54, "Fluxus Capital", fontsize=19, color=TXT, family=SANS,
            fontweight="bold", va="bottom")
    ax.text(W - PAD, 58, f"generated {data.get('generated_at', '')[:16]} ET",
            fontsize=14, color=DIM, family=MONO, va="bottom", ha="right")
    ax.text(PAD, 28, "measurements, not advice   ·   no position sized",
            fontsize=14, color=DIM, family=MONO, va="bottom")

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=BG, dpi=DPI)
    plt.close(fig)
    return out


def render_prompt_card(data: dict, out_path: str | Path, window: str = "") -> Path:
    """The commit-first card: the day's question, and NOTHING that answers it.

    The CDSS deskilling literature says an anchored second opinion is not a
    second opinion. Our chain had the brief going out first and a view filed
    after, which builds the merge's weights on a contaminated sample.

    So this card carries the question, the session's own prior structure, and the
    instruction — and deliberately omits the regime, the levels, the reference
    map and the machine's own direction. A reader cannot be anchored by an answer
    they have not been shown.
    """
    import matplotlib.pyplot as plt

    def draw(ax, top):
        c = _Cursor(ax, top)
        c.at("FLUXUS CAPITAL", 17, ACCENT, MONO, "bold")
        c.at("COMMIT FIRST", 15, WARN, MONO, ha="right")
        c.y -= 34
        head = data.get("date", "")
        if window:
            head += f"   ·   {window}"
        c.text(head, size=32, weight="bold")
        c.rule()

        q = data.get("todays_business")
        if q:
            c.text("TODAY'S QUESTION", size=14, color=MUT, family=MONO, dy=8)
            c.text(q["question"], size=24, weight="bold", dy=16)
        else:
            c.text("No question could be formed from the prior session.",
                   size=20, color=MUT, dy=16)

        # The calendar belongs on THIS card, not the brief. It is a fact about
        # the date, not an opinion about the tape -- it names no level, no
        # regime and no direction, so it cannot anchor a view. Withholding it
        # would not protect independence, only leave a checkable premise
        # unchecked, which is how "CPI day" was written on 2026-08-11.
        cal = data.get("calendar") or {}
        today, soon = cal.get("today") or [], cal.get("upcoming") or []
        if cal:
            c.rule()
            c.text("ON THE CALENDAR", size=14, color=MUT, family=MONO, dy=8)
            if today:
                c.text("  ·  ".join(f"{r['event']} {r.get('time') or ''}".strip()
                                    for r in today),
                       size=21, weight="bold", color=WARN, dy=12)
            else:
                c.text("nothing scheduled today", size=21, color=MUT, dy=12)
            ahead = [r for r in soon if r.get("days_out")]
            if ahead:
                c.text("next:  " + "   ".join(
                    f"{r['event']} {r['date'][5:]} (+{r['days_out']}d)"
                    for r in ahead[:3]), size=17, family=MONO, color=TXT, dy=8)
        c.rule()

        c.text("YOUR VIEW, BEFORE YOU SEE OURS", size=14, color=MUT,
               family=MONO, dy=10)
        c.text("log_view.py  <up|down|range|aside>  <1-3>  \"reason\"",
               size=19, family=MONO, color=ACCENT, dy=14)
        c.text("The full brief follows. A view filed after reading it is recorded "
               "as anchored and scored separately — not withheld, just labelled, "
               "because a second opinion formed from the first is not a second "
               "opinion.", size=16, color=MUT, dy=6)
        return c.y

    fig, ax = _fig(MAX_H)
    used = MAX_H - 52 - draw(ax, MAX_H - 52)
    plt.close(fig)
    footer = 108
    height = used + 52 + footer

    fig, ax = _fig(height)
    draw(ax, height - 52)
    ax.plot([PAD, W - PAD], [footer - 22, footer - 22], color=LINE, lw=1)
    ax.text(PAD, 54, "Fluxus Capital", fontsize=19, color=TXT, family=SANS,
            fontweight="bold", va="bottom")
    ax.text(W - PAD, 58, f"{data.get('generated_at', '')[:16]} ET",
            fontsize=14, color=DIM, family=MONO, va="bottom", ha="right")
    ax.text(PAD, 28, "no levels, no regime, no direction — on purpose",
            fontsize=14, color=DIM, family=MONO, va="bottom")

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=BG, dpi=DPI)
    plt.close(fig)
    return out


def caption(data: dict, window: str = "", limit: int = 1900) -> str:
    """The short text that rides with the image, inside Discord's message cap.

    Truncation is by whole blocks, never mid-sentence: a caption cut at a
    character boundary can invert the meaning of the line it lands in.
    """
    g = data.get("gex") or {}
    blocks = [f"**{g.get('symbol','SPX')} {data.get('date','')}**"
              + (f"  ·  {window}" if window else "")]
    spot, tg = g.get("spot"), g.get("total_gex")
    line = f"spot `{_fmt(spot)}`  ·  {(g.get('regime') or '?').upper()} gamma"
    if tg is not None:
        line += f" `{tg/1e9:+.2f}B`"
    blocks.append(line)

    q = data.get("todays_business")
    if q:
        blocks.append(f"\n**{q['question']}**")

    s = data.get("strongest")
    if s:
        names = " + ".join(m["name"] for m in s["members"])
        blocks.append(f"\nStrongest: **{s['price']:,.0f}** — {names} "
                      f"({s['spread']:.0f}pt apart, two frameworks)")

    sc = (data.get("scorecard") or {}).get("total") or {}
    if sc and sc.get("held_pct") is not None:
        blocks.append(f"\nTrack record: **{sc['held_pct']:.1f}%** of tested levels held "
                      f"({sc.get('held')}/{sc.get('held', 0) + sc.get('broke', 0)})")

    # The signature is not optional and not a block that can be dropped by the
    # truncation loop, so its length is reserved before the loop starts.
    sig = "\n— *Fluxus Capital*"
    room = limit - len(sig)
    out = ""
    for b in blocks:
        if len(out) + len(b) + 1 > room:
            break
        out += b + "\n"
    return out.rstrip() + sig
