"""Model Books preview — one place: the Browse table + the notes card.

Reads the live data the page reads (`frontend/public/data/modelbooks/index.json`
and `suspect.json`) and writes static variants next to this file. Nothing under
`frontend/` is touched. Run from the repo root:

    python3 data/research/ui_previews/2026-09-15/build.py
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
DATA = Path("frontend/public/data/modelbooks")
RESTATE = re.compile(r"^([\d.]+)% in (\d+) days$")
ROWS = 18   # what fits the first screen at 1440x900 on the live page

entries = json.loads((DATA / "index.json").read_text())
suspect = set(json.loads((DATA / "suspect.json").read_text())["entries"])
live = [e for e in entries if e["id"] not in suspect]
by_gain = sorted(live, key=lambda e: -(e.get("gain_pct") or 0))


def restates(e) -> bool:
    """`outcome` is only gain + duration printed again."""
    m = RESTATE.match(e.get("outcome") or "")
    return bool(m) and e.get("gain_pct") is not None \
        and abs(float(m.group(1)) - e["gain_pct"]) < 0.051 \
        and int(m.group(2)) == e.get("duration_days")


annotated = [e for e in by_gain if e.get("key_lessons")]
price_only = [e for e in by_gain if not e.get("key_lessons")]
FIRST_ANNOTATED_RANK = next(i for i, e in enumerate(by_gain) if e.get("key_lessons")) + 1
N_RESTATE = sum(restates(e) for e in entries)

# The book's own claim ("10x in 11 months") against the chart's window
# (gain_pct over duration_days of the bars we ship). Parsed, never typed.
BOOK = re.compile(r"(?:(?P<x>[\d.]+)x|(?P<p>[\d,.]+)%)(?:\s+(?:winner|gain|move))?"
                  r"(?:\s+in\s+(?P<n>[\d.]+)\s+(?P<u>day|week|month|year)s?)?", re.I)
UNIT_DAYS = {"day": 1, "week": 7, "month": 30.44, "year": 365.25}
# Self-made disclosure line, not a standard: 25% apart on either the multiple
# or the length is far enough that a reader would read them as two stories.
APART = 0.25


def book_claim(e):
    m = BOOK.search(e.get("outcome") or "")
    if not m or not (m.group("x") or m.group("p")):
        return None
    mult = float(m.group("x")) if m.group("x") else 1 + float(m.group("p").replace(",", "")) / 100
    days = float(m.group("n")) * UNIT_DAYS[m.group("u").lower()] if m.group("n") else None
    return mult, days


def disagrees(e) -> bool:
    mult, days = book_claim(e)
    chart = 1 + e["gain_pct"] / 100
    off = abs(chart - mult) / mult > APART
    if days:
        off = off or abs(e["duration_days"] - days) / days > APART
    return off


comparable = [e for e in annotated if e.get("gain_pct") is not None and book_claim(e)]
N_COMPARABLE = len(comparable)
N_DISAGREE = sum(disagrees(e) for e in comparable)
N_NO_CHART_GAIN = sum(e.get("gain_pct") is None for e in annotated)

CSS = """
:root{--bg:#e2e0d6;--surface:#f2f0e9;--alt:#e8e6dd;--raised:#dcd9ce;--border:#cbc6b8;
--hair:#dbd7cb;--text:#1c1917;--sec:#4b453e;--muted:#655e55;--bold:#0c0a09;
--profit:#194371;--accent:#2d5f8a;--hover:#e6e3d9;--refused:#b5342c}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
font-family:'IBM Plex Sans',Inter,-apple-system,sans-serif;font-size:13px}
.mono{font-family:'IBM Plex Mono','JetBrains Mono',ui-monospace,monospace}
.wrap{display:flex;gap:12px;padding:24px;max-width:980px}
.col-t{flex:0 0 400px}.col-n{flex:0 0 300px}
.bar{display:flex;align-items:center;gap:8px;margin-bottom:8px;font-size:11px;color:var(--muted)}
.bar .n{margin-left:auto}
.seg{display:flex;gap:2px}.seg span{padding:4px 10px;border-radius:24px;background:var(--surface);color:var(--sec)}
.seg span.on{background:var(--text);color:var(--surface)}
table{width:100%;border-collapse:collapse;background:var(--surface);border-radius:24px;overflow:hidden}
th{font-size:11px;font-weight:500;text-transform:uppercase;letter-spacing:.04em;color:var(--sec);
text-align:left;padding:6px;background:var(--bg);border-bottom:1px solid var(--border)}
td{font-size:11px;padding:6px;border-bottom:1px solid var(--hair);color:var(--sec)}
tr:nth-child(even) td{background:var(--alt)}
tr.sel td{box-shadow:inset 0 1px 0 var(--accent),inset 0 -1px 0 var(--accent)}
td.tk{font-weight:600;color:var(--accent)}td.g{color:var(--profit)}td.src{color:var(--muted)}
td.r{text-align:right}th.r{text-align:right}
tr.div td{background:var(--bg)!important;color:var(--muted);text-align:left;padding:10px 6px}
.chip{display:inline-block;padding:1px 6px;margin:0 2px 2px 0;border-radius:12px;
background:var(--raised);color:var(--sec);font-size:11px}
.card{background:var(--surface);border-radius:24px;padding:16px;display:flex;flex-direction:column;gap:8px}
.card h3{margin:0;font-size:17px;font-weight:600;color:var(--bold)}
.card h3 small{font-size:13px;font-weight:400;color:var(--sec);margin-left:6px}
.lab{color:var(--muted)}.src-line{font-size:11px;color:var(--muted)}
.stat{display:flex;gap:16px}.stat b{font-weight:600;color:var(--profit)}.stat i{font-style:normal;font-weight:500}
.none{font-size:11px;color:var(--muted);font-style:italic}
.out{font-size:11px;color:var(--muted);border-top:1px solid var(--hair);padding-top:6px}
.lessons .k{font-size:11px;font-weight:500;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
blockquote{margin:6px 0 0;border-left:2px solid var(--border);padding-left:10px;
font-style:italic;color:var(--sec);line-height:1.5}
.cap{padding:0 24px;max-width:980px;color:var(--muted);font-size:11px}
"""


def esc(s) -> str:
    return html.escape(str(s))


def pct(v, sep=False) -> str:
    return f"{v:,.0f}%" if sep else f"{v:.0f}%"


def src(s) -> str:
    return {"Big Movers": "BM", "O'Neil": "ON", "Qullamaggie": "QM",
            "TraderLion": "TL", "Minervini": "MV", "General": "GEN"}.get(s, s[:3])


def table(rows, *, pattern_col=True, sep=False, divider_at=None, sel=0) -> str:
    head = "<th>Ticker</th><th>Year</th>" + ("<th>Pattern</th>" if pattern_col else "") \
        + "<th class='r'>Gain ↓</th><th>Src</th>"
    body = []
    for i, e in enumerate(rows):
        if divider_at is not None and i == divider_at:
            span = 5 if pattern_col else 4
            body.append(f"<tr class='div'><td colspan='{span}'>{len(price_only):,} price-only "
                        f"· no pattern, no lessons</td></tr>")
        chips = "".join(f"<span class='chip'>{esc(p.replace('_', ' ').title())}</span>"
                        for p in e["patterns"][:2])
        more = f"<span class='lab'>+{len(e['patterns']) - 2}</span>" if len(e["patterns"]) > 2 else ""
        body.append(
            f"<tr class='{'sel' if i == sel else ''}'><td class='tk'>{esc(e['ticker'])}</td>"
            f"<td class='mono'>{e['year']}</td>"
            + (f"<td>{chips}{more}</td>" if pattern_col else "")
            + f"<td class='mono g r'>{pct(e['gain_pct'], sep)}</td>"
              f"<td class='src'>{src(e['source'])}</td></tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def card(e, *, drop_restate=False, drop_none_for_auto=False, merged=False, book_vs_bars=False) -> str:
    parts = [f"<h3>{esc(e['ticker'])}<small>{e['year']}</small></h3>",
             f"<div class='src-line'>{esc(e['source'])}</div>"]
    if e["patterns"]:
        parts.append("<div>" + "".join(f"<span class='chip'>{esc(p.replace('_', ' ').title())}</span>"
                                       for p in e["patterns"]) + "</div>")
    if book_vs_bars:
        # the two claims sit next to each other, each saying whose it is
        parts.append(f"<div class='stat'><span><span class='lab'>This chart </span>"
                     f"<b>+{e['gain_pct']:,.1f}%</b> <span class='lab'>in</span> "
                     f"<i>{e['duration_days']} days</i></span></div>")
        if e.get("outcome") and not restates(e):
            parts.append(f"<div class='stat'><span><span class='lab'>The book </span>"
                         f"<i>{esc(e['outcome'])}</i></span></div>")
    elif merged:
        parts.append(f"<div class='stat'><span><b>+{e['gain_pct']:,.1f}%</b> "
                     f"<span class='lab'>in</span> <i>{e['duration_days']} days</i></span></div>")
    else:
        parts.append(f"<div class='stat'><span><span class='lab'>Gain </span><b>{e['gain_pct']:.1f}%</b></span>"
                     f"<span><span class='lab'>Duration </span><i>{e['duration_days']}d</i></span></div>")
    if e.get("key_lessons"):
        qs = "".join(f"<blockquote>{esc(q)}</blockquote>" for q in e["key_lessons"])
        parts.append(f"<div class='lessons'><span class='k'>Key lessons</span>{qs}</div>")
    elif not drop_none_for_auto:
        parts.append("<p class='none'>No annotations yet</p>")
    if e.get("outcome") and not book_vs_bars and not (drop_restate and restates(e)):
        parts.append(f"<div class='out'>{esc(e['outcome'])}</div>")
    return f"<div class='card'>{''.join(parts)}</div>"


def page(title, bar, tbl, crd, cap) -> str:
    return (f"<!doctype html><meta charset='utf-8'><title>{esc(title)}</title>"
            "<link rel='stylesheet' href='https://fonts.googleapis.com/css2?family=IBM+Plex+Mono&"
            "family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap'>"
            f"<link rel='stylesheet' href='_shared.css'>"
            f"<div class='wrap'><div class='col-t'><div class='bar'>{bar}</div>{tbl}</div>"
            f"<div class='col-n'>{crd}</div></div><p class='cap'>{cap}</p>")


BAR0 = ("<span class='chip'>Search ticker, lessons…</span><span class='chip'>All Patterns ▾</span>"
        "<span class='chip'>All Sources ▾</span><span>☐ 30 suspect</span>"
        f"<span class='n'>{len(live):,}</span>")

VARIANTS = {
    "v0_current": page(
        "v0 current", BAR0, table(by_gain[:ROWS]), card(by_gain[0]),
        f"Live today. First screen: {ROWS} rows, 0 with a pattern or a lesson; "
        f"the first annotated entry is row #{FIRST_ANNOTATED_RANK}. "
        f"The last line of the card repeats the stat row ({N_RESTATE:,} of {len(entries):,} entries)."),
    "v1_trim": page(
        "v1 trim", BAR0, table(by_gain[:ROWS], pattern_col=False, sep=True),
        card(by_gain[0], drop_restate=True, drop_none_for_auto=True),
        "Remove what repeats or is always empty: the stat row is printed once, "
        "'No annotations yet' goes (a price-only row never gets one), the Pattern column "
        "goes while the list has none, gains get thousands separators."),
    "v2_two_books": page(
        "v2 two books",
        f"<div class='seg'><span class='on'>Annotated {len(annotated)}</span>"
        f"<span>Price-only {len(price_only):,}</span></div><span class='n'>{len(annotated)}</span>",
        table(annotated[:ROWS], sep=True), card(annotated[0], drop_restate=True),
        f"The data is two books under one title. Open on the {len(annotated)} with patterns and lessons; "
        f"the {len(price_only):,} price-only rows are one click away and keep their own table."),
    "v3_annotated_first": page(
        "v3 annotated first", BAR0,
        table(annotated[:10] + price_only[:ROWS - 10], sep=True, divider_at=10),
        card(annotated[0], drop_restate=True),
        "One table, one sort key added in front of gain: annotated rows first, "
        "then a divider row that says what the rest are."),
    "v2a_book_vs_chart": page(
        "v2a book vs chart",
        f"<div class='seg'><span class='on'>Annotated {len(annotated)}</span>"
        f"<span>Price-only {len(price_only):,}</span></div><span class='n'>{len(annotated)}</span>",
        table(annotated[:ROWS], sep=True), card(annotated[0], book_vs_bars=True),
        f"Iteration 1 on v2. The card's two claims measure different windows: of {N_COMPARABLE} "
        f"annotated entries where both can be read, {N_DISAGREE} are more than {APART:.0%} apart "
        f"on the multiple or the length. Each claim now says whose it is, side by side."),
    "v2b_price_only_tab": page(
        "v2b price-only tab",
        f"<div class='seg'><span>Annotated {len(annotated)}</span>"
        f"<span class='on'>Price-only {len(price_only):,}</span></div>"
        f"<span>☐ 30 suspect</span><span class='n'>{len(price_only):,}</span>",
        table(price_only[:ROWS], pattern_col=False, sep=True),
        card(price_only[0], merged=True, drop_restate=True, drop_none_for_auto=True),
        "Iteration 2 on v2: the other tab. No Pattern column (none of these rows has one), "
        "one stat line, no 'No annotations yet', the suspect toggle lives with the rows it hides."),
}

if __name__ == "__main__":
    (HERE / "_shared.css").write_text(CSS)
    for name, doc in VARIANTS.items():
        (HERE / f"{name}.html").write_text(doc)
    print(f"entries {len(entries)} · live {len(live)} · annotated {len(annotated)} · "
          f"price-only {len(price_only)} · restate {N_RESTATE} · first annotated rank {FIRST_ANNOTATED_RANK}")
    print("wrote", ", ".join(VARIANTS))
