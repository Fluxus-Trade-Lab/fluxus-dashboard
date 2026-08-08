"""Flow against positioning — and why a plain ratio would lie."""
import pytest

from pipeline.gex import flow_ratio as F


def test_a_strike_with_proportional_flow_reads_about_one():
    oi = {100.0: 50.0, 101.0: 50.0}
    vol = {100.0: 20.0, 101.0: 20.0}
    rows = {r["strike"]: r for r in F.flow_ratio(oi, vol)}
    assert rows[100.0]["ratio"] == pytest.approx(1.0)


def test_a_strike_being_hit_today_reads_hot_even_though_it_is_small_in_oi():
    # 10% of positioning, 60% of today's flow. The plain series both show it as
    # "not the biggest strike"; the ratio is what surfaces it.
    oi = {100.0: 10.0, 101.0: 90.0}
    vol = {100.0: 60.0, 101.0: 40.0}
    rows = {r["strike"]: r for r in F.flow_ratio(oi, vol)}
    assert rows[100.0]["ratio"] == pytest.approx(6.0)
    assert F.hot_strikes(list(rows.values()))[0]["strike"] == 100.0


def test_opposite_signs_are_flagged_rather_than_folded_into_the_ratio():
    # Positioning long gamma here, today's flow short: a plain gex_vol/gex_oi
    # would return a NEGATIVE "ratio", which means nothing. The magnitude and
    # the disagreement are reported separately.
    # 20% of positioning, 70% of today's flow -> ratio 3.5, comfortably hot, so
    # the sign split in the summary is what is under test rather than the gate.
    oi = {100.0: 20.0, 101.0: 80.0}
    vol = {100.0: -70.0, 101.0: 30.0}
    rows = {r["strike"]: r for r in F.flow_ratio(oi, vol)}
    assert rows[100.0]["ratio"] == pytest.approx(3.5)
    assert rows[100.0]["same_sign"] is False
    s = F.summary(list(rows.values()))
    assert 100.0 in s["opposing"] and 100.0 not in s["adding"]


def test_a_rounding_error_strike_never_reports_a_huge_ratio():
    # 0.1% of positioning against 30% of flow would read as 300x. A table that
    # prints that trains the reader to ignore the column.
    oi = {100.0: 0.1, 101.0: 99.9}
    vol = {100.0: 30.0, 101.0: 70.0}
    rows = {r["strike"]: r for r in F.flow_ratio(oi, vol)}
    assert rows[100.0]["ratio"] is None
    assert "artefact" in rows[100.0]["note"]


def test_strikes_negligible_in_both_series_are_dropped_entirely():
    oi = {100.0: 0.1, 101.0: 999.0}
    vol = {100.0: 0.1, 101.0: 999.0}
    assert [r["strike"] for r in F.flow_ratio(oi, vol)] == [101.0]


def test_only_strikes_present_in_both_series_participate():
    assert [r["strike"] for r in F.flow_ratio({100.0: 5.0, 101.0: 5.0}, {100.0: 5.0})] == [100.0]


def test_an_empty_or_zero_series_yields_nothing_rather_than_dividing_by_zero():
    assert F.flow_ratio({}, {}) == []
    assert F.flow_ratio({100.0: 0.0}, {100.0: 0.0}) == []


def test_summary_separates_adding_from_opposing():
    oi = {100.0: 20.0, 101.0: 20.0, 102.0: 60.0}
    vol = {100.0: 60.0, 101.0: -30.0, 102.0: 10.0}
    s = F.summary(F.flow_ratio(oi, vol))
    assert s["n_hot"] >= 1
    assert set(s["adding"]) | set(s["opposing"]) == set(s["adding"] + s["opposing"])
