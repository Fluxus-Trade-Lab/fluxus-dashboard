"""Screener cap floor (Andy 2026-09-18 「哦市值这个闸是要加上的。」)."""
import math

import pandas as pd

from pipeline.screeners.universe_gate import GATED_SCREENERS, cap_floor


def test_floor_is_one_billion_and_inclusive():
    u = pd.DataFrame({"ticker": list("ABCD"), "market_cap": [1e9, 9.99e8, 5e10, 0]})
    assert list(cap_floor(u)["ticker"]) == ["A", "C"]


def test_missing_or_bad_cap_is_below_the_floor():
    u = pd.DataFrame({"ticker": list("ABC"), "market_cap": [None, math.nan, "n/a"]})
    assert cap_floor(u).empty


def test_frame_without_the_column_passes_through_unchanged():
    u = pd.DataFrame({"ticker": ["A"]})
    assert cap_floor(u) is u


def test_the_five_lists_that_had_no_floor():
    assert set(GATED_SCREENERS) == {"momentum_97", "gainers_4pct", "vol_up_gainers",
                                    "ema21_watch", "healthy_charts",
                                    "ep_stockbee", "ep_qullamaggie"}


def test_both_ep_screeners_run_on_the_capped_universe():
    """Andy 09-18 「市值这个闸是要加上的」 applies to the new EP lists too."""
    assert {"ep_stockbee", "ep_qullamaggie"} <= set(GATED_SCREENERS)
