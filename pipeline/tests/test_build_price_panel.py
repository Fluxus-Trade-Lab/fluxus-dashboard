"""Tests for the price panel builder (pure functions only — no network)."""
import pandas as pd


def _events(rows):
    return pd.DataFrame([{'date': d, 'ticker': t, 'screener': 'vcp'}
                         for d, t in rows], columns=['date', 'ticker', 'screener'])


class TestPanelTickers:
    def test_distinct_sorted_plus_spy(self):
        from pipeline.tools.build_price_panel import panel_tickers
        ev = _events([('2026-05-04', 'ZZZ'), ('2026-05-05', 'AAA'),
                      ('2026-05-06', 'ZZZ')])
        assert panel_tickers(ev) == ['AAA', 'SPY', 'ZZZ']

    def test_spy_not_duplicated(self):
        from pipeline.tools.build_price_panel import panel_tickers
        ev = _events([('2026-05-04', 'SPY'), ('2026-05-05', 'AAA')])
        assert panel_tickers(ev) == ['AAA', 'SPY']

    def test_empty_events_still_yields_spy(self):
        from pipeline.tools.build_price_panel import panel_tickers
        assert panel_tickers(_events([])) == ['SPY']


class TestCoverageReport:
    def test_counts_and_missing_list(self):
        from pipeline.tools.build_price_panel import coverage_report
        rep = coverage_report(['AAA', 'BBB', 'CCC', 'SPY'], ['AAA', 'SPY'])
        assert rep['requested'] == 4 and rep['returned'] == 2
        assert rep['missing'] == ['BBB', 'CCC']

    def test_full_coverage(self):
        from pipeline.tools.build_price_panel import coverage_report
        rep = coverage_report(['AAA', 'SPY'], ['SPY', 'AAA'])
        assert rep['missing'] == [] and rep['returned'] == 2
