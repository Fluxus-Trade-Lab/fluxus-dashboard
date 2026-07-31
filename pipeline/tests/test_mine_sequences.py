"""Tests for the sequence-mining CLI's pure pieces."""
import pandas as pd
import pytest


def _panel_frame(n=60, start_price=100.0, end='2026-06-30'):
    idx = pd.bdate_range(end=end, periods=n)
    closes = [start_price] * n
    return pd.DataFrame({'Open': closes, 'High': [c + 1 for c in closes],
                         'Low': [c - 1 for c in closes], 'Close': closes}, index=idx)


class TestMeasureInstances:
    def test_counts_missing_ticker_as_lost(self):
        from pipeline.research.mine_sequences import measure_instances
        panel = {'ABC': _panel_frame()}
        spy = _panel_frame()
        date = panel['ABC'].index[30].strftime('%Y-%m-%d')
        instances = [{'ticker': 'ABC', 'signal_date': date},
                     {'ticker': 'GONE', 'signal_date': date}]
        outcomes, lost = measure_instances(instances, panel, spy, horizons=(5,))
        assert len(outcomes) == 1 and lost == 1

    def test_counts_unmeasurable_as_lost(self):
        from pipeline.research.mine_sequences import measure_instances
        panel = {'ABC': _panel_frame()}
        spy = _panel_frame()
        late = panel['ABC'].index[-1].strftime('%Y-%m-%d')   # no forward bars
        outcomes, lost = measure_instances(
            [{'ticker': 'ABC', 'signal_date': late}], panel, spy, horizons=(5,))
        assert outcomes == [] and lost == 1

    def test_empty_input(self):
        from pipeline.research.mine_sequences import measure_instances
        assert measure_instances([], {}, _panel_frame(), horizons=(5,)) == ([], 0)


class TestNetOfBaseline:
    def test_subtracts_matching_keys(self):
        from pipeline.research.mine_sequences import net_of_baseline
        seq = {'median_excess_5': 0.08, 'win_rate_5': 0.6, 'median_mfe_r_5': 3.0,
               'median_mae_r_5': -1.0, 'mean_excess_5': 0.07}
        base = {'median_excess_5': 0.01, 'win_rate_5': 0.5, 'median_mfe_r_5': 2.0,
                'median_mae_r_5': -1.5, 'mean_excess_5': 0.02}
        net = net_of_baseline(seq, base, horizons=(5,))
        assert net['net_median_excess_5'] == pytest.approx(0.07)
        assert net['net_win_rate_5'] == pytest.approx(0.1)
        assert net['net_median_mfe_r_5'] == pytest.approx(1.0)
        assert net['net_median_mae_r_5'] == pytest.approx(0.5)

    def test_none_when_either_side_missing(self):
        from pipeline.research.mine_sequences import net_of_baseline
        net = net_of_baseline({'median_excess_5': 0.08}, {'median_excess_5': None},
                              horizons=(5,))
        assert net['net_median_excess_5'] is None
        net2 = net_of_baseline({}, {'median_excess_5': 0.01}, horizons=(5,))
        assert net2['net_median_excess_5'] is None


class TestRenderMarkdown:
    def _rows(self):
        return [
            {'sequence': 'vcp -> gainers_4pct', 'n': 40, 'lost': 3,
             'net_median_excess_10': 0.055, 'median_mfe_r_10': 3.1,
             'median_mae_r_10': -1.2, 'win_rate_10': 0.62,
             'under_powered': False, 'unstable': False},
            {'sequence': 'ema21_watch -> vcp', 'n': 8, 'lost': 0,
             'net_median_excess_10': 0.20, 'median_mfe_r_10': 5.0,
             'median_mae_r_10': -0.5, 'win_rate_10': 0.9,
             'under_powered': True, 'unstable': False},
            {'sequence': 'vcp -> vol_up_gainers', 'n': 35, 'lost': 1,
             'net_median_excess_10': 0.03, 'median_mfe_r_10': 2.0,
             'median_mae_r_10': -1.8, 'win_rate_10': 0.55,
             'under_powered': False, 'unstable': True},
        ]

    def test_limits_are_stated_first(self):
        from pipeline.research.mine_sequences import render_markdown
        md = render_markdown(self._rows(), {'as_of': '2026-07-30', 'window': 10,
                                            'seed': 42, 'min_n': 20,
                                            'sessions': 89, 'tickers': 3872,
                                            'coverage_missing': 120})
        head = md.split('## Ranked')[0]
        assert 'one regime' in head.lower()
        assert 'baseline' in head.lower()
        assert 'survivorship' in head.lower()

    def test_ranked_excludes_flagged_rows(self):
        from pipeline.research.mine_sequences import render_markdown
        md = render_markdown(self._rows(), {'as_of': '2026-07-30', 'window': 10,
                                            'seed': 42, 'min_n': 20,
                                            'sessions': 89, 'tickers': 3872,
                                            'coverage_missing': 0})
        ranked = md.split('## Ranked')[1].split('##')[0]
        assert 'vcp -> gainers_4pct' in ranked
        assert 'ema21_watch -> vcp' not in ranked      # under-powered
        assert 'vcp -> vol_up_gainers' not in ranked   # unstable
        # but both still appear somewhere in the report
        assert 'ema21_watch -> vcp' in md and 'vcp -> vol_up_gainers' in md

    def test_states_when_nothing_clears_the_bar(self):
        from pipeline.research.mine_sequences import render_markdown
        rows = [dict(self._rows()[1])]     # only an under-powered row
        md = render_markdown(rows, {'as_of': '2026-07-30', 'window': 10,
                                    'seed': 42, 'min_n': 20, 'sessions': 89,
                                    'tickers': 100, 'coverage_missing': 0})
        ranked = md.split('## Ranked')[1].split('##')[0]
        assert 'No sequence' in ranked
