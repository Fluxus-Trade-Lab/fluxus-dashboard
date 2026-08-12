"""The gate: extension is not acceptance.

His rule, 2026-08-12: "no trade until price extends beyond the initial balance
and BUILDS there, rather than merely printing through it on the headline."
Everything here exists to keep those two cases apart, because they are identical
on a session high/low and that is precisely why a levels ladder cannot decide.
"""
from __future__ import annotations

import pytest

from pipeline.profile import facilitation as F
from pipeline.profile import tpo as MP


def bars(*spans):
    return [{"low": lo, "high": hi, "volume": 1000} for lo, hi in spans]


IB2 = [(100.0, 105.0), (101.0, 106.0)]          # initial balance 100-106


def sess(*rest):
    b = bars(*IB2, *rest)
    return b, MP.initial_balance(b)


def test_price_that_never_leaves_the_balance_has_nothing_to_accept():
    f = F.facilitation(*sess((102.0, 105.0), (101.5, 105.5)))
    assert f["state"] == "no_extension"
    assert f["tradeable"] is False
    assert "never left" in f["note"]


def test_a_headline_spike_extends_but_is_not_accepted():
    """One bracket pokes 4 points above the IB and comes straight back.

    The session high is 110 either way; only the structure separates this from
    a real range extension.
    """
    b, ib = sess((104.0, 110.0), (102.0, 105.0), (101.0, 104.0))
    f = F.facilitation(b, ib)
    assert f["up"]["extended"] is True
    assert f["up"]["accepted"] is False
    assert f["state"] == "rejected"
    assert f["tradeable"] is False
    assert "went to look and declined" in f["note"]


def test_a_built_extension_is_facilitated():
    b, ib = sess((106.5, 109.0), (107.0, 110.0), (108.0, 111.0))
    f = F.facilitation(b, ib)
    assert f["up"]["accepted"] is True
    assert f["up"]["n_periods_built"] >= F.MIN_BUILT_PERIODS
    assert f["state"] == "facilitated"
    assert f["tradeable"] is True


def test_the_two_cases_share_a_session_high():
    """The point of the module, asserted directly."""
    spike, ib1 = sess((104.0, 110.0), (102.0, 105.0))
    built, ib2 = sess((107.0, 110.0), (107.5, 109.5))
    assert max(x["high"] for x in spike) == max(x["high"] for x in built) == 110.0
    assert F.facilitation(spike, ib1)["state"] == "rejected"
    assert F.facilitation(built, ib2)["state"] == "facilitated"


def test_a_downside_extension_works_the_same_way():
    b, ib = sess((95.0, 98.0), (94.0, 97.0), (93.0, 96.0))
    f = F.facilitation(b, ib)
    assert f["down"]["accepted"] is True
    assert f["state"] == "facilitated"
    assert f["down"]["distance"] == pytest.approx(7.0)


def test_both_sides_extending_is_reported_per_side_not_averaged():
    b, ib = sess((107.0, 110.0), (108.0, 111.0), (92.0, 99.0), (93.0, 98.0))
    f = F.facilitation(b, ib)
    assert f["state"] == "two_sided"
    assert f["up"]["extended"] and f["down"]["extended"]
    # Neither side's verdict is collapsed into the other's.
    assert "up" in f["note"] and "down" in f["note"]


def test_the_initial_balance_brackets_cannot_extend_beyond_themselves():
    # A tall second bracket defines the IB; it must not also count as extending it.
    b, ib = sess((102.0, 104.0))
    f = F.facilitation(b, ib)
    assert f["up"]["n_periods_beyond"] == 0
    assert f["state"] == "no_extension"


def test_a_bracket_that_only_tags_the_line_does_not_count_as_built():
    # Range 101-106.5: just 0.5 of a 5.5-point bracket sits beyond 106.
    b, ib = sess((101.0, 106.5), (101.0, 106.5), (101.0, 106.5))
    f = F.facilitation(b, ib)
    assert f["up"]["extended"] is True
    assert f["up"]["n_periods_built"] == 0
    assert f["state"] == "rejected"


def test_missing_inputs_return_none_rather_than_a_confident_answer():
    assert F.facilitation([], None) is None
    assert F.facilitation(bars((1.0, 2.0)), None) is None


# --- the gate ------------------------------------------------------------

def test_the_gate_says_what_is_missing_not_just_no():
    b, ib = sess((104.0, 110.0), (102.0, 105.0))
    g = F.gate(F.facilitation(b, ib), "up")
    assert g["open"] is False
    assert "built only" in g["reason"] and str(F.MIN_BUILT_PERIODS) in g["reason"]


def test_the_gate_opens_only_on_acceptance():
    b, ib = sess((106.5, 109.0), (107.0, 110.0), (108.0, 111.0))
    assert F.gate(F.facilitation(b, ib), "up")["open"] is True
    # ...and only for the side that was actually accepted.
    assert F.gate(F.facilitation(b, ib), "down")["open"] is False


def test_an_unmeasurable_gate_is_none_not_false():
    g = F.gate(None, "up")
    assert g["open"] is None and g["measurable"] is False


def test_the_gate_refuses_a_direction_it_does_not_model():
    b, ib = sess((107.0, 110.0), (108.0, 111.0))
    with pytest.raises(ValueError, match="must be 'up' or 'down'"):
        F.gate(F.facilitation(b, ib), "range")


# --- the parameters must stay tied to the measurement --------------------

def test_the_thresholds_are_the_swept_and_documented_ones():
    """Changing these silently would orphan the base rate in the docstring."""
    assert F.MIN_BUILD_SHARE == 0.50
    assert F.MIN_BUILT_PERIODS == 2


def test_the_measured_base_rate_is_carried_in_code_not_only_in_prose():
    # A gate that opens on 78% of sessions is not a filter, and the constant is
    # here so nobody can present it as one.
    assert F.BASE_RATE_SESSIONS == 123
    assert 0.7 < F.BASE_RATE_GATE_OPENS < 0.85


def test_the_stored_base_rate_file_matches_the_module(tmp_path):
    import json
    from pathlib import Path
    p = Path("data/profile/facilitation_base_rate.json")
    if not p.exists():
        pytest.skip("base rate not measured in this checkout")
    d = json.loads(p.read_text())
    spx = d["instruments"]["SPX"]
    assert spx["n_sessions"] == F.BASE_RATE_SESSIONS
    assert spx["tradeable_rate"] == pytest.approx(F.BASE_RATE_GATE_OPENS, abs=0.005)
    assert d["thresholds"]["min_build_share"] == F.MIN_BUILD_SHARE
