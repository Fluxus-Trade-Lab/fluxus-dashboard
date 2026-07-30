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
