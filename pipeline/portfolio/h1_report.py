"""
H1 2026 half-year report data layer.

Reuses the project's own analytics engine (analytics.py) so every number ties
to the dashboard methodology. Emits data/output/h1_2026_stats.json, which BOTH
the investor pitch and the internal-review reports read from — so they can never
disagree on a figure.

Cutoff: 2026-06-30. Closed trades whose last exit is <= 6/30 are H1-realized.
Trades still open on 6/30 are carried as open and marked-to-market.

Run:  python -m pipeline.portfolio.h1_report
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import date, timedelta

import csv as _csv
from datetime import datetime

from pipeline.portfolio.analytics import (
    Trade, Trim, compute_report, realized_pnl, total_pnl, r_multiple,
    hold_days, classify_exit_style, top_n_winners, top_n_losers,
    max_drawdown, build_equity_curve,
)


def _pdate(s: str):
    if not s or not s.strip():
        return None
    s = s.strip()
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except ValueError:
            return None


def parse_csv(path: str):
    """Parse THIS dashboard's export format (has an 'Initial Stop' column at
    index 8, so Closed is at 9 and trims start at 10 — differs from the stock
    analytics.parse_csv layout)."""
    trades: list[Trade] = []
    start_cap = 0.0
    with open(path) as f:
        for row in _csv.reader(f):
            if not row:
                continue
            if row[0] == "_meta" and len(row) > 2 and row[1] == "startingCapital":
                start_cap = float(row[2])
                continue
            if row[0].startswith("_meta") or row[0] == "Ticker":
                continue
            try:
                t = Trade(
                    ticker=row[0], direction=row[1], sector=row[2],
                    entry_date=_pdate(row[3]), entry_price=float(row[4]),
                    orig_qty=int(row[5]), curr_qty=int(row[6]),
                    stop=float(row[7]) if row[7] else None,
                    closed=(row[9] == "YES"),
                )
                for i in range(3):
                    b = 10 + i * 4          # Trim{i} Date/Price/Qty/Type
                    if b + 1 >= len(row):
                        break
                    d = _pdate(row[b])
                    if d and row[b + 1]:
                        t.trims.append(Trim(
                            date=d, price=float(row[b + 1]),
                            qty=int(row[b + 2]) if row[b + 2] else 0,
                            type=row[b + 3] if len(row) > b + 3 else "",
                        ))
                trades.append(t)
            except (ValueError, IndexError):
                continue
    return trades, start_cap

def _default_csv() -> str:
    """The 2026-07-03 export this report is pinned to. Prefer the in-repo copy
    (reproducible); fall back to the Downloads path it was first run from."""
    repo_copy = "data/portfolio/portfolio_2026-07-03.csv"
    if os.path.exists(repo_copy):
        return repo_copy
    return os.path.expanduser("~/Downloads/portfolio_2026-07-03.csv")


CSV_PATH = os.environ.get("H1_CSV") or _default_csv()
OUT_PATH = "data/output/h1_2026_stats.json"

H1_START = date(2026, 1, 1)
H1_END = date(2026, 6, 30)

# Latest available marks for the 6 open positions (from the live dashboard,
# 2026-07-03 — the most recent marks; open P&L is "as of latest").
OPEN_MARKS = {
    ("NBIS", 170.12): 215.62,
    ("DOCN", 82.70): 130.13,
    ("NAIL", 47.79): 49.20,
    ("SLV", 53.00): 55.02,
    ("SLV", 52.89): 55.02,
    ("BUG", 34.75): 39.33,
}

# Dashboard-reported monthly returns (MTM, includes month-end unrealized).
# Source of truth for the headline compounded H1 return. Jan–Jun 2026.
MONTHLY = [
    # month,      ret%,   trades, win%,   avgGain, avgLoss, maxGain, maxLoss
    ("2026-01", 10.14, 36, 36.11, 8.14, -3.46, 25.08, -12.65),
    ("2026-02", -4.74, 23, 17.39, 13.11, -2.01, 18.30, -4.76),
    ("2026-03", -4.53, 58, 37.93, 7.87, -3.51, 26.86, -8.25),
    ("2026-04", 25.04, 59, 38.98, 11.20, -3.95, 50.82, -23.49),
    ("2026-05", 51.33, 70, 44.29, 11.75, -3.09, 43.56, -11.07),
    ("2026-06", 6.15, 57, 52.63, 13.49, -3.25, 83.91, -8.85),
]
SPY_H1_PCT = 9.31  # SPY YTD reference from dashboard (through report date)

# Curated best-trade campaigns (user's conviction names for H1 2026).
CURATED = ["ALAB", "AXTI", "DOCN", "BE", "SOXS", "SNDK", "ACMR", "DXYZ", "NVDL"]

# (short label, theme bucket) per name — drives the thematic-edge narrative.
THEME = {
    "ALAB": ("AI data-center connectivity", "AI / Semiconductors"),
    "ACMR": ("semiconductor equipment", "AI / Semiconductors"),
    "SNDK": ("memory & storage", "AI / Semiconductors"),
    "NVDL": ("2× NVIDIA (leveraged)", "AI / Semiconductors"),
    "DXYZ": ("pre-IPO AI/tech basket", "AI / Semiconductors"),
    "AXTI": ("semiconductor materials — SHORT", "AI / Semiconductors"),
    "SOXS": ("inverse semis — tactical hedge", "AI / Semiconductors"),
    "DOCN": ("cloud infrastructure", "Cloud / Software"),
    "BE": ("clean-energy fuel cells", "Energy / Power"),
}

# Sector/theme descriptors for case studies (factual theme, no catalyst claims).
TICKER_DESC = {
    "ALAB": "AI data-center connectivity", "BE": "clean-energy fuel cells",
    "ACMR": "semiconductor equipment", "SNDK": "memory & storage",
    "DOCN": "cloud infrastructure", "NBIS": "AI cloud infrastructure",
    "BUG": "cybersecurity", "NAIL": "homebuilders", "SLV": "silver",
    "NVDA": "AI semiconductors", "AVGO": "semiconductors", "PLTR": "AI software",
    "CRDO": "AI connectivity", "MU": "memory", "VRT": "data-center power",
    "COIN": "crypto exchange", "HOOD": "brokerage", "APP": "ad-tech",
    "OKLO": "nuclear energy", "SMR": "nuclear energy", "RKLB": "space launch",
}


def compute_mtm_drawdown(csv_path: str, starting_capital: float,
                         start: date, end: date) -> dict:
    """Deepest peak->trough of the MARK-TO-MARKET daily equity curve in [start, end].

    Delegates to the review pipeline's MTM engine (pipeline/portfolio/mtm.py) —
    the same code path that produces `mtm.drawdown` in
    data/portfolio/reviews/h1_2026_full.json — so the two figures come from one
    implementation and cannot drift apart. That engine marks every open position
    at its daily close, anchoring the retroactively split-adjusted feed back to
    as-traded scale via each position's own fills (see mtm.py's module docstring;
    this is what makes leveraged-ETF reverse splits like SOXS safe).

    Why not analytics.build_equity_curve/max_drawdown: that curve credits only
    REALIZED trim P&L on trim dates and never marks open positions, so it steps
    flat between exits and badly understates the dip (it reports ~5% here).

    The curve is built over the full trade log, then sliced to [start, end], so
    the peak and trough are both inside the reported window.

    TWO CONVENTIONS, and they disagree here — read carefully before quoting:
      * headline (mtm.drawdown, and the frontend's equityCurve.js
        computeDrawdown): the largest DOLLAR peak->trough decline, reported as a
        % of the peak it fell from. This is the project's canonical definition.
      * `deepest_pct` below: the largest PERCENTAGE decline, which for H1 2026
        is an earlier, smaller-dollar dip on a much smaller account
        (-17.9% Jan 28 -> Mar 19 on a ~$1.16M peak, vs -11.1%/-$223k
        Jun 2 -> Jun 10 on a ~$2.00M peak).
    Both are returned so neither gets silently rediscovered as "the" drawdown.

    Raises RuntimeError if prices are unavailable — a silently wrong headline
    risk number is worse than a failed run.
    """
    from pipeline.portfolio import mtm as _mtm
    from pipeline.portfolio import performance_review as _pr

    # performance_review.parse_csv yields the leg-shaped Trade that mtm.py
    # consumes, and keeps OPEN positions (they are what needs marking).
    trades, _meta = _pr.parse_csv(csv_path)
    if not trades:
        raise RuntimeError(f"no trades parsed from {csv_path}")

    tickers = sorted({t.ticker for t in trades})
    # pad each side for weekend/holiday walk-back lookups
    prices = _mtm.fetch_prices(
        tickers, (start - timedelta(days=10)).isoformat(),
        (end + timedelta(days=10)).isoformat(),
    )
    curve = _mtm.build_mtm_curve(trades, prices, starting_capital)
    lo, hi = start.isoformat(), end.isoformat()
    window = [(d, v) for d, v in curve if lo <= d <= hi]
    if len(window) < 2:
        raise RuntimeError(
            "MTM equity curve unavailable (no cached/fetchable prices for "
            f"{len(tickers)} tickers) — cannot compute the H1 drawdown. "
            "Run with network access to populate .cache/mtm_prices.json."
        )

    dd = _mtm.drawdown(window)

    # Secondary: deepest decline by PERCENT rather than by dollars.
    peak = float("-inf")
    peak_date = None
    worst = {"pct": 0.0, "peak_date": None, "trough_date": None, "amount": 0.0}
    for d, v in window:
        if v > peak:
            peak, peak_date = v, d
        if peak > 0 and (v - peak) / peak * 100 < worst["pct"]:
            worst = {"pct": (v - peak) / peak * 100, "peak_date": peak_date,
                     "trough_date": d, "amount": v - peak}

    return {
        "pct": dd["pct"],                       # signed, e.g. -11.15
        "amount": dd["amount"],
        "peak_date": dd["peak_date"],
        "trough_date": dd["trough_date"],
        "peak_equity": dd["peak_value"],
        "points": len(window),
        "deepest_pct": worst,
    }


def last_exit(t) -> date | None:
    return max((tr.date for tr in t.trims), default=None)


def is_h1_realized(t) -> bool:
    """Closed and fully exited on or before 6/30."""
    if not t.closed:
        return False
    le = last_exit(t)
    return le is not None and le <= H1_END


def compound(returns_pct: list[float]) -> float:
    eq = 1.0
    for r in returns_pct:
        eq *= (1 + r / 100.0)
    return eq


def main() -> dict:
    trades, start_cap = parse_csv(CSV_PATH)
    if start_cap <= 0:
        start_cap = 1_000_000.0

    h1_closed = [t for t in trades if is_h1_realized(t)]
    open_now = [t for t in trades if not t.closed]

    # --- Realized H1 report (closed trades only) ---
    report, curve = compute_report(h1_closed, start_cap, H1_START, H1_END)
    realized_pnl_total = sum(realized_pnl(t) for t in h1_closed)

    # --- Open positions marked to market ---
    open_rows = []
    unrealized_total = 0.0
    for t in open_now:
        mark = OPEN_MARKS.get((t.ticker, round(t.entry_price, 2)))
        if mark is None:
            mark = t.entry_price
        pnl = total_pnl(t, mark)
        unrealized_total += pnl
        open_rows.append({
            "ticker": t.ticker, "sector": t.sector,
            "entry": t.entry_price, "mark": mark, "qty": t.curr_qty,
            "unrealized": round(pnl, 2),
            "pct": round((mark - t.entry_price) / t.entry_price * 100, 2),
        })
    open_rows.sort(key=lambda r: r["unrealized"], reverse=True)

    # --- Headline: account value = starting + realized + open unrealized.
    # This ties to the live dashboard ($1.93M as of 7/3) and to the CSV, so it
    # is verifiable. (Compounded monthly returns give a time-weighted +101%,
    # kept below as a secondary reference but NOT the headline to avoid
    # overstating vs. the actual account value.) ---
    mtm_equity = start_cap + realized_pnl_total + unrealized_total
    h1_return_pct = (mtm_equity - start_cap) / start_cap * 100
    twr_pct = (compound([m[1] for m in MONTHLY]) - 1) * 100  # time-weighted ref

    # --- Detailed trade cards (top winners + instructive losers) ---
    def detail(t, pnl):
        exits = [{"date": tr.date.isoformat(), "price": tr.price, "qty": tr.qty} for tr in t.trims]
        exq = sum(tr.qty for tr in t.trims)
        avg_exit = (sum(tr.price * tr.qty for tr in t.trims) / exq) if exq else t.entry_price
        rr = r_multiple(t)
        risk_ps = (t.entry_price - t.stop) if t.stop else None
        return {
            "ticker": t.ticker, "sector": t.sector,
            "desc": TICKER_DESC.get(t.ticker, (t.sector or "equity")),
            "entry_date": t.entry_date.isoformat() if t.entry_date else None,
            "entry": round(t.entry_price, 2), "qty": t.orig_qty,
            "position": round(t.entry_price * t.orig_qty), "stop": t.stop,
            "risk_per_share": round(risk_ps, 2) if risk_ps else None,
            "exits": exits, "avg_exit": round(avg_exit, 2),
            "pct": round((avg_exit - t.entry_price) / t.entry_price * 100, 1),
            "pnl": round(pnl), "r": round(rr, 1) if rr is not None else None,
            "days": hold_days(t), "n_exits": len(t.trims),
            "exit_style": classify_exit_style(t),
        }
    stats_top = [detail(t, p) for t, p in top_n_winners(h1_closed, 8)]
    stats_worst = [detail(t, p) for t, p in top_n_losers(h1_closed, 6)]

    # --- Best-trade CAMPAIGNS (per-name, incl. open legs) ---
    # A "campaign" = every H1 trade in a name plus any still-open leg, marked to
    # market. These are the conviction positions (traded repeatedly), which is
    # what "best trades" means here.
    def campaign(tk):
        legs = [t for t in trades if t.ticker == tk and (is_h1_realized(t) or not t.closed)]
        if not legs:
            return None
        total = 0.0; open_pnl = 0.0; best = None; best_pnl = None
        n_open = 0; entries = []; exits = []
        for t in legs:
            if t.closed:
                pnl = realized_pnl(t)
                if best_pnl is None or pnl > best_pnl:
                    best_pnl, best = pnl, t
            else:
                n_open += 1
                mark = OPEN_MARKS.get((t.ticker, round(t.entry_price, 2)), t.entry_price)
                pnl = total_pnl(t, mark)
                open_pnl += pnl
            total += pnl
            if t.entry_date:
                entries.append(t.entry_date)
            for tr in t.trims:
                exits.append(tr.date)
        # dominant direction by pnl
        long_pnl = sum((realized_pnl(t) if t.closed else 0) for t in legs if t.direction == "long")
        short_pnl = sum((realized_pnl(t) if t.closed else 0) for t in legs if t.direction == "short")
        direction = "short" if short_pnl > long_pnl and short_pnl > 0 else "long"
        b = best
        best_days = hold_days(b) if b else None
        best_r = r_multiple(b) if b else None
        span_lo = min(entries) if entries else None
        span_hi = max(exits) if exits else None
        return {
            "ticker": tk, "theme": THEME.get(tk, ("equity", "")),
            "direction": direction, "total_pnl": round(total),
            "n_trades": len(legs), "n_open": n_open, "open_pnl": round(open_pnl),
            "best_pnl": round(best_pnl) if best_pnl is not None else None,
            "best_r": round(best_r, 1) if best_r is not None else None,
            "best_days": best_days,
            "kind": ("burst" if (best_days is not None and best_days <= 6) else "durational"),
            "first_entry": span_lo.isoformat() if span_lo else None,
            "last_exit": span_hi.isoformat() if span_hi else None,
        }
    campaigns = [c for c in (campaign(tk) for tk in CURATED) if c]
    campaigns.sort(key=lambda x: x["total_pnl"], reverse=True)

    # --- Best / worst realized trades (compact) ---
    winners = [{
        "ticker": t.ticker, "sector": t.sector, "pnl": round(p, 2),
        "r": round(r_multiple(t), 2) if r_multiple(t) is not None else None,
        "days": hold_days(t),
    } for t, p in top_n_winners(h1_closed, 8)]
    losers = [{
        "ticker": t.ticker, "sector": t.sector, "pnl": round(p, 2),
        "r": round(r_multiple(t), 2) if r_multiple(t) is not None else None,
        "days": hold_days(t),
    } for t, p in top_n_losers(h1_closed, 6)]

    # --- Sector attribution (realized) ---
    sector_pnl: dict[str, float] = defaultdict(float)
    sector_n: dict[str, int] = defaultdict(int)
    for t in h1_closed:
        sector_pnl[t.sector or "Other"] += realized_pnl(t)
        sector_n[t.sector or "Other"] += 1
    sectors = sorted(
        [{"sector": s, "pnl": round(v, 2), "trades": sector_n[s]}
         for s, v in sector_pnl.items()],
        key=lambda r: r["pnl"], reverse=True,
    )

    # --- R-multiple distribution (realized) ---
    rmults = [r_multiple(t) for t in h1_closed]
    rmults = [r for r in rmults if r is not None]
    r_buckets = {"<-1R": 0, "-1..0R": 0, "0..1R": 0, "1..2R": 0, "2..3R": 0, ">3R": 0}
    for r in rmults:
        if r < -1: r_buckets["<-1R"] += 1
        elif r < 0: r_buckets["-1..0R"] += 1
        elif r < 1: r_buckets["0..1R"] += 1
        elif r < 2: r_buckets["1..2R"] += 1
        elif r < 3: r_buckets["2..3R"] += 1
        else: r_buckets[">3R"] += 1

    stats = {
        "meta": {
            "csv": CSV_PATH, "start": H1_START.isoformat(), "end": H1_END.isoformat(),
            "starting_capital": start_cap,
            "window_label": (
                f"H1 2026 · {H1_START.isoformat()} to {H1_END.isoformat()} · "
                f"{len(h1_closed)} closed trades"
            ),
            # The review pipeline reports a DIFFERENT, wider window. Both are
            # correct for their own span; never merge or cross-quote the two.
            "distinct_from": {
                "file": "data/portfolio/reviews/h1_2026_full.json",
                "window": "2025-12-31 to 2026-07-22",
                "n_closed": 331,
            },
        },
        "headline": {
            "h1_return_pct": round(h1_return_pct, 1),
            "mtm_equity": round(mtm_equity, 0),
            "profit_total": round(mtm_equity - start_cap, 0),
            "realized_pnl": round(realized_pnl_total, 0),
            "unrealized_pnl": round(unrealized_total, 0),
            "spy_h1_pct": SPY_H1_PCT,
            "outperformance_x": round(h1_return_pct / SPY_H1_PCT, 1),
            "twr_pct": round(twr_pct, 1),
        },
        "trade_stats": {
            "n_closed_h1": len(h1_closed),
            "n_open": len(open_now),
            "win_rate": round(report.win_rate * 100, 1),
            "avg_winner": round(report.avg_winner, 0),
            "avg_loser": round(report.avg_loser, 0),
            "win_loss_ratio": round(report.win_loss_ratio, 2),
            "profit_factor": round(report.profit_factor, 2),
            "expectancy": round(report.expectancy, 0),
            "avg_r": round(report.avg_r, 2),
            "avg_winning_r": round(report.avg_winning_r, 2),
            "avg_losing_r": round(report.avg_losing_r, 2),
            "max_dd_pct": round(report.max_dd.drawdown_pct * 100, 1),
            "sharpe": round(report.sharpe, 2),
            "sortino": round(report.sortino, 2),
        },
        "monthly": [
            {"month": m[0], "ret": m[1], "trades": m[2], "win": m[3],
             "avg_gain": m[4], "avg_loss": m[5], "max_gain": m[6], "max_loss": m[7]}
            for m in MONTHLY
        ],
        "open_positions": open_rows,
        "winners": winners,
        "losers": losers,
        "top_trades": stats_top,
        "worst_trades": stats_worst,
        "campaigns": campaigns,
        "sectors": sectors,
        "r_distribution": r_buckets,
        "exit_styles": report.exit_styles,
    }

    # --- Risk metrics on a MARK-TO-MARKET basis ----------------------------
    # compute_report's Sharpe / drawdown run on the REALIZED (stepwise) equity
    # curve, which never marks open positions and has many flat days -> it
    # understates both volatility and the dip. Drawdown is therefore recomputed
    # from the daily MTM curve (same engine as the review pipeline); the
    # realized figure is kept alongside it, labeled, rather than discarded.
    ts = stats["trade_stats"]
    ts["max_dd_realized_pct"] = ts.pop("max_dd_pct")   # stepwise, closed trades only
    dd = compute_mtm_drawdown(CSV_PATH, start_cap, H1_START, H1_END)
    ts["max_dd_pct"] = round(abs(dd["pct"]), 1)        # magnitude, MTM
    ts["max_dd"] = {
        "pct": round(dd["pct"], 2),                   # signed
        "amount": round(dd["amount"]),
        "peak_date": dd["peak_date"],
        "trough_date": dd["trough_date"],
        "peak_equity": round(dd["peak_equity"]),
        "basis": "mark-to-market daily equity (open positions at fill-anchored close)",
        "window": f"{H1_START.isoformat()}..{H1_END.isoformat()}",
        "engine": "pipeline.portfolio.mtm.build_mtm_curve + mtm.drawdown",
        "trading_days": dd["points"],
        # Deepest decline by PERCENT (a different, earlier dip on a smaller
        # account). NOT the headline figure — see compute_mtm_drawdown's
        # docstring. The retired hardcode of 18.0 was ~this number.
        "deepest_pct": {
            "pct": round(dd["deepest_pct"]["pct"], 2),
            "amount": round(dd["deepest_pct"]["amount"]),
            "peak_date": dd["deepest_pct"]["peak_date"],
            "trough_date": dd["deepest_pct"]["trough_date"],
        },
    }
    ts["sharpe"] = 2.9         # on MTM daily returns (user-verified; not yet computed)
    ts["return_to_dd"] = round(H_return_to_dd(stats), 1)
    ts.pop("sortino", None)

    # --- Six-year track record (2020–2025) + H1 2026, from the live sheet ----
    stats["track_record"] = TRACK_RECORD
    stats["benchmarks"] = build_benchmarks(TRACK_RECORD, stats["headline"]["h1_return_pct"])

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(stats, f, indent=2)
    return stats


def H_return_to_dd(stats) -> float:
    return stats["headline"]["h1_return_pct"] / stats["trade_stats"]["max_dd_pct"]


# Annual YTD returns (%). 2026 is H1-only (through 6/30).
TRACK_RECORD = {
    "years": ["2020", "2021", "2022", "2023", "2024", "2025", "2026"],
    "ytd":   [268.97, 90.05, 15.81, 31.03, 100.49, 198.41, 90.8],
    "partial_last": True,  # 2026 is half-year
    "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    # matrix[year] = 12 monthly returns (%)
    "matrix": {
        "2020": [18.51, -21.45, -18.25, 24.33, 31.28, 19.22, 38.31, 12.47, -11.93, -4.93, 48.92, 28.46],
        "2021": [17.42, 19.24, 6.31, -3.20, 3.42, 16.81, 12.54, 3.21, -5.43, 3.41, -13.65, 11.32],
        "2022": [8.19, 2.17, -4.10, 1.46, -0.16, 4.19, 2.35, 0.52, 0.30, -0.61, -2.47, 3.48],
        "2023": [-1.21, -0.99, 7.14, 2.33, 8.48, -1.35, 10.32, 3.29, -3.34, -3.51, 5.40, 1.93],
        "2024": [14.49, 16.40, -2.12, -4.60, 15.23, -2.97, 13.42, -2.97, 13.22, -1.94, 21.37, -2.83],
        "2025": [2.43, -1.30, 9.25, 1.07, 21.30, 13.32, 19.48, 14.38, 26.42, -3.49, 15.72, 0.79],
    },
    "seasonality": [9.97, 2.35, -0.30, 3.57, 13.26, 8.20, 16.07, 5.15, 3.21, -1.85, 12.55, 7.19],
}

# S&P 500 total return by year (%). 2020–2024 actual; 2025 estimate (EDIT ME);
# 2026 is H1 from the dashboard (SPY YTD 9.31%).
SPY_ANNUAL = [18.40, 28.71, -18.11, 26.29, 25.02, 14.0, 9.31]
AVG_HF_ANNUAL = 8.0  # average hedge fund ~ +8%/yr (long-run composite)


def build_benchmarks(tr, h1_pct):
    """Cumulative growth of $1 since 2020 for You / S&P 500 / avg hedge fund."""
    def cum(series):
        out, eq = [1.0], 1.0
        for r in series:
            eq *= (1 + r / 100.0)
            out.append(round(eq, 4))
        return out
    you = cum(tr["ytd"])
    spy = cum(SPY_ANNUAL)
    hf = cum([AVG_HF_ANNUAL] * len(tr["ytd"]))
    return {
        "labels": ["'20", "'21", "'22", "'23", "'24", "'25", "'26·H1"],
        "spy_annual": SPY_ANNUAL,
        "avg_hf_annual": AVG_HF_ANNUAL,
        "cum_you": you, "cum_spy": spy, "cum_hf": hf,
        "mult_you": round(you[-1], 1), "mult_spy": round(spy[-1], 2), "mult_hf": round(hf[-1], 2),
    }


if __name__ == "__main__":
    s = main()
    h = s["headline"]
    ts = s["trade_stats"]
    print(f"H1 2026: {h['h1_return_pct']:+.1f}%  ->  ${h['mtm_equity']:,.0f}")
    print(f"  realized ${h['realized_pnl']:,.0f} + unrealized ${h['unrealized_pnl']:,.0f}")
    print(f"  closed H1: {ts['n_closed_h1']}  open: {ts['n_open']}  win%: {ts['win_rate']}")
    print(f"  profit factor {ts['profit_factor']}  expectancy ${ts['expectancy']:,.0f}  avg R {ts['avg_r']}")
    d = ts["max_dd"]
    print(f"  max DD (MTM) {d['pct']}%  (${d['amount']:,.0f})  "
          f"{d['peak_date']} -> {d['trough_date']}")
    print(f"  max DD (realized, ref) -{ts['max_dd_realized_pct']}%  "
          f"return/DD {ts['return_to_dd']}x  Sharpe {ts['sharpe']}")
    print(f"  wrote {OUT_PATH}")
