"""Tests for the local OHLC store — in particular the staleness guard.

Background (the bug these tests exist to prevent): `load_local_ohlc` had a
`min_start` check (history must reach far enough BACK) but nothing rejecting a
cache whose LAST bar is old. On 2026-08-09 PLTR's cached file ended 2026-05-22,
so `load_local_ohlc("PLTR")[-1]["close"]` returned 136.88 — a price 2.5 months
stale. Marked against a 155.37 entry with a 153.00 stop that is -7.8R (a
catastrophic loss); the real 2026-08-07 close of 172.01 is +7.02R (the best
position on the book). The sign was inverted purely by a stale cache.
"""
import datetime as dt
import json

import pytest


def _bars(start: str, n: int, close: float = 100.0):
    """n consecutive daily bars (calendar days; weekends don't matter here)."""
    d0 = dt.date.fromisoformat(start)
    return [{
        "date": (d0 + dt.timedelta(days=i)).isoformat(),
        "open": close, "high": close, "low": close, "close": close,
        "volume": 1_000_000.0,
    } for i in range(n)]


def _write(tmp_path, ticker: str, payload: dict):
    (tmp_path / f"{ticker}.json").write_text(json.dumps(payload))
    return tmp_path


@pytest.fixture
def store(tmp_path):
    """A tickers dir holding one fresh name and one 2.5-month-stale name."""
    _write(tmp_path, "FRESH", {"ohlc_2y": _bars("2026-07-20", 19, close=172.01)})
    _write(tmp_path, "PLTR", {"ohlc_2y": _bars("2026-05-04", 19, close=136.88)})
    return tmp_path


@pytest.fixture
def today(monkeypatch):
    """Pin the market date to 2026-08-09 (the day the bug was found)."""
    from pipeline.tickers import ohlc_store
    monkeypatch.setattr(ohlc_store, "market_today", lambda: dt.date(2026, 8, 9))
    return dt.date(2026, 8, 9)


class TestLoadLocalOhlcDefaults:
    """Default behaviour must not change — historical callers rely on it."""

    def test_returns_bars_for_a_fresh_file(self, store):
        from pipeline.tickers.ohlc_store import load_local_ohlc
        bars = load_local_ohlc("FRESH", tickers_dir=store)
        assert bars[-1]["date"] == "2026-08-07"

    def test_stale_file_still_loads_when_no_guard_requested(self, store, today):
        """A backtest reading deliberate history must keep the old behaviour."""
        from pipeline.tickers.ohlc_store import load_local_ohlc
        bars = load_local_ohlc("PLTR", tickers_dir=store)
        assert bars is not None and bars[-1]["date"] == "2026-05-22"

    def test_missing_file_returns_none(self, store):
        from pipeline.tickers.ohlc_store import load_local_ohlc
        assert load_local_ohlc("NOSUCH", tickers_dir=store) is None

    def test_min_start_still_rejects_shallow_history(self, store):
        from pipeline.tickers.ohlc_store import load_local_ohlc
        assert load_local_ohlc("FRESH", min_start="2025-01-01", tickers_dir=store) is None


class TestMaxAgeDays:
    def test_stale_file_returns_none(self, store, today):
        """The PLTR case: last bar 2026-05-22, asked for <=5 days old."""
        from pipeline.tickers.ohlc_store import load_local_ohlc
        assert load_local_ohlc("PLTR", max_age_days=5, tickers_dir=store) is None

    def test_fresh_file_passes(self, store, today):
        """Last bar 2026-08-07, two days before the pinned market date."""
        from pipeline.tickers.ohlc_store import load_local_ohlc
        bars = load_local_ohlc("FRESH", max_age_days=5, tickers_dir=store)
        assert bars is not None and bars[-1]["close"] == 172.01

    def test_boundary_is_inclusive(self, store, monkeypatch):
        """Exactly max_age_days old is still acceptable (long-weekend gaps)."""
        from pipeline.tickers import ohlc_store
        monkeypatch.setattr(ohlc_store, "market_today", lambda: dt.date(2026, 8, 12))
        assert ohlc_store.load_local_ohlc("FRESH", max_age_days=5, tickers_dir=store) is not None
        monkeypatch.setattr(ohlc_store, "market_today", lambda: dt.date(2026, 8, 13))
        assert ohlc_store.load_local_ohlc("FRESH", max_age_days=5, tickers_dir=store) is None

    def test_uses_market_date_not_host_clock(self, store, monkeypatch):
        """Trading dates come from marketcal — the host runs in JST, 13h ahead."""
        from pipeline.tickers import ohlc_store
        calls = []

        def fake_today():
            calls.append(1)
            return dt.date(2026, 8, 9)

        monkeypatch.setattr(ohlc_store, "market_today", fake_today)
        ohlc_store.load_local_ohlc("FRESH", max_age_days=5, tickers_dir=store)
        assert calls, "max_age_days must resolve 'now' via pipeline.marketcal"

    def test_unparseable_last_date_is_rejected(self, tmp_path, today):
        from pipeline.tickers.ohlc_store import load_local_ohlc
        _write(tmp_path, "JUNK", {"ohlc_2y": [{"date": "not-a-date", "close": 1.0}]})
        assert load_local_ohlc("JUNK", max_age_days=5, tickers_dir=tmp_path) is None


class TestThrough:
    def test_rejects_history_not_reaching_the_date(self, store):
        from pipeline.tickers.ohlc_store import load_local_ohlc
        assert load_local_ohlc("PLTR", through="2026-08-07", tickers_dir=store) is None

    def test_accepts_history_reaching_the_date(self, store):
        from pipeline.tickers.ohlc_store import load_local_ohlc
        assert load_local_ohlc("FRESH", through="2026-08-07", tickers_dir=store) is not None

    def test_needs_no_clock(self, store, monkeypatch):
        """`through` is pure — it must not consult the calendar at all."""
        from pipeline.tickers import ohlc_store

        def boom():
            raise AssertionError("through must not read the clock")

        monkeypatch.setattr(ohlc_store, "market_today", boom)
        assert ohlc_store.load_local_ohlc("FRESH", through="2026-08-01", tickers_dir=store)

    def test_combines_with_min_start(self, store):
        """Both ends are checked: deep enough back AND recent enough forward."""
        from pipeline.tickers.ohlc_store import load_local_ohlc
        # FRESH spans 2026-07-20 → 2026-08-07. Recent enough, but too shallow.
        assert load_local_ohlc("FRESH", min_start="2026-01-01", through="2026-08-07",
                               tickers_dir=store) is None
        # Deep enough and recent enough.
        assert load_local_ohlc("FRESH", min_start="2026-07-20", through="2026-08-07",
                               tickers_dir=store) is not None


class TestLatestClose:
    """The purpose-built mark-to-market accessor — guarded by default."""

    def test_returns_the_last_bar_when_fresh(self, store, today):
        from pipeline.tickers.ohlc_store import latest_close
        bar = latest_close("FRESH", tickers_dir=store)
        assert bar["close"] == 172.01 and bar["date"] == "2026-08-07"

    def test_returns_none_when_stale_by_default(self, store, today):
        """No max_age_days argument: the guard must still apply."""
        from pipeline.tickers.ohlc_store import latest_close
        assert latest_close("PLTR", tickers_dir=store) is None

    def test_returns_none_for_missing_file(self, store, today):
        from pipeline.tickers.ohlc_store import latest_close
        assert latest_close("NOSUCH", tickers_dir=store) is None

    def test_staleness_can_be_widened_explicitly(self, store, today):
        from pipeline.tickers.ohlc_store import latest_close
        assert latest_close("PLTR", max_age_days=120, tickers_dir=store) is not None
