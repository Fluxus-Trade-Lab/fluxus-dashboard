"""Tests for the sequence-mining CLI's pure pieces."""
import pickle
import random

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


class TestSequenceSeed:
    """One shared seed across all sequences means one baseline sample whose
    error is a common shift. Each sequence needs its own draw."""

    def test_deterministic_for_a_label(self):
        from pipeline.research.mine_sequences import sequence_seed
        assert sequence_seed(42, 'vcp -> momentum_97') == \
            sequence_seed(42, 'vcp -> momentum_97')

    def test_different_labels_differ(self):
        from pipeline.research.mine_sequences import sequence_seed
        assert sequence_seed(42, 'vcp -> momentum_97') != \
            sequence_seed(42, 'vcp -> gainers_4pct')

    def test_different_base_seeds_differ(self):
        from pipeline.research.mine_sequences import sequence_seed
        assert sequence_seed(1, 'vcp -> vcp2') != sequence_seed(2, 'vcp -> vcp2')

    def test_in_range(self):
        from pipeline.research.mine_sequences import sequence_seed
        s = sequence_seed(42, 'a -> b')
        assert isinstance(s, int) and 0 <= s <= 0xFFFFFFFF


class TestAverageBaselines:
    def test_averages_each_statistic(self):
        from pipeline.research.mine_sequences import average_baselines
        draws = [{'median_excess_5': 0.02, 'win_rate_5': 0.5, 'n': 10},
                 {'median_excess_5': 0.04, 'win_rate_5': 0.7, 'n': 10}]
        avg = average_baselines(draws, horizons=(5,))
        assert avg['median_excess_5'] == pytest.approx(0.03)
        assert avg['win_rate_5'] == pytest.approx(0.6)

    def test_reports_the_spread_of_per_draw_medians(self):
        from pipeline.research.mine_sequences import average_baselines
        draws = [{'median_excess_5': 0.00}, {'median_excess_5': 0.02},
                 {'median_excess_5': 0.04}]
        avg = average_baselines(draws, horizons=(5,))
        assert avg['baseline_sd_median_excess_5'] == pytest.approx(0.02)

    def test_skips_none_values(self):
        from pipeline.research.mine_sequences import average_baselines
        draws = [{'median_excess_5': None}, {'median_excess_5': 0.06}]
        avg = average_baselines(draws, horizons=(5,))
        assert avg['median_excess_5'] == pytest.approx(0.06)

    def test_all_none_stays_none(self):
        from pipeline.research.mine_sequences import average_baselines
        avg = average_baselines([{'median_excess_5': None}], horizons=(5,))
        assert avg['median_excess_5'] is None
        assert avg['baseline_sd_median_excess_5'] is None

    def test_single_draw_has_zero_spread(self):
        from pipeline.research.mine_sequences import average_baselines
        avg = average_baselines([{'median_excess_5': 0.03}], horizons=(5,))
        assert avg['baseline_sd_median_excess_5'] == pytest.approx(0.0)

    def test_empty(self):
        from pipeline.research.mine_sequences import average_baselines
        avg = average_baselines([], horizons=(5,))
        assert avg['median_excess_5'] is None


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


_META = {'as_of': '2026-07-30', 'window': 10, 'seed': 42, 'min_n': 20,
         'sessions': 89, 'tickers': 3872, 'coverage_missing': 120,
         'horizons': (5, 10, 21), 'baseline_draws': 20, 'hypotheses': 49,
         'candidates': 56, 'powered': 18, 'stable': 12, 'pass_rate': 12 / 18,
         'measurable_last': '2026-06-29', 'measurable_total': 76,
         'first_half_sessions': 45, 'first_half_measurable': 45,
         'second_half_sessions': 44, 'second_half_measurable': 31}

_SURVIVED = '## Survived the guards'


class TestRenderMarkdown:
    def _rows(self):
        return [
            {'sequence': 'vcp -> gainers_4pct', 'n': 40, 'lost': 3,
             'distinct_signal_dates': 25,
             'net_median_excess_10': 0.055, 'baseline_sd_median_excess_10': 0.004,
             'median_mfe_r_10': 3.1, 'net_median_mfe_r_10': 1.1,
             'median_mae_r_10': -1.2, 'net_median_mae_r_10': 0.3,
             'win_rate_10': 0.62, 'net_win_rate_10': 0.12,
             'under_powered': False, 'unstable': False},
            {'sequence': 'ema21_watch -> vcp', 'n': 8, 'lost': 0,
             'distinct_signal_dates': 6,
             'net_median_excess_10': 0.20, 'baseline_sd_median_excess_10': 0.01,
             'median_mfe_r_10': 5.0, 'net_median_mfe_r_10': 3.0,
             'median_mae_r_10': -0.5, 'net_median_mae_r_10': 1.0,
             'win_rate_10': 0.9, 'net_win_rate_10': 0.4,
             'under_powered': True, 'unstable': False},
            {'sequence': 'vcp -> vol_up_gainers', 'n': 35, 'lost': 1,
             'distinct_signal_dates': 20,
             'net_median_excess_10': 0.03, 'baseline_sd_median_excess_10': 0.008,
             'median_mfe_r_10': 2.0, 'net_median_mfe_r_10': 0.2,
             'median_mae_r_10': -1.8, 'net_median_mae_r_10': -0.3,
             'win_rate_10': 0.55, 'net_win_rate_10': 0.05,
             'under_powered': False, 'unstable': True},
            {'sequence': 'momentum_97 -> vcp', 'n': 60, 'lost': 2,
             'distinct_signal_dates': 30,
             'net_median_excess_10': -0.023, 'baseline_sd_median_excess_10': 0.006,
             'median_mfe_r_10': 1.5, 'net_median_mfe_r_10': -0.4,
             'median_mae_r_10': -2.0, 'net_median_mae_r_10': -0.5,
             'win_rate_10': 0.44, 'net_win_rate_10': -0.06,
             'under_powered': False, 'unstable': False},
        ]

    def test_limits_are_stated_first(self):
        from pipeline.research.mine_sequences import render_markdown
        head = render_markdown(self._rows(), _META).split(_SURVIVED)[0]
        assert 'one regime' in head.lower()
        assert 'baseline' in head.lower()
        assert 'survivorship' in head.lower()

    def test_ranked_excludes_flagged_rows(self):
        from pipeline.research.mine_sequences import render_markdown
        md = render_markdown(self._rows(), _META)
        ranked = md.split(_SURVIVED)[1].split('\n## ')[0]
        assert 'vcp -> gainers_4pct' in ranked
        assert 'ema21_watch -> vcp' not in ranked      # under-powered
        assert 'vcp -> vol_up_gainers' not in ranked   # unstable
        # but both still appear somewhere in the report
        assert 'ema21_watch -> vcp' in md and 'vcp -> vol_up_gainers' in md

    def test_states_when_nothing_clears_the_bar(self):
        from pipeline.research.mine_sequences import render_markdown
        rows = [dict(self._rows()[1])]     # only an under-powered row
        md = render_markdown(rows, _META)
        ranked = md.split(_SURVIVED)[1].split('\n## ')[0]
        assert 'No sequence' in ranked

    # ── F3: the preamble's "every number is net" claim must be true ──

    def test_table_prints_net_mfe_mae_and_win_rate(self):
        from pipeline.research.mine_sequences import render_markdown
        md = render_markdown(self._rows(), _META)
        ranked = md.split(_SURVIVED)[1].split('\n## ')[0]
        assert 'net median MFE' in ranked and 'net median MAE' in ranked
        assert 'net win rate' in ranked
        assert '+1.10' in ranked            # net MFE, not the raw 3.1
        assert '+0.30' in ranked            # net MAE, not the raw -1.2
        assert '+12pp' in ranked            # net win rate, not the raw 62%
        assert 'raw 3.10' in ranked         # raw still shown, labelled

    def test_baseline_spread_is_shown(self):
        from pipeline.research.mine_sequences import render_markdown
        ranked = render_markdown(self._rows(), _META).split(_SURVIVED)[1]
        assert 'baseline sd' in ranked

    # ── F6: "cleared the bar" mislabels stable losers ──

    def test_section_does_not_claim_profitability(self):
        from pipeline.research.mine_sequences import render_markdown
        md = render_markdown(self._rows(), _META)
        assert 'NOT a profitability test' in md
        assert 'Positive net edge (1)' in md
        assert 'Negative net edge (1)' in md

    def test_negative_net_edge_row_is_in_the_negative_block(self):
        from pipeline.research.mine_sequences import render_markdown
        md = render_markdown(self._rows(), _META)
        pos = md.split('### Positive net edge')[1].split('### Negative')[0]
        neg = md.split('### Negative net edge')[1].split('\n## ')[0]
        assert 'vcp -> gainers_4pct' in pos and 'momentum_97 -> vcp' not in pos
        assert 'momentum_97 -> vcp' in neg

    # ── F5: recency truncation ──

    def test_limits_disclose_the_unmeasurable_tail_and_asymmetry(self):
        from pipeline.research.mine_sequences import render_markdown
        head = render_markdown(self._rows(), _META).split(_SURVIVED)[0]
        assert '2026-06-29' in head
        assert 'asymmetric' in head.lower()
        assert '45/45' in head and '31/44' in head

    # ── F8: multiplicity and non-independence ──

    def test_limits_state_multiplicity_and_the_observed_pass_rate(self):
        from pipeline.research.mine_sequences import render_markdown
        head = render_markdown(self._rows(), _META).split(_SURVIVED)[0]
        assert '49' in head                       # hypotheses tested
        assert '50%' in head                      # noise expectation
        assert '67%' in head                      # observed pass rate

    def test_limits_explain_non_independence(self):
        from pipeline.research.mine_sequences import render_markdown
        head = render_markdown(self._rows(), _META).split(_SURVIVED)[0]
        assert 'distinct_signal_dates' in head
        assert 'independent' in head.lower()

    def test_table_shows_distinct_signal_dates(self):
        from pipeline.research.mine_sequences import render_markdown
        ranked = render_markdown(self._rows(), _META).split(_SURVIVED)[1]
        assert 'distinct dates' in ranked


class TestMeasurableDates:
    def test_tail_of_the_archive_is_not_measurable(self):
        from pipeline.research.mine_sequences import measurable_dates
        spy = _panel_frame(n=30)
        cal = list(spy.index.strftime('%Y-%m-%d'))
        got = measurable_dates(cal, spy, max_horizon=5)
        # entry is the next bar and 5 forward bars are needed
        assert got[-1] == cal[24]
        assert len(got) == 25

    def test_unknown_dates_are_not_measurable(self):
        from pipeline.research.mine_sequences import measurable_dates
        spy = _panel_frame(n=30)
        assert measurable_dates(['1999-01-04'], spy, max_horizon=5) == []


class TestRankHorizonGuard:
    def test_horizons_without_the_rank_horizon_is_an_error(self):
        from pipeline.research.mine_sequences import main
        with pytest.raises(SystemExit):
            main(['--horizons', '5,21'])


# ── spec §5: the two properties the design promised but never tested ──

def _random_walk(idx, seed, start=100.0):
    rng = random.Random(seed)
    close, closes = start, []
    for _ in range(len(idx)):
        close *= 1 + rng.gauss(0, 0.02)
        closes.append(close)
    return pd.DataFrame(
        {'Open': closes,
         'High': [c * 1.01 for c in closes],
         'Low': [c * 0.99 for c in closes],
         'Close': closes}, index=idx)


class TestBaselineNullProperty:
    """A random-entry baseline measured against ANOTHER random-entry baseline
    must show no edge. If it does, the baseline machinery itself is
    manufacturing one, and every net number in the report is wrong."""

    def test_baseline_versus_baseline_is_approximately_zero(self):
        from pipeline.research.mine_sequences import (
            average_baselines, measure_instances, net_of_baseline)
        from pipeline.research.sequences import random_instances, summarize

        idx = pd.bdate_range(end='2026-06-30', periods=300)
        tickers = [f"T{i:03d}" for i in range(40)]
        panel = {t: _random_walk(idx, seed=1000 + i) for i, t in enumerate(tickers)}
        spy = _random_walk(idx, seed=7, start=500.0)
        panel['SPY'] = spy
        dates = list(idx.strftime('%Y-%m-%d'))[50:-30]
        events = pd.DataFrame([{'date': d, 'ticker': t, 'screener': 'x'}
                               for d in dates for t in tickers])

        cache = {}
        a_inst = random_instances(events, n=400, seed=11)
        a_out, a_lost = measure_instances(a_inst, panel, spy, (10,), cache)
        a = summarize(a_out, horizons=(10,), lost=a_lost)

        draws = []
        for k in range(20):
            b_inst = random_instances(events, n=400, seed=500 + k)
            b_out, b_lost = measure_instances(b_inst, panel, spy, (10,), cache)
            draws.append(summarize(b_out, horizons=(10,), lost=b_lost))
        b = average_baselines(draws, horizons=(10,))

        net = net_of_baseline(a, b, horizons=(10,))
        # Tolerance: 1.5 percentage points of 10-day excess. Daily sigma is 2%,
        # so a 10-day median excess has a sampling spread of roughly 0.3pp at
        # n=400; 1.5pp is ~5x that, loose enough not to flake and tight enough
        # to catch a systematic bias.
        assert abs(net['net_median_excess_10']) < 0.015
        # Win rate should sit at a coin flip, within 6 percentage points.
        assert abs(net['net_win_rate_10']) < 0.06


class TestReproducibility:
    """Same --seed must produce byte-identical rows, or nothing in the report
    can be checked by re-running it."""

    def _fixture(self, tmp_path):
        idx = pd.bdate_range(end='2026-06-30', periods=200)
        tickers = [f"T{i:02d}" for i in range(30)]
        panel = {t: _random_walk(idx, seed=2000 + i) for i, t in enumerate(tickers)}
        panel['SPY'] = _random_walk(idx, seed=3, start=500.0)
        panel_path = tmp_path / 'panel.pkl'
        with open(panel_path, 'wb') as f:
            pickle.dump(panel, f)

        rng = random.Random(0)
        screeners = ['vcp', 'gainers_4pct', 'vol_up_gainers', 'momentum_97']
        dates = list(idx.strftime('%Y-%m-%d'))[60:-30]
        rows = [{'date': d, 'ticker': t, 'screener': s}
                for d in dates for t in tickers for s in screeners
                if rng.random() < 0.3]
        events_path = tmp_path / 'events.csv'
        pd.DataFrame(rows).to_csv(events_path, index=False)
        return events_path, panel_path

    def test_same_seed_gives_identical_output(self, tmp_path, monkeypatch):
        from pipeline.research import mine_sequences

        events_path, panel_path = self._fixture(tmp_path)
        argv = ['--window', '5', '--seed', '42', '--baseline-draws', '3',
                '--events', str(events_path), '--panel', str(panel_path)]

        outs = []
        for run in ('a', 'b'):
            out_dir = tmp_path / run
            monkeypatch.setattr(mine_sequences, '_OUT_DIR', out_dir)
            assert mine_sequences.main(argv) == 0
            csvs = sorted(out_dir.glob('*.csv'))
            assert csvs, "the run produced no CSV"
            outs.append(csvs[0].read_text())
        assert outs[0] == outs[1]

    def test_a_different_seed_changes_the_baseline(self, tmp_path, monkeypatch):
        from pipeline.research import mine_sequences

        events_path, panel_path = self._fixture(tmp_path)
        outs = []
        for run, seed in (('a', '42'), ('b', '43')):
            out_dir = tmp_path / run
            monkeypatch.setattr(mine_sequences, '_OUT_DIR', out_dir)
            assert mine_sequences.main(
                ['--window', '5', '--seed', seed, '--baseline-draws', '3',
                 '--events', str(events_path), '--panel', str(panel_path)]) == 0
            outs.append(sorted(out_dir.glob('*.csv'))[0].read_text())
        assert outs[0] != outs[1]
