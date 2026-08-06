"""Tests for spread-leg detection and netting."""
import pandas as pd
import pytest

from pipeline.flow.spreads import (
    ClassifiedPrint, SpreadPair,
    detect_spreads, net_spread_premium,
)


def _ts(ms_offset=0):
    return pd.Timestamp("2026-07-15 10:00:00", tz="UTC") + pd.Timedelta(
        milliseconds=ms_offset)


def _print(strike, right, size, premium, aggressor, ms=0):
    return ClassifiedPrint(
        timestamp=_ts(ms),
        strike=strike, right=right, size=size,
        premium=premium, aggressor=aggressor,
    )


class TestDetectSpreads:
    def test_perfect_vertical_call_spread(self):
        prints = [
            _print(7550, "C", 10, 15000, "BOT", ms=0),
            _print(7555, "C", 10, 8000, "SOLD", ms=0),
        ]
        pairs, singles = detect_spreads(prints)
        assert len(pairs) == 1
        assert len(singles) == 0
        assert pairs[0].buy_leg.strike == 7550
        assert pairs[0].sell_leg.strike == 7555
        assert pairs[0].net_premium == 15000 - 8000

    def test_perfect_vertical_put_spread(self):
        prints = [
            _print(7560, "P", 5, 6000, "SOLD", ms=0),
            _print(7550, "P", 5, 10000, "BOT", ms=0),
        ]
        pairs, singles = detect_spreads(prints)
        assert len(pairs) == 1
        assert pairs[0].buy_leg.strike == 7550
        assert pairs[0].sell_leg.strike == 7560

    def test_no_match_different_sizes(self):
        prints = [
            _print(7550, "C", 10, 15000, "BOT", ms=0),
            _print(7555, "C", 5, 4000, "SOLD", ms=0),
        ]
        pairs, singles = detect_spreads(prints)
        assert len(pairs) == 0
        assert len(singles) == 2

    def test_no_match_same_aggressor(self):
        prints = [
            _print(7550, "C", 10, 15000, "BOT", ms=0),
            _print(7555, "C", 10, 8000, "BOT", ms=0),
        ]
        pairs, singles = detect_spreads(prints)
        assert len(pairs) == 0
        assert len(singles) == 2

    def test_no_match_different_right(self):
        prints = [
            _print(7550, "C", 10, 15000, "BOT", ms=0),
            _print(7555, "P", 10, 8000, "SOLD", ms=0),
        ]
        pairs, singles = detect_spreads(prints)
        assert len(pairs) == 0
        assert len(singles) == 2

    def test_no_match_too_wide_strike_gap(self):
        prints = [
            _print(7550, "C", 10, 15000, "BOT", ms=0),
            _print(7570, "C", 10, 3000, "SOLD", ms=0),
        ]
        pairs, singles = detect_spreads(prints, max_strike_gap=3,
                                         strike_spacing=5.0)
        assert len(pairs) == 0
        assert len(singles) == 2

    def test_within_max_lag(self):
        prints = [
            _print(7550, "C", 10, 15000, "BOT", ms=0),
            _print(7555, "C", 10, 8000, "SOLD", ms=400),
        ]
        pairs, singles = detect_spreads(prints, max_lag_ms=500)
        assert len(pairs) == 1

    def test_exceeds_max_lag(self):
        prints = [
            _print(7550, "C", 10, 15000, "BOT", ms=0),
            _print(7555, "C", 10, 8000, "SOLD", ms=600),
        ]
        pairs, singles = detect_spreads(prints, max_lag_ms=500)
        assert len(pairs) == 0
        assert len(singles) == 2

    def test_same_strike_no_match(self):
        prints = [
            _print(7550, "C", 10, 15000, "BOT", ms=0),
            _print(7550, "C", 10, 14000, "SOLD", ms=0),
        ]
        pairs, singles = detect_spreads(prints)
        assert len(pairs) == 0
        assert len(singles) == 2

    def test_unknown_aggressor_skipped(self):
        prints = [
            _print(7550, "C", 10, 15000, "UNKNOWN", ms=0),
            _print(7555, "C", 10, 8000, "SOLD", ms=0),
        ]
        pairs, singles = detect_spreads(prints)
        assert len(pairs) == 0
        assert len(singles) == 2

    def test_multiple_pairs(self):
        prints = [
            _print(7550, "C", 10, 15000, "BOT", ms=0),
            _print(7555, "C", 10, 8000, "SOLD", ms=0),
            _print(7560, "P", 20, 30000, "BOT", ms=100),
            _print(7555, "P", 20, 22000, "SOLD", ms=100),
        ]
        pairs, singles = detect_spreads(prints)
        assert len(pairs) == 2
        assert len(singles) == 0

    def test_mixed_spreads_and_singles(self):
        prints = [
            _print(7550, "C", 10, 15000, "BOT", ms=0),
            _print(7555, "C", 10, 8000, "SOLD", ms=0),
            _print(7560, "C", 50, 80000, "BOT", ms=200),
        ]
        pairs, singles = detect_spreads(prints)
        assert len(pairs) == 1
        assert len(singles) == 1
        assert singles[0].strike == 7560

    def test_empty_list(self):
        pairs, singles = detect_spreads([])
        assert len(pairs) == 0
        assert len(singles) == 0

    def test_single_print(self):
        prints = [_print(7550, "C", 10, 15000, "BOT")]
        pairs, singles = detect_spreads(prints)
        assert len(pairs) == 0
        assert len(singles) == 1

    def test_greedy_matching_first_match_wins(self):
        prints = [
            _print(7550, "C", 10, 15000, "BOT", ms=0),
            _print(7555, "C", 10, 8000, "SOLD", ms=0),
            _print(7560, "C", 10, 5000, "SOLD", ms=0),
        ]
        pairs, singles = detect_spreads(prints)
        assert len(pairs) == 1
        assert pairs[0].sell_leg.strike == 7555
        assert len(singles) == 1
        assert singles[0].strike == 7560

    def test_strike_gap_recorded(self):
        prints = [
            _print(7550, "C", 10, 15000, "BOT", ms=0),
            _print(7560, "C", 10, 6000, "SOLD", ms=0),
        ]
        pairs, _ = detect_spreads(prints, max_strike_gap=3,
                                   strike_spacing=5.0)
        assert len(pairs) == 1
        assert pairs[0].strike_gap == 10.0

    def test_custom_strike_spacing(self):
        prints = [
            _print(7550, "C", 10, 15000, "BOT", ms=0),
            _print(7575, "C", 10, 6000, "SOLD", ms=0),
        ]
        pairs_narrow, _ = detect_spreads(prints, max_strike_gap=3,
                                          strike_spacing=5.0)
        assert len(pairs_narrow) == 0
        pairs_wide, _ = detect_spreads(prints, max_strike_gap=3,
                                        strike_spacing=10.0)
        assert len(pairs_wide) == 1


class TestNetSpreadPremium:
    def test_basic_netting(self):
        prints = [
            _print(7550, "C", 10, 15000, "BOT", ms=0),
            _print(7555, "C", 10, 8000, "SOLD", ms=0),
            _print(7560, "C", 50, 80000, "BOT", ms=200),
        ]
        pairs, singles = detect_spreads(prints)
        result = net_spread_premium(pairs, singles)
        assert result["bot_premium"] == 80000
        assert result["sold_premium"] == 0
        assert result["spread_premium"] == 7000
        assert result["n_spreads"] == 1
        assert result["n_singles"] == 1

    def test_all_singles(self):
        prints = [
            _print(7550, "C", 10, 15000, "BOT", ms=0),
            _print(7560, "C", 50, 80000, "SOLD", ms=500),
        ]
        pairs, singles = detect_spreads(prints)
        result = net_spread_premium(pairs, singles)
        assert result["bot_premium"] == 15000
        assert result["sold_premium"] == 80000
        assert result["n_spreads"] == 0

    def test_empty(self):
        result = net_spread_premium([], [])
        assert result["bot_premium"] == 0
        assert result["sold_premium"] == 0
        assert result["spread_premium"] == 0
