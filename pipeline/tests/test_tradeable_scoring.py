"""Cross-sectional scores must be measured against a field you can trade."""

from __future__ import annotations

import logging

import pandas as pd
import pytest

from pipeline.screeners.run_all import compute_universe_scores

SCORE_COLS = ["rs_21d", "rs_63d", "rs_126d", "rs_rating",
              "f_score", "i_score", "h_score"]


def _row(ticker, cap, price, vol, industry="Software - Application", **kw):
    base = {
        "ticker": ticker, "market_cap": cap, "close": price, "avg_volume": vol,
        "industry": industry, "sector": "Technology",
        "perf_1w": 0.01, "perf_1m": 0.05, "perf_3m": 0.10,
        "perf_6m": 0.20, "perf_1y": 0.30, "atr": 1.0,
        "sma20_dist": 0.0, "sma50_dist": 0.0, "high_52w": -0.05,
    }
    base.update(kw)
    return base


@pytest.fixture
def scored():
    logging.disable(logging.CRITICAL)
    rows = [
        _row("LIQ1", 5e9, 100.0, 1_000_000, perf_3m=0.30),
        _row("LIQ2", 2e9, 50.0, 500_000, perf_3m=0.20),
        _row("LIQ3", 1e9, 40.0, 400_000, perf_3m=0.10),
        # Below the floor on cap and on dollar volume respectively.
        _row("TINY", 5e7, 2.0, 50_000, perf_3m=0.90),
        _row("THIN", 1e9, 3.0, 100_000, perf_3m=0.85),
    ]
    return compute_universe_scores(pd.DataFrame(rows)).set_index("ticker")


class TestTradeableGate:
    def test_flags_which_rows_are_tradeable(self, scored):
        assert scored.loc["LIQ1", "tradeable"]
        assert not scored.loc["TINY", "tradeable"]
        assert not scored.loc["THIN", "tradeable"]

    @pytest.mark.parametrize("col", SCORE_COLS)
    def test_outsiders_are_scored_on_the_field_ruler(self, scored, col):
        """2026-08-17: outsiders carry a score too, but it is a percentile of
        the TRADEABLE field, not of a field they belong to. TINY and THIN
        have the best perf_3m in the sample: on the field's ruler that reads
        as 'above every field member' -- and, per the next test, without
        moving a single field member's number."""
        assert pd.notna(scored.loc["TINY", col]), col
        assert pd.notna(scored.loc["THIN", col]), col
        if col == "rs_63d":
            assert scored.loc["TINY", col] >= scored.loc[scored["tradeable"], col].max()

    def test_field_members_read_the_same_with_or_without_outsiders(self):
        logging.disable(logging.CRITICAL)
        rows = [
            _row("LIQ1", 5e9, 100.0, 1_000_000, perf_3m=0.30),
            _row("LIQ2", 2e9, 50.0, 500_000, perf_3m=0.20),
            _row("LIQ3", 1e9, 40.0, 400_000, perf_3m=0.10),
        ]
        alone = compute_universe_scores(pd.DataFrame(rows)).set_index("ticker")
        rows += [_row("TINY", 5e7, 2.0, 50_000, perf_3m=0.90)]
        both = compute_universe_scores(pd.DataFrame(rows)).set_index("ticker")
        for col in SCORE_COLS:
            assert (alone[col].astype(float) == both.loc[alone.index, col].astype(float)).all(), col

    @pytest.mark.parametrize("col", SCORE_COLS)
    def test_tradeable_rows_are_scored(self, scored, col):
        assert pd.notna(scored.loc["LIQ1", col]), col

    def test_illiquid_outperformer_cannot_displace_the_ranking(self, scored):
        """TINY and THIN have the best perf_3m in the sample. Before this gate
        they would have taken the top percentiles and pushed every tradeable
        name down."""
        assert scored.loc["LIQ1", "rs_63d"] == scored.loc[
            scored["tradeable"], "rs_63d"].max()

    def test_raw_performance_survives_for_untraded_rows(self, scored):
        """The screener still shows them, raw perf untouched."""
        assert scored.loc["TINY", "perf_3m"] == pytest.approx(0.90)


class TestIndustryScore:
    def test_industry_median_ignores_untradeable_members(self):
        logging.disable(logging.CRITICAL)
        rows = [
            _row("A1", 5e9, 100.0, 1_000_000, industry="Steel", perf_3m=0.05),
            _row("A2", 5e9, 100.0, 1_000_000, industry="Steel", perf_3m=0.05),
            _row("B1", 5e9, 100.0, 1_000_000, industry="Gold", perf_3m=0.40),
            _row("B2", 5e9, 100.0, 1_000_000, industry="Gold", perf_3m=0.40),
            # A huge print on an untradeable name in Steel.
            _row("JUNK", 4e7, 1.0, 20_000, industry="Steel", perf_3m=9.0),
        ]
        out = compute_universe_scores(pd.DataFrame(rows)).set_index("ticker")
        assert out.loc["B1", "i_score"] > out.loc["A1", "i_score"]
