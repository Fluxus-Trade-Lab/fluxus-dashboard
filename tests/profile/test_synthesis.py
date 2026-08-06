"""The auction/options join — what counts as confluence, and what does not."""
import pytest

from pipeline.profile import synthesis as SY

PROFILE = {"tpo": {
    "tpoc": 7745.0,
    "value_area": {"low": 7725.0, "high": 7765.0, "covered": 0.73, "method": "pair"},
    "initial_balance": {"low": 7769.0, "high": 7794.0},
    "poor_extremes": {"poor_high": False, "poor_low": True, "high": 7795.0,
                      "low": 7720.0, "high_tpos": 1, "low_tpos": 2},
    "tails": {"buying": None,
              "selling": {"low": 7795.0, "high": 7795.0, "length": 1,
                          "significant": False}},
}}
GEX = {"call_wall": 7800.0, "put_wall": 7400.0, "zero_gamma_flip": 7564.7,
       "charm_peak_strike": 7750.0, "regime": "positive",
       "per_strike_gex": {"7800": 5.269e9, "7400": -0.308e9, "7750": 2.4e9}}


def test_two_options_levels_agreeing_is_not_confluence():
    # The old failure mode: gamma and charm are both the dealer book, so their
    # agreement is close to arithmetic. Only cross-framework counts.
    rows = SY.reference_map([], SY.options_levels(GEX), tolerance=60.0)
    assert not any(r["confluence"] for r in rows)


def test_a_tpoc_and_a_charm_peak_five_points_apart_is_confluence():
    rows = SY.reference_map(SY.auction_levels(PROFILE), SY.options_levels(GEX))
    hit = [r for r in rows if r["confluence"] and abs(r["price"] - 7747.5) < 1]
    assert hit, "TPOC 7745 and charm peak 7750 should join at tolerance 5"
    assert set(hit[0]["frameworks"]) == {"auction", "options"}


def test_tolerance_is_reported_because_it_decides_the_answer():
    tight = SY.reference_map(SY.auction_levels(PROFILE), SY.options_levels(GEX),
                             tolerance=1.0)
    assert all(r["tolerance"] == 1.0 for r in tight)
    assert not any(r["confluence"] for r in tight)   # nothing is within 1pt


def test_insignificant_tails_are_not_promoted_to_levels():
    # The 7795 selling tail is one tick and Dalton calls that meaningless; it
    # must not quietly become a level that the call wall then "confirms".
    names = {lv["name"] for lv in SY.auction_levels(PROFILE)}
    assert "selling tail" not in names
    assert "poor low" in names and "poor high" not in names


def test_every_level_survives_into_the_map_even_alone():
    a, o = SY.auction_levels(PROFILE), SY.options_levels(GEX)
    rows = SY.reference_map(a, o)
    assert sum(len(r["members"]) for r in rows) == len(a) + len(o)


def test_map_is_sorted_high_to_low():
    rows = SY.reference_map(SY.auction_levels(PROFILE), SY.options_levels(GEX))
    assert [r["price"] for r in rows] == sorted((r["price"] for r in rows), reverse=True)


def test_negative_tolerance_is_refused():
    with pytest.raises(ValueError, match="tolerance"):
        SY.reference_map([], [], tolerance=-1.0)


# ------------------------------------------------------------- conflicts

def test_a_flip_far_below_the_value_area_is_reported_as_a_conflict():
    cs = SY.conflicts(PROFILE, GEX)
    assert any("flip sits below the value area" == c["issue"] for c in cs)


def test_an_ib_that_never_touched_value_is_reported():
    # IB 7769-7794 sits entirely above value 7725-7765: the day left where it
    # opened, which the gamma regime alone would never tell you.
    cs = SY.conflicts(PROFILE, GEX)
    assert any("initial balance does not overlap" in c["issue"] for c in cs)


def test_a_thin_wall_is_called_an_argmax_over_noise():
    # 0.308B against a 5.269B peak is 5.8% -- flagged at the 10% default.
    cs = SY.conflicts(PROFILE, GEX)
    put = [c for c in cs if c["issue"].startswith("put wall")]
    assert put and "0.31B" in put[0]["detail"]


def test_the_thin_wall_threshold_is_an_argument_and_it_decides_the_answer():
    # The same wall at 5.8% is noise under the 10% default and a real level
    # under a 5% rule. Neither is a fact; the number has to be visible.
    assert any(c["issue"].startswith("put wall")
               for c in SY.conflicts(PROFILE, GEX, thin_wall_frac=0.10))
    assert not any(c["issue"].startswith("put wall")
                   for c in SY.conflicts(PROFILE, GEX, thin_wall_frac=0.05))


def test_a_fat_wall_is_not_flagged():
    cs = SY.conflicts(PROFILE, GEX)
    assert not any(c["issue"].startswith("call wall") for c in cs)


# ------------------------------------------------------------- strongest

def test_strongest_picks_the_tightest_cross_framework_pair():
    rows = SY.reference_map(SY.auction_levels(PROFILE), SY.options_levels(GEX))
    s = SY.strongest(rows)
    assert s and s["confluence"] and s["spread"] <= 5.0


def test_strongest_is_none_when_nothing_agrees():
    assert SY.strongest(SY.reference_map([], SY.options_levels(GEX))) is None


# --------------------------------------------------------- today's business

def test_the_question_above_value_asks_about_acceptance_from_above():
    q = SY.todays_business(PROFILE, GEX, spot=7790.0)
    assert q["frame"] == "above_value"
    assert "7,765" in q["question"]           # yesterday's VAH
    assert "7,800" in q["holds"]              # call wall is the objection
    assert "7,745" in q["fails"]              # TPOC is the magnet on failure


def test_the_question_below_value_mirrors():
    q = SY.todays_business(PROFILE, GEX, spot=7700.0)
    assert q["frame"] == "below_value"
    assert "7,725" in q["question"]           # VAL
    assert "7,400" in q["holds"]              # put wall


def test_the_question_inside_value_is_about_the_balance_holding():
    q = SY.todays_business(PROFILE, GEX, spot=7745.0)
    assert q["frame"] == "inside_value"
    assert "balance" in q["question"]


def test_no_value_area_means_no_question_rather_than_a_generic_one():
    assert SY.todays_business({"tpo": {}}, GEX, spot=7745.0) is None


def test_no_spot_anywhere_means_no_question():
    assert SY.todays_business(PROFILE, {"call_wall": 7800.0}) is None
