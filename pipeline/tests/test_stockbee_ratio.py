"""Tests for the Stockbee 5-day ratio screener's rolling history."""
import json
from datetime import date

import pandas as pd

# A pinned US trading day (Friday) so the test never depends on when it runs.
TODAY = date(2026, 7, 24)


def _universe(gainers: int, losers: int, flat: int = 20) -> pd.DataFrame:
    """Synthetic universe with an exact count of >=4% gainers and <=-4% losers."""
    changes = [0.05] * gainers + [-0.05] * losers + [0.001] * flat
    return pd.DataFrame({
        'ticker': [f'STOCK{i}' for i in range(len(changes))],
        'change_pct': changes,
    })


def _seed(path, entries) -> None:
    path.write_text(json.dumps(entries, indent=2), encoding='utf-8')


def _read(path):
    return json.loads(path.read_text(encoding='utf-8'))


PRIOR = [
    {'date': '2026-07-20', 'gainers': 100, 'losers': 100},
    {'date': '2026-07-21', 'gainers': 100, 'losers': 100},
    {'date': '2026-07-22', 'gainers': 100, 'losers': 100},
    {'date': '2026-07-23', 'gainers': 100, 'losers': 100},
]


class TestSameDayRerun:
    def test_history_keeps_one_entry_per_date(self, tmp_path):
        from pipeline.screeners.stockbee_ratio import run

        path = tmp_path / 'breadth_history.json'
        _seed(path, PRIOR)
        universe = _universe(gainers=200, losers=50)

        run(universe, str(path), today=TODAY)
        run(universe, str(path), today=TODAY)

        dates = [entry['date'] for entry in _read(path)]
        assert dates.count(TODAY.isoformat()) == 1
        assert len(dates) == len(set(dates))

    def test_ratio_is_identical_on_the_second_run(self, tmp_path):
        from pipeline.screeners.stockbee_ratio import run

        path = tmp_path / 'breadth_history.json'
        _seed(path, PRIOR)
        universe = _universe(gainers=200, losers=50)

        first = run(universe, str(path), today=TODAY)
        second = run(universe, str(path), today=TODAY)

        # 4 prior days at 100/100 + today's 200/50 → 600 / 450
        assert first['gainers_5d'] == 600
        assert first['losers_5d'] == 450
        assert second == first

    def test_rerun_does_not_drop_prior_days(self, tmp_path):
        from pipeline.screeners.stockbee_ratio import run

        path = tmp_path / 'breadth_history.json'
        _seed(path, PRIOR)
        universe = _universe(gainers=200, losers=50)

        run(universe, str(path), today=TODAY)
        run(universe, str(path), today=TODAY)

        dates = [entry['date'] for entry in _read(path)]
        assert dates == [e['date'] for e in PRIOR] + [TODAY.isoformat()]


class TestNewDay:
    def test_new_date_is_appended(self, tmp_path):
        from pipeline.screeners.stockbee_ratio import run

        path = tmp_path / 'breadth_history.json'
        _seed(path, PRIOR)

        run(_universe(gainers=200, losers=50), str(path), today=TODAY)
        run(_universe(gainers=10, losers=300), str(path), today=date(2026, 7, 27))

        entries = _read(path)
        assert [e['date'] for e in entries][-2:] == ['2026-07-24', '2026-07-27']
        assert entries[-1] == {'date': '2026-07-27', 'gainers': 10, 'losers': 300}

    def test_window_rolls_off_the_oldest_day(self, tmp_path):
        from pipeline.screeners.stockbee_ratio import run

        path = tmp_path / 'breadth_history.json'
        _seed(path, PRIOR)

        result = run(_universe(gainers=50, losers=50), str(path), today=date(2026, 7, 27))
        # 2026-07-20 falls out of the trailing 5 sessions.
        assert result['gainers_5d'] == 450
        assert result['losers_5d'] == 450


class TestTodayDefault:
    def test_defaults_to_the_current_date(self, tmp_path):
        from pipeline.screeners.stockbee_ratio import run

        path = tmp_path / 'breadth_history.json'
        run(_universe(gainers=10, losers=10), str(path))

        assert _read(path)[-1]['date'] == date.today().isoformat()
