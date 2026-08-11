"""vol_5d_50d -- the ratio math and its refusals.

No network: fetch_volume_ratios is vendor plumbing; what must not drift is
ratio_from_volumes -- the definition of the column.
"""
import pandas as pd
import pytest

from pipeline.screeners.volume_enrichment import ratio_from_volumes, NEAR, BASE


def test_windows_are_the_name():
    # the column is named by these numbers; a change is a different measurement
    assert (NEAR, BASE) == (5, 50)


def test_flat_volume_is_one():
    assert ratio_from_volumes(pd.Series([1_000_000.0] * 60)) == 1.0


def test_surge_reads_above_one():
    vols = [1_000_000.0] * 55 + [3_000_000.0] * 5
    r = ratio_from_volumes(pd.Series(vols))
    # 5d mean 3M over 50d mean (45*1M + 5*3M)/50 = 1.2M
    assert r == round(3_000_000 / 1_200_000, 4)


def test_short_history_is_unmeasured_not_shorter_window():
    # 49 sessions: a "50-day average" does not exist; refuse, don't improvise
    assert ratio_from_volumes(pd.Series([1e6] * (BASE - 1))) is None


def test_nans_do_not_count_as_sessions():
    vals = [1e6] * 49 + [float('nan')] * 10
    assert ratio_from_volumes(pd.Series(vals)) is None


def test_halted_base_is_unmeasurable_not_infinite():
    assert ratio_from_volumes(pd.Series([0.0] * 60)) is None
