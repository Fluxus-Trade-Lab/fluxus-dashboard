"""bs_delta / bs_vega, checked against numerical differentiation of bs_price.

Cross-checking the closed forms against finite differences of the *already
trusted* pricer is a real test: an algebra slip in d1 or a wrong convention
shows up immediately, whereas asserting hand-copied constants would only
restate the formula.
"""
import pytest

from pipeline.gex.blackscholes import bs_price, bs_delta, bs_vega

S, K, T, SIG = 7400.0, 7350.0, 2.0 / 365.0, 0.25


def _numeric_delta(S, K, T, sig, right, h=0.01):
    return (bs_price(S + h, K, T, sig, right) - bs_price(S - h, K, T, sig, right)) / (2 * h)


def _numeric_vega_per_point(S, K, T, sig, right, h=1e-5):
    # d/dsigma in sigma-units, then scaled to one vol POINT (1%).
    d = (bs_price(S, K, T, sig + h, right) - bs_price(S, K, T, sig - h, right)) / (2 * h)
    return d / 100.0


@pytest.mark.parametrize("right", ["C", "P"])
def test_delta_matches_numerical_derivative(right):
    assert bs_delta(S, K, T, SIG, right) == pytest.approx(
        _numeric_delta(S, K, T, SIG, right), abs=1e-4)


@pytest.mark.parametrize("right", ["C", "P"])
def test_vega_matches_numerical_derivative(right):
    assert bs_vega(S, K, T, SIG) == pytest.approx(
        _numeric_vega_per_point(S, K, T, SIG, right), rel=1e-3)


def test_put_call_delta_parity_and_ranges():
    c, p = bs_delta(S, K, T, SIG, "C"), bs_delta(S, K, T, SIG, "P")
    assert c - p == pytest.approx(1.0, abs=1e-9)     # dC/dS - dP/dS = 1
    assert 0.0 < c < 1.0 and -1.0 < p < 0.0


def test_vega_is_per_vol_point_not_per_unit_sigma():
    # A 1-point IV move on a 2DTE ATM SPX option is worth single-digit dollars,
    # not hundreds. Catches the /100 convention being dropped.
    v = bs_vega(S, S, T, SIG)
    assert 0.1 < v < 10.0


def test_deep_itm_and_otm_delta_limits():
    assert bs_delta(S, 100.0, T, SIG, "C") == pytest.approx(1.0, abs=1e-6)
    assert bs_delta(S, 99999.0, T, SIG, "C") == pytest.approx(0.0, abs=1e-6)


def test_invalid_inputs_return_none():
    for bad in ((0, K, T, SIG), (S, K, 0, SIG), (S, K, T, 0)):
        assert bs_delta(*bad, "C") is None
        assert bs_vega(*bad) is None
