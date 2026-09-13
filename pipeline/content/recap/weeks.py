"""ISO-week helpers for the weekly recap (sessions via pipeline.marketcal, ET)."""
from __future__ import annotations

import datetime as dt

from pipeline.marketcal import is_trading_day, last_trading_day


def week_sessions(label: str) -> list[dt.date]:
    """'2026-W37' → NYSE sessions Mon..Fri of that ISO week."""
    y, w = label.split("-W")
    mon = dt.date.fromisocalendar(int(y), int(w), 1)
    return [d for d in (mon + dt.timedelta(days=i) for i in range(5)) if is_trading_day(d)]


def week_label(d: dt.date) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def prior_week_close(label: str) -> dt.date:
    """Last session before the week's Monday (the weekly-change base)."""
    y, w = label.split("-W")
    mon = dt.date.fromisocalendar(int(y), int(w), 1)
    return last_trading_day(mon - dt.timedelta(days=1))
