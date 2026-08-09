import pandas as pd
from pipeline.flow.enrich import enrich_trades


def _ts(seconds):
    return pd.Timestamp("2026-07-15 12:00:00", tz="America/New_York") + pd.Timedelta(seconds=seconds)


def test_enrich_attaches_most_recent_quote():
    quotes = pd.DataFrame({
        "time": [_ts(0), _ts(1), _ts(3)],
        "bid":  [5.00, 5.02, 5.05],
        "ask":  [5.10, 5.12, 5.15],
    })
    trades = pd.DataFrame({
        "time":  [_ts(2), _ts(4)],
        "price": [5.11, 5.10],
        "size":  [1, 2],
    })
    result = enrich_trades(trades, quotes)
    # trade at t=2s → most recent quote at t=1s
    assert result.iloc[0]["bid"] == 5.02
    assert result.iloc[0]["ask"] == 5.12
    # trade at t=4s → most recent quote at t=3s
    assert result.iloc[1]["bid"] == 5.05
    assert result.iloc[1]["ask"] == 5.15


def test_enrich_populates_prev_price():
    quotes = pd.DataFrame({"time": [_ts(0)], "bid": [5.00], "ask": [5.10]})
    trades = pd.DataFrame({
        "time":  [_ts(1), _ts(2), _ts(3)],
        "price": [5.05, 5.06, 5.04],
        "size":  [1, 1, 1],
    })
    result = enrich_trades(trades, quotes)
    assert pd.isna(result.iloc[0]["prev_price"])           # first trade has no prev
    assert result.iloc[1]["prev_price"] == 5.05
    assert result.iloc[2]["prev_price"] == 5.06


def test_enrich_missing_quote_yields_nan():
    # trade at t=0 but no quote earlier — bid/ask should be NaN
    quotes = pd.DataFrame({"time": [_ts(10)], "bid": [5.00], "ask": [5.10]})
    trades = pd.DataFrame({"time": [_ts(0)], "price": [5.05], "size": [1]})
    result = enrich_trades(trades, quotes)
    assert pd.isna(result.iloc[0]["bid"])
    assert pd.isna(result.iloc[0]["ask"])


def test_enrich_respects_tolerance():
    # quote is 10s old and tolerance is 5s → no match
    quotes = pd.DataFrame({"time": [_ts(0)], "bid": [5.00], "ask": [5.10]})
    trades = pd.DataFrame({"time": [_ts(10)], "price": [5.05], "size": [1]})
    result = enrich_trades(trades, quotes, max_lookback_ms=5000)
    assert pd.isna(result.iloc[0]["bid"])
