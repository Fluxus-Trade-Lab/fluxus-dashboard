"""The three windows the Themes page offers must all ship an excess.

Two of them did. 1M did not, so the frontend derived it in the browser from
perf_1m and a separately-fetched SPY row -- one construction implemented
twice, in two languages, which is the arrangement that once put two disagreeing
accelerations on one page. These tests pin the contract so the middle window
cannot quietly go missing again.
"""
from __future__ import annotations

import inspect

import pytest

from pipeline.themes import rs_engine


# Numbers chosen so every window's answer is exact in binary-friendly decimals
# and no two windows share a value -- a test that passes because everything is
# 0.0 proves the fields exist, not that they are wired to the right columns.
BENCH = {"perf_1w": 0.01, "perf_1m": 0.04, "perf_3m": 0.05, "perf_6m": 0.10}
ROW = {"perf_1w": 0.03, "perf_1m": 0.10, "perf_3m": 0.20, "perf_6m": 0.25}


def test_excess_1m_is_the_one_month_difference():
    assert rs_engine.excess_1m(ROW, BENCH) == pytest.approx(0.10 - 0.04)


def test_each_window_reads_its_own_column():
    """The failure this catches is a copy-paste onto the wrong perf column."""
    assert rs_engine.excess_1m(ROW, BENCH) != pytest.approx(
        rs_engine.excess_3m(ROW, BENCH))
    assert rs_engine.excess_3m(ROW, BENCH) == pytest.approx(0.20 - 0.05)


def test_payload_carries_all_three_page_windows():
    """rs_0_1w / excess_1m / excess_3m are what the window buttons read."""
    payload = rs_engine.score_row(ROW, BENCH)
    for field in ("rs_0_1w", "excess_1m", "excess_3m"):
        assert payload[field] is not None, f"{field} missing from score_row"


def test_one_week_excess_reduces_to_the_raw_difference():
    """The first disjoint bucket has nothing chained off it, so 1W excess is
    plain subtraction -- the identity the page's 1W button relies on."""
    payload = rs_engine.score_row(ROW, BENCH)
    assert payload["rs_0_1w"] == pytest.approx(0.03 - 0.01)


def test_excess_1m_is_display_only():
    """`classify` takes the 3M level and the acceleration gate, and nothing
    else. If a future edit routes the 1M level into it, the four states change
    meaning and the 139-ETF validation behind them stops describing what ships.

    Asserted on the signature rather than on outputs: a value test here would
    pass whatever the parameters were, because perf_1m also feeds the
    acceleration gate and cannot be varied independently."""
    params = list(inspect.signature(rs_engine.classify).parameters)
    assert params == ["excess_3m", "rs_accel"], (
        f"classify's inputs changed to {params} -- the four states are only "
        "validated for (excess_3m, rs_accel)")


def test_the_two_level_columns_stay_separate():
    """_NEAR_COL feeds the acceleration gate, _LEVEL_1M_COL feeds the display.
    They hold the same string today; collapsing them into one constant would
    make a re-validation of the gate silently move the page's 1M window."""
    assert rs_engine._LEVEL_1M_COL == "perf_1m"
    assert rs_engine._LEVEL_COL == "perf_3m"
