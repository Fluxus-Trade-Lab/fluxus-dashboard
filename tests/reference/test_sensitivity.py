"""The sweep: what it keeps, what it refuses to hide."""
import pytest

from pipeline.reference import sensitivity as S


def test_a_parameter_that_changes_nothing_is_stable():
    st = S.stability(S.sweep(lambda v: "same", [1, 2, 3]))
    assert st["stable"] is True and st["modal_share"] == 1.0


def test_a_parameter_that_flips_the_answer_names_where_it_flipped():
    st = S.stability(S.sweep(lambda v: "A" if v < 3 else "B", [1, 2, 3, 4]))
    assert st["stable"] is False
    assert st["modal_share"] == 0.5
    # Both answers appear twice; whichever is modal, the other's values are named.
    assert set(st["flips_at"]) in ({1, 2}, {3, 4})


def test_modal_share_says_how_thin_a_conclusion_is():
    # 4 of 5 agree: reportable, but not the same claim as unanimous.
    st = S.stability(S.sweep(lambda v: "A" if v != 9 else "B", [1, 2, 3, 4, 9]))
    assert st["modal"] == "A" and st["modal_share"] == pytest.approx(0.8)


def test_a_failing_parameter_is_kept_because_it_marks_the_edge_of_the_range():
    def fn(v):
        if v == 0:
            raise ZeroDivisionError("undefined here")
        return 1 / v
    runs = S.sweep(fn, [0, 1, 2])
    assert runs[0]["error"].startswith("ZeroDivisionError")
    st = S.stability(runs)
    assert st["n"] == 2 and st["n_failed"] == 1


def test_everything_failing_returns_none_not_a_false_verdict():
    st = S.stability(S.sweep(lambda v: 1 / 0, [1, 2]))
    assert st["stable"] is None and st["n"] == 0


def test_level_sets_compare_order_independently():
    # [7700, 7750] and [7750, 7700] are the same conclusion.
    st = S.stability(S.sweep(lambda v: [7750, 7700] if v else [7700, 7750], [0, 1]))
    assert st["stable"] is True


def test_frange_is_inclusive_and_does_not_drift():
    assert S.frange(0.02, 0.10, 0.02) == [0.02, 0.04, 0.06, 0.08, 0.10]
    assert S.frange(2.5, 10.0, 2.5) == [2.5, 5.0, 7.5, 10.0]


def test_frange_rejects_a_non_positive_step():
    with pytest.raises(ValueError, match="step"):
        S.frange(0, 1, 0)


# ------------------------------------------------------- against real shapes

PROFILE = {"tpo": {
    "tpoc": 7745.0,
    "value_area": {"low": 7725.0, "high": 7765.0, "covered": 0.73, "method": "pair"},
    "initial_balance": {"low": 7769.0, "high": 7794.0},
    "poor_extremes": {"poor_high": False, "poor_low": True, "high": 7795.0,
                      "low": 7720.0, "high_tpos": 1, "low_tpos": 2},
    "tails": {"buying": None, "selling": None},
    "counts": {"7720.0": 1, "7725.0": 3, "7745.0": 6, "7765.0": 3, "7795.0": 1},
}}
GEX = {"call_wall": 7800.0, "put_wall": 7400.0, "zero_gamma_flip": 7564.7,
       "charm_peak_strike": 7750.0, "regime": "positive", "spot": 7737.0,
       "per_strike_gex": {"7800": 5.269e9, "7400": -0.308e9, "7750": 2.4e9}}


def test_the_tolerance_sweep_finds_the_tpoc_charm_pair_and_shows_when_it_dies():
    runs = S.sweep(lambda v: S.strongest_price(PROFILE, GEX, v),
                   S.frange(2.5, 12.5, 2.5))
    answers = [r["result"] for r in runs]
    assert answers[0] is None                  # at 2.5pt nothing is within tolerance
    assert 7747.5 in answers                   # TPOC 7745 + charm peak 7750


def test_the_report_covers_every_published_conclusion():
    rows = S.report(PROFILE, GEX)
    assert {r["conclusion"] for r in rows} == {
        "strongest confluence price", "set of confluence prices",
        "which conflicts are reported", "today's question frame"}
    assert all(r["n"] + r["n_failed"] == r["n_values"] for r in rows)
