"""News & Events candidate pool (T-1003-83): leader / ep / news_failure buckets.

Session 2026-10-02 (Fri); previous session 2026-10-01 (Thu). Offline: every
Finnhub call is a fake, so no test needs FINNHUB_API_KEY.
"""
import datetime as dt

import pytest

from pipeline.screeners import news_pool as NP

SESSION = dt.date(2026, 10, 2)


def _u(ticker, change, *, leader=False, cap=5e9, rel=2.0):
    return {"ticker": ticker, "change_pct": change, "rel_volume": rel,
            "market_cap": cap, "liquid_leader": leader}


def _ev(symbol, actual, est):
    return {"symbol": symbol, "date": "2026-10-01", "epsActual": actual, "epsEstimate": est}


def _no_calls(*a, **k):
    raise AssertionError("Finnhub must not be called without a key")


def _rows_by_bucket(out, bucket):
    return [r["ticker"] for r in out["tickers"] if r["bucket"] == bucket]


class TestLeaders:
    def test_top_ten_by_change_among_liquid_leaders_only(self):
        rows = [_u(f"L{i:02d}", 0.01 * i, leader=True) for i in range(12)]
        rows.append(_u("NOTLEAD", 0.90, leader=False))  # biggest mover, not a leader
        out = NP.build(SESSION, rows, None, None)
        got = _rows_by_bucket(out, "leader")
        assert len(got) == NP.TOP_N == 10
        assert got[0] == "L11" and "NOTLEAD" not in got
        assert out["counts"]["leader"] == 10

    def test_leader_without_change_is_skipped(self):
        rows = [_u("A", None, leader=True), _u("B", 0.02, leader=True)]
        assert _rows_by_bucket(NP.build(SESSION, rows, None, None), "leader") == ["B"]


class TestEpisodic:
    def test_union_of_both_authors_one_row_each(self):
        sb = {"tickers": [{"ticker": "XRPN", "change_pct": 0.68, "rel_volume": 8.3},
                          {"ticker": "AZTA", "change_pct": 0.12, "rel_volume": 3.4}]}
        qm = {"tickers": [{"ticker": "XRPN", "change_pct": 0.68, "rel_volume": 8.3},
                          {"ticker": "SYNA", "change_pct": 0.14, "rel_volume": 8.1}]}
        out = NP.build(SESSION, [], sb, qm)
        ep = [r for r in out["tickers"] if r["bucket"] == "ep"]
        assert sorted(r["ticker"] for r in ep) == ["AZTA", "SYNA", "XRPN"]
        xrpn = next(r for r in ep if r["ticker"] == "XRPN")
        assert xrpn["ep_by"] == ["stockbee", "qullamaggie"]
        assert next(r for r in ep if r["ticker"] == "AZTA")["ep_by"] == ["stockbee"]


class TestNewsFailure:
    def test_beat_and_flat_or_down_is_in_beat_and_up_is_out(self):
        rows = [_u("FLAT", 0.0), _u("DOWN", -0.03), _u("EDGE", 0.01),
                _u("UP", 0.02), _u("MISS", -0.01), _u("TIE", -0.01), _u("SMALL", -0.01, cap=5e8)]
        events = [_ev("FLAT", 1.2, 1.0), _ev("DOWN", 0.5, 0.4), _ev("EDGE", 2.0, 1.5),
                  _ev("UP", 1.1, 1.0), _ev("MISS", 0.8, 1.0), _ev("TIE", 1.0, 1.0),
                  _ev("SMALL", 1.0, 0.5)]
        out = NP.build(SESSION, rows, None, None, key="k",
                       fetch_calendar=lambda s, e, k: events,
                       fetch_news=lambda t, s, e, k: None)
        assert sorted(_rows_by_bucket(out, "news_failure")) == ["DOWN", "EDGE", "FLAT"]
        assert out["news_failure_zero_reason"] is None
        flat = next(r for r in out["tickers"] if r["ticker"] == "FLAT")
        assert flat["earnings"] is True
        assert flat["eps_surprise_pct"] == pytest.approx(20.0)

    def test_zero_estimate_keeps_row_with_null_surprise(self):
        rows = [_u("ZE", -0.02)]
        out = NP.build(SESSION, rows, None, None, key="k",
                       fetch_calendar=lambda s, e, k: [_ev("ZE", 0.1, 0.0)],
                       fetch_news=lambda t, s, e, k: None)
        ze = next(r for r in out["tickers"] if r["ticker"] == "ZE")
        assert ze["bucket"] == "news_failure" and ze["eps_surprise_pct"] is None

    def test_zero_count_says_why(self):
        out = NP.build(SESSION, [_u("UP", 0.05)], None, None, key="k",
                       fetch_calendar=lambda s, e, k: [_ev("UP", 1.1, 1.0)],
                       fetch_news=lambda t, s, e, k: None)
        assert out["counts"]["news_failure"] == 0
        assert "EPS 超预期" in out["news_failure_zero_reason"]


class TestNoKeyAndFailure:
    def test_no_key_makes_no_calls_and_keeps_other_buckets(self):
        rows = [_u("L1", 0.05, leader=True)]
        out = NP.build(SESSION, rows, {"tickers": [{"ticker": "E1", "change_pct": 0.1}]}, None,
                       key=None, fetch_calendar=_no_calls, fetch_news=_no_calls)
        assert out["finnhub"] == "no_key"
        assert out["counts"] == {"leader": 1, "ep": 1, "news_failure": 0}
        assert "FINNHUB_API_KEY" in out["news_failure_zero_reason"]
        assert all(r["headline"] is None for r in out["tickers"])

    def test_calendar_error_does_not_drop_leader_or_ep(self):
        def boom(s, e, k):
            raise RuntimeError("429")
        out = NP.build(SESSION, [_u("L1", 0.05, leader=True)],
                       {"tickers": [{"ticker": "E1", "change_pct": 0.1}]}, None,
                       key="k", fetch_calendar=boom, fetch_news=lambda t, s, e, k: None)
        assert out["finnhub"] == "failed"
        assert out["counts"] == {"leader": 1, "ep": 1, "news_failure": 0}
        assert "调用失败" in out["news_failure_zero_reason"]


class TestHeadlineWindow:
    def test_latest_item_inside_window_wins(self, monkeypatch):
        start = dt.datetime(2026, 10, 1, 16, 0, tzinfo=NP.ET)
        end = dt.datetime(2026, 10, 2, 16, 0, tzinfo=NP.ET)
        inside_early = int(dt.datetime(2026, 10, 1, 18, 0, tzinfo=NP.ET).timestamp())
        inside_late = int(dt.datetime(2026, 10, 2, 9, 45, tzinfo=NP.ET).timestamp())
        after_close = int(dt.datetime(2026, 10, 2, 17, 0, tzinfo=NP.ET).timestamp())
        items = [
            {"headline": "early", "url": "https://x/1", "source": "A", "datetime": inside_early},
            {"headline": "late", "url": "https://x/2", "source": "B", "datetime": inside_late},
            {"headline": "after", "url": "https://x/3", "source": "C", "datetime": after_close},
        ]

        class Resp:
            ok = True

            def json(self):
                return items

        monkeypatch.setattr(NP.requests, "get", lambda *a, **k: Resp())
        got = NP.latest_news("XRPN", start, end, "k")
        assert got["headline"] == "late" and got["url"] == "https://x/2"
        assert got["published_at"].startswith("2026-10-02T13:45")

    def test_nothing_in_window_returns_none(self, monkeypatch):
        class Resp:
            ok = True

            def json(self):
                return [{"headline": "old", "url": "u", "datetime": 1}]

        monkeypatch.setattr(NP.requests, "get", lambda *a, **k: Resp())
        start = dt.datetime(2026, 10, 1, 16, 0, tzinfo=NP.ET)
        end = dt.datetime(2026, 10, 2, 16, 0, tzinfo=NP.ET)
        assert NP.latest_news("XRPN", start, end, "k") is None
