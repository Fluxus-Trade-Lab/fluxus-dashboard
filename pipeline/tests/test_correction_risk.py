"""Tests for the Correction Risk base layer (pipeline/risk/correction_risk.py)."""
from __future__ import annotations

import json
import numpy as np
import pandas as pd
import pytest

from pipeline.risk import correction_risk as CR


def synthetic(n=3000, seed=0):
    """Index path whose drawdowns cluster when a 'vix' series is high, so the
    table must come out monotone; below-200dma stretches are the down legs."""
    rng = np.random.default_rng(seed)
    vix = np.clip(18 + 6 * np.sin(np.arange(n) / 90) + rng.normal(0, 3, n), 9, 60)
    vol = vix / 100 / np.sqrt(252)
    ret = rng.normal(0.0004, 1, n) * vol - 0.0006 * (vix > 24)      # stress days drift down
    px = 100 * np.exp(np.cumsum(ret))
    idx = pd.bdate_range("2010-01-01", periods=n)
    return pd.DataFrame({"^GSPC": px, "^VIX": vix}, index=idx)


class TestPieces:
    def test_episodes_counts_runs_not_sessions(self):
        y = pd.Series([0, 1, 1, 1, 0, 0, 1, 0, 1, 1])
        assert CR.episodes(y) == 3
        assert CR.episodes(pd.Series([1, 1, 0])) == 1
        assert CR.episodes(pd.Series([], dtype=float)) == 0

    def test_label_is_forward_min_over_21_sessions(self):
        px = pd.Series(100.0, index=pd.bdate_range("2020-01-01", periods=60))
        px.iloc[30] = 94.0                                  # one bad day
        f = CR.build_frame(pd.DataFrame({"^GSPC": px, "^VIX": 15.0}))
        # sessions 9..29 see the 6% drop inside their next 21 -> y = 1; session 30 itself does not
        assert f["y"].iloc[9] == 1 and f["y"].iloc[29] == 1
        assert f["y"].iloc[8] == 0 and f["y"].iloc[30] == 0
        assert np.isnan(f["y"].iloc[-1])                    # no forward window yet

    def test_quintile_lookup_edges(self):
        edges = [8.0, 13.3, 16.1, 19.5, 24.2, 90.0]
        assert CR.quintile_of(13.3, edges) == 1 and CR.quintile_of(13.31, edges) == 2
        assert CR.quintile_of(50.0, edges) == 5 and CR.quintile_of(100.0, edges) == 5


class TestTable:
    def test_monotone_on_synthetic_stress(self):
        t = CR.conditional_table(CR.build_frame(synthetic()))
        rates = [t["by_vix_quintile"]["full"][q]["rate"] for q in (1, 2, 3, 4, 5)]
        assert rates[-1] > rates[0]
        assert t["monotone_spearman"]["full"] > 0.5
        assert t["sample"]["episodes"] > 5
        assert 0 < t["base_rate"] < 1

    def test_today_reading_points_at_a_real_cell(self):
        f = CR.build_frame(synthetic())
        t = CR.conditional_table(f)
        r = CR.today_reading(f, t)
        assert r["vix_quintile"] in (1, 2, 3, 4, 5)
        key = f"Q{r['vix_quintile']}_{'above' if r['above_200dma'] else 'below'}200"
        assert r["prob"] == t["by_vix_quintile_x_200dma"][key]["rate"]
        assert r["base_rate"] == t["base_rate"]

    def test_run_is_json_safe_and_carries_the_standard(self):
        rep = CR.run(synthetic(), with_appendix=False)
        json.dumps(rep)
        assert rep["predicts_return"] is False and rep["separates_tail"] is True
        assert "base_rate" in rep and "prob" in rep and rep["overlay"]["note"]
        assert isinstance(rep["caveats"], list) and len(rep["caveats"]) >= 3
