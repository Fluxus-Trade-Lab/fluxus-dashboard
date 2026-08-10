"""Guardrail for the market-time helpers: trading dates must be ET, never the
host's local (JST) clock. See pipeline/marketcal.py."""
import datetime as dt
from zoneinfo import ZoneInfo

from pipeline import marketcal


def test_market_tz_is_eastern():
    assert marketcal.MARKET_TZ.key == "America/New_York"


def test_market_now_is_tz_aware_eastern():
    now = marketcal.market_now()
    assert now.tzinfo is not None
    assert now.utcoffset() in (dt.timedelta(hours=-4), dt.timedelta(hours=-5))


def test_market_today_matches_et_not_host():
    # A moment that is already "tomorrow" in Tokyo but still today in New York:
    # 2026-07-22 13:00 ET == 2026-07-23 02:00 JST. market_today() must say the
    # 22nd (ET), which is exactly the case date.today() got wrong on this Mac.
    instant = dt.datetime(2026, 7, 22, 13, 0, tzinfo=ZoneInfo("America/New_York"))
    assert marketcal.market_today(now=instant) == dt.date(2026, 7, 22)
    # Same instant expressed in JST resolves to the same ET trading date.
    assert marketcal.market_today(now=instant.astimezone(ZoneInfo("Asia/Tokyo"))) \
        == dt.date(2026, 7, 22)


def test_market_today_naive_input_is_treated_as_et():
    # A naive datetime is assumed to already be ET wall-clock, not host-local.
    naive = dt.datetime(2026, 7, 22, 13, 0)
    assert marketcal.market_today(now=naive) == dt.date(2026, 7, 22)


# ── NYSE holiday calendar ────────────────────────────────────────────
# NYSE is not the US federal calendar: it CLOSES Good Friday and stays
# OPEN on Columbus Day and Veterans Day.

NYSE_HOLIDAYS_2026 = [
    dt.date(2026, 1, 1),    # New Year's Day (Thu)
    dt.date(2026, 1, 19),   # MLK Day
    dt.date(2026, 2, 16),   # Washington's Birthday
    dt.date(2026, 4, 3),    # Good Friday
    dt.date(2026, 5, 25),   # Memorial Day
    dt.date(2026, 6, 19),   # Juneteenth (Fri)
    dt.date(2026, 7, 3),    # Independence Day observed (Jul 4 is a Saturday)
    dt.date(2026, 9, 7),    # Labor Day
    dt.date(2026, 11, 26),  # Thanksgiving
    dt.date(2026, 12, 25),  # Christmas (Fri)
]


def test_every_2026_nyse_holiday_is_a_holiday():
    for d in NYSE_HOLIDAYS_2026:
        assert marketcal.is_market_holiday(d) is True, d
        assert marketcal.is_trading_day(d) is False, d


def test_normal_weekday_is_a_trading_day():
    assert marketcal.is_market_holiday(dt.date(2026, 7, 30)) is False
    assert marketcal.is_trading_day(dt.date(2026, 7, 30)) is True


def test_columbus_and_veterans_day_markets_are_open():
    # Federal holidays, but the NYSE trades.
    for d in (dt.date(2026, 10, 12), dt.date(2026, 11, 11)):
        assert marketcal.is_market_holiday(d) is False, d
        assert marketcal.is_trading_day(d) is True, d


def test_weekend_is_not_a_trading_day_but_not_a_holiday():
    assert marketcal.is_trading_day(dt.date(2026, 3, 7)) is False   # Saturday
    assert marketcal.is_trading_day(dt.date(2026, 5, 24)) is False  # Sunday
    # is_market_holiday reports weekday closures only
    assert marketcal.is_market_holiday(dt.date(2026, 3, 7)) is False


def test_weekend_observance_shifts():
    # 2027-01-01 is a Friday — observed in place.
    assert marketcal.is_market_holiday(dt.date(2027, 1, 1)) is True
    # 2022-01-01 was a Saturday; NYSE did not close the Friday before.
    assert marketcal.is_market_holiday(dt.date(2021, 12, 31)) is False
    # 2022-12-26 (Mon) observed Christmas.
    assert marketcal.is_market_holiday(dt.date(2022, 12, 26)) is True
    # 2021-07-05 (Mon) observed Independence Day.
    assert marketcal.is_market_holiday(dt.date(2021, 7, 5)) is True
    # 2022-06-20 (Mon) observed Juneteenth.
    assert marketcal.is_market_holiday(dt.date(2022, 6, 20)) is True


def test_good_friday_across_years():
    assert marketcal.is_market_holiday(dt.date(2025, 4, 18)) is True
    assert marketcal.is_market_holiday(dt.date(2024, 3, 29)) is True


def test_is_trading_day_is_pure_and_accepts_datetime_date_only():
    # Called twice with the same input, same answer; no clock involved.
    d = dt.date(2026, 4, 3)
    assert marketcal.is_trading_day(d) == marketcal.is_trading_day(d) is False


def test_last_trading_day_files_a_weekend_under_friday():
    # The bug this exists for: a Sunday cron wrote 2026-08-09 into an archive
    # keyed by session, carrying the identical SPX close and identical zero
    # advance/decline counts as the real 2026-08-07 row. Same scrape, two dates.
    assert marketcal.last_trading_day(dt.date(2026, 8, 9)) == dt.date(2026, 8, 7)
    assert marketcal.last_trading_day(dt.date(2026, 8, 8)) == dt.date(2026, 8, 7)


def test_last_trading_day_is_identity_on_a_session():
    d = dt.date(2026, 8, 7)
    assert marketcal.last_trading_day(d) == d


def test_last_trading_day_walks_back_over_a_holiday():
    # Good Friday 2026-04-03 closes the exchange, so the Saturday after it and
    # the holiday itself both file under Thursday.
    assert marketcal.is_market_holiday(dt.date(2026, 4, 3)) is True
    assert marketcal.last_trading_day(dt.date(2026, 4, 3)) == dt.date(2026, 4, 2)
    assert marketcal.last_trading_day(dt.date(2026, 4, 5)) == dt.date(2026, 4, 2)


def test_last_trading_day_never_returns_a_non_session():
    # Sweep a year: whatever comes back must itself be a trading day, and must
    # never be later than the date asked about.
    d = dt.date(2026, 1, 1)
    while d < dt.date(2027, 1, 1):
        got = marketcal.last_trading_day(d)
        assert marketcal.is_trading_day(got), (d, got)
        assert got <= d, (d, got)
        d += dt.timedelta(days=1)
