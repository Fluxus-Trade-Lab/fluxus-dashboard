import pandas as pd
from pipeline.flow.aggregate import aggregate_2min


def _ts(minute, second=0):
    return pd.Timestamp("2026-07-15 12:00:00", tz="America/New_York") + pd.Timedelta(minutes=minute, seconds=second)


def _mk(times, prices, sizes, bids, asks):
    df = pd.DataFrame({
        "time": times, "price": prices, "size": sizes,
        "bid": bids, "ask": asks,
    })
    df["prev_price"] = df["price"].shift(1)
    return df


def test_aggregates_premium_and_bot_sold_split():
    # bar 12:00: two prints — one BOT (at ask), one SOLD (at bid)
    df = _mk(
        times=[_ts(0, 10), _ts(0, 30)],
        prices=[5.10, 5.00],
        sizes=[10, 20],
        bids=[5.00, 5.00],
        asks=[5.10, 5.10],
    )
    out = aggregate_2min(df)
    row = out.iloc[0]
    assert row["time_bin"] == _ts(0, 0)
    assert row["premium_total"] == 5.10 * 10 * 100 + 5.00 * 20 * 100
    assert row["bot_premium"] == 5.10 * 10 * 100
    assert row["sold_premium"] == 5.00 * 20 * 100
    assert row["net_premium"] == row["bot_premium"] - row["sold_premium"]
    assert row["n_prints"] == 2


def test_bars_start_on_even_2min():
    # trades scattered across 12:00-12:07
    df = _mk(
        times=[_ts(1, 30), _ts(3, 15), _ts(5, 0), _ts(6, 59)],
        prices=[5.10, 5.10, 5.00, 5.00],
        sizes=[1, 1, 1, 1],
        bids=[5.00]*4, asks=[5.10]*4,
    )
    out = aggregate_2min(df)
    # expect 4 bars: 12:00, 12:02, 12:04, 12:06 (each starting on an even 2-min mark)
    assert list(out["time_bin"]) == [_ts(0), _ts(2), _ts(4), _ts(6)]


def test_threshold_and_top_prints():
    # 20 prints of $100 each + 1 print of $10,000 — the fat print should be flagged
    times = [_ts(0, i) for i in range(20)] + [_ts(0, 50)]
    df = _mk(
        times=times,
        prices=[1.00] * 20 + [100.00],
        sizes=[1] * 20 + [1],
        bids=[0.95] * 21, asks=[1.05] * 21,
    )
    # normalize: 20 prints at premium=100 each, 1 print at premium=10000 — p95 will
    # sit between them so the fat print flags but the small ones do not
    out = aggregate_2min(df)
    row = out.iloc[0]
    assert row["n_prints_over_threshold"] == 1
    assert row["top_prints"][0]["premium"] == 10000.0
