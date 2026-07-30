"""Market-time helpers — the single source of truth for *trading* dates.

RULE: anything that identifies a trading day, expiry, DTE, or session must use
`market_today()` / `market_now()`, never `date.today()` / `datetime.now()`.

Why: this project runs on a Mac in JST (~13h ahead of ET). For most of the US
session the host's local clock is already the next calendar day, so
`date.today()` returns "tomorrow" — which silently mis-stamps output filenames,
shifts expiry/tenor selection a day forward, and mis-counts DTE. Trading dates
follow the exchange (US/Eastern); only genuinely local, daily-life timestamps
should use the host clock.
"""
import datetime as dt
from zoneinfo import ZoneInfo

MARKET_TZ = ZoneInfo("America/New_York")


def market_now() -> dt.datetime:
    """Current instant as a tz-aware datetime in US/Eastern."""
    return dt.datetime.now(MARKET_TZ)


def market_today(now: dt.datetime | None = None) -> dt.date:
    """Today's trading date in US/Eastern.

    `now` is for tests/callers that already hold an instant. A tz-aware value is
    converted to ET; a naive value is assumed to already be ET wall-clock (never
    reinterpreted as host-local, which is the bug this module exists to prevent).
    """
    if now is None:
        return market_now().date()
    if now.tzinfo is not None:
        return now.astimezone(MARKET_TZ).date()
    return now.date()
