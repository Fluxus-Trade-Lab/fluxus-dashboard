"""Vanna and vomma — validated by numerical differentiation, not by inspection.

Every greek in this project that was wrong was wrong in its UNITS, not its
algebra. So each is checked against a finite difference of the quantity it
claims to be the derivative of, in the units it claims.
"""
import pytest

from pipeline.gex.blackscholes import bs_delta, bs_vanna, bs_vega, bs_vomma

S, K, T, SIG = 7700.0, 7750.0, 30 / 365, 0.18


def test_vanna_is_the_derivative_of_delta_in_vol_points():
    h = 0.0001                                   # 0.01 vol points
    num = (bs_delta(S, K, T, SIG + h, "C") - bs_delta(S, K, T, SIG - h, "C")) / (2 * h)
    assert bs_vanna(S, K, T, SIG) == pytest.approx(num / 100.0, rel=1e-3)


def test_vanna_is_also_the_derivative_of_vega_in_spot():
    h = 0.01
    num = (bs_vega(S + h, K, T, SIG) - bs_vega(S - h, K, T, SIG)) / (2 * h)
    assert bs_vanna(S, K, T, SIG) == pytest.approx(num, rel=1e-3)


def test_vanna_is_positive_for_an_otm_call_and_negative_for_an_itm_one():
    # Pinned because I asserted the opposite on the first pass. K > S means
    # log(S/K) < 0 so d2 < 0, and vanna = -phi(d1)*d2/sigma is POSITIVE: an OTM
    # option GAINS delta as vol rises. The ITM case mirrors it -- delta falls
    # back toward 0.5. Dealers short those OTM calls are short positive vanna,
    # so rising IV forces them to buy: the vol-led squeeze.
    assert bs_vanna(7700.0, 8200.0, T, SIG) > 0        # OTM call, d2 < 0
    assert bs_vanna(7700.0, 7200.0, T, SIG) < 0        # ITM call, d2 > 0


def test_vanna_is_the_same_for_a_call_and_a_put_at_one_strike():
    # Put-call parity: the difference is a forward, which has no vol sensitivity.
    # If a caller ever needs a right argument here, something is wrong.
    d_call = bs_delta(S, K, T, SIG, "C")
    d_put = bs_delta(S, K, T, SIG, "P")
    h = 0.0001
    n_c = (bs_delta(S, K, T, SIG + h, "C") - bs_delta(S, K, T, SIG - h, "C")) / (2 * h)
    n_p = (bs_delta(S, K, T, SIG + h, "P") - bs_delta(S, K, T, SIG - h, "P")) / (2 * h)
    assert n_c == pytest.approx(n_p, rel=1e-6)
    assert d_call - d_put == pytest.approx(1.0, abs=0.02)


def test_vanna_nearly_vanishes_at_the_money():
    # At the money delta is ~0.5 whatever vol does, so its vol sensitivity is
    # near zero; the wings are where vanna lives.
    assert abs(bs_vanna(S, S, T, SIG)) < abs(bs_vanna(S, S * 1.06, T, SIG)) / 10


def test_vomma_is_the_derivative_of_vega_in_vol_points():
    h = 0.0001
    num = (bs_vega(S, K, T, SIG + h) - bs_vega(S, K, T, SIG - h)) / (2 * h)
    assert bs_vomma(S, K, T, SIG) == pytest.approx(num / 100.0, rel=1e-3)


def test_expired_or_degenerate_inputs_return_zero_not_nan():
    for f in (bs_vanna, bs_vomma):
        assert f(S, K, 0.0, SIG) == 0.0
        assert f(S, K, T, 0.0) == 0.0
        assert f(0.0, K, T, SIG) == 0.0


def test_the_hundredfold_unit_error_would_be_caught():
    # Per unit sigma rather than per vol point overstates hedging 100x. This is
    # the error the project already made with vega; the guard is that the
    # numerical check above is done in vol points, so a /100 slip fails it.
    h = 0.0001
    per_sigma = (bs_delta(S, K, T, SIG + h, "C") - bs_delta(S, K, T, SIG - h, "C")) / (2 * h)
    assert bs_vanna(S, K, T, SIG) != pytest.approx(per_sigma, rel=1e-2)
    assert bs_vanna(S, K, T, SIG) == pytest.approx(per_sigma / 100.0, rel=1e-3)
