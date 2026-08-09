"""Which force governs a strike — and the normalisation that decides it."""
import pytest

from pipeline.gex import dominance as D


def test_normalisation_is_required_because_the_units_differ():
    # Charm here is 1000x gamma in RAW units but identical in shape. Without
    # normalising, charm would "dominate" every strike trivially and the label
    # would carry no information at all. z-scoring is scale-invariant, so after
    # it the two series are the same and NO strike can be awarded to either.
    gex = {100.0: 1.0, 101.0: -2.0, 102.0: 3.0}
    charm = {100.0: 1000.0, 101.0: -2000.0, 102.0: 3000.0}
    rows = D.dominant_exposure(gex, charm)
    assert not any(r["dominant"] in ("gamma", "charm") for r in rows)
    # 100 is within half a sigma of the grid mean, so it is quiet rather than a
    # draw -- a distinction worth keeping: "too close to call" and "nothing here"
    # are different readings.
    by = {r["strike"]: r["dominant"] for r in rows}
    assert by == {100.0: "neither", 101.0: "both", 102.0: "both"}


def test_the_method_changes_the_answer_and_is_carried_in_the_result():
    gex = {100.0: 10.0, 101.0: 1.0, 102.0: 1.0}
    charm = {100.0: 1.0, 101.0: 1.0, 102.0: 10.0}
    z = D.dominant_exposure(gex, charm, method="zscore")
    m = D.dominant_exposure(gex, charm, method="maxabs")
    assert {r["method"] for r in z} == {"zscore"}
    assert {r["method"] for r in m} == {"maxabs"}


def test_a_quiet_strike_is_not_awarded_to_whichever_is_marginally_larger():
    # Both forces near the grid mean: nothing is happening here, and saying
    # "gamma" because it lost a coin flip would be a fabricated finding.
    gex = {100.0: 0.0, 101.0: 0.001, 102.0: 50.0, 103.0: -50.0}
    charm = {100.0: 0.0, 101.0: 0.0, 102.0: -50.0, 103.0: 50.0}
    rows = {r["strike"]: r for r in D.dominant_exposure(gex, charm)}
    assert rows[101.0]["dominant"] == "neither"


def test_a_near_tie_is_called_both_not_a_winner():
    gex = {100.0: 3.0, 101.0: -3.0, 102.0: 3.05}
    charm = {100.0: 3.0, 101.0: -3.0, 102.0: 3.0}
    rows = {r["strike"]: r for r in D.dominant_exposure(gex, charm, method="maxabs")}
    assert rows[102.0]["dominant"] == "both"


def test_a_clear_charm_strike_is_activated_by_time_not_displacement():
    gex = {100.0: 0.1, 101.0: 0.1, 102.0: 0.1}
    charm = {100.0: 10.0, 101.0: -5.0, 102.0: -5.0}
    rows = {r["strike"]: r for r in D.dominant_exposure(gex, charm)}
    assert rows[100.0]["dominant"] == "charm"
    assert "passage of time" in rows[100.0]["activated_by"]


def test_a_strike_measured_in_only_one_series_is_dropped_not_awarded():
    # Missing charm is not "gamma dominates" — it is a strike we did not measure.
    rows = D.dominant_exposure({100.0: 5.0, 101.0: 5.0}, {100.0: 1.0})
    assert [r["strike"] for r in rows] == [100.0]


def test_same_sign_is_reported_because_agreement_differs_from_magnitude():
    gex = {100.0: 5.0, 101.0: -5.0}
    charm = {100.0: 5.0, 101.0: 5.0}
    rows = {r["strike"]: r for r in D.dominant_exposure(gex, charm)}
    assert rows[100.0]["same_sign"] is True
    assert rows[101.0]["same_sign"] is False


def test_unknown_normalisation_is_refused():
    with pytest.raises(ValueError, match="method"):
        D.normalise({1.0: 1.0}, method="whatever")


def test_a_flat_series_normalises_to_zero_rather_than_dividing_by_zero():
    assert D.normalise({1.0: 7.0, 2.0: 7.0}) == {1.0: 0.0, 2.0: 0.0}


def test_crossover_is_the_closest_thing_to_a_handoff():
    gex = {100.0: 10.0, 101.0: 5.0, 102.0: 1.0}
    charm = {100.0: 1.0, 101.0: 5.0, 102.0: 10.0}
    x = D.crossover(D.dominant_exposure(gex, charm, method="maxabs"))
    assert x["strike"] == 101.0


def test_crossover_ignores_a_tight_gap_between_two_quiet_forces():
    # 200.0 has the smallest gap on the grid (0.02) but both forces are noise
    # there. The handoff must be where something is actually happening --
    # measured on the live 2026-08-05 grid this picked a strike 400 points OTM.
    gex = {100.0: 30.0, 101.0: 28.0, 200.0: 0.5, 201.0: 0.4}
    charm = {100.0: 29.0, 101.0: 5.0, 200.0: 0.48, 201.0: 0.4}
    x = D.crossover(D.dominant_exposure(gex, charm, method="maxabs"))
    assert x is not None and x["strike"] == 100.0


def test_the_nearest_candidate_is_not_automatically_called_a_handoff():
    # Strike 100 is gamma's peak (1.0) and 0.6 of charm's peak: both live, but a
    # 1.67 ratio is not a draw. The closest thing to a crossover on this grid is
    # not a crossover, and the flag says so.
    #
    # Note the fixture cannot express "gamma is 3x charm in raw size" -- BOTH
    # normalisations rescale each series by its own spread, which is the only
    # meaningful comparison between $/1%-move and $-drift-to-expiry. Dominance
    # is always "more extreme for gamma than for charm, each relative to its own
    # grid", never a raw magnitude contest.
    gex = {100.0: 30.0, 101.0: 6.0, 102.0: 6.0}
    charm = {100.0: 6.0, 101.0: 10.0, 102.0: 2.0}
    x = D.crossover(D.dominant_exposure(gex, charm, method="maxabs"))
    assert x is not None and x["is_handoff"] is False


def test_a_real_draw_is_flagged_as_a_handoff():
    gex = {100.0: 30.0, 101.0: 5.0, 102.0: 5.0}
    charm = {100.0: 29.0, 101.0: 30.0, 102.0: 5.0}
    x = D.crossover(D.dominant_exposure(gex, charm, method="maxabs"))
    assert x["strike"] == 100.0 and x["is_handoff"] is True


def test_crossover_of_an_entirely_quiet_grid_is_none():
    flat = {100.0: 1.0, 101.0: 1.0, 102.0: 1.0}
    assert D.crossover(D.dominant_exposure(flat, flat)) is None


def test_summary_counts_the_grid():
    gex = {100.0: 10.0, 101.0: 0.1, 102.0: 0.1}
    charm = {100.0: 0.1, 101.0: 0.1, 102.0: 10.0}
    s = D.summary(D.dominant_exposure(gex, charm))
    assert s["n"] == 3 and sum(s["counts"].values()) == 3
