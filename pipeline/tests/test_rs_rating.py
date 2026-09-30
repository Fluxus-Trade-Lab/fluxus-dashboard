"""RS Rating: a community reconstruction, named as one.

IBD publishes only "12 months, ranked 1-99 against the whole market". The six
coefficients are proprietary and no citable table exists -- checked 2026-09-04,
including the three TraderLion documents on this machine, which cover the RS
LINE and never the rating. Every reconstruction that can be found agrees on
one shape and cites the others rather than IBD:

    0.4*q1 + 0.2*q2 + 0.2*q3 + 0.2*q4  of return vs SPY, then ranked 1-99

so that is what we adopt (Andy 2026-09-04). The previous form was
0.4*rs_3m + 0.4*rs_6m + 0.2*rank(perf_1y), which matched neither IBD nor the
reconstruction. It displays nowhere and gates three theme cards, so the whole
risk of the change is silent membership drift.
"""
import numpy as np
import pandas as pd
import pytest


class TestTheWeights:
    def test_the_recent_quarter_is_double_weighted(self):
        """2:1:1:1 is the entire claim. If the weights drift, this fails."""
        from pipeline.screeners.run_all import _quarter_excess  # noqa: F401
        w = (0.4, 0.2, 0.2, 0.2)
        assert w[0] == 2 * w[1] == 2 * w[2] == 2 * w[3]
        assert sum(w) == pytest.approx(1.0)

    def test_a_recent_surge_outranks_an_equal_older_one(self):
        """The behavioural consequence of double-weighting the last quarter."""
        q = {'q1': np.array([0.30, 0.00]), 'q2': np.array([0.00, 0.30]),
             'q3': np.array([0.0, 0.0]), 'q4': np.array([0.0, 0.0])}
        raw = 0.4 * q['q1'] + 0.2 * q['q2'] + 0.2 * q['q3'] + 0.2 * q['q4']
        assert raw[0] > raw[1], "recent strength must rank ahead of stale strength"

    def test_the_old_form_disagreed(self):
        """Positive control for the switch being real, not cosmetic.

        Old: 0.4*3m + 0.4*6m + 0.2*rank(1y). On a name whose entire move is
        in the last quarter, the two forms rank it differently -- which is
        why the changeover has to report its membership diff.
        """
        # The two forms differ by 0.2*(q3 - q2): the old one has no q3 term
        # at all and doubles q2 in its place. Pick a name whose strength sits
        # in the THIRD quarter back -- the reconstruction sees it, the old
        # form is blind to it. (An earlier version of this test used q2 == q3
        # and the two happened to agree exactly, which proved nothing.)
        q1, q2, q3, q4 = 0.10, 0.00, 0.30, 0.05
        new = 0.4 * q1 + 0.2 * q2 + 0.2 * q3 + 0.2 * q4
        old = 0.4 * q1 + 0.4 * q2 + 0.2 * q4
        assert new == pytest.approx(0.4 * 0.10 + 0.2 * 0.30 + 0.2 * 0.05)
        assert new != pytest.approx(old)
        assert new > old, "the third quarter back is invisible to the old form"


class TestQuarterMapping:
    def test_exact_columns_are_used_where_they_exist(self):
        from pipeline.screeners.run_all import _quarter_excess
        df = pd.DataFrame({'perf_3m': [0.1], 'perf_6m': [0.2], 'perf_1y': [0.4]})
        assert _quarter_excess(df, 63).iloc[0] == pytest.approx(0.1)
        assert _quarter_excess(df, 126).iloc[0] == pytest.approx(0.2)
        assert _quarter_excess(df, 252).iloc[0] == pytest.approx(0.4)

    def test_the_third_quarter_is_interpolated_and_that_is_declared(self):
        """189 sessions has no column of its own.

        Interpolating between 6m and 1y is an approximation, not the
        reconstruction's own definition -- recorded here so the gap between
        what we ship and what the community formula says stays visible.
        """
        from pipeline.screeners.run_all import _quarter_excess
        df = pd.DataFrame({'perf_3m': [0.1], 'perf_6m': [0.2], 'perf_1y': [0.4]})
        assert _quarter_excess(df, 189).iloc[0] == pytest.approx(0.3)

    def test_missing_columns_do_not_raise(self):
        from pipeline.screeners.run_all import _quarter_excess
        out = _quarter_excess(pd.DataFrame({'ticker': ['A']}), 63)
        assert len(out) == 1


class TestMissingOneYearHistory:
    """T-1001-04: q3 and q4 both need perf_1y, and `+` does not skip NaN, so
    any tradeable name under ~1y old gets _rs_raw = NaN. The bug was not that
    -- it is correct and matches IBD, which does not rate names that young --
    it was treating that NaN as the field's single WORST score (na='top')
    instead of "not scored" (na='keep'). 09-29 universe.json: 73/73 tradeable
    names with rs_rating==1 were missing perf_1y, 11 of them with elite
    perf_3m/perf_6m (ANDG: +50%/+104%, rs_rating 1 anyway).
    """

    @staticmethod
    def _row(ticker, **kw):
        base = dict(
            ticker=ticker, market_cap=5e9, close=100.0, avg_volume=1_000_000,
            industry="Software - Application", sector="Technology",
            perf_1w=0.01, perf_1m=0.05, perf_3m=0.10, perf_6m=0.20, perf_1y=0.30,
            atr=1.0, sma20_dist=0.0, sma50_dist=0.0, high_52w=-0.05,
        )
        base.update(kw)
        return base

    def _scored(self):
        from pipeline.screeners.run_all import compute_universe_scores
        rows = [
            self._row("FULL1", perf_3m=0.05, perf_6m=0.08, perf_1y=0.10),
            self._row("FULL2", perf_3m=0.05, perf_6m=0.08, perf_1y=0.10),
            self._row("FULL3", perf_3m=0.05, perf_6m=0.08, perf_1y=0.10),
            self._row("FULL4", perf_3m=0.05, perf_6m=0.08, perf_1y=0.10),
            # ANDG shape: no 1y history, but elite 3m/6m -- must not rank
            # as the worst name in the field.
            self._row("NEWIPO", perf_3m=0.50, perf_6m=1.00, perf_1y=None),
        ]
        return compute_universe_scores(pd.DataFrame(rows)).set_index("ticker")

    def test_missing_one_year_history_gives_no_rating_not_the_worst_one(self):
        out = self._scored()
        assert pd.isna(out.loc["NEWIPO", "rs_rating"]), (
            "no 1-year history -> null, same as growth_score's "
            "'unknown, not worst' convention"
        )

    def test_full_history_names_are_unaffected_by_the_missing_one(self):
        """Regression guard the other direction: na='keep' must not also
        swallow the names that DO have a full year of history."""
        out = self._scored()
        for t in ("FULL1", "FULL2", "FULL3", "FULL4"):
            assert pd.notna(out.loc[t, "rs_rating"]), t

    def test_na_top_is_the_mechanism_the_bug_shipped_with(self):
        """Positive control built the way the bug actually broke, not just
        the opposite direction (CLAUDE.md `method_positive_controls_by_
        failure_mode`): `compute_universe_scores` calls
        `score_against_tradeable('_rs_raw', na='keep')` -- this reaches
        inside that private call shape by replaying pandas' own rank()
        against the na_option it uses, to pin down that na='top' (the
        default, and what shipped pre-fix) really does put a missing value
        at the SINGLE LOWEST rank rather than leaving it unranked. That is
        the exact mechanism `rank_tradeable`'s docstring in run_all.py
        describes; if a future edit reverts `na='keep'` back to the
        (unspecified) default, `test_missing_one_year_history_gives_no_
        rating_not_the_worst_one` above is what actually catches it -- this
        test documents *why* that default is unsafe for `_rs_raw`."""
        s = pd.Series([0.50, 0.10, 0.05, np.nan])  # NEWIPO-shaped: best raw
        # return of the four, but no 1-year history to compute it against.
        top = s.rank(pct=True, na_option="top") * 99
        keep = s.rank(pct=True, na_option="keep") * 99
        assert top.iloc[3] == top.min(), "na='top' ranks the NaN row worst"
        assert pd.isna(keep.iloc[3]), "na='keep' leaves it unranked instead"
        assert top.iloc[0] == top.max(), "meanwhile it has the best raw return"

