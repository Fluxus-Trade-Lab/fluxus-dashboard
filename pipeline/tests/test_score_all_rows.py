"""'全部打分' (2026-08-17): every row carries RS, on the tradeable ruler.

Three properties, each a thing that could silently regress:
  1. tradeable rows score exactly as before -- the field is unchanged;
  2. a non-tradeable row reads its percentile within the tradeable field,
     so it can never sit between two field members it does not belong between;
  3. a row with no perf value gets no score outside the field.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.screeners.run_all import compute_universe_scores


def _universe(n_field=50, n_out=10, seed=1):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n_field + n_out):
        inside = i < n_field
        rows.append({
            "ticker": f"T{i}", "industry": "Ind" + str(i % 3),
            "market_cap": 5e9 if inside else 2e8,
            "avg_volume": 3e6, "close": 50.0, "atr": 1.5,
            "sma20_dist": 0.01, "sma50_dist": 0.05, "high_52w": 0.9, "low_52w": 0.3,
            "perf_1w": rng.normal(0, .05), "perf_1m": rng.normal(0, .1),
            "perf_3m": rng.normal(0, .2), "perf_6m": rng.normal(0, .3),
            "perf_1y": rng.normal(0, .4),
        })
    return pd.DataFrame(rows)


class TestScoreAllRows:
    def test_field_scores_are_unchanged_by_the_outsiders(self):
        u = _universe()
        with_out = compute_universe_scores(u).set_index("ticker")
        alone = compute_universe_scores(u[u.market_cap > 1e9]).set_index("ticker")
        field = alone.index
        for c in ("rs_1m", "rs_3m", "rs_6m", "rs_ibd", "i_score", "h_score"):
            pd.testing.assert_series_equal(with_out.loc[field, c], alone[c], check_names=False)

    def test_outsiders_score_on_the_field_ruler(self):
        out = compute_universe_scores(_universe()).set_index("ticker")
        field = out[out.tradeable]
        for t, r in out[~out.tradeable].iterrows():
            below = (field.perf_3m < r.perf_3m).mean() * 99
            above = (field.perf_3m <= r.perf_3m).mean() * 99
            assert below - 1.5 <= float(r.rs_3m) <= above + 1.5, (t, r.rs_3m, below, above)
        assert out["rs_3m"].notna().all() and out["h_score"].notna().all()

    def test_outsider_without_perf_gets_no_score(self):
        u = _universe()
        u.loc[u.ticker == "T55", ["perf_3m"]] = np.nan
        out = compute_universe_scores(u).set_index("ticker")
        assert pd.isna(out.loc["T55", "rs_3m"])
        # a FIELD member with a missing value keeps the lowest rank (denominator preserved)
        u.loc[u.ticker == "T5", ["perf_3m"]] = np.nan
        out = compute_universe_scores(u).set_index("ticker")
        assert out.loc["T5", "rs_3m"] == out.loc[out.tradeable, "rs_3m"].min()

    def test_liquid_leader_stays_inside_the_field(self):
        u = _universe()
        u.loc[~(u.market_cap > 1e9), "perf_3m"] = 5.0     # outsiders would all be RS 99
        out = compute_universe_scores(u).set_index("ticker")
        assert not out.loc[~out.tradeable, "liquid_leader"].any()
