"""Jones' statistical layer: profile moments and the second value-area definition.

He describes converting profile shapes into explicit statistical functions —
skewness, kurtosis, and a value area defined as 1 sigma of the distribution
rather than as a 70% window grown outward from the POC. Those are two different
objects and this file pins the difference down instead of letting one quietly
stand in for the other.
"""
from __future__ import annotations

import pytest

from pipeline.profile import tpo as MP


def _sym():
    """Symmetric triangle centred on 100."""
    return {98.0: 1, 99.0: 3, 100.0: 5, 101.0: 3, 102.0: 1}


def _right_skewed():
    """Mass at the bottom, a long thin tail up. Mode 98, mean well above it."""
    return {98.0: 9, 99.0: 5, 100.0: 3, 101.0: 2, 102.0: 1, 103.0: 1, 104.0: 1}


# --- moments -------------------------------------------------------------

def test_a_symmetric_profile_has_no_skew():
    m = MP.moments(_sym())
    assert m["skew"] == pytest.approx(0.0, abs=1e-9)
    assert m["mean"] == pytest.approx(100.0)


def test_mass_low_with_a_tail_up_is_positive_skew():
    assert MP.moments(_right_skewed())["skew"] > 0.5


def test_a_flat_profile_has_strongly_negative_excess_kurtosis():
    """The case where a POC is an argmax over near-ties.

    A uniform distribution has excess kurtosis of -1.2; that is the signature
    worth catching, because it is exactly when 'the value area' means least.
    """
    flat = {p: 4 for p in (98.0, 99.0, 100.0, 101.0, 102.0)}
    assert MP.moments(flat)["excess_kurtosis"] == pytest.approx(-1.3, abs=0.05)


def test_a_peaked_profile_has_higher_kurtosis_than_a_flat_one():
    flat = {p: 4 for p in (98.0, 99.0, 100.0, 101.0, 102.0)}
    peaked = {98.0: 1, 99.0: 1, 100.0: 30, 101.0: 1, 102.0: 1}
    assert (MP.moments(peaked)["excess_kurtosis"]
            > MP.moments(flat)["excess_kurtosis"])


def test_a_single_price_reports_shape_as_undefined_not_as_symmetric():
    m = MP.moments({100.0: 12})
    assert m["sd"] == 0.0
    assert m["skew"] is None and m["excess_kurtosis"] is None
    assert "degenerate" in m["note"]


def test_moments_of_nothing_is_none():
    assert MP.moments({}) is None


# --- the sigma value area ------------------------------------------------

def test_sigma_is_an_accepted_method():
    assert "sigma" in MP.VALUE_AREA_METHODS
    va = MP.value_area(_sym(), method="sigma")
    assert va["method"] == "sigma"


def test_an_unknown_method_is_still_refused():
    with pytest.raises(ValueError, match="method must be one of"):
        MP.value_area(_sym(), method="onesigma")


def test_sigma_reports_what_it_actually_held_not_the_textbook_68():
    """A profile is not normal. Quoting 68% would assert a shape never checked."""
    va = MP.value_area(_right_skewed(), method="sigma")
    held = sum(n for p, n in _right_skewed().items()
               if va["low"] <= p <= va["high"])
    assert va["covered"] == pytest.approx(held / sum(_right_skewed().values()))
    assert va["coverage_target"] is None  # coverage is an OUTPUT here, not an input


def test_sigma_is_centred_on_the_mean_and_the_poc_band_on_the_mode():
    counts = _right_skewed()
    sig = MP.value_area(counts, method="sigma")
    m = MP.moments(counts)
    assert (sig["low"] + sig["high"]) / 2 == pytest.approx(m["mean"])
    # The mode is 98; the mean is dragged up by the tail. The two constructions
    # therefore cannot agree on a skewed profile, which is the whole point.
    assert m["mean"] > MP.poc(counts)


def test_the_two_bands_agree_closely_when_the_profile_is_symmetric():
    d = MP.value_area_disagreement(_sym())
    assert abs(d["low_delta"]) <= 1.0 and abs(d["high_delta"]) <= 1.0


def test_the_disagreement_is_reported_not_resolved():
    d = MP.value_area_disagreement(_right_skewed())
    assert set(d) >= {"pair", "sigma", "low_delta", "high_delta", "skew"}
    assert d["low_delta"] != 0
    # Both bands survive in the output; neither is dropped in favour of the other.
    assert d["pair"]["low"] is not None and d["sigma"]["low"] is not None


def test_disagreement_of_nothing_is_none():
    assert MP.value_area_disagreement({}) is None


def test_the_real_session_that_prompted_this(tmp_path):
    """8/11 was the widest gap in the stored set: +6.3 pts on the low edge.

    Rebuilt from the shipped profile so the test fails if either construction
    is changed, not merely if the arithmetic is.
    """
    import json
    from pathlib import Path
    p = Path("data/profile/profile_20260811.json")
    if not p.exists():
        pytest.skip("profile not present in this checkout")
    counts = {float(k): v for k, v in json.loads(p.read_text())["tpo"]["counts"].items()}
    d = MP.value_area_disagreement(counts)
    assert d["low_delta"] == pytest.approx(6.3, abs=0.5)
    # A very flat session -- which is why the POC-anchored band is widest here.
    assert d["excess_kurtosis"] < -1.0
