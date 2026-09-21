"""Sugar Babies = Stockbee's top 30 by 9 million EPs (Andy 2026-09-21 「B 照建议做」).

Pradeep, Investors Underground interview (YouTube A_0ep4ekGWM): "stocks which
have high number of 9 million EPs in a given period", six months or a year,
25-30 names. Until 2026-09-21 the preset counted 4% breakouts and used our own
10 / 2 thresholds, and the Short List read a long roster streak as contrarian.
"""
import numpy as np
import pandas as pd

from pipeline.adapters.yfinance_adapter import ep9m_days
from pipeline.screeners import preset_hits
from pipeline.screeners.name_cards import verdict
from pipeline.screeners.sugar_babies import TOP_N, ranks


def _bars(base_vol, chg, vol_today, n=80):
    c = np.full(n, 10.0); c[-1] = 10.0 * (1 + chg)
    v = np.full(n, float(base_vol)); v[-1] = vol_today
    return c, v


def test_neglected_then_9m_is_an_ep9m():
    assert ep9m_days(*_bars(1_000_000, 0.05, 9_000_000))[-1]


def test_a_name_that_trades_9m_every_day_is_not():
    # the bare 9M rule counted this; his "neglected, then 9M" does not
    assert not ep9m_days(*_bars(20_000_000, 0.05, 25_000_000))[-1]


def test_a_spike_under_9m_is_not():
    assert not ep9m_days(*_bars(100_000, 0.10, 2_000_000))[-1]


def test_needs_more_than_4pct_up():
    assert not ep9m_days(*_bars(1_000_000, 0.04, 9_000_000))[-1]


def test_no_average_no_claim():
    c, v = _bars(1_000_000, 0.05, 9_000_000, n=40)   # < 50 prior bars
    assert not ep9m_days(c, v).any()


def _universe(rows):
    return pd.DataFrame(rows, columns=["ticker", "market_cap", "ep9m_count_6m", "ep9m_count_1y"])


def test_rank_is_top_30_by_6m_then_1y_then_ticker():
    rows = [(f"T{i:02d}", 5e9, 40 - i, 0) for i in range(35)]
    rows += [("AAA", 5e9, 40, 3), ("AAB", 5e9, 40, 3), ("SMALL", 5e8, 99, 99), ("ZERO", 5e9, 0, 9)]
    u = _universe(rows)
    r = ranks(u).set_axis(u["ticker"])
    assert r["AAA"] == 1 and r["AAB"] == 2 and r["T00"] == 3      # tie -> 1y -> ticker
    assert pd.isna(r["SMALL"]) and pd.isna(r["ZERO"])           # $1B floor; zero events out
    assert int(r.notna().sum()) == TOP_N == 30


def test_preset_is_the_rank_not_our_old_thresholds():
    sb = next(p for p in preset_hits.load_presets() if p["name"] == "Sugar Babies")
    f = sb["filters"]
    assert "boCount1y" not in f and "boCount3m" not in f
    assert f["sugarRank"]["min"] == 1 and f["sugarRank"]["max"] == 30
    assert preset_hits.passes({"market_cap": 5e9, "sugar_rank": 7}, f)
    assert not preset_hits.passes({"market_cap": 5e9, "sugar_rank": None}, f)


def test_short_list_no_longer_reads_the_roster_as_contrarian():
    text = verdict({"atr_from_sma50": 2.0}, None, False, [], roster_streak=9)
    assert "反指" not in text and "Sugar Babies" not in text
