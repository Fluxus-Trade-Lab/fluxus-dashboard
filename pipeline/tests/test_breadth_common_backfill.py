"""T-1003-77：普通股口径新高新低的近似回补落在归档与 replay 里。

回补前非空只有 25 天（2026-08-28 起的 live 值），超卖线与 σ 要满 60 天才出现。
回补后 2024-05-15 起每个交易日都有值；回补行 source 标 backfill，live 值不动。
"""
from pathlib import Path

from pipeline.screeners.breadth_store import load_archive

_REPO = Path(__file__).resolve().parents[2]
_ARCHIVE = _REPO / 'data' / 'history' / 'breadth_archive.csv'


def test_common_new_highs_lows_backfilled_to_replay_start():
    arch = load_archive(str(_ARCHIVE))
    assert arch['date'].min() == '2024-05-15'
    for col in ('new_highs_common', 'new_lows_common'):
        assert arch[col].notna().sum() >= 250, col


def test_backfill_rows_carry_approximate_flag_and_live_values_untouched():
    arch = load_archive(str(_ARCHIVE)).set_index('date')
    assert arch.loc['2024-05-15', 'source'] == 'backfill'
    assert arch.loc['2024-05-15', 'new_highs_common'] == 37
    assert arch.loc['2024-05-15', 'new_lows_common'] == 3
    # 2026-10-02 是 live 行，保留 live 值 7 / 27（不被近似重建覆盖）
    assert arch.loc['2026-10-02', 'source'] == 'live'
    assert arch.loc['2026-10-02', 'new_highs_common'] == 7
    assert arch.loc['2026-10-02', 'new_lows_common'] == 27
