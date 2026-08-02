#!/usr/bin/env python3
"""Self-contained HTML performance report — the shareable, chart-rich version of
the markdown review.

Reuses the performance_review engine for every number (so the HTML can never
disagree with the .md/.json), generates matplotlib charts as embedded base64
PNGs, and renders a single dark-themed HTML file (Fluxus house style). Open it in
a browser to read/share, or print → Save as PDF.

Usage:
    python -m pipeline.portfolio.report_html --period h1
    python -m pipeline.portfolio.report_html --period quarterly --quarter 2026Q2
    python -m pipeline.portfolio.report_html --period monthly --month 2026-07
"""
from __future__ import annotations

import argparse
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape

from pipeline.marketcal import market_today
from pipeline.portfolio import performance_review as pr
from pipeline.portfolio import analysis as an
from pipeline.portfolio import report_charts as rc
from pipeline.tickers.ohlc_store import load_local_ohlc


def _select(trades, period, month, quarter, dmin, dmax):
    """Filter trades + build labels, mirroring performance_review.main()."""
    if period == "monthly":
        m = month or dmax[:7]
        sub = [t for t in trades if t.exit_date[:7] == m]
        return sub, f"{m} Review", f"monthly_{m}", m, f"{m} — every trade by R-multiple"
    if period == "quarterly":
        q = quarter or pr._quarter_of(dmax[:7])
        sub = [t for t in trades if pr._quarter_of(t.exit_date[:7]) == q]
        return sub, f"{q} Review · 交易复盘", f"quarterly_{q}", q, f"{q} — every trade by R-multiple"
    name = {"h1": "H1", "annual": "Annual", "all": "Full"}[period]
    return trades, f"{name} Review · 交易复盘", f"{period}_{dmin}_{dmax}", f"{dmin} → {dmax}", \
        f"{name} 2026 — every trade by R-multiple"


def build_doc(trades, meta, period, month, quarter, out_dir, handle):
    cap = meta["startingCapital"]
    dates = [t.entry_date for t in trades] + [t.exit_date for t in trades]
    dmin, dmax = min(dates), max(dates)
    sub, title, stem, period_label, rr_title = _select(trades, period, month, quarter, dmin, dmax)

    mtm = pr.compute_mtm(sub, meta)
    s = pr.overall_stats(sub, cap)
    eqbd0 = (mtm or {}).get("equity_by_date")
    ms = pr.monthly_stats(sub, eqbd0, cap)
    rdist = pr.r_distribution(sub)
    by_dir = pr.by_key(sub, lambda t: t.direction)
    by_tk = pr.by_key(sub, lambda t: t.ticker)[:12]
    eqbd = (mtm or {}).get("equity_by_date")
    bd = an.behavioral_diagnosis(sub, eqbd, cap) if eqbd else None
    ce = None
    try:
        ce = an.capital_efficiency(sub, cap, s["total_pnl"], eqbd)
    except Exception:  # noqa: BLE001
        ce = None
    cs = an.trade_case_studies(sub)

    # RR chart PNG (reuse the review's generator, then embed)
    os.makedirs(out_dir, exist_ok=True)
    rr_path = os.path.join(out_dir, f"{stem}_rr.png")
    pr._rr_chart(sub, cap, rr_path, rr_title, handle)

    charts = {
        "rr": rc.png_from_file(rr_path),
        "equity": rc.equity_curve(eqbd, (mtm or {}).get("drawdown"), cap) if eqbd else None,
        "monthly": rc.monthly_returns(ms),
        "rdist": rc.r_distribution(rdist),
        "deployment": rc.deployment_curve(sub, eqbd, cap) if eqbd else None,
        "cases": rc.case_studies_grid(cs, load_local_ohlc) if cs else None,
    }

    return {
        "title": title, "period_label": period_label, "handle": handle,
        "generated": market_today().isoformat(),
        "source": os.path.basename(meta.get("_csv", "")),
        "s": s, "mtm": mtm, "monthly_stats": ms, "rdist": rdist,
        "by_dir": by_dir, "by_tk": by_tk, "bd": bd, "ce": ce, "cs": cs,
        "charts": charts, "cap": cap,
    }, stem


def _env():
    env = Environment(
        loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["money"] = lambda v: (("-$" if v < 0 else "$") + f"{abs(v):,.0f}") if v is not None else "—"
    env.filters["pct"] = lambda v, d=1: f"{v:+.{d}f}%" if v is not None else "—"
    env.filters["pct0"] = lambda v, d=1: f"{v:.{d}f}%" if v is not None else "—"
    env.filters["num"] = lambda v, d=1: f"{v:,.{d}f}" if v is not None else "—"
    env.filters["signR"] = lambda v: (f"{v:+.1f}R" if v is not None else "—")
    return env


def render_html(doc) -> str:
    return _env().get_template("report.html.j2").render(d=doc)


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.abspath(os.path.join(here, "..", ".."))
    portfolio_dir = os.path.join(repo, "data", "portfolio")

    ap = argparse.ArgumentParser(description="Shareable HTML performance report")
    ap.add_argument("--csv", default=None)
    ap.add_argument("--period", choices=["monthly", "quarterly", "h1", "annual", "all"], default="h1")
    ap.add_argument("--month", default=None)
    ap.add_argument("--quarter", default=None)
    ap.add_argument("--out", default=os.path.join(portfolio_dir, "reviews"))
    ap.add_argument("--label", default=None)
    ap.add_argument("--handle", default="@Fluxus_Z")
    args = ap.parse_args()

    csv_path = args.csv or pr.latest_csv(portfolio_dir)
    if not csv_path or not os.path.exists(csv_path):
        raise SystemExit(f"No CSV found in {portfolio_dir}. Pass --csv.")

    trades, meta = pr.parse_csv(csv_path)
    meta["_csv"] = csv_path
    print("· fetching prices for mark-to-market curve …")
    doc, stem = build_doc(trades, meta, args.period, args.month, args.quarter, args.out, args.handle)
    stem = args.label or stem
    html = render_html(doc)
    out_path = os.path.join(args.out, f"{stem}.html")
    with open(out_path, "w") as f:
        f.write(html)
    print(f"✓ HTML report written:\n  {out_path}")


if __name__ == "__main__":
    main()
