"""`_parse_date` must read the Sheet's timestamp as a JST wall-clock day.

The Apps Script writes a Date cell as `getValues()` + `JSON.stringify`, which
round-trips through UTC: JST midnight becomes '...T15:00:00.000Z' the day
before. Taking the date straight off that string reads one day early for
every entry made before 09:00 JST (390/390 trades, discovered 2026-09-22).
"""
from __future__ import annotations

from datetime import date

from pipeline.portfolio.trade_parser import _parse_date


def test_utc_midnight_jst_timestamp_lands_on_the_jst_day():
    # '15:00:00.000Z' is JST 00:00 the next day.
    assert _parse_date('2026-09-20T15:00:00.000Z') == date(2026, 9, 21)


def test_bare_date_is_kept_as_is():
    assert _parse_date('2026-09-21') == date(2026, 9, 21)


def test_explicit_jst_offset_lands_on_the_stated_day():
    assert _parse_date('2026-09-21T00:00:00+09:00') == date(2026, 9, 21)


def test_utc_timestamp_still_in_the_same_jst_day():
    # 14:59 UTC is still 23:59 JST the same day.
    assert _parse_date('2026-09-20T14:59:00.000Z') == date(2026, 9, 20)


def test_z_without_milliseconds_also_converts():
    assert _parse_date('2026-09-20T15:00:00Z') == date(2026, 9, 21)


def test_blank_and_none_are_none():
    assert _parse_date('') is None
    assert _parse_date(None) is None
