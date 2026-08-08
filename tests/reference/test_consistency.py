"""Self-consistency checks — and the two ways the first version of them was wrong."""
import pytest

from pipeline.reference import consistency as C


def test_a_check_needs_exactly_one_kind_of_tolerance():
    # Absolute tolerance on a quantity spanning orders of magnitude is
    # meaningless; relative tolerance on one crossing zero is worse.
    with pytest.raises(ValueError, match="exactly one"):
        C.check("x", 1.0, 1.0)
    with pytest.raises(ValueError, match="exactly one"):
        C.check("x", 1.0, 1.0, tol_abs=1, tol_rel=0.1)


def test_a_missing_side_is_unavailable_never_ok():
    # Silence where a check should have run is the failure this module prevents.
    r = C.check("x", None, 1.0, tol_abs=1)
    assert r["status"] == "unavailable" and r["drift"] is None


def test_a_relative_tolerance_against_zero_is_undefined_not_passing():
    r = C.check("x", 0.5, 0.0, tol_rel=0.1)
    assert r["status"] == "unavailable"


def test_drift_is_reported_with_its_size():
    r = C.check("x", 110.0, 100.0, tol_rel=0.05, unit=" pts")
    assert r["status"] == "DRIFT" and r["drift"] == pytest.approx(10.0)
    assert "10.00%" in r["detail"]


def test_the_route_is_recorded_because_a_dependent_check_proves_less():
    with pytest.raises(ValueError, match="route"):
        C.check("x", 1.0, 1.0, tol_abs=1, route="vibes")
    assert C.check("x", 1.0, 1.0, tol_abs=1, route="same_source")["route"] == "same_source"


def test_unavailable_counts_against_a_run_rather_than_being_ignored():
    # A pipeline where half the checks quietly did not execute has not passed.
    run = C.run([C.check("a", 1.0, 1.0, tol_abs=1),
                 C.check("b", None, 1.0, tol_abs=1)])
    assert run["clean"] is False and run["unavailable"] == 1


# ------------------------------------------- the two real bugs, pinned down

def _gex():
    return {
        "total_gex": 30.0, "call_wall": 7800.0, "put_wall": 7400.0,
        "per_strike_gex": {"7400": -10.0, "7600": 5.0, "7800": 35.0},
        # The profile is gamma recomputed at each hypothetical spot — a
        # DIFFERENT object from the per-strike map, sharing the word "gamma".
        "profile": [[7590.0, -2.0], [7600.0, -1.0], [7610.0, 1.0], [7620.0, 3.0]],
        "zero_gamma_flip": 7605.0,
        "atm_iv_1dte": 0.18,
    }


def test_the_flip_is_checked_against_the_profile_not_the_per_strike_map():
    # v1 compared the published flip to the coarse per-strike map's cumulative
    # crossing and fired a 97-point drift against a CORRECT pipeline. The two
    # are different quantities; this is the conflated-quantity error the module
    # exists to catch, and it was in the module.
    checks = {c["name"]: c for c in C.gex_checks(_gex())}
    flip = checks["zero-gamma flip vs profile zero-crossing"]
    assert flip["baseline"] == pytest.approx(7605.0)   # midpoint of 7600/7610
    assert flip["status"] == "ok"


def test_a_tied_tpoc_does_not_fire_a_false_alarm():
    # v1 compared TPOC to a bare argmax. Three strikes tied at 10 TPOs on
    # 2026-08-06 and the published value correctly took the one nearest
    # mid-range, so the naive check fired on a correct pipeline.
    prof = {"tpo": {"tpoc": 7712.5, "high": 7720.0, "low": 7700.0,
                    "counts": {"7700.0": 4, "7707.5": 10, "7710.0": 10,
                               "7712.5": 10, "7720.0": 4}}}
    checks = {c["name"]: c for c in C.profile_checks(prof)}
    assert checks["TPOC is one of the max-count strikes"]["status"] == "ok"
    assert "3 strike(s) tied" in checks["TPOC is one of the max-count strikes"]["note"]


def test_a_tpoc_that_is_not_a_max_count_strike_does_fire():
    prof = {"tpo": {"tpoc": 7700.0, "high": 7720.0, "low": 7700.0,
                    "counts": {"7700.0": 4, "7710.0": 10, "7720.0": 4}}}
    checks = {c["name"]: c for c in C.profile_checks(prof)}
    assert checks["TPOC is one of the max-count strikes"]["status"] == "DRIFT"


def test_a_percentage_where_a_fraction_belongs_is_caught():
    # The vega-off-by-100x class: right arithmetic, wrong unit.
    g = {**_gex(), "atm_iv_1dte": 18.0}
    checks = {c["name"]: c for c in C.gex_checks(g)}
    assert checks["ATM IV in a plausible band"]["status"] == "DRIFT"


def test_a_dropped_strike_between_the_sum_and_the_map_is_caught():
    g = {**_gex(), "total_gex": 60.0}
    checks = {c["name"]: c for c in C.gex_checks(g)}
    assert checks["total GEX vs sum of per-strike"]["status"] == "DRIFT"
