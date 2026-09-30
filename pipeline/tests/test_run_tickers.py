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

    def test_accepts_a_third_source_after_heat(self):
        from pipeline.tickers.run_tickers import merge_ticker_sources
        merged = merge_ticker_sources(['AAOI'], ['MU'], ['AAOI', 'PLTR'])
        assert merged == ['AAOI', 'MU', 'PLTR']

    def test_no_sources_is_empty(self):
        from pipeline.tickers.run_tickers import merge_ticker_sources
        assert merge_ticker_sources() == []


class TestStoredTickers:
    """The rolling portfolio+heat universe never rewrites a name that leaves it,
    so its bars freeze silently. `--refresh-existing` folds the already-stored
    names back in; these cover the list it builds."""

    def test_lists_existing_ticker_files(self, tmp_path):
        from pipeline.tickers.run_tickers import stored_tickers
        for sym in ('MU', 'AAOI', 'PLTR'):
            (tmp_path / f'{sym}.json').write_text('{}')
        assert stored_tickers(tmp_path) == ['AAOI', 'MU', 'PLTR']

    def test_skips_underscore_prefixed_files(self, tmp_path):
        from pipeline.tickers.run_tickers import stored_tickers
        (tmp_path / 'MU.json').write_text('{}')
        (tmp_path / '_benchmarks.json').write_text('{}')
        assert stored_tickers(tmp_path) == ['MU']

    def test_ignores_non_json(self, tmp_path):
        from pipeline.tickers.run_tickers import stored_tickers
        (tmp_path / 'MU.json').write_text('{}')
        (tmp_path / 'README.md').write_text('x')
        assert stored_tickers(tmp_path) == ['MU']

    def test_missing_dir_returns_empty(self, tmp_path):
        from pipeline.tickers.run_tickers import stored_tickers
        assert stored_tickers(tmp_path / 'nope') == []

    def test_empty_dir_returns_empty(self, tmp_path):
        from pipeline.tickers.run_tickers import stored_tickers
        assert stored_tickers(tmp_path) == []


class TestPortfolioTickersFromSheet:
    """The OHLC store used to be refreshed by hand from a CSV export, so names
    opened after the last export had no OHLC and trade_postmortem skipped them
    (7/355 on 2026-08-16, all current open positions). The portfolio side of
    the fetch set now comes straight from the Sheet the browser writes to."""

    def _trade(self, ticker, closed, qty, exit_days_ago=None):
        from datetime import date, timedelta
        from pipeline.portfolio.trade_parser import Trade, TrimEvent
        from pipeline.marketcal import market_today
        trims = []
        if closed:
            d = market_today() - timedelta(days=exit_days_ago)
            trims = [TrimEvent(date=d, price=10.0, qty=qty or 1, type="sell")]
        return Trade(ticker=ticker, direction="long", sector="Tech", entry_date=date(2026, 1, 5),
                     entry_price=10.0, original_qty=qty or 1, current_qty=qty,
                     stop_price=9.0, initial_stop=9.0, closed=closed, trims=tuple(trims))

    def test_open_positions_and_recent_closes_only(self, monkeypatch):
        from pipeline.tickers import run_tickers as RT
        trades = [self._trade("HPE", False, 100), self._trade("RBRK", False, 50),
                  self._trade("OLD", True, 0, exit_days_ago=200),
                  self._trade("NEW", True, 0, exit_days_ago=10)]
        monkeypatch.setattr(RT, "_sheet_trades", lambda: trades)
        assert RT.relevant_tickers_from_sheet(90) == ["HPE", "NEW", "RBRK"]

    def test_sheet_unavailable_returns_none_not_empty(self, monkeypatch):
        """No credentials / GAS down must not be mistaken for 'no positions':
        the caller falls back to the CSV or skips, it never fetches nothing
        and calls it done."""
        from pipeline.tickers import run_tickers as RT
        from pipeline.portfolio.sheets_source import SheetsUnavailable
        def boom(): raise SheetsUnavailable("no env")
        monkeypatch.setattr(RT, "_sheet_trades", boom)


class TestRunEarningsHistoryEmptySummary:
    """T-1001-04: Yahoo blocking crumb-authenticated endpoints (401) or
    rate-limiting (429) makes earnings_history come back empty for most/all
    of a run WITHOUT raising -- yfinance swallows the HTTP error itself.
    `run()` must count this and warn once the empty share crosses
    EARNINGS_EMPTY_ALERT_SHARE, since nothing else in the log ties the cause
    (vendor 401/429) to the effect (empty fields) for a human or an alert.
    Keyed on earnings_history, not next_earnings: next_earnings now carries
    forward across a bad night (_next_earnings_carry) and can look populated
    even when tonight's live fetch failed, but earnings_history never does
    (_quarterly_carry refuses to carry a section that was empty last night)."""

    def _fake_data(self, sym, earnings_history):
        return {
            'ticker': sym, 'fetched_at': '2026-09-28T23:00:00Z', '_schema': 'v2',
            'current_price': 1.0, 'info': {}, 'earnings_history': earnings_history,
            'next_earnings': {}, 'quarterly_metrics': [], 'analyst': {},
            'quarterly_asof': '2026-09-28T23:00:00Z', 'news': [],
        }

    def test_warns_when_earnings_history_empty_share_crosses_threshold(self, tmp_path, monkeypatch, caplog):
        import logging
        from pipeline.tickers import run_tickers as RT
        tickers = ["AAA", "BBB", "CCC"]
        monkeypatch.setattr(RT, "fetch_ticker_data",
                             lambda sym, prior=None: self._fake_data(sym, []))
        monkeypatch.setattr(RT, "write_ticker_json", lambda sym, data, out: out / f"{sym}.json")
        with caplog.at_level(logging.WARNING, logger="pipeline.tickers.run_tickers"):
            summary = RT.run(tickers, tmp_path, sleep_between=0)
        assert summary['earnings_history_empty'] == ["AAA", "BBB", "CCC"]
        assert any("earnings_history empty" in r.message for r in caplog.records)

    def test_no_warning_under_normal_coverage_gaps(self, tmp_path, monkeypatch, caplog):
        """A handful of names with no reported quarters yet is normal (204/244
        non-empty baseline on a healthy night, 2026-09-18) and must not page
        anyone."""
        import logging
        from pipeline.tickers import run_tickers as RT
        tickers = ["AAA", "BBB", "CCC", "DDD"]
        def fake_fetch(sym, prior=None):
            hist = [] if sym == "AAA" else [{'period_end': '2026-06-30'}]
            return self._fake_data(sym, hist)
        monkeypatch.setattr(RT, "fetch_ticker_data", fake_fetch)
        monkeypatch.setattr(RT, "write_ticker_json", lambda sym, data, out: out / f"{sym}.json")
        with caplog.at_level(logging.WARNING, logger="pipeline.tickers.run_tickers"):
            summary = RT.run(tickers, tmp_path, sleep_between=0)
        assert summary['earnings_history_empty'] == ["AAA"]
        assert not any("earnings_history empty" in r.message for r in caplog.records)
        assert RT.relevant_tickers_from_sheet(90) is None
