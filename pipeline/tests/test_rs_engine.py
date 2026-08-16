"""Tests for the RS engine: disjoint windows, acceleration, four-state."""

from __future__ import annotations

import math

import pytest

from pipeline.themes import rs_engine


def _row(**kw):
    base = {"perf_1w": 0.0, "perf_1m": 0.0, "perf_3m": 0.0, "perf_6m": 0.0}
    base.update(kw)
    return base


FLAT = _row()


class TestDisjointReturns:
    def test_chains_cumulative_windows_apart(self):
        # +2% in the last week, +10% over the month => the 1w..1m stretch
        # must be the residual, not the raw 10%.
        out = rs_engine.disjoint_returns(_row(perf_1w=0.02, perf_1m=0.10))
        assert out["0_1w"] == pytest.approx(0.02)
        assert out["1w_1m"] == pytest.approx(1.10 / 1.02 - 1)

    def test_buckets_recompound_to_the_cumulative(self):
        row = _row(perf_1w=0.03, perf_1m=0.08, perf_3m=0.20, perf_6m=0.35)
        out = rs_engine.disjoint_returns(row)
        chained = 1.0
        for bucket in rs_engine.BUCKETS:
            chained *= 1.0 + out[bucket]
        assert chained - 1.0 == pytest.approx(0.35)

    def test_missing_input_yields_nan_not_zero(self):
        # A missing field must not read as "flat" -- that would put the name
        # in a state it did not earn.
        out = rs_engine.disjoint_returns(_row(perf_1m=None))
        assert math.isnan(out["1w_1m"])

    def test_non_numeric_is_tolerated(self):
        out = rs_engine.disjoint_returns(_row(perf_1m="n/a"))
        assert math.isnan(out["1w_1m"])


class TestClassify:
    @pytest.mark.parametrize(
        "level,accel,expected",
        [
            (0.05, 0.01, "Leading"),
            (0.05, -0.01, "Weakening"),
            (-0.05, 0.01, "Improving"),
            (-0.05, -0.01, "Lagging"),
        ],
    )
    def test_four_states(self, level, accel, expected):
        assert rs_engine.classify(level, accel) == expected

    def test_unusable_inputs_return_none(self):
        assert rs_engine.classify(float("nan"), 0.1) is None
        assert rs_engine.classify(0.1, float("nan")) is None


class TestLevelAndAccelAreIndependent:
    def test_level_is_the_cumulative_three_month_excess(self):
        """Regression: level once came from a disjoint bucket that accel also
        used, making them mechanical mirrors and collapsing nearly every group
        into Weakening."""
        row = _row(perf_1w=0.01, perf_1m=0.09, perf_3m=0.15, perf_6m=0.2)
        payload = rs_engine.score_row(row, FLAT)
        assert payload["excess_3m"] == pytest.approx(0.15)
        assert payload["rs_accel"] != pytest.approx(-payload["excess_3m"])

    def test_level_is_excess_over_benchmark(self):
        bench = _row(perf_3m=0.04)
        payload = rs_engine.score_row(_row(perf_3m=0.10), bench)
        assert payload["excess_3m"] == pytest.approx(0.06)

    def test_accel_compares_last_month_against_the_two_before_it(self):
        """Month-scale windows: every scheme with a <=2-week near bucket failed
        half-sample consistency in validate_accel.py."""
        # +6% last month; 3m total +6% => the 1m..3m stretch was flat.
        row = _row(perf_1m=0.06, perf_3m=0.06)
        payload = rs_engine.score_row(row, FLAT)
        prior = (1.06 / 1.06) - 1.0
        assert payload["rs_accel"] == pytest.approx(0.06 - prior)

    def test_a_fading_leader_reads_as_decelerating(self):
        # Big 3m gain but a flat last month => accel must be negative.
        row = _row(perf_1m=0.00, perf_3m=0.30)
        payload = rs_engine.score_row(row, FLAT)
        assert payload["rs_accel"] < 0
        assert payload["state"] == "Weakening"


class TestAccelIsAGateNotASlope:
    """`rs_accel` compares one month against the two before it *in total*
    (FOUR_STATE_DESIGN.md section 8): a group outperforming at a perfectly
    steady pace gets a NEGATIVE rs_accel and reads Weakening. That gate is
    validated and stays. But the page must not translate it into the word
    "decelerating" -- so the payload also carries `rs_accel_rate`, the same
    comparison with the prior stretch folded to a one-month rate, which is
    zero for a steady pace. Words come from the rate; the state comes from
    the gate."""

    def test_steady_pace_is_negative_gate_but_zero_rate(self):
        # +2% every month vs a flat benchmark: near = 2%, prior (2 months) = 4.04%.
        row = _row(perf_1m=0.02, perf_3m=1.02 ** 3 - 1)
        payload = rs_engine.score_row(row, FLAT)
        assert payload["rs_accel"] < 0
        assert payload["state"] == "Weakening"
        assert payload["rs_accel_rate"] == pytest.approx(0.0, abs=1e-9)

    def test_true_deceleration_is_negative_in_both(self):
        # +8% then +8% over the two prior months, +1% in the last: slowing.
        row = _row(perf_1m=0.01, perf_3m=1.01 * 1.08 * 1.08 - 1)
        payload = rs_engine.score_row(row, FLAT)
        assert payload["rs_accel"] < 0
        assert payload["rs_accel_rate"] < 0

    def test_true_acceleration_is_positive_in_both(self):
        row = _row(perf_1m=0.08, perf_3m=1.08 * 1.01 * 1.01 - 1)
        payload = rs_engine.score_row(row, FLAT)
        assert payload["rs_accel"] > 0
        assert payload["rs_accel_rate"] > 0

    def test_rate_is_relative_to_the_benchmark(self):
        # Row and benchmark identical => no excess anywhere => rate exactly 0.
        row = _row(perf_1m=0.05, perf_3m=0.20)
        payload = rs_engine.score_row(row, dict(row))
        assert payload["rs_accel_rate"] == pytest.approx(0.0, abs=1e-9)

    def test_missing_input_yields_none(self):
        payload = rs_engine.score_row(_row(perf_3m=None), FLAT)
        assert payload["rs_accel_rate"] is None


class TestAggregateRows:
    def test_median_survives_a_corporate_action_artefact(self):
        """Regression: one Finviz row printing +31,192% moved an industry's
        mean 1-month return from +5% to +629%."""
        rows = [_row(perf_1m=0.05) for _ in range(9)]
        rows.append(_row(perf_1m=311.9))
        agg = rs_engine.aggregate_rows(rows)
        assert agg["perf_1m"] == pytest.approx(0.05)

    def test_implausible_values_are_dropped_entirely(self):
        rows = [_row(perf_1m=0.05), _row(perf_1m=0.07), _row(perf_1m=999.0)]
        agg = rs_engine.aggregate_rows(rows)
        assert agg["perf_1m"] == pytest.approx(0.06)

    def test_mean_is_available_but_not_default(self):
        rows = [_row(perf_1m=0.0), _row(perf_1m=0.10)]
        assert rs_engine.aggregate_rows(rows, method="mean")["perf_1m"] == pytest.approx(0.05)

    def test_all_missing_yields_nan(self):
        agg = rs_engine.aggregate_rows([_row(perf_1m=None), _row(perf_1m=None)])
        assert math.isnan(agg["perf_1m"])


class TestScoreGroups:
    def _universe(self):
        return (
            [{"ticker": f"A{i}", "industry": "Alpha", "perf_1w": 0.03,
              "perf_1m": 0.10, "perf_3m": 0.1, "perf_6m": 0.1} for i in range(6)]
            + [{"ticker": f"B{i}", "industry": "Beta", "perf_1w": -0.03,
                "perf_1m": -0.10, "perf_3m": 0.0, "perf_6m": 0.0} for i in range(6)]
            + [{"ticker": "C0", "industry": "Tiny", "perf_1w": 0.5,
                "perf_1m": 0.5, "perf_3m": 0.5, "perf_6m": 0.5}]
        )

    def test_drops_groups_below_min_members(self):
        groups = rs_engine.score_groups(self._universe(), "industry", FLAT, min_members=5)
        assert {g["group"] for g in groups} == {"Alpha", "Beta"}

    def test_sorted_by_relative_strength_descending(self):
        groups = rs_engine.score_groups(self._universe(), "industry", FLAT, min_members=5)
        assert [g["group"] for g in groups] == ["Alpha", "Beta"]

    def test_carries_constituents(self):
        groups = rs_engine.score_groups(self._universe(), "industry", FLAT, min_members=5)
        alpha = next(g for g in groups if g["group"] == "Alpha")
        assert alpha["members"] == 6
        assert "A0" in alpha["tickers"]


class TestRankWithinGroup:
    def test_top_quartile_flags_the_strongest_quarter(self):
        universe = [
            {"ticker": t, "industry": "Alpha", "perf_1w": 0.0,
             "perf_1m": 0.0, "perf_3m": v, "perf_6m": 0.0}
            for t, v in [("W", 0.40), ("X", 0.30), ("Y", 0.20), ("Z", 0.10)]
        ]
        scored = rs_engine.rank_within_group(universe, "industry", FLAT)
        assert scored["W"]["top_quartile"] is True
        assert scored["Z"]["top_quartile"] is False


class TestPersistence:
    def _row(self, **kw):
        base = {"perf_1w": 0.0, "perf_1m": 0.0, "perf_3m": 0.0,
                "perf_6m": 0.0, "perf_1y": 0.0}
        base.update(kw)
        return base

    def test_counts_horizons_beaten_against_benchmark(self):
        row = self._row(perf_1w=0.1, perf_1m=0.1, perf_3m=-0.1)
        bench = self._row()
        hits, seen = rs_engine.persistence(row, bench)
        assert (hits, seen) == (2, 5)

    def test_denominator_shrinks_when_benchmark_lacks_a_window(self):
        """SPY carries only 1w/1m/3m, so a stock cannot be scored out of 5
        against it -- returning a bare 2 would read as 2/5, not 2/3."""
        bench = {"perf_1w": 0.0, "perf_1m": 0.0, "perf_3m": 0.0}
        row = self._row(perf_1w=0.1, perf_1m=0.1)
        hits, seen = rs_engine.persistence(row, bench)
        assert (hits, seen) == (2, 3)

    def test_cohort_mode_uses_top_quartile_not_the_benchmark(self):
        cohort = [self._row(perf_1w=v, perf_1m=v, perf_3m=v,
                            perf_6m=v, perf_1y=v)
                  for v in (0.0, 0.1, 0.2, 0.3)]
        strong = self._row(perf_1w=0.9, perf_1m=0.9, perf_3m=0.9,
                           perf_6m=0.9, perf_1y=0.9)
        weak = self._row(perf_1w=-0.9, perf_1m=-0.9, perf_3m=-0.9,
                         perf_6m=-0.9, perf_1y=-0.9)
        assert rs_engine.persistence(strong, {}, cohort=cohort) == (5, 5)
        assert rs_engine.persistence(weak, {}, cohort=cohort) == (0, 5)

    def test_all_missing_returns_none(self):
        blank = {c: None for c in rs_engine.PERSISTENCE_COLS}
        assert rs_engine.persistence(blank, blank) is None

    def test_aggregate_carries_every_window_persistence_needs(self):
        """Regression: aggregate_rows covered only CUMULATIVE_COLS, so group
        rows lacked perf_1y and were silently scored out of 4."""
        rows = [self._row(perf_1y=0.2), self._row(perf_1y=0.4)]
        agg = rs_engine.aggregate_rows(rows)
        for col in rs_engine.PERSISTENCE_COLS:
            assert col in agg, col


class TestOneDayChange:
    """`perf_1d` is the session's change, aggregated exactly like the other
    perf_* columns (median, artefacts dropped) so a theme table can show 1D
    next to 1W. It is a display column: not an RS bucket, not a persistence
    horizon -- a one-day move says nothing about relative strength and must
    not widen the persistence denominator."""

    def test_aggregate_takes_the_median_change_pct(self):
        rows = [_row(change_pct=0.01), _row(change_pct=0.03), _row(change_pct=-0.02)]
        assert rs_engine.aggregate_rows(rows)["perf_1d"] == pytest.approx(0.01)

    def test_missing_change_pct_is_nan_not_zero(self):
        assert math.isnan(rs_engine.aggregate_rows([_row()])["perf_1d"])

    def test_score_row_carries_it_from_change_pct_or_perf_1d(self):
        # A universe/ETF row (change_pct) and an aggregated row (perf_1d)
        # both land on the same output name.
        assert rs_engine.score_row(_row(change_pct=0.02), FLAT)["perf_1d"] == pytest.approx(0.02)
        assert rs_engine.score_row(_row(perf_1d=0.02), FLAT)["perf_1d"] == pytest.approx(0.02)
        assert rs_engine.score_row(_row(), FLAT)["perf_1d"] is None

    def test_it_is_not_a_persistence_horizon(self):
        assert "perf_1d" not in rs_engine.PERSISTENCE_COLS
        assert "perf_1d" not in rs_engine.CUMULATIVE_COLS
        with_1d = rs_engine.score_row(_row(change_pct=0.5, perf_1w=0.01), _row())
        without = rs_engine.score_row(_row(perf_1w=0.01), _row())
        assert with_1d["persistence_of"] == without["persistence_of"]
        assert with_1d["persistence"] == without["persistence"]
