"""Tests for breadth_metrics screener."""
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
    def _run(self, tmp_path, universe=None):
        from pipeline.screeners.breadth_metrics import run
        universe = universe if universe is not None else _make_universe(2000)
        return run(universe, str(tmp_path / 'archive.csv'), spx_close=7400.0)

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


class TestFourWeekNewHighsLows:
    """4w new highs/lows -- the matched-horizon companion to the 52w pair.

    Added 2026-08-31. The 252-session reading is structurally blind to a
    four-week deterioration (a name has to undercut a whole year of lows to
    count), which is why on 2026-08-28 it was the lone dissenter while three
    other breadth readings fell. These tests pin the two properties that
    make the new pair trustworthy: it counts on the SAME rule as the 52w
    pair, and a missing input reads as NULL rather than as "none today".
    """

    def _uni(self, **over):
        import pandas as pd
        base = {
            'ticker': ['A', 'B', 'C', 'D'],
            'close': [100.0, 100.0, 100.0, 100.0],
            'change_pct': [0.01, -0.01, 0.01, -0.01],
            'perf_1m': [0.0] * 4, 'perf_3m': [0.0] * 4,
            'sma20_dist': [0.0] * 4, 'sma40_dist': [0.0] * 4,
            'sma50_dist': [0.0] * 4, 'sma200_dist': [0.0] * 4,
            'high_52w': [-0.20] * 4, 'low_52w': [0.20] * 4,
            # A at its 20d high, B at its 20d low, C and D in the middle
            'high_20d': [0.0, -0.15, -0.08, -0.09],
            'low_20d': [0.30, 0.0, 0.11, 0.12],
        }
        base.update(over)
        return pd.DataFrame(base)

    def test_counts_names_at_their_4w_extreme(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        r = compute_snapshot(self._uni())
        assert r['new_highs_4w'] == 1     # A only
        assert r['new_lows_4w'] == 1      # B only

    def test_uses_the_same_tolerance_as_the_52w_pair(self):
        """Within 0.1% of the extreme still counts -- quotes are not exact."""
        from pipeline.screeners.breadth_metrics import compute_snapshot
        r = compute_snapshot(self._uni(high_20d=[-0.0005, -0.15, -0.08, -0.09]))
        assert r['new_highs_4w'] == 1
        r2 = compute_snapshot(self._uni(high_20d=[-0.02, -0.15, -0.08, -0.09]))
        assert r2['new_highs_4w'] == 0    # 2% off the high is NOT a new high

    def test_missing_column_is_null_not_zero(self):
        """The failure that would matter: an absent input reading as calm.

        If the adapter stops emitting high_20d/low_20d, the count must go
        NULL so a guard can see it. Zero would render as "no new lows today"
        -- the most bullish possible reading of a data outage.
        """
        from pipeline.screeners.breadth_metrics import compute_snapshot
        u = self._uni().drop(columns=['high_20d', 'low_20d'])
        r = compute_snapshot(u)
        assert r['new_highs_4w'] is None
        assert r['new_lows_4w'] is None

    def test_4w_is_more_sensitive_than_52w_on_the_same_rows(self):
        """The whole point: names can be at 4w lows without being at 52w lows.

        Positive control for the premise -- if this ever fails, the two
        windows are returning the same thing and the new pair is pointless.
        """
        from pipeline.screeners.breadth_metrics import compute_snapshot
        # every name is far from its 52w low but sitting on its 20d low
        u = self._uni(low_52w=[0.40] * 4, low_20d=[0.0] * 4)
        r = compute_snapshot(u)
        assert r['new_lows'] == 0
        assert r['new_lows_4w'] == 4


class TestCommonStockUniverse:
    """The standard new-high/new-low universe is COMMON STOCKS ONLY.

    NYSE, Nasdaq and NYSE Arca publish their counts with UITs, closed-end
    funds, warrants, preferreds, ETFs, SPACs and non-SIC issues removed --
    by SECURITY TYPE, not by size. On 2026-08-28, 58 of the 66 names counted
    as 52-week new highs were Finviz `industry == "Shell Companies"`, i.e.
    SPACs, which accrete toward trust value and so print new highs almost
    every session regardless of the market. That is why the reading could
    not deteriorate on a day 3,386 names fell.

    These tests replaced a set written against a $5/share + $5M-volume gate,
    which was my own invention before I checked whether a professional
    definition existed. It did.
    """

    def _uni(self, **over):
        import pandas as pd
        base = {
            'ticker': ['SPAC1', 'SPAC2', 'BIGCO', 'SMALLCO'],
            # SMALLCO is a genuinely small common stock: the size gate would
            # have thrown it out, the standard keeps it, and breadth exists
            # precisely to hear from names like it.
            'industry': ['Shell Companies', 'Shell Companies',
                         'Software - Application', 'Banks - Regional'],
            'close': [10.20, 10.20, 80.0, 6.0],
            'avg_volume': [16_000, 16_000, 2_000_000, 20_000],
            'bars_n': [250, 250, 250, 250],
            'change_pct': [0.0, 0.0, 0.01, 0.01],
            'perf_1m': [0.0] * 4, 'perf_3m': [0.0] * 4,
            'sma20_dist': [0.0] * 4, 'sma40_dist': [0.0] * 4,
            'sma50_dist': [0.0] * 4, 'sma200_dist': [0.0] * 4,
            'high_52w': [0.0, 0.0, 0.0, 0.0],
            'low_52w': [0.50, 0.50, 0.60, 0.60],
            'high_20d': [0.0, 0.0, 0.0, 0.0],
            'low_20d': [0.20, 0.20, 0.25, 0.25],
        }
        base.update(over)
        return pd.DataFrame(base)

    def test_shells_are_excluded_and_small_common_stocks_are_not(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        r = compute_snapshot(self._uni())
        assert r['new_highs'] == 4            # raw: everything
        assert r['new_highs_common'] == 2     # BIGCO and SMALLCO
        assert r['new_highs_4w_common'] == 2
        assert r['common_universe'] == 2

    def test_a_size_gate_would_have_dropped_the_small_common_stock(self):
        """Positive control for choosing type over size.

        SMALLCO trades $120k a day. The $5M gate I wrote first would have
        removed it along with the SPACs -- silencing a real common stock,
        which is the opposite of what a breadth reading is for. If this ever
        starts failing, the type filter has quietly become a size filter.
        """
        from pipeline.screeners.breadth_metrics import compute_snapshot
        u = self._uni()
        small = u[u['ticker'] == 'SMALLCO']
        assert float(small['close'].iloc[0] * small['avg_volume'].iloc[0]) < 5_000_000
        r = compute_snapshot(u)
        assert r['new_highs_common'] == 2     # SMALLCO still counted

    def test_raw_counts_are_untouched_by_the_filter(self):
        """Continuity: 574 archive rows stand behind new_highs/new_lows.

        Redefining them in place would put a SECOND level break into a series
        that already has one (universe 3000 -> 5614 on 2026-08-14).
        """
        from pipeline.screeners.breadth_metrics import compute_snapshot
        filtered = compute_snapshot(self._uni())
        plain = compute_snapshot(self._uni().drop(columns=['industry']))
        assert filtered['new_highs'] == plain['new_highs'] == 4

    def test_missing_industry_is_null_not_zero(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        r = compute_snapshot(self._uni().drop(columns=['industry']))
        for k in ('new_highs_common', 'new_lows_common',
                  'new_highs_4w_common', 'new_lows_4w_common', 'common_universe'):
            assert r[k] is None, f"{k} should be NULL when industry is absent"

    def test_the_2x2_is_complete(self):
        """Window effect and contamination effect must be separately readable.

        One filtered number would confound them: any move could be either
        cause. Four counts on {20d, 252d} x {raw, common} cannot.
        """
        from pipeline.screeners.breadth_metrics import compute_snapshot
        r = compute_snapshot(self._uni())
        for k in ('new_highs', 'new_highs_4w', 'new_highs_common', 'new_highs_4w_common',
                  'new_lows', 'new_lows_4w', 'new_lows_common', 'new_lows_4w_common'):
            assert k in r


class TestMinimumHistory:
    """A 52-week high requires 52 weeks of existence.

    2026-08-28: of the 66 names counted as 52w new highs, 32% had under 126
    bars and the shortest (OCAC) had 19. Nineteen sessions cannot produce a
    252-session extreme -- the name's entire life is the lookback window.
    The liquidity gate happened to remove most of them, but for the wrong
    reason: a liquid recent IPO ($50M/day, 60 bars) passes liquidity and is
    still not eligible for a 52-week high.
    """

    def _uni(self, **over):
        import pandas as pd
        base = {
            # OLD: liquid, full history, at its high -> counts
            # IPO: liquid, 60 bars, at its "52w high" -> must NOT count for
            #      52w, but IS eligible for the 20-day one
            # BABY: 12 bars -> eligible for neither
            'ticker': ['OLD', 'IPO', 'BABY'],
            'industry': ['Software - Application'] * 3,
            'close': [80.0, 40.0, 30.0],
            'avg_volume': [2_000_000, 2_000_000, 2_000_000],
            'bars_n': [250, 60, 12],
            'change_pct': [0.01, 0.01, 0.01],
            'perf_1m': [0.0] * 3, 'perf_3m': [0.0] * 3,
            'sma20_dist': [0.0] * 3, 'sma40_dist': [0.0] * 3,
            'sma50_dist': [0.0] * 3, 'sma200_dist': [0.0] * 3,
            'high_52w': [0.0, 0.0, 0.0], 'low_52w': [0.5, 0.5, 0.5],
            'high_20d': [0.0, 0.0, 0.0], 'low_20d': [0.2, 0.2, 0.2],
        }
        base.update(over)
        return pd.DataFrame(base)

    def test_a_recent_ipo_is_not_a_52_week_high(self):
        """The case the security-type filter cannot catch: a real common
        stock that simply has not existed long enough."""
        from pipeline.screeners.breadth_metrics import compute_snapshot
        r = compute_snapshot(self._uni())
        assert r['new_highs'] == 3          # ungated: all three, unchanged
        assert r['new_highs_common'] == 1      # only OLD has 52 weeks behind it

    def test_the_same_ipo_is_eligible_for_the_4_week_high(self):
        """Per-window floors: 60 bars is plenty for a 20-session extreme."""
        from pipeline.screeners.breadth_metrics import compute_snapshot
        r = compute_snapshot(self._uni())
        assert r['new_highs_4w_common'] == 2   # OLD and IPO; BABY has 12 bars

    def test_short_history_count_is_reported_not_hidden(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        r = compute_snapshot(self._uni())
        assert r['short_history_n'] == 2    # IPO and BABY

    def test_missing_bar_count_is_null_not_zero(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        u = self._uni().drop(columns=['bars_n'])
        r = compute_snapshot(u)
        for k in ('new_highs_common', 'new_lows_common',
                  'new_highs_4w_common', 'new_lows_4w_common', 'short_history_n'):
            assert r[k] is None, f"{k} must be NULL when bar counts are absent"


class TestIndexScopedBreadth:
    """Percent-above-MA is meaningless without saying WHICH index.

    StockCharts publishes this family per index -- $SPXA200R for the S&P 500,
    $NYA200R for the NYSE. Ours was computed on a 5,630-name screener universe
    matching no published index, so it could not be compared with anything.
    Measured 2026-09-03 on the same market: our full universe read 53.45 for
    %>200SMA, our >=$10B slice 70.09, Andy's reference card 70.77, and that
    card's own S5TH chart 66.40.
    """

    def _uni(self, **over):
        import pandas as pd
        base = {
            'ticker': ['IN1', 'IN2', 'OUT1', 'OUT2'],
            'industry': ['Software - Application'] * 4,
            'close': [50.0] * 4, 'avg_volume': [2_000_000] * 4, 'bars_n': [250] * 4,
            'change_pct': [0.01] * 4, 'perf_1m': [0.0] * 4, 'perf_3m': [0.0] * 4,
            # members strong, non-members weak: the two readings must diverge
            'sma20_dist': [0.05, 0.05, -0.05, -0.05],
            'sma40_dist': [0.05, 0.05, -0.05, -0.05],
            'sma50_dist': [0.05, 0.05, -0.05, -0.05],
            'sma200_dist': [0.05, 0.05, -0.05, -0.05],
            'high_52w': [-0.2] * 4, 'low_52w': [0.2] * 4,
            'in_sp500': [True, True, False, False],
        }
        base.update(over)
        return pd.DataFrame(base)

    def test_the_index_reading_differs_from_the_universe_reading(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        r = compute_snapshot(self._uni())
        assert r['pct_above_200sma'] == 50.0        # whole universe
        assert r['pct_above_200sma_sp500'] == 100.0  # members only
        assert r['sp500_members'] == 2

    def test_the_whole_universe_columns_are_untouched(self):
        """574 rows of archive stand behind them; this must be additive."""
        from pipeline.screeners.breadth_metrics import compute_snapshot
        with_idx = compute_snapshot(self._uni())
        without = compute_snapshot(self._uni().drop(columns=['in_sp500']))
        for k in ('pct_above_20sma', 't2108', 'pct_above_50sma', 'pct_above_200sma'):
            assert with_idx[k] == without[k]

    def test_missing_membership_is_null_not_the_whole_universe(self):
        """The substitution that caused the problem must not be the fallback.

        Silently reporting the 5,630-name reading under an S&P 500 name is
        precisely how a number stops being comparable.
        """
        from pipeline.screeners.breadth_metrics import compute_snapshot
        r = compute_snapshot(self._uni().drop(columns=['in_sp500']))
        for k in ('pct_above_20sma_sp500', 't2108_sp500',
                  'pct_above_50sma_sp500', 'pct_above_200sma_sp500', 'sp500_members'):
            assert r[k] is None, f"{k} fell back instead of going NULL"

    def test_an_empty_membership_set_is_also_null(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        r = compute_snapshot(self._uni(in_sp500=[False] * 4))
        assert r['pct_above_200sma_sp500'] is None
        assert r['sp500_members'] is None


class TestStockbeeBreadth:
    """`up_4pct` counts only the price leg of a three-condition scan.

    Pradeep Bonde's 4% scan is a daily cross-sectional count and asks for
    close >= +4%, volume above the PREVIOUS day's, and volume over 100,000,
    on US common stocks. Our archive column has only ever had the first.
    `bo_count_*` was corrected to all three on 2026-09-04, but that is the
    per-ticker rolling count -- our own aggregation. This is the reading
    Stockbee actually publishes.
    """

    def _uni(self, **over):
        import pandas as pd
        base = {
            'ticker': ['EXPAND', 'SHRINK', 'SPAC', 'THIN'],
            'industry': ['Software - Application', 'Software - Application',
                         'Shell Companies', 'Software - Application'],
            'close': [50.0] * 4, 'avg_volume': [2_000_000] * 4, 'bars_n': [250] * 4,
            'change_pct': [0.05] * 4,            # all four cleared +4%
            'volume':      [900_000, 800_000, 900_000, 50_000],
            'prev_volume': [500_000, 900_000, 500_000, 10_000],
            'perf_1m': [0.0] * 4, 'perf_3m': [0.0] * 4,
            'sma20_dist': [0.0] * 4, 'sma40_dist': [0.0] * 4,
            'sma50_dist': [0.0] * 4, 'sma200_dist': [0.0] * 4,
            'high_52w': [-0.2] * 4, 'low_52w': [0.2] * 4,
        }
        base.update(over)
        return pd.DataFrame(base)

    def test_each_condition_removes_its_own_name(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        r = compute_snapshot(self._uni())
        assert r['up_4pct'] == 4              # price leg alone
        assert r['up_4pct_stockbee'] == 1     # SHRINK, SPAC and THIN all fail

    def test_volume_expansion_is_required(self):
        """The condition the archive column never had."""
        from pipeline.screeners.breadth_metrics import compute_snapshot
        r = compute_snapshot(self._uni(volume=[900_000] * 4,
                                       prev_volume=[1_000_000] * 4))
        assert r['up_4pct'] == 4
        assert r['up_4pct_stockbee'] == 0

    def test_the_hundred_thousand_floor_applies(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        r = compute_snapshot(self._uni(volume=[99_999] * 4, prev_volume=[1] * 4))
        assert r['up_4pct_stockbee'] == 0

    def test_the_original_columns_do_not_move(self):
        """574 archive rows. This is additive or it is a level break."""
        from pipeline.screeners.breadth_metrics import compute_snapshot
        with_v = compute_snapshot(self._uni())
        without = compute_snapshot(self._uni().drop(columns=['prev_volume']))
        assert with_v['up_4pct'] == without['up_4pct'] == 4
        assert with_v['down_4pct'] == without['down_4pct']

    def test_missing_prev_volume_is_null_not_zero(self):
        """Zero would read as 'nobody expanded today' -- the calmest possible
        rendering of a column that has not arrived yet."""
        from pipeline.screeners.breadth_metrics import compute_snapshot
        r = compute_snapshot(self._uni().drop(columns=['prev_volume']))
        assert r['up_4pct_stockbee'] is None
        assert r['down_4pct_stockbee'] is None
