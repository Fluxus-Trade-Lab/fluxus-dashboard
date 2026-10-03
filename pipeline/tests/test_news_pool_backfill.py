"""news_pool backfill: rate limits are retried (a 429 must not read as 'no
headline'), and sessions before the EP files existed say 'not measured'."""
import datetime as dt
import json

from pipeline.tools import news_pool_backfill as B


class _Resp:
    def __init__(self, code):
        self.status_code = code


def test_throttle_retries_429(monkeypatch):
    seq = iter([429, 429, 200])
    monkeypatch.setattr(B.requests, "get", lambda url, **kw: _Resp(next(seq)))
    monkeypatch.setattr(B.time, "sleep", lambda s: None)
    t = B._Throttled()
    assert t.get("u").status_code == 200
    assert (t.calls, t.rate_limited) == (3, 2)


def test_sessions_skip_weekends_and_holidays():
    got = B.sessions(dt.date(2026, 9, 4), dt.date(2026, 9, 8))
    assert got == [dt.date(2026, 9, 4), dt.date(2026, 9, 8)]   # 09-07 Labor Day


def test_session_before_ep_files_is_marked_unmeasured(tmp_path, monkeypatch):
    s = dt.date(2026, 9, 1)
    ts = "2026-09-01T22:00:00+00:00"
    universe = {"timestamp": ts, "rows": [
        {"ticker": "AAA", "liquid_leader": True, "change_pct": 0.05, "market_cap": 5e9}]}
    monkeypatch.setattr(B, "OUT_DIR", tmp_path)
    monkeypatch.setattr(B, "commits_by_session", lambda since: {s: "abc123def"})
    monkeypatch.setattr(B, "_show", lambda sha, p: universe if p == B.UNIVERSE else None)
    monkeypatch.setattr(B.NP, "earnings_calendar", lambda *a, **k: [])
    monkeypatch.setattr(B.NP, "latest_news", lambda *a, **k: None)
    calls = {}
    real_build = B.NP.build

    def build(*a, **k):
        k["fetch_calendar"] = lambda *x: []
        k["fetch_news"] = lambda *x: {"headline": "h", "url": "u", "source": "s",
                                      "published_at": ts}
        calls["n"] = 1
        return real_build(*a, **k)

    monkeypatch.setattr(B.NP, "build", build)
    assert B.main(["--start", "2026-09-01", "--end", "2026-09-01", "--key", "k"]) == 0
    doc = json.loads((tmp_path / "2026-09-01.json").read_text())
    assert doc["as_of"] == "2026-09-01"
    assert doc["counts"]["leader"] == 1 and doc["counts"]["ep"] == 0
    assert "还没有发布" in doc["backfill"]["ep_unmeasured"]
    assert doc["tickers"][0]["headline"] == "h"
    assert set(doc["tickers"][0]) >= {"headline", "url", "source", "published_at"}
    assert "summary" not in json.dumps(doc)                    # no article body in a public repo
