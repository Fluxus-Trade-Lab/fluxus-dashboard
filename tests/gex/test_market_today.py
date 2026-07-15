from unittest.mock import patch
from datetime import datetime, date
from zoneinfo import ZoneInfo
from pipeline.gex.engine import _market_today

def test_market_today_uses_eastern_not_system_local():
    # Bug repro: system local (e.g. JST) already rolled to next calendar day
    # while US Eastern time has not. 15:43 UTC = 11:43 ET (same day) but
    # 00:43 the *next* day in JST.
    fixed_utc = datetime(2026, 7, 15, 15, 43, tzinfo=ZoneInfo("UTC"))
    with patch("pipeline.gex.engine.datetime") as mock_dt:
        mock_dt.now.side_effect = lambda tz=None: (
            fixed_utc.astimezone(tz) if tz else fixed_utc)
        result = _market_today()
    assert result == date(2026, 7, 15), f"got {result}, JST-contaminated bug would give 2026-07-16"
