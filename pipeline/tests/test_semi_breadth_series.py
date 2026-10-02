"""Gates on the semiconductor-pool breadth series (T-1002-80).

The study is `data/research/semi_breadth_2026-10-02/build_series.py`. It
restates four thresholds that live in `pipeline/screeners/breadth_metrics.py`
(0.1% extreme tolerance, 200-bar floor for 52-week extremes, 20-bar floor for
4-week extremes, excluded industries) because it builds a daily series from
bars while production reads one Finviz snapshot. Restating is the defect
surface, so each threshold is probed from BOTH sides here -- one name just
inside and one just outside. A one-sided probe passes for a gate that was
wired to always-true, which is how the 252-bar floor in the first version of
`panels()` went unnoticed: it only ever showed up as a denominator one short.

The script's own `verify_control()` checks a different thing -- that the
rulers agree with the published snapshot on one real session. These are the
unit gates; that is the calibration.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "data/research/semi_breadth_2026-10-02/build_series.py"

pytestmark = pytest.mark.skipif(not SCRIPT.exists(), reason="study not present")

DATES = pd.bdate_range("2024-09-02", periods=600)


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("semi_breadth_series", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _frame(closes, highs=None, lows=None) -> pd.DataFrame:
    """One name's bars, right-aligned on the date index so `len` is its age."""
    idx = DATES[-len(closes):]
    return pd.DataFrame({"High": highs if highs is not None else closes,
                         "Low": lows if lows is not None else closes,
                         "Close": closes}, index=idx, dtype=float)


def _day(mod, bars: dict, industry: dict | None = None):
    panel = mod.panels(bars)
    industry = industry or {t: "Semiconductors" for t in bars}
    return mod.count_day(panel, sorted(bars), industry, DATES[-1])


def test_above_50sma_counts_and_denominator(mod):
    out = _day(mod, {"UP": _frame([100.0] * 299 + [200.0]),
                     "DOWN": _frame([200.0] * 299 + [100.0])})
    assert (out["n50"], out["a50"]) == (2, 1)
    assert mod.pct(out["a50"], out["n50"]) == 50.0


def test_a_name_without_50_bars_is_not_in_the_denominator(mod):
    # Production reads Finviz's sma50_dist, which is NULL before 50 bars. A
    # young name must be absent from the denominator, not scored as "below".
    out = _day(mod, {"OLD": _frame([100.0] * 299 + [200.0]),
                     "NEW": _frame([50.0] * 30)})
    assert out["n50"] == 1
    assert mod.pct(out["a50"], out["n50"]) == 100.0
    assert out["present"] == 2


def test_pct_is_null_not_zero_on_an_empty_denominator(mod):
    # A 0.0 here would read as "every semi is below its 50-day" -- the most
    # alarming possible rendering of a missing input.
    assert mod.pct(0, 0) is None
    assert mod.pct(0, 1) == 0.0


@pytest.mark.parametrize("bars_n, gated, counted", [
    (200, 1, 1),   # exactly at MIN_BARS_52W -> inside
    (199, 0, 0),   # one bar short -> outside
])
def test_the_52_week_floor_is_200_bars_not_the_window_length(mod, bars_n, gated, counted):
    # The regression this file exists for. With min_periods left at the pandas
    # default the floor silently becomes 252, and the only visible symptom is
    # a denominator one short -- which no one-sided test would catch.
    closes = [100.0] * (bars_n - 1) + [300.0]
    out = _day(mod, {"PEAK": _frame(closes)})
    assert out["g52"] == gated
    assert out["nh52"] == counted


@pytest.mark.parametrize("bars_n, gated", [(20, 1), (19, 0)])
def test_the_4_week_floor_is_20_bars(mod, bars_n, gated):
    out = _day(mod, {"PEAK": _frame([100.0] * (bars_n - 1) + [300.0])})
    assert out["g4"] == gated
    assert out["nh4"] == gated


@pytest.mark.parametrize("gap, expected", [(0.0005, 1), (0.005, 0)])
def test_new_high_tolerance_is_one_tenth_of_a_percent(mod, gap, expected):
    # Only the close moves between the two cases: the 252-session high is set
    # by the same last bar either way, so nothing but the tolerance decides.
    highs = [100.0] * 299 + [300.0]
    closes = [100.0] * 299 + [300.0 * (1 - gap)]
    out = _day(mod, {"PEAK": _frame(closes, highs=highs)})
    assert out["nh52"] == expected


@pytest.mark.parametrize("gap, expected", [(0.0005, 1), (0.005, 0)])
def test_new_low_tolerance_is_one_tenth_of_a_percent(mod, gap, expected):
    lows = [100.0] * 299 + [10.0]
    closes = [100.0] * 299 + [10.0 * (1 + gap)]
    out = _day(mod, {"TROUGH": _frame(closes, lows=lows)})
    assert out["nl52"] == expected


def test_52_week_extremes_use_intraday_prices_not_closes(mod):
    # Finviz's 52-week range is built on intraday highs. A name that printed a
    # higher high three weeks ago and closes at a new CLOSING high today must
    # not count -- that distinction is the study's negative control arm, and
    # it has to hold in the counting path too.
    closes = [100.0] * 280 + [150.0] * 19 + [200.0]
    highs = [100.0] * 280 + [260.0] + [150.0] * 18 + [200.0]
    out = _day(mod, {"NEAR": _frame(closes, highs=highs)})
    assert out["nh52"] == 0
    assert out["g52"] == 1


def test_excluded_industry_drops_out_of_the_extreme_counts_only(mod):
    peak = [100.0] * 299 + [300.0]
    out = _day(mod, {"SPAC": _frame(peak), "REAL": _frame(peak)},
               industry={"SPAC": "Shell Companies", "REAL": "Semiconductors"})
    assert (out["g52"], out["nh52"]) == (1, 1)
    # Both stay in the percent-above pools: production's pct_above_50sma has
    # no industry gate (breadth_metrics.py:222 counts the whole universe).
    assert out["n50"] == 2
    assert out["present"] == 2


def test_the_published_pool_is_the_three_theme_groups(mod):
    pool = mod.load_pool(ROOT)
    assert pool["as_of"] == "2026-10-01"
    assert set(pool["groups"]) == set(mod.GROUPS)
    assert len(pool["pool"]) == 120
    # Union, not sum: the three groups overlap.
    assert len(pool["pool"]) < sum(len(v) for v in pool["groups"].values())
