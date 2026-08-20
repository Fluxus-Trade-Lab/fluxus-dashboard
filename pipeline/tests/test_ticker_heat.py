"""Tests for heat scoring — which tickers are stacking signals."""
import pandas as pd
import pytest

from pipeline.screeners.ticker_events import EVENT_COLUMNS


def _ev(date, ticker, screener, **kw):
    row = {c: None for c in EVENT_COLUMNS}
    row.update({'date': date, 'ticker': ticker, 'screener': screener, 'group': ''})
    row.update(kw)
    return row


def _frame(rows):
    return pd.DataFrame(rows, columns=EVENT_COLUMNS)


class TestComputeHeat:
    def test_distinct_screeners_beat_repeats(self):
        """A 5x gainers_4pct name must rank below vcp + episodic_pivot."""
        from pipeline.screeners.ticker_heat import compute_heat
        rows = [_ev(f'2026-05-{d:02d}', 'NOISY', 'gainers_4pct') for d in range(1, 6)]
        rows += [_ev('2026-05-04', 'QUIET', 'vcp'),
                 _ev('2026-05-05', 'QUIET', 'episodic_pivot')]
        heat = compute_heat(_frame(rows), '2026-05-05')
        assert [h['ticker'] for h in heat] == ['QUIET', 'NOISY']
        quiet = heat[0]
        assert quiet['score'] == pytest.approx(6.0)      # 3 + 3, no repeats
        noisy = heat[1]
        assert noisy['score'] == pytest.approx(1.5)   # 1 * min(1+.25*4, 1.5) = 1.5 (cap)

    def test_score_shape_and_fields(self):
        from pipeline.screeners.ticker_heat import compute_heat
        rows = [_ev('2026-05-01', 'ABC', 'vcp', sector='Technology'),
                _ev('2026-05-03', 'ABC', 'gainers_4pct', sector='Technology'),
                _ev('2026-05-05', 'ABC', 'vcp', sector=None)]
        heat = compute_heat(_frame(rows), '2026-05-05')
        assert len(heat) == 1
        h = heat[0]
        assert set(h) == {'ticker', 'score', 'screeners', 'first_seen',
                          'last_seen', 'days_span', 'sector', 'confluence_days'}
        assert h['first_seen'] == '2026-05-01' and h['last_seen'] == '2026-05-05'
        assert h['days_span'] == 3          # 3 distinct archive dates in range
        assert h['sector'] == 'Technology'  # most recent non-null
        names = {s['name']: s for s in h['screeners']}
        assert names['vcp']['hits'] == 2 and names['vcp']['last_date'] == '2026-05-05'
        # vcp: 3*(1+.25*1)=3.75, gainers_4pct: 1 -> 4.75
        assert h['score'] == pytest.approx(4.75)

    def test_no_peek_ignores_rows_after_as_of(self):
        from pipeline.screeners.ticker_heat import compute_heat
        rows = [_ev('2026-05-01', 'ABC', 'vcp'),
                _ev('2026-05-09', 'ABC', 'episodic_pivot'),
                _ev('2026-05-09', 'FUTURE', 'vcp')]
        heat = compute_heat(_frame(rows), '2026-05-01')
        assert [h['ticker'] for h in heat] == ['ABC']
        assert heat[0]['score'] == pytest.approx(3.0)

    def test_window_counts_archive_dates_not_calendar_days(self):
        from pipeline.screeners.ticker_heat import compute_heat
        dates = [f'2026-05-{d:02d}' for d in range(1, 21)]   # 20 archive dates
        rows = [_ev(d, 'ABC', 'gainers_4pct') for d in dates]
        rows.append(_ev(dates[0], 'OLD', 'vcp'))             # falls out of a 15-window
        heat = compute_heat(_frame(rows), dates[-1], window=15)
        assert [h['ticker'] for h in heat] == ['ABC']

    def test_unknown_screener_ignored(self):
        from pipeline.screeners.ticker_heat import compute_heat
        heat = compute_heat(_frame([_ev('2026-05-01', 'ABC', 'not_a_screener')]),
                            '2026-05-01')
        assert heat == []

    def test_empty_inputs(self):
        from pipeline.screeners.ticker_heat import compute_heat
        assert compute_heat(_frame([]), '2026-05-01') == []
        assert compute_heat(_frame([_ev('2026-05-01', 'ABC', 'vcp')]), '2020-01-01') == []

    def test_ties_break_on_ticker(self):
        from pipeline.screeners.ticker_heat import compute_heat
        rows = [_ev('2026-05-01', 'BBB', 'vcp'), _ev('2026-05-01', 'AAA', 'vcp')]
        heat = compute_heat(_frame(rows), '2026-05-01')
        assert [h['ticker'] for h in heat] == ['AAA', 'BBB']

    def test_repeat_cap_binds_at_15_hits(self):
        """15 hits on one screener caps out at weight*1.5, not weight*4.5."""
        from pipeline.screeners.ticker_heat import compute_heat
        dates = [f'2026-05-{d:02d}' for d in range(1, 16)]   # 15 archive dates
        rows = [_ev(d, 'SPAM', 'momentum_97') for d in dates]
        heat = compute_heat(_frame(rows), dates[-1], window=15)
        assert len(heat) == 1
        assert heat[0]['score'] == pytest.approx(3 * 1.5)   # weight=3, cap=1.5 -> 4.5

    def test_repeat_cap_binds_exactly_at_3_hits(self):
        """3 hits: 1+.25*2 = 1.5 lands exactly on the cap, no further reduction."""
        from pipeline.screeners.ticker_heat import compute_heat
        rows = [_ev(f'2026-05-0{d}', 'ABC', 'gainers_4pct') for d in (1, 2, 3)]
        heat = compute_heat(_frame(rows), '2026-05-03')
        assert heat[0]['score'] == pytest.approx(1 * 1.5)

    def test_repeat_below_cap_unchanged(self):
        """2 hits: 1+.25*1 = 1.25 is below the cap, unaffected by it."""
        from pipeline.screeners.ticker_heat import compute_heat
        rows = [_ev(f'2026-05-0{d}', 'ABC', 'gainers_4pct') for d in (1, 2)]
        heat = compute_heat(_frame(rows), '2026-05-02')
        assert heat[0]['score'] == pytest.approx(1 * 1.25)

    def test_single_screener_repeat_ranks_below_multi_screener_confluence(self):
        """A single-screener name hit 15x (capped at 3*1.5=4.5) must rank below
        a name with two distinct quality screeners hit once each (3+3=6.0) —
        confluence beats repeat noise even under the cap."""
        from pipeline.screeners.ticker_heat import compute_heat
        dates = [f'2026-05-{d:02d}' for d in range(1, 16)]
        rows = [_ev(d, 'SPAM', 'momentum_97') for d in dates]
        rows += [_ev('2026-05-14', 'CONFLUENCE', 'vcp'),
                 _ev('2026-05-15', 'CONFLUENCE', 'episodic_pivot')]
        heat = compute_heat(_frame(rows), dates[-1], window=15)
        assert [h['ticker'] for h in heat] == ['CONFLUENCE', 'SPAM']
        assert heat[0]['score'] == pytest.approx(6.0)
        assert heat[1]['score'] == pytest.approx(4.5)

    def test_weights_single_source(self):
        from pipeline.screeners.ticker_heat import WEIGHTS
        assert WEIGHTS['vcp'] == 3 and WEIGHTS['episodic_pivot'] == 3
        assert WEIGHTS['momentum_97'] == 3 and WEIGHTS['gainers_4pct'] == 1
        assert len(WEIGHTS) == 7


class TestBuilders:
    def test_heating_up_caps_and_orders(self):
        from pipeline.screeners.ticker_heat import build_heating_up, HEATING_UP_LIMIT
        rows = []
        for i in range(60):
            rows.append(_ev('2026-05-01', f'T{i:03d}', 'vcp'))
            if i < 10:                      # ten names get a second screener
                rows.append(_ev('2026-05-02', f'T{i:03d}', 'episodic_pivot'))
        out = build_heating_up(_frame(rows), '2026-05-02')
        assert out['as_of'] == '2026-05-02'
        assert len(out['rows']) == HEATING_UP_LIMIT
        assert [r['ticker'] for r in out['rows'][:3]] == ['T000', 'T001', 'T002']
        assert out['rows'][0]['score'] > out['rows'][-1]['score']

    def test_index_groups_by_ticker_newest_first(self):
        from pipeline.screeners.ticker_heat import build_ticker_events_index
        rows = [_ev('2026-05-01', 'ABC', 'vcp', num_contractions=3),
                _ev('2026-05-05', 'ABC', 'gainers_4pct', change_pct=0.06),
                _ev('2026-05-05', 'XYZ', 'vcp')]
        out = build_ticker_events_index(_frame(rows), '2026-05-05')
        assert set(out['events']) == {'ABC', 'XYZ'}
        abc = out['events']['ABC']
        assert [e['date'] for e in abc] == ['2026-05-05', '2026-05-01']
        assert abc[0]['screener'] == 'gainers_4pct'
        assert abc[0]['change_pct'] == 0.06
        assert abc[1]['num_contractions'] == 3
        assert 'ticker' not in abc[0]     # implied by the key

    def test_index_excludes_future_and_old_rows(self):
        from pipeline.screeners.ticker_heat import build_ticker_events_index
        rows = [_ev('2025-01-05', 'OLD', 'vcp'),
                _ev('2026-05-01', 'ABC', 'vcp'),
                _ev('2026-06-01', 'FUTURE', 'vcp')]
        out = build_ticker_events_index(_frame(rows), '2026-05-05', months=6)
        assert set(out['events']) == {'ABC'}

    def test_index_is_json_safe(self):
        import json
        import numpy as np
        from pipeline.screeners.ticker_heat import build_ticker_events_index
        rows = [_ev('2026-05-01', 'ABC', 'vcp', change_pct=np.nan)]
        out = build_ticker_events_index(_frame(rows), '2026-05-01')
        assert 'change_pct' not in out['events']['ABC'][0]   # None-valued keys omitted
        json.dumps(out)

    def test_index_omits_none_keys_retains_present(self):
        from pipeline.screeners.ticker_heat import build_ticker_events_index
        rows = [_ev('2026-05-01', 'ABC', 'vcp', change_pct=0.05, num_contractions=None,
                    rel_volume=None)]
        out = build_ticker_events_index(_frame(rows), '2026-05-01')
        entry = out['events']['ABC'][0]
        assert entry['date'] == '2026-05-01'
        assert entry['screener'] == 'vcp'
        assert entry['change_pct'] == 0.05
        assert 'num_contractions' not in entry
        assert 'rel_volume' not in entry


from pipeline.screeners.ticker_heat import compute_heat


class TestSameDayConfluence:
    """MRNA 2026-08-19: four screeners on one day scored 9.0 vs a 9.5 cutoff."""

    def test_three_plus_distinct_on_one_day_earn_the_bonus(self):
        rows = [_ev('2026-05-05', 'BOMB', s) for s in
                ('episodic_pivot', 'momentum_97', 'gainers_4pct', 'vol_up_gainers')]
        rows += [_ev('2026-05-05', 'DUO', s) for s in ('episodic_pivot', 'gainers_4pct', 'vcp')]
        heat = compute_heat(_frame(rows), '2026-05-05')
        by = {h['ticker']: h for h in heat}
        assert by['BOMB']['score'] == pytest.approx(3 + 3 + 1 + 1 + 2.0)   # weights + bonus
        assert by['BOMB']['confluence_days'] == 1
        # three distinct is a normal strong day (23.5/day on the archive), no bonus
        assert by['DUO']['score'] == pytest.approx(7.0) and by['DUO']['confluence_days'] == 0

    def test_bonus_is_per_qualifying_day(self):
        rows = [_ev(d, 'TWICE', s) for d in ('2026-05-04', '2026-05-05')
                for s in ('episodic_pivot', 'momentum_97', 'vcp', 'gainers_4pct')]
        heat = compute_heat(_frame(rows), '2026-05-05')
        h = heat[0]
        assert h['confluence_days'] == 2
