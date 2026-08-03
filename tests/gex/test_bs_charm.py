"""bs_charm, pinned by numerical differentiation and by its sign behaviour.

Charm's failure mode is a sign flip, not a magnitude error — d(delta)/dt and
d(delta)/dT differ only by sign, and getting it backwards would invert every
downstream "dealers must buy/sell into the close" read. So the sign is asserted
separately from the magnitude, on both sides of the strike.
"""
import pytest

from pipeline.gex.blackscholes import bs_charm, bs_delta

S, SIG = 100.0, 0.25
T = 30.0 / 365.0


def _numeric_charm(S, K, T, sig, right, h=1e-6):
    """-d(delta)/dT per day: T shrinks as calendar time advances."""
    dd_dT = (bs_delta(S, K, T + h, sig, right) - bs_delta(S, K, T - h, sig, right)) / (2 * h)
    return -dd_dT / 365.0


@pytest.mark.parametrize("K", [80.0, 95.0, 100.0, 105.0, 120.0])
@pytest.mark.parametrize("right", ["C", "P"])
def test_charm_matches_numerical_derivative(K, right):
    assert bs_charm(S, K, T, SIG) == pytest.approx(
        _numeric_charm(S, K, T, SIG, right), rel=1e-4, abs=1e-12)


def test_charm_is_identical_for_calls_and_puts():
    # With r=q=0, put delta = call delta - 1; the constant vanishes under d/dt.
    assert _numeric_charm(S, 105.0, T, SIG, "C") == pytest.approx(
        _numeric_charm(S, 105.0, T, SIG, "P"), rel=1e-6)


def test_sign_itm_call_delta_climbs_toward_one():
    # Deep ITM call: as expiry nears, delta -> 1, so delta is INCREASING.
    assert bs_charm(S, 80.0, T, SIG) > 0


def test_sign_otm_call_delta_bleeds_toward_zero():
    # OTM call: as expiry nears, delta -> 0, so delta is DECREASING.
    assert bs_charm(S, 120.0, T, SIG) < 0


def test_charm_grows_as_expiry_approaches():
    # The whole reason charm matters on 0DTE: the drift accelerates into expiry.
    far = abs(bs_charm(S, 105.0, 60.0 / 365.0, SIG))
    near = abs(bs_charm(S, 105.0, 2.0 / 365.0, SIG))
    assert near > far * 5


def test_nonzero_rate_matches_numerical_derivative():
    # bs_delta carries r, so the r-branch can still be pinned numerically.
    r, K = 0.043, 105.0
    h = 1e-6
    dd_dT = (bs_delta(S, K, T + h, SIG, "C", r) - bs_delta(S, K, T - h, SIG, "C", r)) / (2 * h)
    assert bs_charm(S, K, T, SIG, "C", r=r) == pytest.approx(-dd_dT / 365.0, rel=1e-4)


def test_dividend_yield_splits_calls_and_puts():
    # With q=0 the two rights coincide; a carry term separates them, and the
    # split is exactly q*e^(-qT)*[N(d1) + N(-d1)] / 365 = q*e^(-qT)/365.
    K, q = 105.0, 0.015
    c = bs_charm(S, K, T, SIG, "C", q=q)
    p = bs_charm(S, K, T, SIG, "P", q=q)
    assert c != p
    import math
    assert c - p == pytest.approx(q * math.exp(-q * T) / 365.0, rel=1e-9)
    # and both stay close to the q=0 value — the carry term is a small correction
    base = bs_charm(S, K, T, SIG)
    assert abs(c - base) < abs(base) * 0.10


def test_invalid_inputs_return_none():
    for bad in ((0, 100.0, T, SIG), (S, 100.0, 0, SIG), (S, 100.0, T, 0)):
        assert bs_charm(*bad) is None
