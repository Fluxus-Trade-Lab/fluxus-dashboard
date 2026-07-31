"""Tests for the ticker event archive."""
import pytest


class TestExtractEvents:
    def test_flat_tickers_shape(self):
        from pipeline.screeners.ticker_events import extract_events, EVENT_COLUMNS
        payload = {'count': 2, 'tickers': [
            {'ticker': 'ABC', 'change_pct': 0.062, 'volume': 1_200_000,
             'sector': 'Technology', 'atr_ext': 1.4},
            {'ticker': 'XYZ', 'change_pct': 0.041, 'volume': 900_000,
             'sector': 'Energy', 'atr_ext': 0.9},
        ]}
        rows = extract_events('gainers_4pct', payload, '2026-05-04')
        assert len(rows) == 2
        assert set(rows[0]) == set(EVENT_COLUMNS)
        assert rows[0]['date'] == '2026-05-04'
        assert rows[0]['ticker'] == 'ABC'
        assert rows[0]['screener'] == 'gainers_4pct'
        assert rows[0]['group'] == ''
        assert rows[0]['change_pct'] == 0.062
        assert rows[0]['num_contractions'] is None

    def test_results_shape_vcp(self):
        from pipeline.screeners.ticker_events import extract_events
        payload = {'count': 1, 'results': [
            {'ticker': 'DEF', 'num_contractions': 3, 'pct_to_pivot': 0.021,
             'atr_ext': 0.5},
        ]}
        rows = extract_events('vcp', payload, '2026-05-04')
        assert len(rows) == 1
        assert rows[0]['screener'] == 'vcp'
        assert rows[0]['num_contractions'] == 3
        assert rows[0]['pct_to_pivot'] == 0.021
        assert rows[0]['change_pct'] is None

    def test_nested_buckets_carry_group(self):
        from pipeline.screeners.ticker_events import extract_events
        payload = {'count': 3, 'buckets': {
            '100': [{'ticker': 'AAA', 'change_pct': 0.01}],
            '97': [{'ticker': 'BBB'}, {'ticker': 'CCC'}],
        }}
        rows = extract_events('momentum_97', payload, '2026-05-04')
        assert len(rows) == 3
        by_ticker = {r['ticker']: r for r in rows}
        assert by_ticker['AAA']['group'] == '100'
        assert by_ticker['BBB']['group'] == '97'
        assert all(r['screener'] == 'momentum_97' for r in rows)

    def test_nested_rs_groups(self):
        from pipeline.screeners.ticker_events import extract_events
        payload = {'count': 1, 'rs_groups': {'90': [{'ticker': 'GHI'}]}}
        rows = extract_events('ema21_watch', payload, '2026-05-04')
        assert len(rows) == 1 and rows[0]['group'] == '90'

    def test_plain_string_entries_supported(self):
        """Some screeners may store bare symbols rather than dicts."""
        from pipeline.screeners.ticker_events import extract_events
        payload = {'tickers': ['JKL', 'MNO']}
        rows = extract_events('episodic_pivot', payload, '2026-05-04')
        assert [r['ticker'] for r in rows] == ['JKL', 'MNO']
        assert rows[0]['change_pct'] is None

    def test_empty_and_malformed_yield_no_rows(self):
        from pipeline.screeners.ticker_events import extract_events
        assert extract_events('gainers_4pct', {'count': 0, 'tickers': []}, '2026-05-04') == []
        assert extract_events('gainers_4pct', {}, '2026-05-04') == []
        assert extract_events('gainers_4pct', {'tickers': 'not-a-list'}, '2026-05-04') == []
        assert extract_events('vcp', {'results': [{'no_ticker': 1}]}, '2026-05-04') == []
        assert extract_events('unknown_screener', {'tickers': [{'ticker': 'A'}]}, '2026-05-04') == []

    def test_screener_files_covers_all_seven(self):
        from pipeline.screeners.ticker_events import SCREENER_FILES
        assert set(SCREENER_FILES) == {
            'gainers_4pct', 'vol_up_gainers', 'episodic_pivot', 'vcp',
            'momentum_97', 'healthy_charts', 'ema21_watch'}
