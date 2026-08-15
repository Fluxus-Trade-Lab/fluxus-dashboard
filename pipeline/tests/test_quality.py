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
        """A healthy rate with no baseline reports the absence honestly."""
        v = Q.assess({"avg_volume": 0.015}, history(0.01, n=2))
        f = v["fields"]["avg_volume"]
        assert f["status"] == "ok" and f["baseline"] is None
        assert "no baseline yet" in f["evidence"]

    # Inverted 2026-08-12. This used to assert that 8% missing with no baseline
    # was "ok" — it was pinning the blind spot, not a behaviour. See
    # TestBootstrapLimit for what replaced it.
    def test_a_broken_rate_with_no_baseline_no_longer_passes(self):
        v = Q.assess({"avg_volume": 0.08}, history(0.01, n=2))
        assert v["fields"]["avg_volume"]["status"] == "degraded"

    # Inverted 2026-08-15: with no history at all there is no way to tell a
    # dead feed from a column that never lived, and halting the whole pipeline
    # on ignorance is worse than publishing with a loud warning.
    def test_no_history_at_all_warns_rather_than_halts(self):
        v = Q.assess({"avg_volume": 0.5}, [])
        assert v["fields"]["avg_volume"]["status"] == "degraded"
        assert "first recorded run" in v["fields"]["avg_volume"]["evidence"]

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


class TestBootstrapLimit:
    """A guard with no history graded nothing, which is exactly the week it is
    newest. On 2026-08-12, with two runs stored, avg_volume hit 22.4% and the
    run passed as ok: no baseline to depart from, and under the ceiling."""

    def test_the_actual_2026_08_12_collapse_trips_without_a_baseline(self):
        v = Q.assess({"avg_volume": 0.2238}, history(0.0199, n=2))
        assert v["fields"]["avg_volume"]["status"] == "degraded"
        assert "bootstrap" in v["fields"]["avg_volume"]["evidence"]

    def test_a_healthy_rate_still_passes_without_a_baseline(self):
        for rate in (0.012, 0.0199):
            v = Q.assess({"avg_volume": rate}, history(0.0199, n=2))
            assert v["fields"]["avg_volume"]["status"] == "ok"

    def test_the_bootstrap_sits_between_the_observed_clusters(self):
        """Healthy runs measured 1.2% and 2.0%; broken ones 8.2% and 22.4%."""
        assert 0.02 < Q.BOOTSTRAP_DEGRADED < 0.082

    def test_a_real_baseline_overrides_the_bootstrap(self):
        """A field that genuinely sits above the bootstrap limit must not alarm
        forever once its own history says that level is normal."""
        v = Q.assess({"avg_volume": 0.09}, history(0.088, n=10))
        assert v["fields"]["avg_volume"]["status"] == "ok"


class TestSelfMaintainingLedger:
    """The change_pct lesson: a hand-kept TRACKED list has exactly one failure
    mode — the column nobody added. Finviz renamed a header, the column went
    100% null for a week, and the guard said "ok" every night because the
    column was not on its list. The list is now derived from the data and the
    guard's own history."""

    def test_discovery_includes_every_row_column(self):
        rows_ = [{"ticker": "A", "change_pct": 0.01, "brand_new_col": 5}]
        fields = Q.discovered_fields(rows_, [])
        assert "brand_new_col" in fields and "change_pct" in fields
        assert "ticker" not in fields

    def test_a_renamed_away_column_is_still_watched(self):
        """The column vanishes from the rows; history remembers it existed."""
        rows_ = [{"ticker": "A", "close": 1.0}]
        hist = [{"date": "2026-08-13", "close": "0.002", "change_pct": "0.001"}]
        fields = Q.discovered_fields(rows_, hist)
        assert "change_pct" in fields

    def test_a_dead_feed_is_severe(self):
        """Used to be populated (0.1% missing), now gone entirely."""
        v = Q.assess({"change_pct": 1.0},
                     [{"date": "d", "change_pct": "0.001"}])
        assert v["fields"]["change_pct"]["status"] == "severe"
        assert "died" in v["fields"]["change_pct"]["evidence"]

    def test_a_never_populated_column_is_unpopulated_not_severe(self):
        """eps_growth_next_y has been 100% null its whole life. Halting the
        pipeline over it would teach everyone to ignore the guard."""
        v = Q.assess({"eps_growth_next_y": 1.0},
                     [{"date": "d", "eps_growth_next_y": "1.0"}])
        f = v["fields"]["eps_growth_next_y"]
        assert f["status"] == "unpopulated"
        assert v["status"] == "ok"

    def test_one_stored_run_is_enough_to_catch_a_death(self):
        """min_reference needs one observation, not five — a new column is
        protected the day after it first appears."""
        assert Q.min_reference([{"date": "d", "x": "0.01"}], "x") == 0.01
        assert Q.min_reference([], "x") is None

    def test_the_ledger_widens_for_new_columns(self, tmp_path):
        p = tmp_path / "q.csv"
        Q.append_history("2026-08-14", {"avg_volume": 0.01}, p)
        Q.append_history("2026-08-15", {"avg_volume": 0.01, "change_pct": 0.002}, p)
        rows_ = Q.read_history(p)
        assert "change_pct" in rows_[0]           # 旧行获得空值列
        assert rows_[1]["change_pct"] == "0.002"

    def test_check_grades_undeclared_columns(self, tmp_path):
        """End to end: a column absent from TRACKED still gets measured."""
        p = tmp_path / "q.csv"
        data = [{"ticker": "A", "market_cap": 1e10, "avg_volume": 1e6,
                 "close": 5.0, "volume": 1e6, "perf_1w": 0.1, "perf_1m": 0.1,
                 "perf_3m": 0.1, "perf_6m": 0.1, "perf_1y": 0.1,
                 "sector": "T", "industry": "S", "mystery_col": 1.0}] * 10
        v = Q.check(data, "2026-08-15", p)
        assert "mystery_col" in v["fields"]


class TestSiteWideGuard:
    """The maintenance scope is every file the site reads, per the operator's
    directive after change_pct died unwatched for a week."""

    ROWS = [{"ticker": "SPY", "perf_1w": 0.01, "rrs_rank": 50}] * 10

    def test_check_source_keeps_a_ledger_per_source(self, tmp_path):
        v = Q.check_source("etf_data", self.ROWS, "2026-08-15", tmp_path)
        assert (tmp_path / "etf_data.csv").exists()
        assert "perf_1w" in v["fields"]

    def test_a_source_column_death_is_caught_next_run(self, tmp_path):
        Q.check_source("etf_data", self.ROWS, "2026-08-14", tmp_path)
        dead = [{"ticker": "SPY", "perf_1w": None, "rrs_rank": 50}] * 10
        v = Q.check_source("etf_data", dead, "2026-08-15", tmp_path)
        assert v["fields"]["perf_1w"]["status"] == "severe"

    def test_extractors_never_raise(self):
        for name in Q.SITE_SOURCES:
            assert Q.site_rows(name, {"garbage": True}) in (None, [],)
        assert Q.site_rows("signals", {"timestamp": "x", "SPY": {"close": 1}}) \
            == [{"close": 1}]

    def test_check_site_consolidates(self, tmp_path):
        import json as J
        out = tmp_path / "out"; out.mkdir()
        (out / "signals.json").write_text(J.dumps(
            {"timestamp": "t", "SPY": {"close": 1.0, "sma50": 2.0}}))
        rep = Q.check_site(out, "2026-08-15", tmp_path / "hist")
        assert rep["sources"]["signals"]["status"] in ("ok", "degraded")
        assert rep["sources"]["etf_data"]["status"] == "missing"
        assert rep["status"] == "severe"   # missing files are severe
