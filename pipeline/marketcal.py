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

from pandas.tseries.holiday import (
    AbstractHolidayCalendar,
    GoodFriday,
    Holiday,
    USLaborDay,
    USMartinLutherKingJr,
    USMemorialDay,
    USPresidentsDay,
    USThanksgivingDay,
    nearest_workday,
    sunday_to_monday,
)

MARKET_TZ = ZoneInfo("America/New_York")

# The shared phrase for "this date was never a session". Writers stamp it as a
# stale_reason instead of persisting a row; readers match on it to tell a
# routine weekend apart from a broken pipeline. One literal so they agree.
NOT_A_TRADING_SESSION = "not a trading session"


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


# ── NYSE holiday calendar ────────────────────────────────────────────
# Built from pandas.tseries.holiday rules rather than a market-calendar
# package: neither pandas_market_calendars nor exchange_calendars is a
# dependency here and this is the whole of what we need.
#
# The NYSE calendar is NOT the US federal calendar. It closes on Good
# Friday (not a federal holiday) and trades on Columbus Day and Veterans
# Day (which are federal holidays). Ad-hoc closures (presidential funerals,
# 9/11, Hurricane Sandy) are out of scope — this covers the recurring rules.

class NYSEHolidayCalendar(AbstractHolidayCalendar):
    """Recurring NYSE full-day closures."""

    rules = [
        Holiday("New Year's Day", month=1, day=1, observance=sunday_to_monday),
        USMartinLutherKingJr,                       # 3rd Monday of January
        USPresidentsDay,                            # 3rd Monday of February
        GoodFriday,                                 # Easter - 2 days
        USMemorialDay,                              # last Monday of May
        Holiday('Juneteenth', month=6, day=19, start_date='2021-06-18',
                observance=nearest_workday),
        Holiday('Independence Day', month=7, day=4, observance=nearest_workday),
        USLaborDay,                                 # 1st Monday of September
        USThanksgivingDay,                          # 4th Thursday of November
        Holiday('Christmas', month=12, day=25, observance=nearest_workday),
    ]


_HOLIDAY_CACHE: set[dt.date] | None = None


def _holiday_set() -> set[dt.date]:
    """Memoized set of NYSE closure dates over a generous date range."""
    global _HOLIDAY_CACHE
    if _HOLIDAY_CACHE is None:
        stamps = NYSEHolidayCalendar().holidays(
            start=dt.date(1990, 1, 1), end=dt.date(2050, 12, 31))
        _HOLIDAY_CACHE = {s.date() for s in stamps}
    return _HOLIDAY_CACHE


def is_market_holiday(d: dt.date) -> bool:
    """Is this date a NYSE holiday closure? Pure, no clock.

    Reports *weekday* closures only: a Saturday or Sunday is not a
    "holiday", it is simply not a session. Use `is_trading_day` for the
    combined test.
    """
    if d.weekday() >= 5:
        return False
    return d in _holiday_set()


def is_trading_day(d: dt.date) -> bool:
    """Is this date a regular NYSE trading session? Pure, no clock."""
    return d.weekday() < 5 and not is_market_holiday(d)
