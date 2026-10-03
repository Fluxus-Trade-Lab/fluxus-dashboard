"""Gates on the SMH-vs-SOXX internal-breadth series (T-1004-10).

The study is `data/research/semi_etf_breadth_2026-10-04/build_series.py`. It
reuses the rulers already gated by `test_semi_breadth_series.py` (T-1002-80),
so this file does not re-probe those tolerances. What is new here, and what
these tests are for, is the **weighted arm**: the same breadth question
answered with each name counted at its index weight instead of as one name.

The weighted arm has two ways to be quietly wrong, and both of them produce a
plausible-looking series:

1. the sign could be inverted (returning the weight *below* the line), which
   on a basket whose heavy names lead looks like a smaller gap, not a bug;
2. the denominator could be the full published weight instead of the weight of
   the names that actually have the reading that day, which makes the arm read
   low by exactly the weight of whatever is missing -- the same shape as the
   252-vs-200-bar floor that went unnoticed in T-1002-80.

So every weighted test below is two-sided: the heavy name is put on each side
of the line in turn, and the expected number is written out as a literal
rather than derived from the weight dict the code reads.
"""
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / "data/research/semi_etf_breadth_2026-10-04"
SCRIPT = STUDY / "build_series.py"

pytestmark = pytest.mark.skipif(not SCRIPT.exists(), reason="study not present")

DATES = pd.bdate_range("2024-09-02", periods=600)


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("semi_etf_breadth_series", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _frame(closes, highs=None, lows=None) -> pd.DataFrame:
    """One name's bars, right-aligned on the date index so `len` is its age."""
    idx = DATES[-len(closes):]
    return pd.DataFrame({"High": highs if highs is not None else closes,
                         "Low": lows if lows is not None else closes,
                         "Close": closes}, index=idx, dtype=float)


def _up(n=300):
    return _frame([100.0] * (n - 1) + [200.0])


def _down(n=300):
    return _frame([200.0] * (n - 1) + [100.0])


def _day(mod, bars: dict, weights: dict, industry: dict | None = None):
    panel = mod.panels(bars)
    industry = industry or {t: "Semiconductors" for t in bars}
    return mod.count_day(panel, weights, industry, DATES[-1])


# ── the weighted arm ─────────────────────────────────────────────────────

def test_weighted_arm_counts_weight_not_names(mod):
    """Heavy name above, light name below: equal says 50, weighted says 90."""
    out = _day(mod, {"HEAVY": _up(), "LIGHT": _down()},
               {"HEAVY": 90.0, "LIGHT": 10.0})
    assert out["eq_pct_above_50sma"] == 50.0
    assert out["wt_pct_above_50sma"] == 90.0


def test_weighted_arm_is_the_share_above_not_below(mod):
    """Mirror of the above. A sign flip passes the first test and fails here."""
    out = _day(mod, {"HEAVY": _down(), "LIGHT": _up()},
               {"HEAVY": 90.0, "LIGHT": 10.0})
    assert out["eq_pct_above_50sma"] == 50.0
    assert out["wt_pct_above_50sma"] == 10.0


def test_weighted_denominator_drops_a_name_with_no_50d_sma(mod):
    """YOUNG has 40 bars, so it has no 50-day average and belongs to neither
    arm's denominator. Taking the full published weight instead would read
    75.0 (90 of 120) rather than 100.0 (90 of 90)."""
    out = _day(mod, {"HEAVY": _up(), "YOUNG": _up(40)},
               {"HEAVY": 90.0, "YOUNG": 30.0})
    assert out["n_present"] == 2
    assert out["n_with_sma50"] == 1
    assert out["eq_pct_above_50sma"] == 100.0
    assert out["wt_pct_above_50sma"] == 100.0


def test_weighted_denominator_drops_the_young_name_on_both_sides(mod):
    """Same basket, HEAVY now below the line. 0.0, not 25.0 (30 of 120)."""
    out = _day(mod, {"HEAVY": _down(), "YOUNG": _up(40)},
               {"HEAVY": 90.0, "YOUNG": 30.0})
    assert out["eq_pct_above_50sma"] == 0.0
    assert out["wt_pct_above_50sma"] == 0.0


def test_a_name_absent_from_the_panel_is_not_counted_as_below(mod):
    """A holding with no bars at all must leave both arms alone, not read as
    a name below its average -- that would understate breadth by one name."""
    panel = mod.panels({"HEAVY": _up()})
    out = mod.count_day(panel, {"HEAVY": 90.0, "DELISTED": 10.0},
                        {"HEAVY": "Semiconductors"}, DATES[-1])
    assert out["n_present"] == 1
    assert out["eq_pct_above_50sma"] == 100.0
    assert out["wt_pct_above_50sma"] == 100.0


def test_equal_and_weighted_arms_diverge_in_both_directions(mod):
    """The study's headline is the sign of (weighted - equal). Build a basket
    where that sign is known, then invert it."""
    heavy_leads = _day(mod, {"BIG": _up(), "S1": _down(), "S2": _down(), "S3": _down()},
                       {"BIG": 70.0, "S1": 10.0, "S2": 10.0, "S3": 10.0})
    assert heavy_leads["eq_pct_above_50sma"] == 25.0
    assert heavy_leads["wt_pct_above_50sma"] == 70.0

    heavy_lags = _day(mod, {"BIG": _down(), "S1": _up(), "S2": _up(), "S3": _up()},
                      {"BIG": 70.0, "S1": 10.0, "S2": 10.0, "S3": 10.0})
    assert heavy_lags["eq_pct_above_50sma"] == 75.0
    assert heavy_lags["wt_pct_above_50sma"] == 30.0


def test_pct_is_null_not_zero_on_an_empty_denominator(mod):
    assert mod.pct(0, 0) is None
    out = _day(mod, {"YOUNG": _up(40)}, {"YOUNG": 100.0})
    assert out["n_present"] == 1
    assert out["eq_pct_above_50sma"] is None
    assert out["wt_pct_above_50sma"] is None


# ── the rulers stay tied to production ───────────────────────────────────

def test_restated_rulers_match_breadth_metrics(mod):
    """The four thresholds are restated, not imported (production reads one
    Finviz snapshot; this reads bars). Drift between the two is the defect, so
    compare against the live module rather than against a literal here."""
    from pipeline.screeners import breadth_metrics as bm
    assert mod.NEW_HIGH_THRESHOLD == bm._NEW_HIGH_THRESHOLD
    assert mod.NEW_LOW_THRESHOLD == bm._NEW_LOW_THRESHOLD
    assert mod.EXCLUDED_INDUSTRIES == bm._EXCLUDED_INDUSTRIES
    assert mod.MIN_BARS_52W == bm._MIN_BARS_52W
    assert mod.MIN_BARS_4W == bm._MIN_BARS_4W


@pytest.mark.parametrize("bars_n, gated", [(199, 0), (200, 1)])
def test_the_52_week_floor_is_200_bars_on_this_code_path_too(mod, bars_n, gated):
    """T-1002-80's `panels()` once imposed a 252-bar floor by leaving
    `min_periods` at the pandas default. This script copied `panels()`, so the
    floor is probed from both sides here as well."""
    out = _day(mod, {"X": _frame([100.0] * bars_n)}, {"X": 100.0})
    assert out["n_gate_52w"] == gated


def test_excluded_industry_leaves_the_percentages_alone(mod):
    """`Shell Companies` drops out of the extreme counts only -- the two
    breadth arms still see the name. Production draws the same line
    (breadth_metrics.py:108 vs :360)."""
    bars = {"SHELL": _up(), "REAL": _down()}
    out = _day(mod, bars, {"SHELL": 50.0, "REAL": 50.0},
               {"SHELL": "Shell Companies", "REAL": "Semiconductors"})
    assert out["n_gate_52w"] == 1
    assert out["eq_pct_above_50sma"] == 50.0
    assert out["wt_pct_above_50sma"] == 50.0


# ── the committed artefacts agree with each other ────────────────────────

def test_holdings_files_and_published_facts_agree():
    """`etf_facts.json` is what the write-up quotes; the holdings CSVs are the
    issuer snapshots it was built from. A re-download that changed the basket
    without a rebuild shows up here."""
    facts = json.loads((STUDY / "etf_facts.json").read_text())
    for etf, fname in (("SMH", "holdings_smh_2026-10-01.csv"),
                       ("SOXX", "holdings_soxx_2026-10-01.csv")):
        rows = list(csv.DictReader((STUDY / fname).open()))
        weights = [float(r["weight_pct"]) for r in rows]
        assert facts["etfs"][etf]["n_equity_holdings"] == len(rows)
        assert facts["etfs"][etf]["max_weight_pct"] == round(max(weights), 2)
        assert 95.0 < sum(weights) < 101.0
        assert fname.endswith(facts["holdings_as_of"] + ".csv")


def test_series_covers_both_etfs_over_the_published_window():
    facts = json.loads((STUDY / "etf_facts.json").read_text())
    rows = list(csv.DictReader((STUDY / "semi_etf_breadth_series.csv").open()))
    assert [rows[0]["date"], rows[-1]["date"]] == facts["window"]
    for side in ("smh", "soxx"):
        for col in ("eq_pct_above_50sma", "wt_pct_above_50sma",
                    "eq_pct_above_200sma", "new_highs_52w", "etf_dist_52w_high"):
            assert all(r[f"{side}_{col}"] != "" for r in rows), f"{side}_{col} has gaps"
