"""The arithmetic that decides whether a claim about skill is even askable."""
from __future__ import annotations

import pytest

from pipeline.reference import power as P


# --- against a textbook baseline ----------------------------------------

def test_sessions_needed_matches_the_standard_result():
    """One-proportion power, 60% vs 50%, alpha=.05 one-sided, 80% power.

    The closed form gives 152.x, so 153 whole sessions. Checked against the
    general rule of thumb n ~= (z_a+z_b)^2 * p(1-p) / d^2 = 6.18*0.25/0.01
    ~= 155, which the exact two-variance form tightens slightly because p1's
    variance is smaller. Rounding is UP: a fractional session buys nothing.
    """
    assert P.sessions_needed(0.60) == 153


def test_a_smaller_edge_costs_far_more_than_proportionally():
    # Halving the edge roughly quadruples the sample -- the fact that makes
    # small-edge claims practically undecidable on a daily cadence.
    assert P.sessions_needed(0.55) == 617
    assert P.sessions_needed(0.55) / P.sessions_needed(0.60) == pytest.approx(4, abs=0.2)


def test_a_zero_effect_is_refused_rather_than_returned_as_huge():
    with pytest.raises(ValueError, match="name the edge you are claiming"):
        P.sessions_needed(0.5)


def test_power_rises_with_n_and_with_the_edge():
    assert P.power(20, 0.60) < P.power(200, 0.60)
    assert P.power(50, 0.55) < P.power(50, 0.75)


def test_power_at_the_null_is_the_alpha_it_was_given():
    assert P.power(500, 0.5 + 1e-9, 0.5, alpha=0.05) == pytest.approx(0.05, abs=1e-3)


def test_power_and_sessions_needed_agree_at_the_boundary():
    for p in (0.55, 0.60, 0.65, 0.70):
        n = P.sessions_needed(p)
        assert P.power(n, p) >= 0.80
        assert P.power(n - 1, p) < 0.805  # not wildly over-shooting


# --- the finding that prompted the module -------------------------------

def test_the_shipped_gate_of_20_is_underpowered_for_a_ten_point_edge():
    v = P.verdict(20, 0.60)
    assert v["status"] == "underpowered"
    assert v["power"] < 0.25
    assert v["short_by"] == 133


def test_twenty_sessions_can_only_see_a_very_large_edge():
    f = P.detectable(20)
    assert 0.70 < f < 0.80  # anything smaller is invisible at n=20


def test_six_sessions_the_machines_actual_sample_see_nothing_useful():
    # The live scorecard sits at n=6 with a 33% hit rate. That is not evidence
    # of a bad model; it is not evidence of anything.
    assert P.interval(6) > 0.39
    f = P.detectable(6)
    assert f is None or f > 0.90


def test_interval_defaults_to_the_widest_case():
    # p=0.5 maximises the variance, so the default must not flatter the sample.
    assert P.interval(100) >= P.interval(100, p=0.3)


# --- probes are not free -------------------------------------------------

def test_family_error_grows_with_the_number_of_probes():
    assert P.family_error(1) == pytest.approx(0.05)
    assert P.family_error(20) == pytest.approx(0.642, abs=0.002)


def test_the_forty_two_mined_sequences_were_almost_certain_to_show_a_winner():
    """0 of 42 beat a matched baseline -- and 42 probes throw a false positive
    88% of the time, so the first run's +4.4% was the expected artifact."""
    assert P.family_error(42) > 0.88


def test_zero_probes_cannot_be_wrong():
    assert P.family_error(0) == 0.0


# --- the verdict is a statement, never a boolean -------------------------

def test_verdict_says_what_it_is_short_by_and_what_it_could_see():
    v = P.verdict(60, 0.65)
    assert set(v) >= {"power", "sessions_needed", "short_by",
                      "smallest_detectable", "status", "note"}
    assert "trading years" in v["note"]
    assert isinstance(v["status"], str)  # not a bool


def test_a_sufficient_sample_is_marked_decidable():
    v = P.verdict(200, 0.60)
    assert v["status"] == "decidable"
    assert v["short_by"] == 0


def test_report_states_the_cost_of_every_edge_it_lists():
    r = P.report()
    assert "trading years" in r
    assert "no edge reliably visible" in r or "smallest visible edge" in r
    assert "false positive" in r


def test_bad_inputs_raise_rather_than_returning_a_plausible_number():
    with pytest.raises(ValueError):
        P.power(0, 0.6)
    with pytest.raises(ValueError):
        P.power(10, 1.0)
    with pytest.raises(ValueError):
        P.interval(0)
    with pytest.raises(ValueError):
        P.family_error(-1)


# --- the frontier: what is knowable on a daily cadence -------------------

def test_a_rare_setup_needs_calendar_years_even_with_a_big_edge():
    # 10-condition pattern, 75% hit rate, fires ~4x a year.
    d = P.years_to_decide(0.75, fires_per_year=4)
    assert d["occurrences_needed"] == 23
    assert d["years"] > 5
    assert d["decidable_within_3y"] is False


def test_the_same_edge_becomes_decidable_when_the_setup_is_common():
    d = P.years_to_decide(0.75, fires_per_year=26)  # ~twice a month
    assert d["years"] < 1
    assert d["decidable_within_3y"] is True


def test_a_daily_signal_with_a_small_edge_is_the_slow_case():
    # Fires every session, but only 60/50 -- still most of a year.
    d = P.years_to_decide(0.60, fires_per_year=252)
    assert 0.5 < d["years"] < 0.7


def test_a_setup_that_never_fires_is_refused_not_returned_as_infinite():
    with pytest.raises(ValueError, match="never fires"):
        P.years_to_decide(0.70, fires_per_year=0)


def test_frontier_marks_which_cells_are_reachable():
    f = P.frontier()
    assert "settled inside 3 years" in f
    assert "." in f
