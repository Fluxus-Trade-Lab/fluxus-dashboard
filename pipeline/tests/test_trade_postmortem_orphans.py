"""Orphan post-mortem files -- Visual Vera, DATA_CONTRACTS §七 2026-09-13.

A trade id embeds its entry date. Correcting the date in the Sheet wrote a new
file and left the old one; the index globs the directory, so the stale twin was
counted again (closed +4, a phantom HOOD open row on 2026-09-12).
"""
import json
from datetime import date
from types import SimpleNamespace

import pandas as pd
import pytest

from pipeline.portfolio import trade_postmortem as tp


def _trade(ticker, d):
    return SimpleNamespace(ticker=ticker, entry_date=d, direction='long')


def _touch(dirpath, stem):
    (dirpath / f'{stem}.json').write_text('{}')


@pytest.fixture
def stub(monkeypatch):
    """Make every trade 'succeed' without OHLC maths -- these tests are about
    which files exist afterwards, not what is in them."""
    df = pd.DataFrame({'close': [1.0]}, index=[date(2020, 1, 1)])
    monkeypatch.setattr(tp, '_load_ohlc_df', lambda t: df)
    for name in ('_compute_entry_snapshot', '_compute_path_analytics'):
        monkeypatch.setattr(tp, name, lambda *a: {})
    for name in ('_classify_setup', '_classify_lesson', '_generate_narrative'):
        monkeypatch.setattr(tp, name, lambda *a: 'x')
    monkeypatch.setattr(tp, '_trade_to_dict', lambda t: {'ticker': t.ticker})
    monkeypatch.setattr(tp, '_slice_ohlc', lambda *a: [])


def test_a_corrected_entry_date_removes_the_old_file(tmp_path, stub):
    """The 09-12 shape: 08-18 file left beside the 08-19 correction."""
    _touch(tmp_path, 'HOOD_2026-08-18_000')
    _touch(tmp_path, 'HOOD_2026-08-18_001')
    s = tp.generate_postmortems([_trade('HOOD', date(2026, 8, 19)),
                                 _trade('HOOD', date(2026, 8, 19))], tmp_path)
    assert sorted(p.stem for p in tmp_path.glob('*.json')) == \
        ['HOOD_2026-08-19_000', 'HOOD_2026-08-19_001']
    assert s['removed'] == ['HOOD_2026-08-18_000', 'HOOD_2026-08-18_001']


def test_a_real_same_day_trade_without_a_twin_is_kept(tmp_path, stub):
    """NOW 08-18 has no 08-19 twin -- it is a real trade and must survive."""
    s = tp.generate_postmortems([_trade('NOW', date(2026, 8, 18)),
                                 _trade('SOFI', date(2026, 8, 19))], tmp_path)
    _touch(tmp_path, 'SOFI_2026-08-18_000')
    s = tp.generate_postmortems([_trade('NOW', date(2026, 8, 18)),
                                 _trade('SOFI', date(2026, 8, 19))], tmp_path)
    assert {p.stem for p in tmp_path.glob('*.json')} == \
        {'NOW_2026-08-18_000', 'SOFI_2026-08-19_000'}
    assert s['removed'] == ['SOFI_2026-08-18_000']


def test_a_skipped_trade_keeps_the_file_an_earlier_run_wrote(tmp_path, monkeypatch):
    """No OHLC today is not 'the trade is gone'. Deleting on skip would erase
    old post-mortems whenever the price window moves past them."""
    monkeypatch.setattr(tp, '_load_ohlc_df', lambda t: None)
    _touch(tmp_path, 'OLD_2025-01-02_000')
    s = tp.generate_postmortems([_trade('OLD', date(2025, 1, 2))], tmp_path)
    assert (tmp_path / 'OLD_2025-01-02_000.json').exists()
    assert s['removed'] == [] and len(s['skipped']) == 1


def test_an_empty_book_deletes_nothing(tmp_path, stub):
    """A Sheet that comes back empty must not wipe the journal."""
    _touch(tmp_path, 'HOOD_2026-08-19_000')
    s = tp.generate_postmortems([], tmp_path)
    assert (tmp_path / 'HOOD_2026-08-19_000.json').exists()
    assert s['removed'] == []


def test_the_index_is_never_treated_as_an_orphan_and_counts_only_live_files(tmp_path, stub):
    _touch(tmp_path, 'MRNA_2026-08-18_000')
    (tmp_path / '_index.json').write_text('{"trades": []}')
    tp.generate_postmortems([_trade('MRNA', date(2026, 8, 19))], tmp_path)
    assert (tmp_path / '_index.json').exists()
    live = tmp_path / 'MRNA_2026-08-19_000.json'
    rec = json.loads(live.read_text())
    rec.update({'trade': {'ticker': 'MRNA', 'direction': 'long', 'entry_date': '2026-08-19',
                          'closed': True}, 'path_analytics': {}, 'setup_type': 'x', 'lesson': 'x'})
    live.write_text(json.dumps(rec))
    tp._build_index(tmp_path)
    ids = [r['trade_id'] for r in json.loads((tmp_path / '_index.json').read_text())['trades']]
    assert ids == ['MRNA_2026-08-19_000']
