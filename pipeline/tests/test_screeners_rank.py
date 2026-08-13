"""The rank-NaN defect, guarded across every screener that ranks.

`na_option='bottom'` names the option by RANK POSITION, so a missing value
takes the LARGEST rank -- the top of a percentile scale. It has now been found
three separate times in this codebase, so this file tests the property rather
than any one call site.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pipeline.screeners import ema21_watch, healthy_charts, momentum_97


def universe(n_real=100, n_missing=30):
    """Real names with spread returns, plus rows whose returns are all NaN."""
    rows = []
    for i in range(n_real):
        r = 0.30 - i * 0.005
        rows.append({"ticker": f"R{i}", "sector": "Technology",
                     "perf_1w": r / 4, "perf_1m": r / 2,
                     "perf_3m": r, "perf_6m": r * 1.5})
    for i in range(n_missing):
        rows.append({"ticker": f"N{i}", "sector": "Technology",
                     "perf_1w": np.nan, "perf_1m": np.nan,
                     "perf_3m": np.nan, "perf_6m": np.nan})
    return pd.DataFrame(rows)


class TestMissingReturnsNeverRankTop:
    def test_composite_rs_puts_unknown_names_at_the_bottom(self):
        df = universe()
        comp = momentum_97._compute_composite_rs(df)
        known, unknown = comp[:100], comp[100:]
        assert unknown.max() < known.min(), (
            "a name with no returns outranked every name with returns")

    def test_the_97th_percentile_selects_real_leaders(self):
        """The 2026-08-12 failure: 1,259 all-NaN rows shared one composite of
        88.26, the 97th percentile landed inside that constant block, and the
        screener returned those rows and nothing else."""
        out = momentum_97.run(universe())
        picked = [t["ticker"] for b in out["buckets"].values() for t in b]
        assert picked, "screener returned nothing"
        assert all(t.startswith("R") for t in picked), f"unknown names selected: {picked}"

    def test_bracket_screeners_stay_reachable_when_a_fifth_is_missing(self):
        """The mirror failure: NaN rows occupying the top of the ranking pushed
        every real name under the bracket floor of 80, so both screeners
        returned zero rows on an ordinary tape."""
        s = universe()["perf_3m"]
        for module in (healthy_charts, ema21_watch):
            rs = module._perf_3m_rs(s)
            assert rs[:100].max() > module._MIN_RS_BRACKET, (
                f"{module.__name__}: best real name only reached {rs[:100].max():.1f}")

    @pytest.mark.parametrize("missing_share", [0.05, 0.25, 0.5])
    def test_holds_at_any_missing_share(self, missing_share):
        n_real = 100
        df = universe(n_real, int(n_real * missing_share / (1 - missing_share)))
        comp = momentum_97._compute_composite_rs(df)
        assert comp[n_real:].max() < comp[:n_real].min()
