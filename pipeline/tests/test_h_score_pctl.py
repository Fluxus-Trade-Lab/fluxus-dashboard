"""A weighted average of five percentiles is not a percentile.

Measured on the 2026-09-03 universe (n=5,380): the top h_score decile held
0.6% of names instead of 10%, the bottom 1.0%, and the 30-40 bucket 21.3%.
IQR 29 against 50, SD 18.6 against 28.6. The cause is arithmetic -- the
components are nearly independent (f_score correlates 0.00-0.12 with the
others, i_score 0.00-0.31), so averaging concentrates the result near the
middle.

It never hurt the ranking: every consumer sorts by h_score, and a monotone
squeeze preserves order. It hurt the READING -- h_score is published as
`hybrid_rs` beside real percentiles, where 62 means "top 22%" in one column
and "top 38%" in the other.

Worth recording how this was found, because the first test proposed for it
would have missed it: the handoff suggested checking min/max, expecting a
range visibly narrower than [1,99]. The real range is [1,97] -- 98% of the
interval, which looks fine. A handful of extreme names hold the ends open
while the mass piles up in the middle. Density answers the question; range
does not.
"""
import numpy as np
import pandas as pd
import pytest


def _rank(values):
    """The transform under test, isolated: percentile within the population."""
    s = pd.Series(values, dtype=float)
    return s.rank(method="average", pct=True) * 99


class TestRankingRestoresTheScale:
    def test_averaging_independent_percentiles_compresses(self):
        """The premise. If this fails, there was nothing to fix."""
        rng = np.random.default_rng(3)
        n = 5000
        comps = [rng.uniform(0, 99, n) for _ in range(5)]
        w = [2, 3, 1, 2, 2]
        avg = sum(c * k for c, k in zip(comps, w)) / sum(w)
        top_decile_share = (avg >= 90).mean()
        assert top_decile_share < 0.02, (
            f"expected heavy compression, got {top_decile_share:.1%} above 90")
        iqr = np.percentile(avg, 75) - np.percentile(avg, 25)
        assert iqr < 35, f"IQR {iqr:.0f} -- not compressed, premise is wrong"

    def test_ranking_makes_the_deciles_even_again(self):
        rng = np.random.default_rng(3)
        n = 5000
        comps = [rng.uniform(0, 99, n) for _ in range(5)]
        avg = sum(c * k for c, k in zip(comps, [2, 3, 1, 2, 2])) / 10
        pct = _rank(avg)
        for lo in range(0, 90, 10):
            share = ((pct >= lo) & (pct < lo + 10)).mean()
            assert 0.07 < share < 0.13, f"decile {lo}-{lo+10} holds {share:.1%}"

    def test_ranking_preserves_the_order_exactly(self):
        """Every consumer sorts by this. The fix must not reorder anything."""
        rng = np.random.default_rng(7)
        raw = pd.Series(rng.normal(45, 18, 2000))
        pct = _rank(raw)
        assert list(raw.rank(method="average")) == list(pct.rank(method="average"))

    def test_range_would_not_have_revealed_it(self):
        """The check that fails to find the defect, kept as a warning.

        min/max reach the ends even under heavy compression, because a few
        names always sit at the extremes. Asserting on range would have
        returned a clean bill of health.
        """
        rng = np.random.default_rng(3)
        comps = [rng.uniform(0, 99, 5000) for _ in range(5)]
        avg = sum(c * k for c, k in zip(comps, [2, 3, 1, 2, 2])) / 10
        assert avg.min() < 25 and avg.max() > 75      # "range looks broad"
        assert (avg >= 90).mean() < 0.02              # density says otherwise
