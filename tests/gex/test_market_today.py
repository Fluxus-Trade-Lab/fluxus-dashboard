from datetime import datetime, date
from zoneinfo import ZoneInfo

import pipeline.marketcal as marketcal
from pipeline.gex.engine import _market_today

def test_engine_market_today_delegates_to_marketcal():
    # engine._market_today is now the shared helper, not a private reimpl.
    assert _market_today is marketcal.market_today

def test_market_today_uses_eastern_not_system_local():
    # Bug repro: system local (e.g. JST) already rolled to next calendar day
    # while US Eastern time has not. 15:43 UTC = 11:43 ET (same day) but
    # 00:43 the *next* day in JST. The ET date must win.
    fixed_utc = datetime(2026, 7, 15, 15, 43, tzinfo=ZoneInfo("UTC"))
    result = _market_today(now=fixed_utc)
    assert result == date(2026, 7, 15), f"got {result}, JST-contaminated bug would give 2026-07-16"
