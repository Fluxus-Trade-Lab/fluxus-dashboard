"""The premarket digest must not pick names from a stale universe (Andy 2026-09-17:
Dashboard data is the morning's foundation; OPS dependents audit item 1)."""
import datetime as dt
import json

import pytest

from pipeline.discord import premarket_digest as pd
from pipeline.marketcal import MARKET_TZ

# 08:00 ET Thursday 2026-09-17 -> last completed session is Wed 2026-09-16.
NOW = dt.datetime(2026, 9, 17, 8, 0, tzinfo=MARKET_TZ)


def _universe(tmp_path, monkeypatch, timestamp):
    p = tmp_path / "universe.json"
    p.write_text(json.dumps({"timestamp": timestamp, "count": 1,
                             "rows": [{"ticker": "AAA", "close": 10, "avg_volume": 10**6}]}))
    monkeypatch.setattr(pd, "UNIVERSE_PATH", p)


@pytest.mark.parametrize("ts,fresh", [
    ("2026-09-16T23:03:26+00:00", True),    # nightly for 09-16 (19:03 ET)
    ("2026-09-17T07:30:00+00:00", True),    # late backstop, 03:30 ET next day -> still 09-16
    ("2026-09-15T23:17:48+00:00", False),   # yesterday's file
    ("", False),
])
def test_universe_session_is_checked_against_the_last_completed_session(tmp_path, monkeypatch, ts, fresh):
    _universe(tmp_path, monkeypatch, ts)
    assert pd.universe_is_fresh(NOW) is fresh


def test_a_stale_universe_posts_a_delay_line_and_never_fetches(tmp_path, monkeypatch):
    _universe(tmp_path, monkeypatch, "2026-09-15T23:17:48+00:00")
    monkeypatch.setattr(pd, "_now_et", lambda: NOW)
    monkeypatch.setattr(pd, "fetch_premarket_data",
                        lambda *a, **k: pytest.fail("must not scan a stale universe"))
    sent = []
    monkeypatch.setattr(pd, "post_to_discord", lambda payload: sent.append(payload) or True)
    assert pd.run(force=True) == 0
    assert len(sent) == 1
    body = json.dumps(sent[0], ensure_ascii=False)
    assert "2026-09-15" in body and "2026-09-16" in body
    assert "embeds" not in sent[0]


def test_a_fresh_universe_still_scans(tmp_path, monkeypatch):
    _universe(tmp_path, monkeypatch, "2026-09-16T23:03:26+00:00")
    monkeypatch.setattr(pd, "_now_et", lambda: NOW)
    called = []
    monkeypatch.setattr(pd, "fetch_premarket_data", lambda c: called.append(c) or [])
    monkeypatch.setattr(pd, "tag_catalysts", lambda rows: None)
    monkeypatch.setattr(pd, "rank_with_claude", lambda rows: None)
    monkeypatch.setattr(pd, "write_audit", lambda rows, rt: None)
    monkeypatch.setattr(pd, "post_to_discord", lambda payload: True)
    assert pd.run(force=True) == 0
    assert called
