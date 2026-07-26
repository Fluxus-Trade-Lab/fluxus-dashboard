#!/usr/bin/env python3
"""Mark-to-market daily equity curve + drawdown / risk ratios.

The reporting-standard drawdown is peak-to-trough of the END-OF-DAY
mark-to-market equity (cash + open positions marked at the day's close), which
`performance_review.py`'s realized-only figure understates.

Split robustness (important): the price feed is retroactively split-adjusted and
split feeds (incl. yfinance `.splits`) are UNRELIABLE for frequently-splitting
leveraged ETFs — e.g. yfinance misses a ~1:18 SOXS split on 2026-05-26, leaving a
huge discontinuity in the "adjusted" close. So we do NOT trust any split list.
Instead each position's daily marks are anchored to its OWN as-traded fills:
    correction(ticker, era) = median(fill_price / adjusted_close_on_fill_date)
grouped into eras that break on >30% jumps (a split). Multiplying an era's
adjusted closes by this constant restores the as-traded scale while preserving
real day-to-day returns. Self-contained from the trade log; immune to bad splits.

Requires yfinance + pandas + numpy. Fetches are cached to `.cache/mtm_prices.json`.
"""
from __future__ import annotations

import json
import os
from statistics import median

CACHE_PATH = ".cache/mtm_prices.json"


def fetch_prices(tickers, start, end, cache_path=CACHE_PATH):
    """{ticker: {'close': {date: adjClose}}} via yfinance (auto_adjust=False).

    Cached; only missing tickers are fetched. Returns {} if yfinance unavailable.
    """
    cache = {}
    if os.path.exists(cache_path):
        try:
            cache = json.load(open(cache_path))
        except (ValueError, OSError):
            cache = {}
    need = [t for t in tickers if t not in cache]
    if need:
        try:
            import warnings
            warnings.filterwarnings("ignore")
            import yfinance as yf
        except ImportError:
            return cache
        try:
            df = yf.download(need, start=start, end=end, auto_adjust=False,
                             actions=False, group_by="ticker", progress=False, threads=True)
        except Exception:  # noqa: BLE001 — network/parse failures shouldn't crash a review
            return cache
        for t in need:
            try:
                sub = df[t] if len(need) > 1 else df
                close = sub["Close"].dropna()
                cache[t] = {"close": {str(d.date()): float(v) for d, v in close.items()}}
            except Exception:  # noqa: BLE001
                cache[t] = {"close": {}}
        try:
            os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
            json.dump(cache, open(cache_path, "w"))
        except OSError:
            pass
    return cache


def _adj_close(prices, tk, date):
    """Adjusted close on `date`, walking back up to 6 days for weekends/holidays."""
    import datetime as dt
    closes = prices.get(tk, {}).get("close", {})
    d = dt.date.fromisoformat(date)
    for back in range(7):
        k = (d - dt.timedelta(days=back)).isoformat()
        if k in closes:
            return closes[k]
    return None


def _build_corrections(trades, prices):
    """Per-ticker era list: [{start,end,factor}] from fill/adjusted anchoring."""
    fills = {}
    for t in trades:
        pts = [(t.entry_date, t.entry)] + [(lg.date, lg.price) for lg in t.legs]
        for d, px in pts:
            a = _adj_close(prices, t.ticker, d)
            if a and a > 0 and px and px > 0:
                fills.setdefault(t.ticker, []).append((d, px / a))
    eras_by_tk = {}
    for tk, pts in fills.items():
        pts.sort()
        eras = []
        for d, f in pts:
            if eras:
                m = median(eras[-1]["factors"])
                if abs(f - m) / m < 0.30:
                    eras[-1]["factors"].append(f)
                    eras[-1]["end"] = d
                    continue
            eras.append({"start": d, "end": d, "factors": [f]})
        for e in eras:
            e["factor"] = median(e["factors"])
        eras_by_tk[tk] = eras
    return eras_by_tk


def _correction(eras_by_tk, tk, date):
    import datetime as dt
    eras = eras_by_tk.get(tk)
    if not eras:
        return 1.0
    for e in eras:
        if e["start"] <= date <= e["end"]:
            return e["factor"]
    d = dt.date.fromisoformat(date)
    best = min(eras, key=lambda e: min(
        abs((d - dt.date.fromisoformat(e["start"])).days),
        abs((d - dt.date.fromisoformat(e["end"])).days)))
    return best["factor"]


def build_mtm_curve(trades, prices, starting_capital):
    """EOD mark-to-market equity curve: [(date, equity)] over business days.

    equity(D) = capital + realized_to_date(D) + open_unrealized(D), with open
    positions marked at fill-anchored as-traded close. Returns [] if no prices.
    """
    import datetime as dt
    if not trades or not prices:
        return []
    eras = _build_corrections(trades, prices)

    dmin = min(t.entry_date for t in trades)
    dmax = max((lg.date for t in trades for lg in t.legs), default=dmin)

    # business days dmin..dmax
    days = []
    d = dt.date.fromisoformat(dmin)
    end = dt.date.fromisoformat(dmax)
    while d <= end:
        if d.weekday() < 5:
            days.append(d.isoformat())
        d += dt.timedelta(days=1)

    curve = []
    for ds in days:
        realized = 0.0
        unreal = 0.0
        for t in trades:
            if t.entry_date > ds:
                continue
            sign = 1 if t.direction == "long" else -1
            sold = 0.0
            for lg in t.legs:
                if lg.date <= ds:
                    realized += sign * (lg.price - t.entry) * lg.qty
                    sold += lg.qty
            held = t.orig_qty - sold
            if held > 0.5:
                a = _adj_close(prices, t.ticker, ds)
                if a is not None:
                    c = a * _correction(eras, t.ticker, ds)
                    unreal += sign * (c - t.entry) * held
        curve.append((ds, starting_capital + realized + unreal))
    return curve


def drawdown(curve):
    """Max peak-to-trough drawdown on an [(date, value)] curve."""
    peak = float("-inf")
    peak_date = None
    mdd = 0.0
    mdd_pct = 0.0
    trough_date = None
    at_peak = None
    peak_at_mdd = None
    for ds, v in curve:
        if v > peak:
            peak = v
            peak_date = ds
        if peak <= 0:
            continue
        dd = v - peak
        if dd < mdd:
            mdd = dd
            mdd_pct = dd / peak * 100
            trough_date = ds
            at_peak = peak_date
            peak_at_mdd = peak
    return {"amount": mdd, "pct": mdd_pct, "peak_date": at_peak,
            "trough_date": trough_date, "peak_value": peak_at_mdd}


def risk_ratios(curve, starting_capital, risk_free=0.04, ppy=252):
    """Sharpe / Sortino / Calmar / CAGR / annualized vol from the daily curve."""
    vals = [v for _, v in curve]
    if len(vals) < 3:
        return {}
    rets = [vals[i] / vals[i - 1] - 1 for i in range(1, len(vals)) if vals[i - 1] > 0]
    n = len(rets)
    mean = sum(rets) / n
    var = sum((r - mean) ** 2 for r in rets) / (n - 1)
    sd = var ** 0.5
    down = (sum(min(r, 0) ** 2 for r in rets) / n) ** 0.5
    rf_d = risk_free / ppy
    sharpe = (mean - rf_d) / sd * (ppy ** 0.5) if sd > 0 else None
    sortino = (mean - rf_d) / down * (ppy ** 0.5) if down > 0 else None
    years = n / ppy
    cagr = (vals[-1] / vals[0]) ** (1 / years) - 1 if years > 0 and vals[0] > 0 else None
    dd = drawdown(curve)
    calmar = cagr / (abs(dd["pct"]) / 100) if cagr is not None and dd["pct"] < 0 else None
    return {"sharpe": sharpe, "sortino": sortino, "calmar": calmar, "cagr": cagr,
            "vol_ann": sd * (ppy ** 0.5), "peak_equity": max(vals),
            "peak_return_pct": (max(vals) - starting_capital) / starting_capital * 100}
