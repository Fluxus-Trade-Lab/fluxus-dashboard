"""build_pack's portfolio closes: a missing T-day bar must never silently fall
back to a prior session's close (09-16 incident, INBOX L2803 — pack.json
printed 09-15's close/R as 09-16's: +122.29%/HOOD +3.69R instead of the real
+121.40%/+2.07R). Red on the positive control (T-day bar missing) before the
fix; green after."""
import datetime as dt

import pandas as pd
import pytest

from pipeline.content.recap import build_pack
from pipeline.content.recap.visual import book_out

T = "2026-09-16"


# ------------------------------------------------------------------ _last_close (pure)
def test_last_close_uses_t_day_bar_when_present():
    rows = [(dt.date(2026, 9, 15), 10.0), (dt.date(2026, 9, 16), 12.5)]
    px, stale = build_pack._last_close(rows, dt.date(2026, 9, 16))
    assert px == 12.5 and stale is False


def test_last_close_flags_stale_when_t_day_bar_missing():
    """The positive control: only a prior session's bar exists. Before the fix
    this silently became T's close; the fix must mark it stale instead."""
    rows = [(dt.date(2026, 9, 14), 10.0), (dt.date(2026, 9, 15), 11.0)]
    px, stale = build_pack._last_close(rows, dt.date(2026, 9, 16))
    assert stale is True


def test_last_close_flags_stale_when_nothing_available():
    px, stale = build_pack._last_close([], dt.date(2026, 9, 16))
    assert px is None and stale is True


# ------------------------------------------------------------------ _closes (yfinance seam)
def _fake_download_single(rows: list[tuple[str, float]]):
    idx = pd.to_datetime([d for d, _ in rows])
    return pd.DataFrame({"Close": [c for _, c in rows]}, index=idx)


def test_closes_returns_price_when_t_day_bar_present(monkeypatch):
    df = _fake_download_single([("2026-09-15", 10.0), ("2026-09-16", 12.5)])
    import yfinance as yf
    monkeypatch.setattr(yf, "download", lambda *a, **k: df)
    out, stale = build_pack._closes(["HOOD"], T)
    assert out == {"HOOD": 12.5} and stale == []


def test_closes_does_not_silently_use_prior_close_when_t_day_bar_missing(monkeypatch):
    df = _fake_download_single([("2026-09-14", 10.0), ("2026-09-15", 11.0)])
    import yfinance as yf
    monkeypatch.setattr(yf, "download", lambda *a, **k: df)
    out, stale = build_pack._closes(["HOOD"], T)
    assert "HOOD" not in out, "T-day bar missing but a price still came back — that's the 09-16 bug"
    assert stale == ["HOOD"]


# ------------------------------------------------------------------ book_block
def _trade(ticker="HOOD", entry_date="2026-09-10", entry_price=100.0, qty=100):
    return {"ticker": ticker, "direction": "long", "entryDate": entry_date, "entryPrice": entry_price,
            "originalQty": qty, "currentQty": qty, "stopPrice": 95.0, "initialStop": 95.0,
            "isClosed": False, "trims": []}


def _gas(trades):
    return {"stockTrades": trades, "meta": {"startingCapital": 100000}}


def test_book_block_flags_closes_stale_and_omits_the_stale_price(monkeypatch):
    monkeypatch.setattr(build_pack, "_closes", lambda tickers, t: ({}, list(tickers)))
    out = build_pack.book_block(T, _gas([_trade()]))
    assert out["closes_stale"] is True
    assert out["stale_close"] == ["HOOD"]
    assert "HOOD" in out["missing_close"]
    assert out["positions"] == [], "a stale close must not produce a priced position"


def test_book_block_clean_when_t_day_bar_present(monkeypatch):
    monkeypatch.setattr(build_pack, "_closes", lambda tickers, t: ({"HOOD": 105.0}, []))
    out = build_pack.book_block(T, _gas([_trade()]))
    assert out["closes_stale"] is False
    assert "stale_close" not in out
    assert out["missing_close"] == []
    assert out["positions"][0]["ticker"] == "HOOD"


# ------------------------------------------------------------------ render gate (visual.book_out)
def test_render_refuses_to_build_the_page_when_closes_are_stale():
    with pytest.raises(SystemExit):
        book_out({"closes_stale": True, "stale_close": ["HOOD"]}, T)


def test_render_passes_through_a_clean_book():
    bkk = {"closes_stale": False, "return_pct": 1.2, "cash_pct": 60.0, "open_names": 3, "closed_trades": 5,
           "open_R_total": 2.1, "realized_R_period": 0.5,
           "positions": [{"ticker": "HOOD", "direction": "long", "entry_date": "2026-09-10", "open_R": 0.8}]}
    out = book_out(bkk, T)
    # ticker / side / entry / stop_R / open_R (Andy 2026-09-23 R ladder). A pack
    # built before stop_R existed degrades to a blank stop rather than a guess,
    # which is the same behaviour as a position whose entry stop was never
    # recorded 「initialStop 缺失的仓位 stop 栏留空不猜」.
    # ticker / side / entry / cost / stop / open_R (Andy 2026-09-24: cost and stop
    # are prices). This fixture is a pre-2026-09-24 pack, which has neither — the
    # cells degrade to blank rather than blocking a re-render of an old issue.
    assert out["pos"] == [["HOOD", "long", "2026-09-10", None, None, None, 0.8]]
    assert out["legs"] == []


def test_render_returns_none_when_there_is_no_book_yet():
    assert book_out({}, T) is None
