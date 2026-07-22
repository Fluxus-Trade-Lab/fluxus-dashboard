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
