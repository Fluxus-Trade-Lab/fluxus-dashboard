"""Tests for the Heating Up ticker-source merge in run_tickers.py (pure functions only —
no network calls, no fetching)."""
import json

import pytest


def _write(tmp_path, name, obj):
    path = tmp_path / name
    path.write_text(json.dumps(obj))
    return path


def _heating_up(tickers):
    """Build a minimal heating_up.json payload, rows pre-sorted by score desc."""
    return {
        'timestamp': '2026-08-07T01:03:54.097123+00:00',
        'as_of': '2026-08-06',
        'rows': [{'ticker': t, 'score': 100 - i} for i, t in enumerate(tickers)],
    }


class TestHeatTickers:
    def test_returns_top_n_in_order(self, tmp_path):
        from pipeline.tickers.run_tickers import heat_tickers
        path = _write(tmp_path, 'heating_up.json', _heating_up(['DDD', 'FTK', 'APPS', 'MU', 'PLTR']))
        assert heat_tickers(path, top_n=3) == ['DDD', 'FTK', 'APPS']

    def test_uppercases(self, tmp_path):
        from pipeline.tickers.run_tickers import heat_tickers
        path = _write(tmp_path, 'heating_up.json', _heating_up(['ddd', 'Ftk']))
        assert heat_tickers(path, top_n=5) == ['DDD', 'FTK']

    def test_dedupes_preserving_first_occurrence(self, tmp_path):
        from pipeline.tickers.run_tickers import heat_tickers
        path = _write(tmp_path, 'heating_up.json', _heating_up(['DDD', 'FTK', 'ddd', 'APPS']))
        assert heat_tickers(path, top_n=10) == ['DDD', 'FTK', 'APPS']

    def test_top_n_zero_returns_empty(self, tmp_path):
        from pipeline.tickers.run_tickers import heat_tickers
        path = _write(tmp_path, 'heating_up.json', _heating_up(['DDD', 'FTK']))
        assert heat_tickers(path, top_n=0) == []

    def test_top_n_larger_than_rows_returns_everything(self, tmp_path):
        from pipeline.tickers.run_tickers import heat_tickers
        path = _write(tmp_path, 'heating_up.json', _heating_up(['DDD', 'FTK']))
        assert heat_tickers(path, top_n=50) == ['DDD', 'FTK']

    def test_missing_file_returns_empty(self, tmp_path):
        from pipeline.tickers.run_tickers import heat_tickers
        assert heat_tickers(tmp_path / 'nope.json', top_n=25) == []

    def test_malformed_json_returns_empty(self, tmp_path):
        from pipeline.tickers.run_tickers import heat_tickers
        path = tmp_path / 'bad.json'
        path.write_text('{not valid json')
        assert heat_tickers(path, top_n=25) == []

    def test_empty_object_no_rows_returns_empty(self, tmp_path):
        from pipeline.tickers.run_tickers import heat_tickers
        path = _write(tmp_path, 'heating_up.json', {})
        assert heat_tickers(path, top_n=25) == []

    def test_row_missing_ticker_is_skipped(self, tmp_path):
        from pipeline.tickers.run_tickers import heat_tickers
        obj = {
            'timestamp': 't', 'as_of': 'd',
            'rows': [{'score': 10}, {'ticker': 'APPS', 'score': 9}],
        }
        path = _write(tmp_path, 'heating_up.json', obj)
        assert heat_tickers(path, top_n=25) == ['APPS']

    def test_rows_not_a_list_returns_empty(self, tmp_path):
        from pipeline.tickers.run_tickers import heat_tickers
        path = _write(tmp_path, 'heating_up.json', {'rows': 'nope'})
        assert heat_tickers(path, top_n=25) == []

    def test_row_not_a_dict_is_skipped(self, tmp_path):
        from pipeline.tickers.run_tickers import heat_tickers
        obj = {'rows': ['APPS', {'ticker': 'MU'}]}
        path = _write(tmp_path, 'heating_up.json', obj)
        assert heat_tickers(path, top_n=25) == ['MU']

    def test_ticker_none_is_skipped(self, tmp_path):
        from pipeline.tickers.run_tickers import heat_tickers
        obj = {'rows': [{'ticker': None}, {'ticker': 'MU'}]}
        path = _write(tmp_path, 'heating_up.json', obj)
        assert heat_tickers(path, top_n=25) == ['MU']


class TestMergeTickerSources:
    def test_portfolio_first_then_heat_only(self):
        from pipeline.tickers.run_tickers import merge_ticker_sources
        merged = merge_ticker_sources(['AAOI', 'MU'], ['MU', 'APPS', 'PLTR'])
        assert merged == ['AAOI', 'MU', 'APPS', 'PLTR']

    def test_case_insensitive_dedupe(self):
        from pipeline.tickers.run_tickers import merge_ticker_sources
        merged = merge_ticker_sources(['AAOI'], ['aaoi', 'APPS'])
        assert merged == ['AAOI', 'APPS']

    def test_empty_heat_returns_portfolio_unchanged(self):
        from pipeline.tickers.run_tickers import merge_ticker_sources
        assert merge_ticker_sources(['AAOI', 'MU'], []) == ['AAOI', 'MU']

    def test_empty_portfolio_returns_heat(self):
        from pipeline.tickers.run_tickers import merge_ticker_sources
        assert merge_ticker_sources([], ['APPS', 'MU']) == ['APPS', 'MU']
