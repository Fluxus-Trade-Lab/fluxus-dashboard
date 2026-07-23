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


def _gamma_svg(g: dict, window: int = 175) -> str:
    """Diverging horizontal bar chart of per-strike net GEX around spot.

    Bar length encodes size ($GEX/1%); green = positive (dampening), red =
    negative (amplifying). Spot, flip and the walls are annotated. Pure inline
    SVG so it stays self-contained and CSP-safe.
    """
    ps = g.get("per_strike_gex") or {}
    spot = g.get("spot")
    if not ps or not spot:
        return ""
    items = sorted(((float(k), float(v)) for k, v in ps.items()
                    if abs(float(k) - spot) <= window), key=lambda kv: kv[0])
    if not items:
        return ""
    strikes = [k for k, _ in items]
    maxabs = max(abs(v) for _, v in items) or 1.0

    W, rowh, padL, padR, padT = 760, 17, 78, 24, 26
    H = len(items) * rowh + padT + 18
    cx = padL + (W - padL - padR) / 2.0          # zero axis
    half = (W - padL - padR) / 2.0 - 46          # leave room for value labels
    call_wall, put_wall = g.get("call_wall"), g.get("put_wall")
    flip = g.get("zero_gamma_flip")

    parts = [f"<svg viewBox='0 0 {W} {H}' width='100%' role='img' "
             f"style='font-family:var(--mono);font-size:10px'>"]
    parts.append(f"<line x1='{cx:.0f}' y1='{padT-6}' x2='{cx:.0f}' y2='{H-14}' "
                 f"stroke='#2A3440' stroke-width='1'/>")
    # bars top=highest strike
    for i, (k, v) in enumerate(reversed(items)):
        y = padT + i * rowh
        w = abs(v) / maxabs * half
        pos = v >= 0
        x = cx if pos else cx - w
        color = "#42B96A" if pos else "#EF5E6B"
        is_wall = (k == call_wall or k == put_wall)
        op = "0.95" if is_wall else "0.6"
        parts.append(f"<rect x='{x:.1f}' y='{y:.0f}' width='{max(w,0.5):.1f}' height='{rowh-4}' "
                     f"fill='{color}' opacity='{op}' rx='1.5'/>")
        klbl = f"{k:,.0f}"
        weight = "700" if is_wall else "400"
        kcolor = "#C7CDD8" if is_wall else "#79828F"
        parts.append(f"<text x='{padL-8}' y='{y+rowh-7:.0f}' text-anchor='end' "
                     f"fill='{kcolor}' font-weight='{weight}'>{klbl}</text>")
        # value label at bar tip
        vlbl = f"{v/1e9:+.2f}B"
        vx = (cx + w + 4) if pos else (cx - w - 4)
        anchor = "start" if pos else "end"
        parts.append(f"<text x='{vx:.1f}' y='{y+rowh-7:.0f}' text-anchor='{anchor}' "
                     f"fill='#525b69'>{vlbl}</text>")

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
              "<span class='pos'>■</span> positive (dampens) &nbsp; "
              "<span class='neg'>■</span> negative (amplifies) &nbsp;·&nbsp; "
              "bold = wall &nbsp;·&nbsp; bar length = $GEX per 1%</div>")
    return (f"<section><p class='lbl'>Gamma profile — per-strike net GEX "
            f"(±{window} around spot)</p>{''.join(parts)}{legend}</section>")


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
        f"{_gamma_svg(g)}"
        f"{em_html}{vix_html}"
        f"<p class='foot'>GEX from data/gex/ · EM/VIX pulled live when available · "
        f"snapshot cached in data/snapshots/. Not advice.</p>"
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
