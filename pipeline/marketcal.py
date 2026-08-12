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


def last_trading_day(d: dt.date | None = None) -> dt.date:
    """The most recent NYSE session on or before `d` (default: today in ET).

    `market_today()` answers "what is the date in New York", which is the right
    question for a timestamp and the wrong one for a session label. A cron that
    fires on a Saturday, a Sunday or Good Friday gets a real calendar date back
    and, if that date is written into an archive keyed by session, invents a
    trading day that never happened.

    That is not hypothetical: the 2026-08-09 (Sunday) row and the 2026-08-07
    (Friday) row carried an identical SPX close and identical zero advance /
    decline counts, because they were the same scrape labelled twice.

    Pure with respect to the clock once `d` is supplied, so it is testable
    without freezing time.
    """
    day = market_today() if d is None else d
    # NYSE never closes for more than a handful of consecutive days; the bound
    # keeps a bad holiday table from turning this into an infinite loop.
    for _ in range(10):
        if is_trading_day(day):
            return day
        day -= dt.timedelta(days=1)
    raise RuntimeError(f"no trading day within 10 days of {d or 'today'}")


# Regular NYSE close. Half-days close at 13:00 and are not modelled here; the
# cost of ignoring them is a label that stays on the previous session for
# three extra hours, which errs in the safe direction.
MARKET_CLOSE = dt.time(16, 0)


def last_completed_session(now: dt.datetime | None = None) -> dt.date:
    """The most recent NYSE session whose close has already happened.

    `last_trading_day()` answers "what session is on or before this date",
    which is right for interpreting a dated file and wrong for labelling data
    scraped NOW: asked at 05:44 ET on a Monday it says Monday, but Monday's
    session has not opened and every vendor is still serving Friday's close.

    Not hypothetical either: a premarket-Monday manual run stamped 589 rows of
    Friday's tape as 2026-08-10 in the ticker-events archive, which is
    append-only and would have kept them forever. Archives keyed by date and
    rewritten by the post-close cron self-heal; append-only ones do not, and
    this is the label they must use.

    Pure once `now` is supplied. A naive datetime is assumed to be ET
    wall-clock already, matching `market_today`.
    """
    ts = market_now() if now is None else now
    if ts.tzinfo is not None:
        ts = ts.astimezone(MARKET_TZ)
    day = ts.date()
    if not is_trading_day(day) or ts.time() < MARKET_CLOSE:
        day -= dt.timedelta(days=1)
    return last_trading_day(day)
