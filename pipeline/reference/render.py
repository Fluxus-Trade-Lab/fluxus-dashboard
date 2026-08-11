"""Render reference dicts to self-contained, shareable HTML.

Same dark theme as the GEX brief so the family of documents looks consistent.
Pure string-building from a dict — no IO, no recompute.
"""
from __future__ import annotations

THEME_CSS = """
:root{--bg:#0A0D13;--panel:#111621;--line:#1E2633;--txt:#C7CDD8;--mut:#79828F;
--dim:#525b69;--accent:#5AA9FF;--good:#42B96A;--bad:#EF5E6B;--warn:#D6A34C;
--mono:ui-monospace,Menlo,Consolas,monospace;
--sans:-apple-system,"Segoe UI",system-ui,sans-serif}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--txt);font-family:var(--sans);margin:0;padding:38px 20px 60px}
.doc{max-width:820px;margin:0 auto}
h1{font-size:26px;font-weight:600;margin:2px 0 6px}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);margin:0 0 10px}
.meta{font-family:var(--mono);font-size:12px;color:var(--dim);border-top:1px solid var(--line);
border-bottom:1px solid var(--line);padding:10px 0;margin-top:12px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}
section{margin-top:28px}
.lbl{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--mut);
margin:0 0 12px;display:flex;align-items:center;gap:10px}
.lbl::after{content:"";flex:1;height:1px;background:var(--line)}
table{width:100%;border-collapse:collapse;font-size:13px;border:1px solid var(--line);border-radius:8px;overflow:hidden}
th{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);
text-align:right;padding:9px 12px;background:#0E131C;border-bottom:1px solid var(--line)}
th:first-child{text-align:left}
td{padding:9px 12px;border-bottom:1px solid var(--line);font-variant-numeric:tabular-nums;text-align:right}
td:first-child{text-align:left}
tr:last-child td{border-bottom:none}
tr.focus td{background:rgba(90,169,255,.09)}
.mono{font-family:var(--mono)}
.pos{color:var(--good)}.neg{color:#F4838C}.warn{color:#E0B463}.mut{color:var(--mut)}
.bar{display:inline-block;height:9px;border-radius:2px;vertical-align:middle}
.foot{margin-top:32px;padding-top:12px;border-top:1px solid var(--line);font-family:var(--mono);font-size:11px;color:var(--dim)}
"""


def _cls(v: float) -> str:
    return "pos" if v > 0 else ("neg" if v < 0 else "mut")


def _page(title: str, body: str) -> str:
    return (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{title}</title><style>{THEME_CSS}</style></head>"
            f"<body><div class='doc'>{body}</div></body></html>")


def _kv_table(rows: list[tuple[str, str, str]]) -> str:
    """rows = [(label, value, css_class)] -> a 2-col table."""
    body = "".join(
        f"<tr><td class='mut'>{lbl}</td><td class='{cls}'>{val}</td></tr>"
        for lbl, val, cls in rows
    )
    return f"<table><tbody>{body}</tbody></table>"


CONFLUENCE_FRAC = 0.40   # a strike counts as "loaded" at >=40% of that metric's max


def _gamma_svg(g: dict, window: int = 175) -> str:
    """Per-strike dealer positioning: net GEX (thick) over charm drift (thin).

    Bar length encodes size; green = positive, red = negative. The two metrics
    share a row and a zero axis because the point is the COMPARISON: gamma
    forces re-hedging when spot moves, charm when time passes. A strike where
    both are large AND same-signed is under two independent forcings, which is
    a stronger read than either bar alone — those rows are boxed and listed.
    Pure inline SVG so it stays self-contained and CSP-safe.
    """
    ps = g.get("per_strike_gex") or {}
    spot = g.get("spot")
    if not ps or not spot:
        return ""
    items = sorted(((float(k), float(v)) for k, v in ps.items()
                    if abs(float(k) - spot) <= window), key=lambda kv: kv[0])
    if not items:
        return ""
    charm = {float(k): float(v) for k, v in (g.get("per_strike_charm") or {}).items()}
    strikes = [k for k, _ in items]
    maxabs = max(abs(v) for _, v in items) or 1.0
    cmax = max((abs(charm.get(k, 0.0)) for k in strikes), default=0.0) or 1.0

    # Same sign and both loaded -> two independent forcings agree.
    conf = {k for k, v in items
            if charm.get(k) is not None and v * charm.get(k, 0.0) > 0
            and abs(v) >= CONFLUENCE_FRAC * maxabs
            and abs(charm.get(k, 0.0)) >= CONFLUENCE_FRAC * cmax}

    W, rowh, padL, padR, padT = 760, 20, 78, 24, 26
    H = len(items) * rowh + padT + 18
    cx = padL + (W - padL - padR) / 2.0          # zero axis
    half = (W - padL - padR) / 2.0 - 46          # leave room for value labels
    call_wall, put_wall = g.get("call_wall"), g.get("put_wall")

    parts = [f"<svg viewBox='0 0 {W} {H}' width='100%' role='img' "
             f"style='font-family:var(--mono);font-size:10px'>"]
    parts.append(f"<line x1='{cx:.0f}' y1='{padT-6}' x2='{cx:.0f}' y2='{H-14}' "
                 f"stroke='#2A3440' stroke-width='1'/>")
    # bars top=highest strike
    for i, (k, v) in enumerate(reversed(items)):
        y = padT + i * rowh
        if k in conf:
            parts.append(f"<rect x='{padL-40}' y='{y-2:.0f}' width='{W-padL-padR+44}' "
                         f"height='{rowh-1}' fill='#5AA9FF' opacity='0.10' rx='3'/>")
        # gamma: thick bar
        w = abs(v) / maxabs * half
        pos = v >= 0
        color = "#42B96A" if pos else "#EF5E6B"
        is_wall = (k == call_wall or k == put_wall)
        parts.append(f"<rect x='{(cx if pos else cx - w):.1f}' y='{y:.0f}' "
                     f"width='{max(w,0.5):.1f}' height='9' "
                     f"fill='{color}' opacity='{'0.95' if is_wall else '0.6'}' rx='1.5'/>")
        # charm: thin bar underneath, same axis
        cv = charm.get(k)
        if cv is not None:
            cw = abs(cv) / cmax * half
            cpos = cv >= 0
            parts.append(f"<rect x='{(cx if cpos else cx - cw):.1f}' y='{y+10:.0f}' "
                         f"width='{max(cw,0.5):.1f}' height='5' "
                         f"fill='{'#42B96A' if cpos else '#EF5E6B'}' opacity='0.35' rx='1'/>")
        klbl = f"{k:,.0f}"
        kcolor = "#C7CDD8" if (is_wall or k in conf) else "#79828F"
        parts.append(f"<text x='{padL-8}' y='{y+rowh-9:.0f}' text-anchor='end' "
                     f"fill='{kcolor}' font-weight='{'700' if is_wall or k in conf else '400'}'>{klbl}</text>")
        vlbl = f"{v/1e9:+.2f}B"
        vx = (cx + w + 4) if pos else (cx - w - 4)
        parts.append(f"<text x='{vx:.1f}' y='{y+rowh-9:.0f}' "
                     f"text-anchor='{'start' if pos else 'end'}' fill='#525b69'>{vlbl}</text>")

    # spot line (interpolate y from strike grid)
    lo, hi = strikes[0], strikes[-1]
    if hi > lo:
        frac = (hi - spot) / (hi - lo)              # 0 at top(hi) .. 1 at bottom(lo)
        ys = padT + frac * (len(items) * rowh)
        parts.append(f"<line x1='{padL-2}' y1='{ys:.0f}' x2='{W-padR}' y2='{ys:.0f}' "
                     f"stroke='#5AA9FF' stroke-width='1' stroke-dasharray='4 3'/>")
        parts.append(f"<text x='{W-padR}' y='{ys-3:.0f}' text-anchor='end' "
                     f"fill='#5AA9FF'>spot {spot:,.0f}</text>")
    parts.append("</svg>")
    legend = ("<div class='mut' style='font-size:11px;margin-top:6px'>"
              "<span class='pos'>■</span> positive &nbsp; <span class='neg'>■</span> negative"
              " &nbsp;·&nbsp; thick = net GEX per 1% &nbsp;·&nbsp; thin = delta drift to expiry"
              " &nbsp;·&nbsp; bold = wall</div>")
    if conf:
        rows = "".join(
            f"<tr><td class='mono'>{k:,.0f}</td>"
            f"<td class='{'pos' if dict(items)[k] > 0 else 'neg'}'>{dict(items)[k]/1e9:+.2f}B</td>"
            f"<td class='{'pos' if charm[k] > 0 else 'neg'}'>{charm[k]/1e9:+.2f}B</td></tr>"
            for k in sorted(conf, reverse=True))
        legend += (
            "<p class='lbl' style='margin-top:18px'>Gamma × charm confluence</p>"
            "<table><thead><tr><th>Strike</th><th>Net GEX</th><th>Drift to expiry</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
            "<div class='mut' style='font-size:11px;margin-top:6px'>Both metrics same-signed and "
            f"&ge;{CONFLUENCE_FRAC:.0%} of their max — two independent forcings on one strike.</div>")
    else:
        legend += ("<div class='mut' style='font-size:11px;margin-top:10px'>"
                   "No strike carries both a large gamma and a large same-signed charm load today.</div>")
    return (f"<section><p class='lbl'>Dealer positioning — net GEX + charm drift "
            f"(±{window} around spot)</p>{''.join(parts)}{legend}</section>")


def _pct_phrase(p: dict | None) -> str:
    """Percentile with its sample size — n is never dropped on the way to the page."""
    if not p or p.get("pct") is None:
        return "no history yet"
    warn = " (thin sample)" if p.get("thin") else ""
    return f"{p['pct']:.0f}th pct of last {p['n']}{warn}"


def _migration_html(m: dict | None) -> str:
    """Day-over-day wall movement — the most narrative-ready number we compute."""
    if not m or not m.get("note"):
        return ""
    rows = [(k.replace("_", " ").title(), f"{m[k]:+.0f}",
             "pos" if m[k] > 0 else "neg")
            for k in ("call_wall", "put_wall", "flip") if m.get(k) is not None]
    body = _kv_table(rows) if rows else ""
    return (f"<section><p class='lbl'>Since prior session</p>{body}"
            f"<div class='mut' style='font-size:12px;margin-top:8px'>{m['note']}</div></section>")


def _sequence_html(seq: list | None) -> str:
    """How the rails moved during the session, in order.

    A dated file only ever shows the last state of the day; the ORDER the walls
    moved in is the part that says what actually happened. One entry means one
    pull — shown as such rather than hidden.
    """
    if not seq:
        return ""
    if len(seq) == 1:
        return ("<section><p class='lbl'>Session sequence</p>"
                "<div class='mut' style='font-size:12px'>Single pull today — no "
                "intraday movement recorded yet.</div></section>")
    rows = ""
    for st in seq:
        t_ = (st.get("generated_at") or "")[11:16]
        mv = st.get("moved")
        moved = ", ".join(f"{k.replace('_',' ')} {v:+.0f}" for k, v in mv.items()) if mv else "—"
        rows += (f"<tr><td class='mono'>{t_}</td>"
                 f"<td class='mono'>{st.get('spot'):,.0f}</td>"
                 f"<td class='mono'>{st.get('put_wall'):,.0f} / {st.get('flip'):,.0f} / "
                 f"{st.get('call_wall'):,.0f}</td>"
                 f"<td class='{'warn' if mv else 'mut'}'>{moved}</td></tr>")
    return ("<section><p class='lbl'>Session sequence — how the rails moved</p>"
            "<table><thead><tr><th>ET</th><th>Spot</th><th>put / flip / call</th>"
            f"<th>moved</th></tr></thead><tbody>{rows}</tbody></table></section>")


def _ladder_html(ladder: list | None) -> str:
    """The strikes behind the headline walls — targets and stops between them."""
    if not ladder:
        return ""
    rows = "".join(
        f"<tr><td class='mut'>{r['rank']}</td><td class='mono'>{r['strike']:,.0f}</td>"
        f"<td class='{'pos' if r['gex'] > 0 else 'neg'}'>{r['gex']/1e9:+.2f}B</td>"
        f"<td class='mut'>{r['distance']:+.0f} {r['side']}</td></tr>" for r in ladder)
    return ("<section><p class='lbl'>Behind the walls — ranked secondary levels</p>"
            "<table><thead><tr><th>#</th><th>Strike</th><th>Net GEX</th><th>vs spot</th>"
            f"</tr></thead><tbody>{rows}</tbody></table></section>")


def _transition_html(t: dict | None) -> str:
    """State moves in the GEX series, with the honest distance from a test."""
    if not t or not t.get("recent"):
        return ""
    rows = "".join(
        f"<tr class='{'focus' if r['speed'] >= 2 else ''}'>"
        f"<td class='mono'>{r['session']}</td>"
        f"<td class='mut'>{r['from_state']}</td><td>{r['to_state']}</td>"
        f"<td class='mono {'warn' if r['speed'] >= 2 else 'mut'}'>{r['speed']}</td>"
        f"<td class='mono {'pos' if r['delta'] > 0 else 'neg'}'>{r['delta']:+.1f}B</td>"
        f"</tr>" for r in t["recent"])
    return ("<section><p class='lbl'>GEX as a transition, not a number</p>"
            "<table><thead><tr><th>session</th><th>from</th><th>to</th>"
            "<th>states skipped</th><th>delta</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
            "<div class='mut' style='font-size:12px;margin-top:6px'>"
            "Boundaries are percentiles of <b>our own</b> series, not ported dollar "
            "levels — a source's &minus;5B collapse is routine here, so his thresholds "
            "describe his distribution. "
            f"<b>{t['note']}</b></div></section>")


def _scorecard_html(sc: dict | None, session: str | None = None) -> str:
    """Our own track record, printed next to today's call.

    A brief that shows only today's levels is unfalsifiable by construction. This
    block is what makes the rest of the page cost something: the same four level
    names, scored forward-only against every session since they were published.
    `untested` is shown but never folded into the rate — a level the market never
    reached is not a level that held.
    """
    if not sc or not sc.get("by_level"):
        return ""
    order = ("call_wall", "zero_gamma_flip", "put_wall", "charm_peak_strike")
    rows = ""
    for name in [n for n in order if n in sc["by_level"]]:
        s = sc["by_level"][name]
        pct = s["held_pct"]
        cls = "mut" if pct is None else ("pos" if pct >= 60 else "neg" if pct <= 50 else "warn")
        shown = "n/a" if pct is None else f"{pct:.1f}%"
        rows += (f"<tr><td>{name.replace('_',' ')}</td>"
                 f"<td class='mono'>{s['held']}</td><td class='mono'>{s['broke']}</td>"
                 f"<td class='mono mut'>{s['untested']}</td>"
                 f"<td class='mono {cls}'>{shown}</td></tr>")
    t = sc["total"]
    total_pct = "n/a" if t["held_pct"] is None else f"{t['held_pct']:.1f}%"
    rows += (f"<tr><td><b>total</b></td><td class='mono'><b>{t['held']}</b></td>"
             f"<td class='mono'><b>{t['broke']}</b></td>"
             f"<td class='mono mut'>{t['untested']}</td>"
             f"<td class='mono'><b>{total_pct}</b></td></tr>")
    note = ("<div class='mut' style='font-size:12px;margin-top:6px'>"
            "Forward-scored only — every row was published before the session it was "
            "graded against. Percentages exclude untested levels.</div>")
    return ("<section><p class='lbl'>Track record — did our own levels hold?</p>"
            "<table><thead><tr><th>Level</th><th>held</th><th>broke</th>"
            "<th>untested</th><th>held % (of tested)</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>{note}</section>")


def _calendar_html(cal: dict | None) -> str:
    """What is scheduled, and — as loudly — what we do not track.

    A calendar listing two events reads as "those are the only two". We hold CPI
    and FOMC and nothing else, so the untracked list is printed beside them;
    without it the section is a lie of omission, which is the exact failure it
    was built to stop.
    """
    if not cal:
        return ""
    today, soon = cal.get("today") or [], cal.get("upcoming") or []
    if today:
        head = " · ".join(
            f"<b class='neg'>{r['event']}</b> {r.get('time') or ''} ET"
            f" <span class='mut'>{r.get('name','')}</span>" for r in today)
    else:
        head = "<span class='mut'>nothing scheduled today</span>"
    ahead = [r for r in soon if r.get("days_out")]
    nxt = ("<div class='mono mut' style='font-size:12px;margin-top:8px'>next &nbsp; "
           + " &nbsp; ".join(f"{r['event']} {r['date']} (+{r['days_out']}d)"
                             for r in ahead[:4]) + "</div>") if ahead else ""
    tracked = sorted({r["event"] for r in (today + soon)}) or ["CPI", "FOMC"]
    note = ("<div class='mut' style='font-size:11px;margin-top:10px'>Tracking "
            f"{', '.join(tracked)} only. Any other event is reported as "
            "<i>unknown</i>, never as absent.</div>")
    return (f"<section><p class='lbl'>On the calendar</p>"
            f"<div style='font-size:14px'>{head}</div>{nxt}{note}</section>")


def _business_html(q: dict | None) -> str:
    """The day's one question, asked before the session — a fork, not a forecast."""
    if not q:
        return ""
    return ("<section><p class='lbl'>Today's business</p>"
            f"<div style='font-size:15px;line-height:1.5'><b>{q['question']}</b></div>"
            "<div style='display:flex;gap:14px;margin-top:12px;flex-wrap:wrap'>"
            "<div style='flex:1;min-width:240px;border:1px solid var(--line);border-radius:8px;padding:12px'>"
            "<div class='pos mono' style='font-size:11px;letter-spacing:.1em'>HOLDS</div>"
            f"<div class='mut' style='font-size:13px;line-height:1.6;margin-top:4px'>{q['holds']}</div></div>"
            "<div style='flex:1;min-width:240px;border:1px solid var(--line);border-radius:8px;padding:12px'>"
            "<div class='neg mono' style='font-size:11px;letter-spacing:.1em'>FAILS</div>"
            f"<div class='mut' style='font-size:13px;line-height:1.6;margin-top:4px'>{q['fails']}</div></div>"
            "</div></section>")


def _refmap_html(rows: list | None, strongest: dict | None) -> str:
    """The integrated map: auction levels and dealer levels on one ladder."""
    if not rows:
        return ""
    head = ""
    if strongest:
        names = " + ".join(g["name"] for g in strongest["members"])
        head = (f"<div style='font-size:14px;margin-bottom:12px'>Strongest read: two "
                f"independent frameworks land on <b>{strongest['price']:,.0f}</b> "
                f"({names}, {strongest['spread']:.0f}pt apart).</div>")
    tr = ""
    for row in rows:
        mem = " + ".join(f"{g['name']} {g['price']:,.0f}" for g in row["members"])
        badge = ("<span class='pos mono'>both</span>" if row["confluence"]
                 else f"<span class='mut mono'>{'/'.join(row['frameworks'])}</span>")
        tr += (f"<tr class='{'focus' if row['confluence'] else ''}'>"
               f"<td class='mono'>{row['price']:,.0f}</td><td>{mem}</td><td>{badge}</td></tr>")
    return ("<section><p class='lbl'>Integrated reference map — auction vs dealer book</p>"
            f"{head}<table><thead><tr><th>price</th><th>levels</th><th>frameworks</th>"
            f"</tr></thead><tbody>{tr}</tbody></table>"
            "<div class='mut' style='font-size:12px;margin-top:6px'>Confluence requires "
            "levels from BOTH frameworks — gamma agreeing with charm is the same book "
            "twice and does not count.</div></section>")


def _resolution_html(res: dict | None) -> str:
    """How the conflict resolves — printed with the conflicts, not instead.

    The rule is stated on the page so it cannot be applied selectively: the
    auction says WHAT, the dealer book says WHERE and HOW it would break.
    """
    if not res or not res.get("reading"):
        return ""
    mech = (f"<div class='mut' style='font-size:13px;line-height:1.6;margin-top:8px'>"
            f"{res['mechanism']}</div>" if res.get("mechanism") else "")
    return ("<section><p class='lbl'>How it resolves</p>"
            f"<div style='font-size:15px;line-height:1.6'>{res['reading']}</div>{mech}"
            f"<div class='mut' style='font-size:12px;margin-top:10px'>{res['note']}</div>"
            "</section>")


def _conflicts_html(cons: list | None) -> str:
    """What disagrees. A brief that only prints agreement cannot be wrong."""
    if not cons:
        return ""
    body = "".join(
        f"<div style='margin:12px 0'><div class='neg mono' style='font-size:11px;"
        f"letter-spacing:.08em;text-transform:uppercase'>{c['issue']}</div>"
        f"<div class='mut' style='font-size:13px;line-height:1.6;margin-top:3px'>"
        f"{c['detail']}</div></div>" for c in cons)
    return f"<section><p class='lbl'>What conflicts</p>{body}</section>"


def render_snapshot_md(data: dict) -> str:
    """Markdown twin of the HTML brief — pasteable into Substack/Discord."""
    g = data["gex"]
    L = [f"# {g.get('symbol','SPX')} — {data['date']}", ""]
    spot = g.get("spot")
    L.append(f"**Spot** {spot:,.0f}  ·  **Regime** {(g.get('regime') or '?').upper()}"
             + (f" ({g['total_gex']/1e9:+.2f}B)" if g.get("total_gex") is not None else ""))
    if data.get("gex_percentile"):
        L.append(f"**Net GEX vs history:** {_pct_phrase(data['gex_percentile'])}")
    L += ["", "## Rails", "",
          "| Level | Strike |", "|---|---|",
          f"| Call wall | {g.get('call_wall'):,.0f} |" if g.get("call_wall") else "",
          f"| Zero-gamma flip | {g.get('zero_gamma_flip'):,.0f} |" if g.get("zero_gamma_flip") else "",
          f"| Put wall / pin | {g.get('put_wall'):,.0f} |" if g.get("put_wall") else ""]
    m = data.get("wall_migration")
    if m and m.get("note"):
        parts = [f"{k.replace('_',' ')} {m[k]:+.0f}" for k in ("call_wall", "put_wall", "flip")
                 if m.get(k) is not None]
        L += ["", f"**Since prior session:** {m['note']}"
              + (f"  ({', '.join(parts)})" if parts else "")]
    lad = data.get("secondary_levels") or []
    if lad:
        L += ["", "## Behind the walls", "",
              "| # | Strike | Net GEX | vs spot |", "|---|---|---|---|"]
        L += [f"| {r['rank']} | {r['strike']:,.0f} | {r['gex']/1e9:+.2f}B | "
              f"{r['distance']:+.0f} ({r['side']}) |" for r in lad]
    em = data.get("expected_move")
    if em:
        L += ["", "## Expected move", "", "| Expiry | Move | Range |", "|---|---|---|"]
        L += [f"| {e['label']} ({e['expiry']}) | ±{e['pts']:.0f} ({e['pct']:.2f}%) | "
              f"{e['low']:,.0f} – {e['high']:,.0f} |" for e in em]
    v = data.get("vix")
    if v:
        term = v.get("vix3m", 0) - v.get("vix", 0)
        L += ["", f"**VIX** {v['vix']:.2f} · **VIX3M** {v['vix3m']:.2f} · "
              f"term {term:+.2f} ({'contango' if term > 0 else 'backwardation'})"]
    L += ["", "---", f"*Generated {data['generated_at']}. Levels are computed, not "
          "predicted — see method. Not advice.*"]
    return "\n".join(x for x in L if x != "")


def render_snapshot_html(data: dict) -> str:
    """Daily market snapshot: GEX rails + expected move + VIX term structure."""
    g = data["gex"]
    spot = g.get("spot")
    regime = (g.get("regime") or "?").upper()
    reg_cls = "neg" if regime == "NEGATIVE" else ("pos" if regime == "POSITIVE" else "mut")
    gex_rows = [
        ("Spot", f"{spot:,.0f}" if spot else "—", "mono"),
        ("Regime", f"{regime} ({g['total_gex']/1e9:+.2f}B)" if g.get("total_gex") is not None else regime, reg_cls),
        ("Call wall", f"{g['call_wall']:,.0f}" if g.get("call_wall") else "—", "mono"),
        ("Zero-gamma flip", f"{g['zero_gamma_flip']:,.0f}" if g.get("zero_gamma_flip") else "—", "mono"),
        ("Put wall / pin", f"{g['put_wall']:,.0f}" if g.get("put_wall") else "—", "mono"),
    ]
    p = data.get("gex_percentile")
    if p and p.get("pct") is not None:
        gex_rows.insert(2, ("Net GEX vs history", _pct_phrase(p),
                            "warn" if p.get("thin") else "mut"))
    iv1, ivs = g.get("atm_iv_1dte"), g.get("atm_iv_swing")
    if iv1 or ivs:
        gex_rows.append(("ATM IV (1DTE / swing)",
                         f"{(iv1 or 0)*100:.1f}% / {(ivs or 0)*100:.1f}%", "mut"))
    gex_tbl = _kv_table(gex_rows)

    em = data.get("expected_move")
    if em:
        em_rows = []
        for e in em:
            rng = f"{e['low']:,.0f} – {e['high']:,.0f}"
            em_rows.append((f"{e['label']} ({e['expiry']})",
                            f"±{e['pts']:.0f} ({e['pct']:.2f}%) → {rng}", "mono"))
        em_html = f"<section><p class='lbl'>Expected move (ATM straddle)</p>{_kv_table(em_rows)}</section>"
    else:
        em_html = "<section><p class='lbl'>Expected move</p><p class='mut mono'>unavailable — TWS was down at build time</p></section>"

    vix = data.get("vix")
    if vix:
        term = vix.get("vix3m", 0) - vix.get("vix", 0)
        struct = "contango (calm)" if term > 0 else "backwardation (stress)"
        vix_html = ("<section><p class='lbl'>Volatility</p>" + _kv_table([
            ("VIX", f"{vix['vix']:.2f}", "mono"),
            ("VIX3M", f"{vix['vix3m']:.2f}", "mono"),
            ("Term (3M − spot)", f"{term:+.2f} — {struct}", "pos" if term > 0 else "neg"),
        ]) + "</section>")
    else:
        vix_html = ""

    body = (
        f"<p class='eyebrow'>{g.get('symbol','SPX')} · Daily Snapshot</p>"
        f"<h1>{data['date']} market snapshot</h1>"
        f"<div class='meta'><span>generated {data['generated_at']}</span>"
        f"<span class='{reg_cls}'>{regime} gamma</span></div>"
        f"<section><p class='lbl'>Dealer gamma rails</p>{gex_tbl}</section>"
        f"{_migration_html(data.get('wall_migration'))}"
        f"{_gamma_svg(g)}"
        f"{_ladder_html(data.get('secondary_levels'))}"
        f"{_sequence_html(data.get('intraday_sequence'))}"
        f"{_calendar_html(data.get('calendar'))}"
        f"{_business_html(data.get('todays_business'))}"
        f"{_refmap_html(data.get('reference_map'), data.get('strongest'))}"
        f"{_conflicts_html(data.get('conflicts'))}"
        f"{_resolution_html(data.get('resolution'))}"
        f"{_transition_html(data.get('gex_transition'))}"
        f"{_scorecard_html(data.get('scorecard'))}"
        f"{em_html}{vix_html}"
        f"<p class='foot'>Generated by machine (AI-Human): levels computed from the "
        f"IBKR chain by an automated pipeline, reviewed by a human before publication. "
        f"Method is published alongside — every number here is reproducible. "
        f"Not advice.</p>"
    )
    return _page(f"{g.get('symbol','SPX')} Snapshot {data['date']}", body)


def render_seasonality_html(data: dict, symbol: str, generated_at: str) -> str:
    h = data["history"]
    focus = data.get("focus_month")
    rows = ""
    for m in data["months"]:
        mean, med = m["mean_pct"], m["median_pct"]
        win = m["win_pct"]
        # width proportional to |mean|, capped
        w = min(abs(mean) / 3.0 * 90, 90)
        color = "var(--good)" if mean > 0 else "var(--bad)"
        bar = f"<span class='bar' style='width:{w:.0f}px;background:{color}'></span>"
        focus_cls = " class='focus'" if focus and m["month"] == focus else ""
        rows += (
            f"<tr{focus_cls}><td>{m['name']}</td>"
            f"<td class='{_cls(mean)}'>{mean:+.2f}%</td>"
            f"<td class='{_cls(med)}'>{med:+.2f}%</td>"
            f"<td class='{'pos' if win>=50 else 'neg'}'>{win:.0f}%</td>"
            f"<td class='mut'>{m['stdev_pct']:.2f}</td>"
            f"<td class='neg'>{m['min_pct']:+.1f}</td>"
            f"<td class='pos'>{m['max_pct']:+.1f}</td>"
            f"<td class='mut'>{m['rvol_pct']:.1f}%</td>"
            f"<td>{bar}</td></tr>"
        )
    table = (
        "<table><thead><tr><th>Month</th><th>Mean</th><th>Median</th><th>Win</th>"
        "<th>Stdev</th><th>Min</th><th>Max</th><th>RVol</th><th></th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )

    detail = ""
    if focus:
        fm = next((m for m in data["months"] if m["month"] == focus), None)
        yrs = data["by_year"].get(str(focus), [])
        yr_rows = "".join(
            f"<tr><td>{r['year']}</td><td class='{_cls(r['ret_pct'])}'>{r['ret_pct']:+.2f}%</td></tr>"
            for r in yrs
        )
        if fm:
            detail = (
                f"<section><p class='lbl'>{fm['name']} — year by year</p>"
                f"<table><thead><tr><th>Year</th><th>Return</th></tr></thead>"
                f"<tbody>{yr_rows}</tbody></table></section>"
            )

    body = (
        f"<p class='eyebrow'>{symbol} · Monthly Seasonality</p>"
        f"<h1>What each month usually does</h1>"
        f"<div class='meta'><span>{h['start']} → {h['end']} · {h['n_days']:,} days</span>"
        f"<span>full-sample RVol {data['full_sample_rvol_pct']:.1f}%</span></div>"
        f"<section><p class='lbl'>Full-month returns by calendar month</p>{table}</section>"
        f"{detail}"
        f"<p class='foot'>Generated {generated_at} · cached in data/reference/ · "
        f"month return = month-end close vs prior month-end. Not advice.</p>"
    )
    return _page(f"{symbol} Seasonality", body)
