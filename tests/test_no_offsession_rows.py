"""Guardrail: no history row may be written on a non-trading day.

Companion to test_no_naive_clock.py. That test stops the *host* clock from
mis-stamping a trading date; this one stops a correct ET date that simply is
not a session from being written at all.

The bug it locks down: on 2026-08-08, a Saturday, the pipeline wrote a full
breadth row with up_4pct=0, down_4pct=0, advances=0, declines=0. Nothing had
moved because nothing was open — Finviz serves the universe with no change data
outside a session — but the row is indistinguishable from a real day of dead
flat tape, and every downstream reader (state board, poster measurement line,
5-day ratio) took it at face value. `market_today()` was working correctly; it
returns the ET *calendar* date, and Saturday is a perfectly good calendar date.

A missing session is honest. A zeroed one is not.
"""
import datetime as dt
from pathlib import Path

import pandas as pd
import pytest

SATURDAY = dt.date(2026, 8, 8)
SUNDAY = dt.date(2026, 8, 9)
JULY_FOURTH = dt.date(2026, 7, 3)   # Independence Day observed (Sat 7/4 -> Fri 7/3)
FRIDAY = dt.date(2026, 8, 7)


def _universe(n=3000):
    """A universe healthy enough to clear every guard except the calendar."""
    return pd.DataFrame({
        'ticker': [f'T{i}' for i in range(n)],
        'change_pct': [0.01] * n,
        'perf_1m': [0.05] * n,
        'perf_3m': [0.05] * n,
        'sma20_dist': [0.01] * n,
        'sma40_dist': [0.01] * n,
        'sma50_dist': [0.01] * n,
        'sma200_dist': [0.01] * n,
        'high_52w': [-0.10] * n,
        'low_52w': [0.50] * n,
    })


def _archive(tmp_path):
    return str(tmp_path / 'breadth_archive.csv')


@pytest.mark.parametrize('day,label', [
    (SATURDAY, 'Saturday'),
    (SUNDAY, 'Sunday'),
    (JULY_FOURTH, 'Independence Day (observed)'),
])
def test_breadth_writes_no_row_off_session(tmp_path, day, label):
    from pipeline.screeners.breadth_metrics import run

    path = _archive(tmp_path)
    result = run(_universe(), path, spx_close=7700.0, today=day)

    assert not Path(path).exists(), (
        f"{label} {day.isoformat()} wrote a breadth archive row"
    )
    assert result['data_quality']['stale'] is True
    assert result['data_quality']['reason'] == 'not a trading session'


def test_breadth_off_session_serves_the_last_real_session(tmp_path):
    """Not a zeroed row: the last measured session, flagged stale."""
    from pipeline.screeners.breadth_metrics import run

    path = _archive(tmp_path)
    friday = run(_universe(), path, spx_close=7700.0, today=FRIDAY)
    assert friday['data_quality'] == {'stale': False}
    assert friday['breadth']['advances'] == 3000

    saturday = run(_universe(0), path, spx_close=None, today=SATURDAY)

    archive = pd.read_csv(path, dtype={'date': str})
    assert list(archive['date']) == [FRIDAY.isoformat()]        # untouched
    assert saturday['data_quality']['as_of'] == FRIDAY.isoformat()
    # The numbers on screen are Friday's, not Saturday's zeros.
    assert saturday['breadth']['advances'] == 3000
    assert saturday['history']['dates'] == [FRIDAY.isoformat()]


def test_stockbee_history_writes_no_entry_off_session(tmp_path):
    """The second write path into data/history/ has the same calendar bug."""
    from pipeline.screeners.stockbee_ratio import run

    path = str(tmp_path / 'breadth_history.json')
    run(_universe(100), path, today=FRIDAY)
    before = pd.read_json(path).to_dict(orient='records')

    out = run(_universe(100), path, today=SATURDAY)

    assert pd.read_json(path).to_dict(orient='records') == before
    assert out['stale'] is True
    assert out['stale_reason'] == 'not a trading session'
    assert out['as_of'] == FRIDAY.isoformat()


def test_archive_on_disk_contains_only_trading_days():
    """The committed archive itself — the artifact the bad row landed in."""
    from pipeline.marketcal import is_trading_day

    repo = Path(__file__).resolve().parent.parent
    archive = repo / 'data' / 'history' / 'breadth_archive.csv'
    if not archive.exists():
        pytest.skip('no breadth archive checked out')

    dates = pd.read_csv(archive, dtype={'date': str})['date']
    offenders = [
        f"{d} ({dt.date.fromisoformat(d).strftime('%A')})"
        for d in dates
        if not is_trading_day(dt.date.fromisoformat(d))
    ]
    assert not offenders, (
        'breadth_archive.csv has rows on non-trading days — their zero counts '
        'read as a flat tape:\n  ' + '\n  '.join(offenders)
    )
