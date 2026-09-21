"""Andy 2026-09-21 on the self-made-number recheck: 「用stockbee口径。thrust改名不要撞名。EP用新配方」.

Three places still read the retired price-only columns after the 09-18 switch:
the Market State percentiles (printed next to Stockbee digits), the Conditions
0-100 inputs (one of them keyed 'thrust'), and the Short List EP mark.
"""
import numpy as np
import pandas as pd

import pipeline.screeners.breadth_signals as bs
from pipeline.screeners.name_cards import marks_from_bars


def _frame(n, old_up, sb_up, start='2026-08-10'):
    dates = pd.bdate_range(start, periods=n).strftime('%Y-%m-%d')
    return pd.DataFrame({'date': dates, 'up_4pct': old_up, 'down_4pct': 100.0,
                         'up_4pct_stockbee': sb_up, 'down_4pct_stockbee': 100.0,
                         't2108': 50.0, 'ratio_5d_stockbee': 1.0, 'mcclellan_osc': 0.0,
                         'new_highs_common': 5, 'new_lows_common': 5,
                         'up_25pct_qtr_stockbee': 5, 'down_25pct_qtr_stockbee': 5})


def test_percentile_ranks_the_stockbee_count_not_the_old_one():
    n = 70
    old_up = np.arange(n, dtype=float)            # old column: today is the max
    sb_up = np.arange(n, 0, -1, dtype=float)      # Stockbee column: today is the min
    ctx = bs.percentile_context(_frame(n, old_up, sb_up))
    assert ctx['up_4pct'] == 1                    # 1 of 70 -> the Stockbee reading


def test_young_stockbee_column_has_no_percentile():
    n = 70
    sb = np.full(n, np.nan)
    sb[-10:] = np.arange(10)                      # only 10 sessions of Stockbee data
    ctx = bs.percentile_context(_frame(n, np.arange(n, dtype=float), sb))
    assert 'up_4pct' not in ctx                   # blank, never the old column
    assert 't2108' in ctx                         # non-Stockbee keys unaffected


def test_sixty_sessions_is_the_floor():
    for n, present in ((59, False), (60, True)):
        ctx = bs.percentile_context(_frame(n, np.zeros(n), np.arange(n, dtype=float)))
        assert ('up_4pct' in ctx) is present, n


def test_conditions_read_stockbee_columns_and_no_condition_is_called_thrust():
    assert 'thrust' not in bs._CONDITION_SPREADS and 'thrust' not in bs._CONDITION_NEUTRAL
    assert bs._CONDITION_SPREADS['net_4pct'] == ('up_4pct_stockbee', 'down_4pct_stockbee')
    f = pd.DataFrame({'ratio_5d': [3.0], 'ratio_5d_stockbee': [0.4],
                      'up_4pct': [500], 'down_4pct': [10],
                      'up_4pct_stockbee': [10], 'down_4pct_stockbee': [500],
                      'new_highs': [90], 'new_lows': [1],
                      'new_highs_common': [1], 'new_lows_common': [90]})
    m = bs._condition_frame(f)
    assert m['ratio_5d'].iloc[0] == 0.4
    assert m['net_4pct'].iloc[0] == -490
    assert m['nh_nl'].iloc[0] == -89


def test_condition_missing_before_its_column_lands_is_unmeasured():
    f = pd.DataFrame({'date': ['2026-09-01', '2026-09-02'],
                      'up_4pct': [500, 500], 'down_4pct': [10, 10],
                      'up_4pct_stockbee': [np.nan, 10], 'down_4pct_stockbee': [np.nan, 500]})
    m = bs._condition_frame(f)
    assert pd.isna(m['net_4pct'].iloc[0])        # not back-filled from the old count


def _bars(chg_today, vol_today, n=80, base_vol=1_000_000.0):
    close = [100.0] * (n - 1) + [100.0 * (1 + chg_today)]
    vol = [base_vol] * (n - 1) + [vol_today]
    idx = pd.bdate_range('2026-01-02', periods=n)
    return pd.DataFrame({'Open': close, 'Close': close, 'Volume': vol}, index=idx)


def _kinds_today(hist):
    marks = marks_from_bars(hist, None)
    last = str(hist.index[-1].date())
    return next((m['kinds'] for m in marks if m['d'] == last), [])


def test_ep_mark_is_the_stockbee_scan():
    # +5% on 3.5x the prior 50-day average: Stockbee EP; the old +10% recipe said no
    assert 'EP' in _kinds_today(_bars(0.05, 3_500_000))
    # +12% on 3.5x but under his 300,000 floor: not EP (the old recipe said yes)
    assert 'EP' not in _kinds_today(_bars(0.12, 280_000, base_vol=80_000))
    # exactly 3x is not "> 3x"
    assert 'EP' not in _kinds_today(_bars(0.05, 3_000_000))
