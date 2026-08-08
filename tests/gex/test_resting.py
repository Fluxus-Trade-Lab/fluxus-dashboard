"""Displayed NBBO size — the field we had been discarding.

Untested-and-shipped is how the day-volume bug reached production: the field
name looked right and returned NaN on every option ticker. These are the pure
parts, tested before the live read can be verified.
"""
import importlib.util
from pathlib import Path

import pandas as pd
import pytest

spec = importlib.util.spec_from_file_location(
    "gexmod", Path(__file__).resolve().parents[2] / "scripts" / "gex_levels.py")
gex = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gex)


def test_a_nan_size_is_missing_not_zero():
    # A strike nobody is quoting and a strike quoted at zero are different facts.
    assert gex._num(float("nan")) is None
    assert gex._num(None) is None
    assert gex._num("not a number") is None
    assert gex._num(0) == 0.0
    assert gex._num(37) == 37.0


def _frame(rows):
    return pd.DataFrame(rows, columns=["strike", "bid_size", "ask_size"])


def test_imbalance_is_plus_one_when_all_resting_size_is_on_the_bid():
    out = gex._resting_by_strike(_frame([(7700.0, 50.0, 0.0)]))
    assert out[7700.0]["imbalance"] == 1.0


def test_imbalance_is_minus_one_when_all_of_it_is_on_the_offer():
    out = gex._resting_by_strike(_frame([(7700.0, 0.0, 50.0)]))
    assert out[7700.0]["imbalance"] == -1.0


def test_both_rights_at_a_strike_are_summed():
    out = gex._resting_by_strike(_frame([(7700.0, 30.0, 10.0), (7700.0, 20.0, 40.0)]))
    assert out[7700.0]["bid_size"] == 50.0 and out[7700.0]["ask_size"] == 50.0
    assert out[7700.0]["imbalance"] == 0.0


def test_an_unquoted_strike_is_omitted_not_reported_as_balanced():
    # Reporting 0.0 imbalance for a strike nobody quotes would read as "evenly
    # matched", which is the opposite of what an empty book means.
    out = gex._resting_by_strike(_frame([(7700.0, 0.0, 0.0), (7750.0, 5.0, 5.0)]))
    assert 7700.0 not in out and 7750.0 in out


def test_missing_sizes_do_not_poison_the_sum():
    out = gex._resting_by_strike(
        _frame([(7700.0, None, 10.0), (7700.0, 20.0, None)]))
    assert out[7700.0]["bid_size"] == 20.0 and out[7700.0]["ask_size"] == 10.0


def test_a_chain_with_no_sizes_at_all_returns_none_rather_than_an_empty_read():
    assert gex._resting_by_strike(_frame([(7700.0, None, None)])) is None
