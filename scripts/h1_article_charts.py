#!/usr/bin/env python3
"""Standalone PNGs for the H1 flagship letter.

The HTML report embeds its charts as base64, which is useless for Substack --
that needs image files to upload. This renders the three the letter actually
uses, light-theme, at upload resolution:

    equity vs SPY vs QQQ  ·  R distribution  ·  monthly returns

    python scripts/h1_article_charts.py

Benchmarks come from IBKR (house rule: never TradingView), fetched through the
same path as scripts/benchmark_window.py and cached to JSON so re-runs don't
need TWS running.
"""
import datetime as dt
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.portfolio.performance_review import compute_mtm, parse_csv  # noqa: E402

CSV = Path("data/portfolio/portfolio_2026-07-26.csv")
if not CSV.exists():
    CSV = Path.home() / "Downloads" / "portfolio_2026-07-26.csv"
OUT = Path("Fluxus_Substack/assets")
BENCH_CACHE = OUT / "benchmarks_h1_2026.json"
START, END = "2025-12-31", "2026-07-22"

INK = "#111418"
MUTED = "#8b9199"
GRID = "#e6e8ec"
YOU = "#111418"
SPY_C = "#9aa1aa"
QQQ_C = "#c8804a"
LOSS = "#c0523f"
WIN = "#3f7d5a"


def style(ax):
    ax.set_facecolor("white")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {path}")


def benchmarks(dates):
    """{ticker: {date: close}} for SPY/QQQ, from cache or IBKR."""
    if BENCH_CACHE.exists():
        return json.loads(BENCH_CACHE.read_text())
    from ib_async import IB, Stock
    ib, last = IB(), None
    for port in (7496, 7497, 4001, 4002):
        for cid in (12, 13, 14, 15):
            try:
                ib.connect("127.0.0.1", port, clientId=cid, timeout=8)
                last = None
                break
            except Exception as exc:  # noqa: BLE001
                last = exc
                if "refused" in str(exc).lower():
                    break
        if last is None:
            break
    if last is not None:
        raise SystemExit(f"no IBKR connection (needed once to seed {BENCH_CACHE}): {last}")
    out = {}
    end = dt.date.fromisoformat(max(dates)) + dt.timedelta(days=1)
    for tk in ("SPY", "QQQ"):
        c = Stock(tk, "SMART", "USD")
        ib.qualifyContracts(c)
        bars = ib.reqHistoricalData(
            c, endDateTime=f"{end:%Y%m%d} 23:59:59 US/Eastern", durationStr="9 M",
            barSizeSetting="1 day", whatToShow="TRADES", useRTH=True,
            formatDate=1, timeout=90)
        out[tk] = {str(b.date): b.close for b in bars}
        ib.sleep(3)
    ib.disconnect()
    OUT.mkdir(parents=True, exist_ok=True)
    BENCH_CACHE.write_text(json.dumps(out))
    return out


def rebase(closes, dates):
    """Benchmark rebased to 0% on the first date, forward-filled onto `dates`."""
    keys = sorted(closes)
    base, out, last = None, [], None
    for d in dates:
        prior = [k for k in keys if k <= d]
        if prior:
            last = closes[prior[-1]]
        if last is None:
            out.append(0.0)
            continue
        if base is None:
            base = last
        out.append((last / base - 1) * 100)
    return out


def chart_equity(equity, cap, dd, bench):
    dates = sorted(equity)
    you = [(equity[d] / cap - 1) * 100 for d in dates]
    xs = [dt.date.fromisoformat(d) for d in dates]

    fig, ax = plt.subplots(figsize=(10, 5.2))
    style(ax)
    if dd and dd.get("peak_date") and dd.get("trough_date"):
        ax.axvspan(dt.date.fromisoformat(dd["peak_date"]),
                   dt.date.fromisoformat(dd["trough_date"]),
                   color="#f2d9d4", alpha=0.75, lw=0, zorder=0)
    ax.plot(xs, rebase(bench["SPY"], dates), color=SPY_C, lw=1.6, label="SPY")
    ax.plot(xs, rebase(bench["QQQ"], dates), color=QQQ_C, lw=1.6, label="QQQ")
    ax.plot(xs, you, color=YOU, lw=2.4, label="The account")
    ax.axhline(0, color=GRID, lw=1)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:+.0f}%"))
    ax.legend(frameon=False, loc="upper left", fontsize=10, labelcolor=INK)
    ax.set_title("Same seven months, three lines",
                 color=INK, fontsize=13, loc="left", pad=14)
    if dd:
        ax.annotate(f"−{abs(dd['pct']):.1f}% drawdown",
                    xy=(dt.date.fromisoformat(dd["trough_date"]), max(you) * 0.62),
                    color=LOSS, fontsize=9, ha="center")
    save(fig, "h1_equity_vs_benchmarks.png")


def r_buckets(trades):
    """Strict boundaries, so the chart matches the letter's prose.

    The review JSON's `-2R..-1R` bucket is inclusive at -1R, which sweeps in the
    11 trades that stopped at exactly -1R and makes "worse than -1R" read as 42.
    Those 11 are stops that worked, not stops that failed -- they belong on the
    -1R..0 side. Cutting strictly at r < -1 gives the 31 that actually overran.
    """
    rs = [t.R for t in trades if t.R is not None]
    edges = [(-1e9, -2), (-2, -1), (-1, 0), (0, 1), (1, 2), (2, 3), (3, 1e9)]
    return [sum(1 for r in rs if lo <= r < hi) for lo, hi in edges]


def chart_r(vals):
    labels = ["worse than\n−2R", "−2R..−1R", "−1R..0", "0..1R", "1R..2R", "2R..3R", "≥ 3R"]
    colors = [LOSS] * 3 + [WIN] * 4
    fig, ax = plt.subplots(figsize=(10, 4.4))
    style(ax)
    bars = ax.bar(labels, vals, color=colors, width=0.62)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 2, str(v),
                ha="center", color=INK, fontsize=10)
    ax.set_ylim(0, max(vals) * 1.18)
    ax.set_title("Where 331 trades actually landed",
                 color=INK, fontsize=13, loc="left", pad=14)
    save(fig, "h1_r_distribution.png")


def chart_monthly(monthly):
    months = sorted(monthly)
    pnl = [monthly[m]["pnl"] for m in months]
    labels = [dt.date.fromisoformat(m + "-01").strftime("%b") for m in months]
    fig, ax = plt.subplots(figsize=(10, 4.4))
    style(ax)
    bars = ax.bar(labels, [p / 1000 for p in pnl],
                  color=[WIN if p >= 0 else LOSS for p in pnl], width=0.62)
    for b, p in zip(bars, pnl):
        ax.text(b.get_x() + b.get_width() / 2, p / 1000 + 6,
                f"{p/1000:+.0f}k", ha="center", color=INK, fontsize=10)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:+.0f}k"))
    ax.set_ylim(min(0, min(pnl) / 1000) - 20, max(pnl) / 1000 * 1.2)
    ax.set_title("Realized P&L by month — the year is April through June",
                 color=INK, fontsize=13, loc="left", pad=14)
    save(fig, "h1_monthly_pnl.png")


def main():
    trades, meta = parse_csv(str(CSV))
    cap = meta["startingCapital"]
    mtm = compute_mtm(trades, meta)
    if not mtm:
        raise SystemExit("mtm curve unavailable (needs price data)")
    equity = {d: v for d, v in mtm["equity_by_date"].items() if START <= d <= END}
    full = json.loads(Path("data/portfolio/reviews/h1_2026_full.json").read_text())

    chart_equity(equity, cap, full["mtm"]["drawdown"], benchmarks(sorted(equity)))
    chart_r(r_buckets(trades))
    chart_monthly(full["monthly"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
