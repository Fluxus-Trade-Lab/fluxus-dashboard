"""The board's thrust row is the engine's thrust, not a second copy of the rule.

2026-09-18: breadth_signals moved thrust to Stockbee's own definition
(05319404, back-to-back 300+ on the three-leg count); state_board.py kept the
single-day price-only rule and was caught by the provenance audit the same day.
"""
import pandas as pd
import pytest

from pipeline.screeners.state_board import state_board


def _frame(prev, today, price_only=(900, 10)):
    base = dict(up_25pct_qtr=400, down_25pct_qtr=300, pct_above_20sma=55.0,
                pct_above_200sma=55.0, t2108=50.0, new_highs=30, new_lows=10,
                up_4pct=price_only[0], down_4pct=price_only[1])
    rows = [dict(base, date='2026-09-16', up_4pct_stockbee=prev[0], down_4pct_stockbee=prev[1]),
            dict(base, date='2026-09-17', up_4pct_stockbee=today[0], down_4pct_stockbee=today[1])]
    return pd.DataFrame(rows)


def _thrust(frame):
    return next(r for r in state_board(frame) if r['key'] == 'thrust')


@pytest.mark.parametrize("prev,today,level", [
    ((310, 40), (420, 30), 4),     # back-to-back up
    ((40, 330), (30, 305), 0),     # back-to-back down
    ((159, 246), (384, 88), 2),    # 09-17: one 300 day is not a thrust
    ((320, 310), (400, 380), 2),   # churn
])
def test_board_thrust_row_follows_the_engine(prev, today, level):
    assert _thrust(_frame(prev, today))['level'] == level


def test_price_only_count_cannot_light_the_row():
    """up_4pct 900 (price leg only) with a quiet Stockbee count stays neutral."""
    assert _thrust(_frame((100, 20), (120, 10), price_only=(900, 10)))['level'] == 2


def test_rows_without_stockbee_columns_are_unavailable():
    f = _frame((0, 0), (0, 0)).drop(columns=['up_4pct_stockbee', 'down_4pct_stockbee'])
    assert _thrust(f)['level'] is None
