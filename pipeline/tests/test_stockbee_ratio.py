"""Tests for the stockbee_ratio screener."""
import json
from datetime import date

import pandas as pd

from pipeline.screeners.stockbee_ratio import run


def _make_universe(gainers: int, losers: int, flat: int = 5) -> pd.DataFrame:
    """Universe with exactly *gainers* names >= +4 % and *losers* <= -4 %."""
    changes = [0.05] * gainers + [-0.05] * losers + [0.001] * flat
    return pd.DataFrame({
        'ticker': [f'STOCK{i}' for i in range(len(changes))],
        'change_pct': changes,
    })


def _seed_history(path, entries) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2), encoding='utf-8')


# 10 sessions: the 5 oldest carry lopsided counts so that any leakage into
# the trailing window would blow the ratio far past its expected value.
_OLD = [
    {'date': f'2026-07-{d:02d}', 'gainers': 1000, 'losers': 1}
    for d in range(1, 6)
]
_RECENT = [
    {'date': f'2026-07-{d:02d}', 'gainers': 10, 'losers': 10}
    for d in range(6, 11)
]
_SEEDED = _OLD + _RECENT


class TestHistoryArchive:
    def test_older_entries_survive_a_new_run(self, tmp_path):
        history_path = tmp_path / 'breadth_history.json'
        _seed_history(history_path, _SEEDED)

        run(_make_universe(3, 2), str(history_path), today=date(2026, 7, 13))

        saved = json.loads(history_path.read_text(encoding='utf-8'))
        assert len(saved) == 11
        assert saved[:10] == _SEEDED
        assert saved[-1] == {'date': '2026-07-13', 'gainers': 3, 'losers': 2}

    def test_ratio_uses_only_trailing_five_sessions(self, tmp_path):
        history_path = tmp_path / 'breadth_history.json'
        _seed_history(history_path, _SEEDED)

        result = run(_make_universe(3, 2), str(history_path), today=date(2026, 7, 13))

        # Trailing 5 = the 4 most recent seeded sessions (10/10 each) + today.
        assert result['gainers_5d'] == 4 * 10 + 3
        assert result['losers_5d'] == 4 * 10 + 2
        assert result['ratio_5d'] == round(43 / 42, 4)
        assert result['signal'] == 'NEUTRAL'

    def test_same_date_rerun_replaces_instead_of_duplicating(self, tmp_path):
        history_path = tmp_path / 'breadth_history.json'
        _seed_history(history_path, _SEEDED)

        run(_make_universe(3, 2), str(history_path), today=date(2026, 7, 13))
        result = run(_make_universe(7, 1), str(history_path), today=date(2026, 7, 13))

        saved = json.loads(history_path.read_text(encoding='utf-8'))
        assert len(saved) == 11
        assert saved[-1] == {'date': '2026-07-13', 'gainers': 7, 'losers': 1}
        # Today counted once, not twice.
        assert result['gainers_5d'] == 4 * 10 + 7
        assert result['losers_5d'] == 4 * 10 + 1

    def test_archive_caps_at_30_entries(self, tmp_path):
        history_path = tmp_path / 'breadth_history.json'
        seeded = [
            {'date': f'2026-06-{d:02d}', 'gainers': 10, 'losers': 10}
            for d in range(1, 31)
        ]
        _seed_history(history_path, seeded)

        run(_make_universe(3, 2), str(history_path), today=date(2026, 7, 1))

        saved = json.loads(history_path.read_text(encoding='utf-8'))
        assert len(saved) == 30
        assert saved[0]['date'] == '2026-06-02'
        assert saved[-1]['date'] == '2026-07-01'

    def test_missing_history_file_starts_fresh(self, tmp_path):
        history_path = tmp_path / 'nested' / 'breadth_history.json'

        result = run(_make_universe(6, 2), str(history_path), today=date(2026, 7, 13))

        saved = json.loads(history_path.read_text(encoding='utf-8'))
        assert saved == [{'date': '2026-07-13', 'gainers': 6, 'losers': 2}]
        assert result['gainers_5d'] == 6
        assert result['losers_5d'] == 2
