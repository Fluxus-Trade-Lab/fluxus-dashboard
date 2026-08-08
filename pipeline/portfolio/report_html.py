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
from pipeline.portfolio import mtm as _mtm
from pipeline.portfolio.rr_chart import generate_rr_chart
from pipeline.tickers.ohlc_store import load_local_ohlc


def _rr_pair(sub, cap, out_dir, stem, label, handle):
    """Base64 the RR chart in light + dark."""
    def one(dark):
        path = os.path.join(out_dir, f"{stem}_rr{'_dark' if dark else ''}.png")
        generate_rr_chart(sub, cap, path, period_label=label, handle=handle,
                          title="Every trade by R-multiple", dark=dark)
        return rc.png_from_file(path)
    return {"light": one(False), "dark": one(True)}


def _both(fn):
    return {"light": fn(False), "dark": fn(True)}


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
    by_tk = pr.by_key(sub, lambda t: t.ticker)[:10]
    eqbd = (mtm or {}).get("equity_by_date")
    bd = an.behavioral_diagnosis(sub, eqbd, cap) if eqbd else None
    ce = None
    try:
        ce = an.capital_efficiency(sub, cap, s["total_pnl"], eqbd)
    except Exception:  # noqa: BLE001
        ce = None
    cs = an.trade_case_studies(sub)

    # Charts are rendered in BOTH light and dark so the in-page theme toggle can
    # swap them — keeping the charts consistent with whichever theme is active.
    os.makedirs(out_dir, exist_ok=True)
    dd = (mtm or {}).get("drawdown")

    ps_light, ps_stats = rc.position_sizes(sub, eqbd, cap, dark=False)
    ps_dark, _ = rc.position_sizes(sub, eqbd, cap, dark=True)

    charts = {
        "rr": _rr_pair(sub, cap, out_dir, stem, rr_title, handle),
        "sizes": {"light": ps_light, "dark": ps_dark} if ps_light else None,
        "equity": _both(lambda d: rc.equity_curve(eqbd, dd, cap, dark=d)) if eqbd else None,
        "monthly": _both(lambda d: rc.monthly_returns(ms, dark=d)),
        "rdist": _both(lambda d: rc.r_distribution(rdist, dark=d)),
        "deployment": _both(lambda d: rc.deployment_curve(sub, eqbd, cap, dark=d)) if eqbd else None,
        "cases": _both(lambda d: rc.case_studies_grid(cs, load_local_ohlc, dark=d)) if cs else None,
        # review charts
        "cum_r": _both(lambda d: rc.cumulative_r(sub, dark=d)),
        "dd_dist": _both(lambda d: rc.drawdown_distribution(eqbd, dark=d)) if eqbd else None,
        "rolling_pf": _both(lambda d: rc.rolling_profit_factor(sub, dark=d)),
        "pareto": _both(lambda d: rc.profit_concentration(sub, dark=d)),
        "streaks": _both(lambda d: rc.losing_streaks(sub, dark=d)),
    }

    return {
        "scope": "period",
        "title": title, "period_label": period_label, "handle": handle,
        "generated": market_today().isoformat(),
        "source": os.path.basename(meta.get("_csv", "")),
        "s": s, "mtm": mtm, "monthly_stats": ms, "rdist": rdist, "size_stats": ps_stats,
        "by_dir": by_dir, "by_tk": by_tk, "bd": bd, "ce": ce, "cs": cs,
        "charts": charts, "cap": cap,
    }, stem


def build_month_doc(trades, meta, month, full_mtm, out_dir, handle):
    """One month's report. Realized stats scope to trades CLOSED in the month;
    the equity/return come from the MTM curve (which marks positions still open at
    month-end), and open positions are listed + marked to market."""
    cap = meta["startingCapital"]
    eqbd = (full_mtm or {}).get("equity_by_date") or {}
    prices = (full_mtm or {}).get("prices")
    m_days = sorted(d for d in eqbd if d[:7] == month)
    if not m_days:
        return None, None
    m_end = m_days[-1]
    prior = sorted(d for d in eqbd if d < m_days[0])
    prev_eq = eqbd[prior[-1]] if prior else cap
    m_end_eq = eqbd[m_end]

    month_ret = (m_end_eq / prev_eq - 1) * 100 if prev_eq else 0.0
    month_pnl = m_end_eq - prev_eq
    cum_ret = (m_end_eq / cap - 1) * 100

    closed = [t for t in trades if t.exit_date[:7] == month]
    s = pr.overall_stats(closed, cap) if closed else None
    realized = sum(t.pnl for t in closed)

    # intra-month equity slice + its drawdown (base = prev month-end equity)
    month_curve = [(d, eqbd[d]) for d in m_days]
    m_dd = _mtm.drawdown(month_curve)
    month_eqbd = {d: eqbd[d] for d in m_days}

    rdist = pr.r_distribution(closed)
    by_dir = pr.by_key(closed, lambda t: t.direction)
    by_tk = pr.by_key(closed, lambda t: t.ticker)[:10]
    cs = an.trade_case_studies(closed)
    opens = _mtm.open_positions(trades, prices, m_end, m_end_eq) if prices else []

    ps_light, ps_stats = rc.position_sizes(closed, eqbd, cap, dark=False)
    ps_dark, _ = rc.position_sizes(closed, eqbd, cap, dark=True)

    stem = f"monthly_{month}"
    charts = {
        "rr": _rr_pair(closed, cap, out_dir, stem, f"{month} — every trade by R", handle) if len(closed) >= 3 else None,
        "sizes": {"light": ps_light, "dark": ps_dark} if ps_light else None,
        "equity": _both(lambda d: rc.equity_curve(month_eqbd, m_dd, prev_eq, dark=d,
                                                  ylabel="Return (month)")),
        "rdist": _both(lambda d: rc.r_distribution(rdist, dark=d)),
        "deployment": _both(lambda d: rc.deployment_curve(closed, month_eqbd, prev_eq, dark=d)),
        "cases": _both(lambda d: rc.case_studies_grid(cs, load_local_ohlc, dark=d)) if cs else None,
    }

    doc = {
        "scope": "month", "month": month,
        "title": f"{month} · Monthly Review · 月度复盘",
        "period_label": month, "handle": handle,
        "generated": market_today().isoformat(),
        "source": os.path.basename(meta.get("_csv", "")),
        "cap": cap,
        "m": {
            "ret": month_ret, "pnl": month_pnl, "realized": realized, "cum": cum_ret,
            "closed_n": len(closed),
            "win_rate": s["win_rate"] if s else None,
            "payoff": s["payoff"] if s else None,
            "sum_R": s["sum_R"] if s else None,
            "avg_hold": s["avg_hold_days"] if s else None,
            "dd_pct": m_dd["pct"], "dd_peak": m_dd["peak_date"], "dd_trough": m_dd["trough_date"],
            "open_n": len(opens), "end_equity": m_end_eq,
        },
        "opens": opens, "rdist": rdist, "by_dir": by_dir, "by_tk": by_tk, "cs": cs,
        "size_stats": ps_stats, "charts": charts,
    }
    return doc, stem


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
    ap.add_argument("--all-months", action="store_true",
                    help="generate one monthly report per month present in the data")
    args = ap.parse_args()

    csv_path = args.csv or pr.latest_csv(portfolio_dir)
    if not csv_path or not os.path.exists(csv_path):
        raise SystemExit(f"No CSV found in {portfolio_dir}. Pass --csv.")

    trades, meta = pr.parse_csv(csv_path)
    meta["_csv"] = csv_path
    os.makedirs(args.out, exist_ok=True)

    if args.all_months:
        print("· fetching prices for mark-to-market curve …")
        full = pr.compute_mtm(trades, meta)
        if not full:
            raise SystemExit("MTM curve unavailable (needed for monthly reports).")
        months = [d["month"] for d in pr.monthly_stats(trades, full["equity_by_date"], meta["startingCapital"])]
        written = []
        for m in months:
            doc, stem = build_month_doc(trades, meta, m, full, args.out, args.handle)
            if not doc:
                continue
            with open(os.path.join(args.out, f"{stem}.html"), "w") as f:
                f.write(render_html(doc))
            written.append(f"{stem}.html")
            print(f"  ✓ {stem}.html  ({doc['m']['closed_n']} closed · {doc['m']['open_n']} open at month-end)")
        print(f"✓ {len(written)} monthly reports written to {args.out}")
        return

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
