"""Tests for the universe quality guard."""

from __future__ import annotations

import pytest

from pipeline import quality as Q


def rows(n=100, **overrides):
    """n well-formed rows; `overrides` sets a field to None on the first k."""
    base = {"market_cap": 1e10, "avg_volume": 1e6, "close": 50.0, "volume": 1e6,
            "perf_1w": 0.01, "perf_1m": 0.02, "perf_3m": 0.03, "perf_6m": 0.04,
            "perf_1y": 0.05, "sector": "Technology", "industry": "Software"}
    out = [dict(base) for _ in range(n)]
    for field, k in overrides.items():
        for r in out[:k]:
            r[field] = None
    return out


def history(rate, n=10, field="avg_volume"):
    return [{"date": f"2026-07-{i+1:02d}", field: str(rate)} for i in range(n)]


class TestNullRate:
    def test_counts_none_and_nan_and_empty(self):
        rs = [{"a": 1}, {"a": None}, {"a": ""}, {"a": float("nan")}, {}]
        assert Q.null_rate(rs, "a") == pytest.approx(0.8)

    def test_empty_input_is_fully_missing_not_perfect(self):
        """Zero rows must not read as a clean run — that is the shape of a
        silent total failure."""
        assert Q.null_rate([], "a") == 1.0


class TestTradeableStatus:
    ARGS = (1e9, 2e6)

    def test_a_measurable_liquid_name_is_tradeable(self):
        r = {"market_cap": 5e9, "avg_volume": 1e6, "close": 50.0}
        assert Q.tradeable_status(r, *self.ARGS) == "tradeable"

    def test_a_measurable_illiquid_name_is_excluded(self):
        r = {"market_cap": 5e9, "avg_volume": 100.0, "close": 2.0}
        assert Q.tradeable_status(r, *self.ARGS) == "excluded"

    def test_a_missing_column_is_unmeasurable_not_excluded(self):
        """The Rocket Lab case: $49.5B of market cap dropped out of the
        tradeable set because avg_volume was absent, and the drop looked
        identical to a genuinely illiquid name."""
        r = {"market_cap": 49.5e9, "avg_volume": None, "close": 82.83}
        assert Q.tradeable_status(r, *self.ARGS) == "unmeasurable"


class TestAssess:
    def test_a_field_at_its_baseline_is_ok(self):
        v = Q.assess({"avg_volume": 0.012}, history(0.012))
        assert v["fields"]["avg_volume"]["status"] == "ok"
        assert v["status"] == "ok"

    def test_the_actual_regression_trips(self):
        """1.2% to 8.2% — the 2026-08-09 collapse, which shipped unnoticed."""
        v = Q.assess({"avg_volume": 0.082}, history(0.012))
        assert v["fields"]["avg_volume"]["status"] == "degraded"
        assert "8.2%" in v["fields"]["avg_volume"]["evidence"]

    def test_a_tripling_of_a_tiny_rate_does_not_trip(self):
        """0.2% to 0.6% is noise. Both gates must be crossed, or a field that
        normally sits near zero alarms every other week and gets ignored."""
        v = Q.assess({"avg_volume": 0.006}, history(0.002))
        assert v["fields"]["avg_volume"]["status"] == "ok"

    def test_a_small_rise_on_an_already_high_rate_does_not_trip(self):
        v = Q.assess({"avg_volume": 0.12}, history(0.09))
        assert v["fields"]["avg_volume"]["status"] == "ok"

    def test_no_baseline_yet_says_so_rather_than_guessing(self):
        v = Q.assess({"avg_volume": 0.08}, history(0.01, n=2))
        f = v["fields"]["avg_volume"]
        assert f["status"] == "ok" and f["baseline"] is None
        assert "no baseline yet" in f["evidence"]

    def test_the_ceiling_applies_without_any_baseline(self):
        v = Q.assess({"avg_volume": 0.5}, [])
        assert v["fields"]["avg_volume"]["status"] == "severe"
        assert v["status"] == "severe"

    def test_severe_outranks_degraded_in_the_run_verdict(self):
        v = Q.assess({"avg_volume": 0.5, "perf_3m": 0.09},
                     history(0.01) + [{"date": "x", "perf_3m": "0.01"}] * 10)
        assert v["status"] == "severe"


class TestHistory:
    def test_rerunning_a_date_replaces_rather_than_doubles(self, tmp_path):
        p = tmp_path / "q.csv"
        Q.append_history("2026-08-10", {"avg_volume": 0.01}, p)
        Q.append_history("2026-08-10", {"avg_volume": 0.02}, p)
        rows_ = Q.read_history(p)
        assert len(rows_) == 1 and rows_[0]["avg_volume"] == "0.02"

    def test_a_bad_day_still_enters_the_baseline(self, tmp_path):
        """Excluding bad runs would let a slow drift raise the baseline until
        nothing ever trips again."""
        p = tmp_path / "q.csv"
        Q.check(rows(100, avg_volume=90), "2026-08-10", p)
        assert Q.read_history(p)[0]["avg_volume"] == "0.9"

    def test_baseline_needs_enough_runs(self):
        assert Q.baseline(history(0.01, n=Q.MIN_HISTORY - 1), "avg_volume") is None
        assert Q.baseline(history(0.01, n=Q.MIN_HISTORY), "avg_volume") is not None

    def test_baseline_is_the_median_not_the_mean(self):
        h = [{"date": str(i), "avg_volume": v}
             for i, v in enumerate(["0.01", "0.01", "0.01", "0.01", "0.99"])]
        assert Q.baseline(h, "avg_volume") == pytest.approx(0.01)


class TestCheck:
    def test_returns_a_gradeable_block_and_records_it(self, tmp_path):
        p = tmp_path / "q.csv"
        v = Q.check(rows(100, avg_volume=8), "2026-08-10", p)
        assert v["fields"]["avg_volume"]["rate"] == pytest.approx(0.08)
        assert set(v) >= {"status", "fields", "runs_in_baseline"}
        assert len(Q.read_history(p)) == 1
