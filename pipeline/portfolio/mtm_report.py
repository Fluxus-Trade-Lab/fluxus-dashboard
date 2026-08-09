"""Mark-to-market performance report (real daily prices).

Wires the cached yfinance OHLC fetcher (`ohlc_cache`) into the pure-stdlib
mark-to-market curve builder in `analytics`, so the headline return, drawdown
and risk numbers reconcile with the live Fluxus dashboard (which marks every
open position at its real daily close — see equityCurve.js).

It also reports an INTRADAY drawdown envelope using each bar's High/Low, which
the close-based dashboard curve cannot show.

Run:
    python -m pipeline.portfolio.mtm_report                       # latest CSV
    python -m pipeline.portfolio.mtm_report --csv path/to.csv --end 2026-06-03
"""
from __future__ import annotations

import argparse
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import pstdev
from typing import Optional

from pipeline.marketcal import market_today
from pipeline.portfolio import analytics as A
from pipeline.portfolio.ohlc_cache import fetch_ohlc
from pipeline.portfolio.trade_parser import Trade as RawTrade, find_latest_csv, parse_csv

logger = logging.getLogger(__name__)

_WALK_BACK_DAYS = 10  # mirror equityCurve.js lookupPrice


# ── price provider ──────────────────────────────────────────────────────────

class PriceCache:
    """Daily OHLC lookup backed by `ohlc_cache.fetch_ohlc`.

    Builds an in-memory {ticker: {iso_date: (close, low, high)}} map and serves
    `get(ticker, day, field)` with up to 10-day walk-back to the last known bar
    (matching the dashboard's lookupPrice). Returns None when nothing is found
    in the window so the curve builder can fall back to entry price.
    """

    def __init__(self, tickers: list[str], start: date, end: date):
        self._px: dict[str, dict[str, tuple[float, float, float]]] = {}
        self.missing: list[str] = []
        for tk in sorted(set(tickers)):
            df = fetch_ohlc(tk, start, end)
            if df is None or df.empty:
                self.missing.append(tk)
                continue
            table: dict[str, tuple[float, float, float]] = {}
            for ts, row in df.iterrows():
                table[ts.date().isoformat()] = (
                    float(row["Close"]), float(row["Low"]), float(row["High"])
                )
            self._px[tk] = table

    def get(self, ticker: str, day: date, field: str) -> Optional[float]:
        table = self._px.get(ticker)
        if not table:
            return None
        idx = {"close": 0, "low": 1, "high": 2}[field]
        for back in range(_WALK_BACK_DAYS):
            key = (day - timedelta(days=back)).isoformat()
            hit = table.get(key)
            if hit is not None:
                return hit[idx]
        return None


# ── trade adapter ───────────────────────────────────────────────────────────

def _to_analytics_trade(t: RawTrade) -> A.Trade:
    """Convert the parser's Trade to the analytics Trade model.

    Uses initial_stop (locked at entry) as the R denominator stop, consistent
    with the rest of the analytics report.
    """
    return A.Trade(
        ticker=t.ticker,
        direction=t.direction,
        sector=t.sector,
        entry_date=t.entry_date,
        entry_price=t.entry_price,
        orig_qty=t.original_qty,
        curr_qty=t.current_qty,
        stop=t.initial_stop,
        closed=t.closed,
        trims=[A.Trim(date=tr.date, price=tr.price, qty=tr.qty, type=tr.type)
               for tr in t.trims],
    )


def _starting_capital(csv_path: Path, default: float = 1_000_000.0) -> float:
    for line in csv_path.read_text().splitlines()[:5]:
        if line.startswith("_meta,startingCapital,"):
            try:
                return float(line.split(",")[2])
            except (IndexError, ValueError):
                break
    return default


# ── public API ──────────────────────────────────────────────────────────────

def build_mtm_curve(
    csv_path: Path,
    end_date: date,
    starting_capital: Optional[float] = None,
) -> tuple[list[A.MTMEquityPoint], list[A.Trade], float, PriceCache]:
    """Parse the CSV, fetch prices, and build the daily MTM curve.

    Returns (curve, analytics_trades, starting_capital, price_cache).
    """
    raw = parse_csv(csv_path)
    trades = [_to_analytics_trade(t) for t in raw]
    cap = starting_capital if starting_capital is not None else _starting_capital(csv_path)

    start = min(t.entry_date for t in trades)
    prices = PriceCache([t.ticker for t in trades], start, end_date)
    if prices.missing:
        logger.warning(
            "No OHLC for %d tickers (falling back to entry price): %s",
            len(prices.missing), prices.missing,
        )

    curve = A.build_mtm_equity_curve(trades, cap, start, end_date, prices.get)
    return curve, trades, cap, prices


# ── CLI report ──────────────────────────────────────────────────────────────

def _print_report(curve, trades, cap, end_date):
    eq = [p.equity for p in curve]
    ret = (eq[-1] / cap - 1) * 100

    close_dd = A.max_drawdown(curve)
    intra_dd = A.max_intraday_drawdown(curve)
    rets = A.daily_returns(curve)
    sharpe = A.sharpe_ratio(rets)
    sortino = A.sortino_ratio(rets)
    ann_vol = pstdev(rets) * (252 ** 0.5) * 100 if len(rets) > 1 else 0.0
    sma20 = A.sma(eq, 20)

    print("=" * 72)
    print(f"MARK-TO-MARKET REPORT — real daily OHLC — through {end_date}")
    print("=" * 72)
    print(f"\n  Starting capital:  ${cap:,.0f}")
    print(f"  Ending equity:     ${eq[-1]:,.0f}")
    print(f"  Total return:      {ret:+.2f}%")
    peak_i = eq.index(max(eq))
    print(f"  Peak equity:       ${max(eq):,.0f}  on {curve[peak_i].date}")

    print("\n── DRAWDOWN ──")
    print(f"  Close-to-close:    {close_dd.drawdown_pct*100:.2f}%   "
          f"{curve[close_dd.peak_idx].date} → {curve[close_dd.trough_idx].date}  "
          f"(rec {curve[close_dd.recovery_idx].date if close_dd.recovery_idx else 'open'})")
    print(f"  Intraday envelope: {intra_dd.drawdown_pct*100:.2f}%   "
          f"{curve[intra_dd.peak_idx].date} → {curve[intra_dd.trough_idx].date}  "
          f"(longs@low / shorts@high — conservative)")

    print("\n── RISK-ADJUSTED (calendar daily MTM, n={}) ──".format(len(rets)))
    print(f"  Annualized vol:    {ann_vol:.1f}%")
    print(f"  Sharpe:            {sharpe:.2f}")
    print(f"  Sortino:           {sortino:.2f}")
    cal = ret / (close_dd.drawdown_pct * 100) if close_dd.drawdown_pct > 0 else 0
    print(f"  Calmar:            {cal:.2f}")

    print("\n── EQUITY vs 20-DAY SMA ──")
    ls = sma20[-1]
    if ls:
        print(f"  Final: equity ${eq[-1]:,.0f} vs 20SMA ${ls:,.0f} "
              f"({(eq[-1]-ls)/ls*100:+.2f}%)")
    below = sum(1 for i in range(max(0, len(eq) - 60), len(eq))
                if sma20[i] is not None and eq[i] < sma20[i])
    print(f"  Last 60 trading days below 20SMA: {below}")

    print("\n── DRAWDOWNS ≥ 3% (close basis) ──")
    for w in A.find_drawdown_windows(curve, min_dd=0.03):
        rec = curve[w.recovery_idx].date if w.recovery_idx is not None else "open"
        print(f"  {w.drawdown_pct*100:>5.2f}%  {curve[w.peak_idx].date} → "
              f"{curve[w.trough_idx].date}  (${w.peak_equity:,.0f} → "
              f"${w.trough_equity:,.0f})  rec={rec}")


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", type=Path, default=None,
                    help="portfolio CSV (defaults to latest in data/portfolio)")
    ap.add_argument("--end", type=str, default=None,
                    help="end date YYYY-MM-DD (defaults to today)")
    ap.add_argument("--capital", type=float, default=None,
                    help="override starting capital")
    args = ap.parse_args(argv)

    csv_path = args.csv or find_latest_csv()
    if csv_path is None or not Path(csv_path).exists():
        ap.error("no CSV found — pass --csv")
    end_date = (datetime.strptime(args.end, "%Y-%m-%d").date()
                if args.end else market_today())

    curve, trades, cap, _ = build_mtm_curve(Path(csv_path), end_date, args.capital)
    _print_report(curve, trades, cap, end_date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
