"""Tests for the one-time breadth backfill tool (pure functions only — no network)."""
import numpy as np
import pandas as pd
import pytest


def _make_closes(n_days=260, n_tickers=50, seed=7):
    """Random-walk closes, business-day index ending 2026-07-24."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(end='2026-07-24', periods=n_days)
    prices = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, (n_days, n_tickers)), axis=0))
    return pd.DataFrame(prices, index=idx, columns=[f'S{i}' for i in range(n_tickers)])


class TestComputeBackfillRows:
    def test_only_dates_with_200_prior_sessions(self):
        from pipeline.tools.backfill_breadth import compute_backfill_rows
        closes = _make_closes(260)
        spx = closes['S0']
        rows = compute_backfill_rows(closes, spx)
        assert len(rows) == 260 - 200
        assert (rows['source'] == 'backfill').all()

    def test_dates_are_iso_session_dates(self):
        from pipeline.tools.backfill_breadth import compute_backfill_rows
        closes = _make_closes(210)
        rows = compute_backfill_rows(closes, closes['S0'])
        assert rows['date'].iloc[0] == closes.index[200].strftime('%Y-%m-%d')

    def test_counts_match_hand_computation_on_last_day(self):
        from pipeline.tools.backfill_breadth import compute_backfill_rows
        closes = _make_closes(220)
        rows = compute_backfill_rows(closes, closes['S0'])
        last_date = closes.index[-1]
        chg = closes.loc[last_date] / closes.iloc[-2] - 1
        assert rows.iloc[-1]['up_4pct'] == int((chg >= 0.04).sum())
        assert rows.iloc[-1]['advances'] == int((chg > 0).sum())
        sma200 = closes.rolling(200).mean().loc[last_date]
        assert rows.iloc[-1]['pct_above_200sma'] == pytest.approx(
            float((closes.loc[last_date] > sma200).sum()) / closes.shape[1] * 100, abs=0.01)

    def test_new_highs_true_extremes(self):
        from pipeline.tools.backfill_breadth import compute_backfill_rows
        # Monotonically rising market: every scored day, every stock is at its 52w high
        idx = pd.bdate_range(end='2026-07-24', periods=210)
        closes = pd.DataFrame(
            {'A': np.linspace(100, 200, 210), 'B': np.linspace(50, 80, 210)}, index=idx)
        rows = compute_backfill_rows(closes, closes['A'])
        assert (rows['new_highs'] == 2).all()
        assert (rows['new_lows'] == 0).all()
        # Same result when intraday extremes are supplied explicitly and equal close
        rows_hl = compute_backfill_rows(closes, closes['A'], highs=closes, lows=closes)
        assert (rows_hl['new_highs'] == 2).all()
        assert (rows_hl['new_lows'] == 0).all()

    def test_new_highs_use_intraday_extremes_when_given(self):
        """Live semantics: close vs 1y max of intraday High / min of intraday Low.

        A close that ties the close-based 52w max is NOT a new high when an
        earlier bar printed a higher intraday High.
        """
        from pipeline.tools.backfill_breadth import compute_backfill_rows
        idx = pd.bdate_range(end='2026-07-24', periods=210)
        closes = pd.DataFrame({'A': np.full(210, 100.0)}, index=idx)
        highs = closes.copy()
        highs.iloc[50, 0] = 130.0  # a lone intraday spike a year's-worth ago
        lows = closes.copy()

        close_based = compute_backfill_rows(closes, closes['A'])
        assert (close_based['new_highs'] == 1).all()  # flat closes all tie the max

        intraday = compute_backfill_rows(closes, closes['A'], highs=highs, lows=lows)
        assert (intraday['new_highs'] == 0).all()  # 100 is far below the 130 High

    def test_new_lows_use_intraday_low_when_given(self):
        from pipeline.tools.backfill_breadth import compute_backfill_rows
        idx = pd.bdate_range(end='2026-07-24', periods=210)
        closes = pd.DataFrame({'A': np.full(210, 100.0)}, index=idx)
        highs = closes.copy()
        lows = closes.copy()
        lows.iloc[50, 0] = 70.0
        rows = compute_backfill_rows(closes, closes['A'], highs=highs, lows=lows)
        assert (rows['new_lows'] == 0).all()

    def test_perf_windows_match_live_iloc_offsets(self):
        """Live uses iloc[-21]/iloc[-63] = 20/62 sessions back; perf_34d = 34."""
        from pipeline.tools.backfill_breadth import compute_backfill_rows
        closes = _make_closes(230)
        rows = compute_backfill_rows(closes, closes['S0'])
        last = rows.iloc[-1]
        c = closes.iloc[-1]
        p1m = c / closes.iloc[-21] - 1
        p3m = c / closes.iloc[-63] - 1
        p34 = c / closes.iloc[-35] - 1
        assert last['up_25pct_month'] == int((p1m >= 0.25).sum())
        assert last['down_25pct_month'] == int((p1m <= -0.25).sum())
        assert last['up_25pct_qtr'] == int((p3m >= 0.25).sum())
        assert last['up_13pct_34d'] == int((p34 >= 0.13).sum())

    def test_universe_size_counts_non_nan(self):
        from pipeline.tools.backfill_breadth import compute_backfill_rows
        closes = _make_closes(210, n_tickers=10)
        closes.iloc[-1, 0] = np.nan  # one ticker missing on the last day
        rows = compute_backfill_rows(closes, closes['S1'])
        assert rows.iloc[-1]['universe_size'] == 9


class TestMergeBackfill:
    def test_live_wins_on_collision(self):
        from pipeline.tools.backfill_breadth import merge_backfill
        live = pd.DataFrame([{'date': '2026-07-24', 'source': 'live', 'advances': 999}])
        back = pd.DataFrame([
            {'date': '2026-07-23', 'source': 'backfill', 'advances': 1},
            {'date': '2026-07-24', 'source': 'backfill', 'advances': 2},
        ])
        merged = merge_backfill(live, back)
        assert len(merged) == 2
        row = merged[merged['date'] == '2026-07-24'].iloc[0]
        assert row['source'] == 'live' and row['advances'] == 999
        assert list(merged['date']) == ['2026-07-23', '2026-07-24']

    def test_implausible_live_rows_replaced_by_backfill(self):
        from pipeline.tools.backfill_breadth import merge_backfill
        live = pd.DataFrame([
            {'date': '2026-07-15', 'source': 'live', 'advances': 5, 'pct_above_200sma': 0.4},
            {'date': '2026-07-16', 'source': 'live', 'advances': 1500, 'pct_above_200sma': 46.0},
        ])
        back = pd.DataFrame([
            {'date': '2026-07-15', 'source': 'backfill', 'advances': 1400, 'pct_above_200sma': 45.0},
            {'date': '2026-07-16', 'source': 'backfill', 'advances': 1450, 'pct_above_200sma': 45.5},
        ])
        merged = merge_backfill(live, back)
        assert len(merged) == 2
        r15 = merged[merged['date'] == '2026-07-15'].iloc[0]
        assert r15['source'] == 'backfill' and r15['advances'] == 1400  # poisoned live replaced
        r16 = merged[merged['date'] == '2026-07-16'].iloc[0]
        assert r16['source'] == 'live' and r16['advances'] == 1500      # honest live wins

    def test_implausible_live_row_kept_when_no_backfill_for_date(self):
        from pipeline.tools.backfill_breadth import merge_backfill
        live = pd.DataFrame([{'date': '2026-07-15', 'source': 'live', 'advances': 5, 'pct_above_200sma': 0.4}])
        back = pd.DataFrame([{'date': '2026-07-14', 'source': 'backfill', 'advances': 1400, 'pct_above_200sma': 45.0}])
        merged = merge_backfill(live, back)
        assert len(merged) == 2  # implausible live survives when backfill has nothing for that date

    def test_tiny_universe_live_row_replaced_by_backfill(self):
        from pipeline.tools.backfill_breadth import merge_backfill
        live = pd.DataFrame([
            {'date': '2026-06-08', 'source': 'live', 'advances': 84,
             'universe_size': 200, 'pct_above_200sma': 56.5},
        ])
        back = pd.DataFrame([
            {'date': '2026-06-08', 'source': 'backfill', 'advances': 1300,
             'universe_size': 2700, 'pct_above_200sma': 55.0},
        ])
        merged = merge_backfill(live, back)
        assert len(merged) == 1
        assert merged.iloc[0]['source'] == 'backfill' and merged.iloc[0]['advances'] == 1300

    def test_non_session_live_rows_dropped_inside_backfill_range(self):
        from pipeline.tools.backfill_breadth import merge_backfill
        live = pd.DataFrame([
            {'date': '2026-05-22', 'source': 'live', 'advances': 1449, 'pct_above_200sma': 59.1},
            {'date': '2026-05-24', 'source': 'live', 'advances': 1448, 'pct_above_200sma': 59.1},  # Sunday
            {'date': '2026-05-25', 'source': 'live', 'advances': 1449, 'pct_above_200sma': 59.1},  # holiday
        ])
        back = pd.DataFrame([
            {'date': '2026-05-22', 'source': 'backfill', 'advances': 1400, 'pct_above_200sma': 58.0},
            {'date': '2026-05-26', 'source': 'backfill', 'advances': 1500, 'pct_above_200sma': 58.5},
        ])
        merged = merge_backfill(live, back)
        assert list(merged['date']) == ['2026-05-22', '2026-05-26']
        assert merged[merged['date'] == '2026-05-22'].iloc[0]['source'] == 'live'  # honest live still wins

    def test_surviving_live_rows_hydrated_from_same_date_reconstruction(self):
        """Old live rows carry pre-v2 NH/NL semantics and null 13% columns.

        The reconstruction is the same universe on the same day under the new
        semantics, so exactly those four columns are overwritten; everything
        else (source, advances, ...) stays live.
        """
        from pipeline.tools.backfill_breadth import merge_backfill
        live = pd.DataFrame([{
            'date': '2026-07-28', 'source': 'live', 'advances': 1608,
            'pct_above_200sma': 46.73, 'universe_size': 3000,
            'new_highs': 327, 'new_lows': 99,
            'up_13pct_34d': pd.NA, 'down_13pct_34d': pd.NA,
        }])
        back = pd.DataFrame([{
            'date': '2026-07-28', 'source': 'backfill', 'advances': 1400,
            'pct_above_200sma': 45.0, 'universe_size': 2980,
            'new_highs': 30, 'new_lows': 90,
            'up_13pct_34d': 550, 'down_13pct_34d': 610,
        }])
        merged = merge_backfill(live, back)
        assert len(merged) == 1
        row = merged.iloc[0]
        assert row['source'] == 'live'
        assert row['advances'] == 1608           # live's own measurements untouched
        assert row['universe_size'] == 3000
        assert row['pct_above_200sma'] == 46.73
        assert row['new_highs'] == 30            # new semantics
        assert row['new_lows'] == 90
        assert row['up_13pct_34d'] == 550        # previously null
        assert row['down_13pct_34d'] == 610

    def test_live_rows_without_reconstruction_are_not_hydrated(self):
        from pipeline.tools.backfill_breadth import merge_backfill
        live = pd.DataFrame([{
            'date': '2026-08-02', 'source': 'live', 'advances': 1500,
            'pct_above_200sma': 50.0, 'new_highs': 42,
        }])
        back = pd.DataFrame([{
            'date': '2026-07-28', 'source': 'backfill', 'advances': 1400,
            'pct_above_200sma': 45.0, 'new_highs': 30,
        }])
        merged = merge_backfill(live, back)
        row = merged[merged['date'] == '2026-08-02'].iloc[0]
        assert row['new_highs'] == 42

    def test_live_rows_outside_backfill_range_kept(self):
        from pipeline.tools.backfill_breadth import merge_backfill
        live = pd.DataFrame([
            {'date': '2026-08-02', 'source': 'live', 'advances': 1500, 'pct_above_200sma': 50.0},  # after range
        ])
        back = pd.DataFrame([
            {'date': '2026-07-28', 'source': 'backfill', 'advances': 1400, 'pct_above_200sma': 45.0},
        ])
        merged = merge_backfill(live, back)
        assert len(merged) == 2
