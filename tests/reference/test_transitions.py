"""GEX as states and transitions — and what the module refuses to claim."""
import pytest

from pipeline.reference import transitions as T


def _series(vals, start=3):
    return [(f"2026-08-{start+i:02d}", v) for i, v in enumerate(vals)]


def test_boundaries_are_percentiles_of_our_own_series_not_dollar_levels():
    # His -5B "collapse" is routine for us; a ported threshold would be a
    # statement about HIS distribution.
    small = T.state_boundaries([-2.0, -1.0, 0.0, 1.0, 2.0])
    large = T.state_boundaries([-20.0, -10.0, 0.0, 10.0, 20.0])
    assert small != large
    assert max(small) < max(large)


def test_speed_counts_state_boundaries_crossed_not_dollars():
    rows = T.transitions(_series([-20.0, -10.0, 0.0, 10.0, 20.0, -20.0]))
    assert rows[-1]["speed"] >= 3          # top of the range to the bottom
    assert rows[-1]["direction"] == "erosion"


def test_a_move_that_stays_inside_one_state_is_speed_zero():
    # Needs a sample big enough that a percentile cut does not land BETWEEN two
    # near-identical values. On six points it did, splitting 0.0 from 0.05 into
    # adjacent states -- the small-sample artefact MIN_HISTORY exists to flag,
    # and one our own twenty-session series is still subject to.
    vals = [-30.0, -20.0, -12.0, -6.0, -1.0, 0.0, 0.1, 6.0, 12.0, 20.0, 30.0]
    bounds = T.state_boundaries(vals)
    assert T.classify(0.0, bounds) == T.classify(0.1, bounds)
    rows = {r["session"]: r for r in T.transitions(_series(vals))}
    held = [r for r in rows.values() if r["speed"] == 0]
    assert held and all(r["direction"] == "held" for r in held)


def test_rebuild_and_erosion_are_named_by_direction():
    rows = T.transitions(_series([-20.0, 20.0, 0.0, 10.0, -10.0]))
    assert rows[0]["direction"] == "rebuild"


def test_notable_keeps_only_transitions_that_skipped_states():
    rows = T.transitions(_series([-20.0, -10.0, 0.0, 10.0, 20.0, 0.0]))
    assert all(r["speed"] >= 2 for r in T.notable(rows))


def test_a_thin_history_is_flagged_uncalibrated():
    rows = T.transitions(_series([1.0, 2.0, 3.0]))
    assert rows[0]["calibrated"] is False
    assert rows[0]["n_history"] == 3


def test_the_summary_refuses_to_call_itself_testable_on_our_sample():
    # The source's strongest finding fires ~1 in 950 sessions. With twenty we
    # would expect 0.02 of them.
    rows = T.transitions(_series([float(i) for i in range(20)]))
    s = T.summary(rows)
    assert s["testable"] is False
    assert "950" in s["note"] and "short" in s["note"]


def test_an_empty_or_single_point_series_yields_nothing():
    assert T.transitions([]) == []
    assert T.transitions(_series([1.0])) == []
    assert T.summary([])["n"] == 0
