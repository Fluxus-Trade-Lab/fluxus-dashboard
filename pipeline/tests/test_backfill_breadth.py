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
