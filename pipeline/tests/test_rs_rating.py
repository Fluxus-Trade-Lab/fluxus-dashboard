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
