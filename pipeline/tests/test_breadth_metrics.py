"""Tests for breadth_metrics screener."""
import datetime as dt

import pytest
import pandas as pd
import numpy as np


def _make_universe(n=100) -> pd.DataFrame:
    """Generate synthetic universe for breadth testing."""
    np.random.seed(42)
    return pd.DataFrame({
        'ticker': [f'STOCK{i}' for i in range(n)],
        'close': np.random.uniform(10, 500, n),
        'change_pct': np.random.uniform(-0.10, 0.10, n),
        'perf_1m': np.random.uniform(-0.40, 0.60, n),
        'perf_3m': np.random.uniform(-0.40, 0.60, n),
        'sma20_dist': np.random.uniform(-0.20, 0.20, n),
        'sma40_dist': np.random.uniform(-0.20, 0.20, n),
        'sma50_dist': np.random.uniform(-0.20, 0.20, n),
        'sma200_dist': np.random.uniform(-0.20, 0.20, n),
        'high_52w': np.random.uniform(-0.50, 0.0, n),  # fraction, not price
        'low_52w': np.random.uniform(0.0, 1.0, n),
    })


class TestComputeSnapshot:
    def test_returns_expected_keys(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        universe = _make_universe()
        result = compute_snapshot(universe)
        # MM keys
        assert 'up_4pct' in result
        assert 'down_4pct' in result
        assert 'up_25pct_qtr' in result
        assert 'down_25pct_qtr' in result
        assert 'up_25pct_month' in result
        assert 'down_25pct_month' in result
        assert 'up_50pct_month' in result
        assert 'down_50pct_month' in result
        # Breadth keys
        assert 't2108' in result
        assert 'pct_above_200sma' in result
        assert 'pct_above_50sma' in result
        assert 'pct_above_20sma' in result
        assert 'advances' in result
        assert 'declines' in result
        assert 'new_highs' in result
        assert 'new_lows' in result
        assert 'net_advances' in result
        assert 'universe_size' in result

    def test_counts_are_non_negative(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        universe = _make_universe()
        result = compute_snapshot(universe)
        for key in ['up_4pct', 'down_4pct', 'advances', 'declines', 'new_highs', 'new_lows']:
            assert result[key] >= 0

    def test_percentages_in_range(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        universe = _make_universe()
        result = compute_snapshot(universe)
        for key in ['t2108', 'pct_above_200sma', 'pct_above_50sma', 'pct_above_20sma']:
            assert 0 <= result[key] <= 100

    def test_universe_size_matches(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        universe = _make_universe(200)
        result = compute_snapshot(universe)
        assert result['universe_size'] == 200

    def test_empty_universe(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        universe = _make_universe(0)
        result = compute_snapshot(universe)
        assert result['universe_size'] == 0
        assert result['advances'] == 0

    def test_all_up_4pct(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        universe = _make_universe(50)
        universe['change_pct'] = 0.05  # all +5%
        result = compute_snapshot(universe)
        assert result['up_4pct'] == 50
        assert result['down_4pct'] == 0


class Test13Pct34d:
    def test_counts_13pct_34d(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        universe = _make_universe(10)
        universe['perf_34d'] = [0.20, 0.13, 0.129, -0.14, -0.13, -0.05, None, 0.0, 0.5, -0.5]
        result = compute_snapshot(universe)
        assert result['up_13pct_34d'] == 3    # 0.20, 0.13, 0.5
        assert result['down_13pct_34d'] == 3  # -0.14, -0.13, -0.5

    def test_missing_column_counts_zero(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        universe = _make_universe(10)  # has no perf_34d column
        result = compute_snapshot(universe)
        assert result['up_13pct_34d'] == 0
        assert result['down_13pct_34d'] == 0


class TestRunOnStore:
    # Pinned, or the suite writes no row on any weekend it happens to run.
    _SESSION = dt.date(2026, 7, 27)                      # a Monday

    def _run(self, tmp_path, universe=None, today=None):
        from pipeline.screeners.breadth_metrics import run
        universe = universe if universe is not None else _make_universe(2000)
        return run(universe, str(tmp_path / 'archive.csv'), spx_close=7400.0,
                   today=today or self._SESSION)

    def test_output_schema_backward_compatible(self, tmp_path):
        result = self._run(tmp_path)
        for key in ['universe_size', 'spx_close', 'mm', 'breadth', 'history']:
            assert key in result
        for key in ['up_4pct', 'down_4pct', 'ratio_5d', 'ratio_10d',
                    'up_25pct_qtr', 'down_25pct_qtr', 'up_13pct_34d', 'down_13pct_34d']:
            assert key in result['mm']
        for key in ['t2108', 'pct_above_200sma', 'advances', 'declines',
                    'new_highs', 'new_lows', 'ad_line', 'mcclellan_osc']:
            assert key in result['breadth']
        for key in ['dates', 'pct_above_200sma', 'pct_above_50sma',
                    'pct_above_20sma', 'mcclellan_osc', 'rows']:
            assert key in result['history']
        assert result['data_quality'] == {'stale': False}
        assert result['history']['rows'][-1]['source'] == 'live'

    def test_rerun_same_day_is_idempotent(self, tmp_path):
        import pandas as pd
        self._run(tmp_path)
        self._run(tmp_path)
        frame = pd.read_csv(tmp_path / 'archive.csv')
        assert len(frame) == 1

    def test_guard_rejection_keeps_archive_and_flags_stale(self, tmp_path):
        import pandas as pd
        self._run(tmp_path)                                  # good day 1
        bad = _make_universe(500)                            # universe collapse
        result = self._run(tmp_path, universe=bad)
        assert result['data_quality']['stale'] is True
        assert 'universe' in result['data_quality']['reason']
        frame = pd.read_csv(tmp_path / 'archive.csv')
        assert len(frame) == 1                               # untouched
        # output still serves yesterday's data
        assert len(result['history']['rows']) == 1


class TestTrueNhNl:
    def test_new_high_requires_at_extreme(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        universe = _make_universe(4)
        # high_52w is (close/52w_high - 1): 0 = at high, -0.0005 within tolerance,
        # -0.015 was a "new high" under the old 2% rule and must NOT count now.
        universe['high_52w'] = [0.0, -0.0005, -0.015, -0.30]
        universe['low_52w'] = [0.0, 0.0009, 0.015, 0.80]
        result = compute_snapshot(universe)
        assert result['new_highs'] == 2
        assert result['new_lows'] == 2
