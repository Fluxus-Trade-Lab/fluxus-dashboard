"""Monthly seasonality from a daily close series — pure, cacheable computation.

`monthly_seasonality()` takes a date-indexed daily close Series and returns a
plain dict (JSON-serialisable) of per-calendar-month full-month return stats and
realized vol. It is deliberately free of any IBKR / IO concerns so it can be
unit-tested and so the expensive 15-year history pull is done once, cached to
JSON, and never recomputed at read time.
"""
from __future__ import annotations

import calendar

import numpy as np
import pandas as pd

_MONTHS = list(calendar.month_abbr)  # ["", "Jan", ..., "Dec"]


def monthly_seasonality(close: pd.Series) -> dict:
    close = close.sort_index()
    daily_ret = close.pct_change()

    # Full-month return = month-end close vs prior month-end close.
    month_end = close.resample("ME").last()
    mret = (month_end.pct_change().dropna() * 100.0)

    # Realized vol (annualized) per calendar month, from daily returns.
    rvol_by_month = (
        daily_ret.groupby(daily_ret.index.month).std() * np.sqrt(252) * 100.0
    )

    months, by_year = [], {}
    for m in range(1, 13):
        rs = mret[mret.index.month == m]
        if rs.empty:
            continue
        arr = rs.to_numpy()
        months.append({
            "month": m,
            "name": _MONTHS[m],
            "n": int(arr.size),
            "mean_pct": round(float(arr.mean()), 3),
            "median_pct": round(float(np.median(arr)), 3),
            "win_pct": round(float((arr > 0).mean() * 100.0), 1),
            "stdev_pct": round(float(arr.std()), 3),
            "min_pct": round(float(arr.min()), 3),
            "max_pct": round(float(arr.max()), 3),
            "rvol_pct": round(float(rvol_by_month.get(m, float("nan"))), 2),
        })
        by_year[str(m)] = [
            {"year": int(ts.year), "ret_pct": round(float(v), 3)}
            for ts, v in rs.items()
        ]

    return {
        "history": {
            "start": str(close.index[0].date()),
            "end": str(close.index[-1].date()),
            "n_days": int(close.size),
        },
        "full_sample_rvol_pct": round(float(daily_ret.std() * np.sqrt(252) * 100.0), 2),
        "months": months,
        "by_year": by_year,
    }
