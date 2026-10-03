"""News & Events candidate pool (T-1003-83): bucket rules, reaction-day
logic, headline window, and the explicit no-key path. No network: the
Finnhub client is replaced with a fake."""

import datetime as dt

import pytest

from pipeline.screeners import news_pool as np_

SESSION = dt.date(2026, 10, 2)  # Friday
PRIOR = dt.date(2026, 10, 1)  # Thursday


def _row(t, chg, rs=None, sma50=None, rel=2.0):
    return {"ticker": t, "change_pct": chg, "rs_rating": rs, "sma50_dist": sma50, "rel_volume": rel}


def _ts(day, hh, mm=0):
    return dt.datetime.combine(day, dt.time(hh, mm), np_.ET).timestamp()


# ---- leader -----------------------------------------------------------------

def test_leader_requires_rs_and_above_sma50_and_takes_top_change():
    rows = [
        _row("AAA", 0.05, rs=95, sma50=0.10),
        _row("BBB", 0.09, rs=95, sma50=-0.02),  # below 50 SMA -> out
        _row("CCC", 0.08, rs=85, sma50=0.10),  # RS too low -> out
        _row("DDD", 0.07, rs=None, sma50=0.10),  # rs NaN -> excluded, not ranked low
        _row("EEE", 0.06, rs=90, sma50=0.01),  # RS boundary 90 -> in
    ]
    assert np_.leader_tickers(rows) == ["EEE", "AAA"]  # by change: +6 % then +5 %


def test_leader_caps_at_n():
    rows = [_row(f"T{i}", 0.01 * i, rs=99, sma50=0.1) for i in range(15)]
    got = np_.leader_tickers(rows)
    assert len(got) == np_.LEADER_N
    assert got[0] == "T14"


# ---- ep ----------------------------------------------------------------------

def test_ep_union_dedupes_both_authors():
    sb = {"tickers": [{"ticker": "X"}, {"ticker": "Y"}]}
    qu = {"tickers": [{"ticker": "Y"}, {"ticker": "Z"}]}
    assert np_.ep_tickers(sb, qu) == ["X", "Y", "Z"]


# ---- reaction day -------------------------------------------------------------

def test_reaction_earnings_session_bmo_and_prior_amc_only():
    events = [
        {"symbol": "BMO", "date": SESSION.isoformat(), "hour": "bmo"},
        {"symbol": "AMC", "date": PRIOR.isoformat(), "hour": "amc"},
        {"symbol": "OLD", "date": PRIOR.isoformat(), "hour": "bmo"},  # reacted prior session
        {"symbol": "", "date": SESSION.isoformat()},
    ]
    got = np_.reaction_earnings(events, SESSION, PRIOR)
    assert set(got) == {"BMO", "AMC"}


def test_eps_surprise_pct_and_missing():
    assert np_.eps_surprise_pct({"epsActual": 1.1, "epsEstimate": 1.0}) == pytest.approx(10.0)
    assert np_.eps_surprise_pct({"epsActual": 0.9, "epsEstimate": -1.0}) == pytest.approx(190.0)
    assert np_.eps_surprise_pct({"epsActual": None, "epsEstimate": 1.0}) is None
    assert np_.eps_surprise_pct({"epsActual": 1.0, "epsEstimate": 0}) is None


# ---- headline window ----------------------------------------------------------

def test_latest_headline_inside_window_only():
    start, end = _ts(PRIOR, 16), _ts(SESSION, 16)
    items = [
        {"datetime": _ts(PRIOR, 9), "headline": "before window", "url": "u0", "source": "s"},
        {"datetime": _ts(PRIOR, 17), "headline": "earlier", "url": "u1", "source": "s"},
        {"datetime": _ts(SESSION, 8), "headline": "latest", "url": "u2", "source": "Reuters"},
        {"datetime": _ts(SESSION, 17), "headline": "after close", "url": "u3", "source": "s"},
    ]
    hit = np_.latest_headline(items, start, end)
    assert hit["headline"] == "latest"
    assert hit["url"] == "u2"
    assert hit["source"] == "Reuters"
    assert set(hit) == {"headline", "url", "source", "published_at"}  # no body stored


def test_latest_headline_none_when_empty():
    assert np_.latest_headline([], 0, 1) is None


# ---- build ---------------------------------------------------------------------

SB = {"tickers": [{"ticker": "EPX"}]}
QU = {"tickers": []}


def test_build_without_key_is_explicit_not_empty():
    rows = [
        _row("LEAD", 0.05, rs=95, sma50=0.1),
        _row("EPX", 0.12, rs=50, sma50=-0.1),
    ]
    out = np_.build(rows, SB, QU, key=None, session=SESSION)
    assert out["bucket_counts"] == {"leader": 1, "ep": 1, "news_failure": 0}
    assert all(x["headline"] is None and x["earnings"] is None for x in out["tickers"])
    assert any("FINNHUB_API_KEY" in u for u in out["unmeasured"])
    assert out["news_failure_note"].startswith("0: earnings calendar not measured")


class _FakeClient:
    def __init__(self, key, events=None, news=None, fail_calendar=False):
        self._events = events or []
        self._news = news or {}
        self._fail = fail_calendar

    def earnings_calendar(self, start, end):
        if self._fail:
            raise RuntimeError("boom")
        assert start == PRIOR and end == SESSION
        return self._events

    def company_news(self, symbol, start, end):
        return self._news.get(symbol, [])


def _patch(monkeypatch, **kw):
    monkeypatch.setattr(np_, "FinnhubClient", lambda key, **_: _FakeClient(key, **kw))


def test_build_news_failure_beat_but_weak_reaction(monkeypatch):
    rows = [
        _row("BEAT", 0.005, rs=40, sma50=0.0),  # beat, +0.5 % -> news_failure
        _row("BIGUP", 0.06, rs=40, sma50=0.0),  # beat but moved up -> not a failure
        _row("MISS", 0.0, rs=40, sma50=0.0),  # miss -> not a failure
    ]
    events = [
        {"symbol": "BEAT", "date": SESSION.isoformat(), "hour": "bmo", "epsActual": 1.2, "epsEstimate": 1.0},
        {"symbol": "BIGUP", "date": SESSION.isoformat(), "hour": "bmo", "epsActual": 1.2, "epsEstimate": 1.0},
        {"symbol": "MISS", "date": SESSION.isoformat(), "hour": "bmo", "epsActual": 0.8, "epsEstimate": 1.0},
    ]
    news = {"BEAT": [{"datetime": _ts(SESSION, 7), "headline": "Beats", "url": "https://x", "source": "PR"}]}
    _patch(monkeypatch, events=events, news=news)
    out = np_.build(rows, SB, QU, key="k", session=SESSION)
    nf = [x for x in out["tickers"] if x["bucket"] == "news_failure"]
    assert [x["ticker"] for x in nf] == ["BEAT"]
    assert nf[0]["earnings"] is True
    assert nf[0]["eps_surprise_pct"] == pytest.approx(20.0)
    assert nf[0]["headline"] == "Beats"
    assert "news_failure_note" not in out  # non-zero count, no note needed
    assert out["unmeasured"] == []


def test_build_zero_news_failure_has_reason(monkeypatch):
    _patch(monkeypatch, events=[])
    out = np_.build([_row("LEAD", 0.05, rs=95, sma50=0.1)], {"tickers": []}, QU, key="k", session=SESSION)
    assert out["bucket_counts"]["news_failure"] == 0
    assert out["news_failure_note"] == "0: no eligible earnings beat with reaction <= +1%"
    assert out["tickers"][0]["earnings"] is False


def test_build_calendar_failure_is_unmeasured_not_false(monkeypatch):
    _patch(monkeypatch, fail_calendar=True)
    out = np_.build([_row("LEAD", 0.05, rs=95, sma50=0.1)], {"tickers": []}, QU, key="k", session=SESSION)
    assert out["tickers"][0]["earnings"] is None  # unknown, not False
    assert any("calendar call failed" in u for u in out["unmeasured"])
    assert out["news_failure_note"] == "0: earnings calendar not measured this run"
