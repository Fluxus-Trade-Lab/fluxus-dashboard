"""Tests for the breadth signal engine (Spec 2)."""
import math
import numpy as np
import pandas as pd
import pytest


def _row(**kw):
    base = {
        'ratio_5d': 1.2, 'ratio_10d': 1.1, 'up_4pct': 150, 'down_4pct': 100,
        'up_25pct_qtr': 400, 'down_25pct_qtr': 300,
        'up_13pct_34d': 500, 'down_13pct_34d': 400,
        'mcclellan_osc': 10.0, 'new_highs': 30, 'new_lows': 10,
        'pct_above_200sma': 55.0, 't2108': 50.0,
    }
    base.update(kw)
    return base


class TestBreadthVotes:
    def test_all_keys_present_and_valid(self):
        from pipeline.screeners.breadth_signals import breadth_votes
        votes = breadth_votes(_row())
        assert set(votes) == {'ratio_5d', 'ratio_10d', 'thrust', 'qtr_spread',
                              'spread_13_34', 'mcclellan', 'nh_nl', 'pct200',
                              't2108_zone'}
        assert all(v in ('bull', 'bear', 'neutral') for v in votes.values())

    def test_ratio_boundaries(self):
        from pipeline.screeners.breadth_signals import breadth_votes
        assert breadth_votes(_row(ratio_5d=1.0))['ratio_5d'] == 'bull'
        assert breadth_votes(_row(ratio_5d=0.99))['ratio_5d'] == 'neutral'
        assert breadth_votes(_row(ratio_5d=0.5))['ratio_5d'] == 'neutral'
        assert breadth_votes(_row(ratio_5d=0.49))['ratio_5d'] == 'bear'

    def test_thrust_rules(self):
        from pipeline.screeners.breadth_signals import breadth_votes
        assert breadth_votes(_row(up_4pct=300, down_4pct=50))['thrust'] == 'bull'
        assert breadth_votes(_row(up_4pct=50, down_4pct=300))['thrust'] == 'bear'
        # both >= 300 -> churn, neutral vote
        assert breadth_votes(_row(up_4pct=350, down_4pct=320))['thrust'] == 'neutral'
        assert breadth_votes(_row(up_4pct=299, down_4pct=100))['thrust'] == 'neutral'

    def test_spreads_and_mcclellan_and_nhnl(self):
        from pipeline.screeners.breadth_signals import breadth_votes
        v = breadth_votes(_row(up_25pct_qtr=100, down_25pct_qtr=200,
                               up_13pct_34d=100, down_13pct_34d=200,
                               mcclellan_osc=-5.0, new_highs=3, new_lows=9))
        assert v['qtr_spread'] == 'bear'
        assert v['spread_13_34'] == 'bear'
        assert v['mcclellan'] == 'bear'
        assert v['nh_nl'] == 'bear'
        assert breadth_votes(_row(up_25pct_qtr=200, down_25pct_qtr=200))['qtr_spread'] == 'neutral'

    def test_pct200_zones(self):
        from pipeline.screeners.breadth_signals import breadth_votes
        assert breadth_votes(_row(pct_above_200sma=50.0))['pct200'] == 'bull'
        assert breadth_votes(_row(pct_above_200sma=40.0))['pct200'] == 'neutral'
        assert breadth_votes(_row(pct_above_200sma=29.9))['pct200'] == 'bear'

    def test_t2108_zones(self):
        from pipeline.screeners.breadth_signals import breadth_votes
        assert breadth_votes(_row(t2108=70.0))['t2108_zone'] == 'bull'
        assert breadth_votes(_row(t2108=30.0))['t2108_zone'] == 'bear'
        assert breadth_votes(_row(t2108=50.0))['t2108_zone'] == 'neutral'
        # extremes vote neutral here — overrides handle them at composition
        assert breadth_votes(_row(t2108=10.0))['t2108_zone'] == 'neutral'
        assert breadth_votes(_row(t2108=90.0))['t2108_zone'] == 'neutral'

    def test_nan_and_none_vote_neutral(self):
        from pipeline.screeners.breadth_signals import breadth_votes
        v = breadth_votes(_row(ratio_5d=None, mcclellan_osc=float('nan'),
                               t2108=None, up_4pct=None))
        assert v['ratio_5d'] == 'neutral'
        assert v['mcclellan'] == 'neutral'
        assert v['t2108_zone'] == 'neutral'
        assert v['thrust'] == 'neutral'

    def test_thresholds_single_source(self):
        from pipeline.screeners import breadth_signals
        assert breadth_signals.THRESHOLDS['thrust']['count'] == 300
        assert breadth_signals.THRESHOLDS['t2108_zone']['oversold'] == 20
        assert breadth_signals.THRESHOLDS['t2108_zone']['overbought'] == 80


def _hist(closes, highs=None, lows=None, end='2026-07-29'):
    n = len(closes)
    # Roll a weekend `end` back to the prior business day: pandas' bdate_range
    # silently yields n-1 periods when `end` is not a business day.
    end_bd = pd.offsets.BDay().rollback(pd.Timestamp(end))
    idx = pd.bdate_range(end=end_bd, periods=n)
    return pd.DataFrame({
        'Close': closes,
        'High': highs if highs is not None else [c + 1 for c in closes],
        'Low': lows if lows is not None else [c - 1 for c in closes],
    }, index=idx)


class TestStochastics:
    def test_hand_computed_with_fixed_range(self):
        from pipeline.screeners.breadth_signals import compute_stochastics
        # Highs pinned at 100, lows at 0 -> raw %K == close, hand-computable
        closes = [50.0] * 14 + [80.0, 60.0, 40.0]
        hist = _hist(closes, highs=[100.0] * 17, lows=[0.0] * 17)
        fast, slow = compute_stochastics(hist)
        assert fast.iloc[-1] == pytest.approx((80 + 60 + 40) / 3)
        # slow = SMA3(fast): fast[-3..-1] = mean(50,50,80), mean(50,80,60), mean(80,60,40)
        f3 = [(50 + 50 + 80) / 3, (50 + 80 + 60) / 3, (80 + 60 + 40) / 3]
        assert slow.iloc[-1] == pytest.approx(sum(f3) / 3)

    def test_flat_market_carries_forward_no_nan(self):
        from pipeline.screeners.breadth_signals import compute_stochastics
        hist = _hist([100.0] * 20, highs=[100.0] * 20, lows=[100.0] * 20)
        fast, slow = compute_stochastics(hist)
        assert not fast.tail(5).isna().any()
        assert fast.iloc[-1] == pytest.approx(50.0)  # seeded carry-forward

    def test_rising_market_pegs_100(self):
        from pipeline.screeners.breadth_signals import compute_stochastics
        closes = [100.0 + i for i in range(30)]
        hist = _hist(closes, highs=closes, lows=[c for c in closes])
        # highs == closes rising -> close is always the 14d high -> raw = 100
        fast, slow = compute_stochastics(hist)
        assert fast.iloc[-1] == pytest.approx(100.0)
        assert slow.iloc[-1] == pytest.approx(100.0)


class TestDangerSignals:
    def test_healthy_tape_no_signals(self):
        from pipeline.screeners.breadth_signals import danger_signals
        closes = [100.0 + i for i in range(40)]   # rising, above SMA20
        hist = _hist(closes)
        sig = danger_signals(hist)
        assert set(sig) == {'below_20sma', 'stoch_cross', 'stoch_down',
                            'lower_lows', 'close_below_lows'}
        assert sig['below_20sma'] is False
        assert sig['lower_lows'] is False
        assert sig['close_below_lows'] is False

    def test_breakdown_tape_fires_price_signals(self):
        from pipeline.screeners.breadth_signals import danger_signals
        closes = [100.0] * 30 + [95.0, 90.0, 85.0, 80.0]  # sharp break
        lows = [99.0] * 30 + [94.0, 89.0, 84.0, 79.0]      # 3+ lower lows
        hist = _hist(closes, lows=lows)
        sig = danger_signals(hist)
        assert sig['below_20sma'] is True
        assert sig['lower_lows'] is True     # 79 < 84 < 89 < 94
        assert sig['close_below_lows'] is True  # 80 < min(94, 89, 84)
        assert sig['stoch_cross'] is True    # falling tape: fast under slow
        assert sig['stoch_down'] is True

    def test_warn_counts_shape(self):
        from pipeline.screeners.breadth_signals import warn_counts
        closes = [100.0 + (i % 7) - 3 for i in range(200)]
        hist = _hist(closes)
        wc = warn_counts(hist, days=130)
        assert len(wc) == 130
        assert set(wc[0]) == {'date', 'count'}
        assert all(0 <= w['count'] <= 5 for w in wc)
        assert wc[-1]['date'] == hist.index[-1].strftime('%Y-%m-%d')


def _ohlc(closes, end='2026-07-29'):
    h = _hist(closes, end=end)
    h['Open'] = h['Close'].shift(1).fillna(h['Close'])
    return h


class TestDangerAt:
    def test_slices_to_prior_session(self):
        from pipeline.screeners.breadth_signals import danger_at
        closes = [100.0] * 30 + [95.0, 90.0, 85.0, 80.0]
        lows = [99.0] * 30 + [94.0, 89.0, 84.0, 79.0]
        hist = _hist(closes, lows=lows, end='2026-07-30')
        d = danger_at(hist, '2026-07-29')
        assert d['date'] == '2026-07-29'
        assert d['count'] == sum(d['signals'].values())
        # sliced-to-07-29 signals must match evaluating the truncated hist
        # directly (not the full hist through 07-30) — pins the slicing itself
        from pipeline.screeners.breadth_signals import danger_signals
        truncated_hist = hist.loc[hist.index.strftime('%Y-%m-%d') <= '2026-07-29']
        assert d['signals'] == danger_signals(truncated_hist)

    def test_date_beyond_last_session_clamps(self):
        from pipeline.screeners.breadth_signals import danger_at
        closes = [100.0 + i for i in range(40)]
        hist = _hist(closes, end='2026-07-30')
        last_date = hist.index[-1].strftime('%Y-%m-%d')
        d = danger_at(hist, '2099-01-01')
        assert d['date'] == last_date


class TestMarketHealth:
    def test_shape_and_alignment(self):
        from pipeline.screeners.breadth_signals import market_health
        spy = _ohlc([100.0 + i * 0.1 for i in range(250)])
        qqq = _ohlc([200.0 + i * 0.2 for i in range(250)])
        health = market_health(spy, qqq, days=130)
        for key in ('spy', 'qqq'):
            blk = health[key]
            assert len(blk['candles']) == 130
            assert len(blk['sma20']) == len(blk['sma50']) == len(blk['sma200']) == 130
            assert set(blk['candles'][0]) == {'date', 'o', 'h', 'l', 'c'}
            assert set(blk['danger']) == {'signals', 'count'}
            assert blk['danger']['count'] == sum(blk['danger']['signals'].values())
            assert len(blk['warn_history']) == 130
            assert blk['warn_history'][-1]['date'] == blk['candles'][-1]['date']

    def test_truncate_health(self):
        from pipeline.screeners.breadth_signals import market_health, truncate_health
        spy = _ohlc([100.0 + i * 0.1 for i in range(250)])
        qqq = _ohlc([200.0 + i * 0.2 for i in range(250)])
        health = market_health(spy, qqq, days=130)
        cut_date = health['spy']['candles'][99]['date']
        t = truncate_health(health, cut_date)
        assert len(t['spy']['candles']) == 100
        assert t['spy']['candles'][-1]['date'] == cut_date
        assert t['spy']['danger']['count'] == t['spy']['warn_history'][-1]['count']
        assert truncate_health(health, '1990-01-01') is None


def _frame(rows):
    return pd.DataFrame(rows)


def _bull_row(**kw):
    base = dict(ratio_5d=1.5, ratio_10d=1.3, up_4pct=350, down_4pct=80,
                up_25pct_qtr=500, down_25pct_qtr=200, up_13pct_34d=700,
                down_13pct_34d=300, mcclellan_osc=25.0, new_highs=40,
                new_lows=5, pct_above_200sma=62.0, t2108=65.0)
    base.update(kw)
    return _row(**base)


def _bear_row(**kw):
    base = dict(ratio_5d=0.3, ratio_10d=0.4, up_4pct=60, down_4pct=400,
                up_25pct_qtr=150, down_25pct_qtr=600, up_13pct_34d=200,
                down_13pct_34d=800, mcclellan_osc=-40.0, new_highs=2,
                new_lows=30, pct_above_200sma=25.0, t2108=28.0)
    base.update(kw)
    return _row(**base)


def _health_stub(spy_count=0, qqq_count=0, close=100.0, sma20=95.0,
                 sma50=90.0, sma200=85.0, date='2026-07-29'):
    def blk(count):
        return {'candles': [{'date': date, 'o': close, 'h': close, 'l': close, 'c': close}],
                'sma20': [sma20], 'sma50': [sma50], 'sma200': [sma200],
                'danger': {'signals': {}, 'count': count},
                'warn_history': [{'date': date, 'count': count}]}
    return {'spy': blk(spy_count), 'qqq': blk(qqq_count)}


class TestEvaluate:
    def test_clean_bull_day(self):
        from pipeline.screeners.breadth_signals import evaluate
        frame = _frame([{'date': '2026-07-29', **_bull_row()}])
        v = evaluate(frame, _health_stub())
        assert v['env'] == 'BULLISH'
        assert v['risk'] == 'Low'
        assert v['spy_state'] == 'Uptrend' and v['qqq_state'] == 'Uptrend'
        assert v['alignment'] == 'Aligned'
        assert 'Confirmed bull' in v['confirmation']
        assert len(v['votes']) == 12

    def test_clean_bear_day(self):
        from pipeline.screeners.breadth_signals import evaluate
        health = _health_stub(spy_count=5, qqq_count=4, close=80.0,
                              sma20=95.0, sma50=100.0, sma200=105.0)
        frame = _frame([{'date': '2026-07-29', **_bear_row()}])
        v = evaluate(frame, health)
        assert v['env'] == 'BEARISH'
        assert v['risk'] == 'High'          # 5 + 4 = 9 warnings
        assert v['spy_state'] == 'Downtrend'
        assert 'Confirmed bear' in v['confirmation']

    def test_oversold_override_outranks_score(self):
        from pipeline.screeners.breadth_signals import evaluate
        frame = _frame([{'date': '2026-07-29', **_bear_row(t2108=15.0)}])
        v = evaluate(frame, _health_stub(spy_count=5, qqq_count=5))
        assert v['env'] == 'OVERSOLD'
        assert any('thrust' in n.lower() or 'reversal' in n.lower() for n in v['notes'])

    def test_overbought_override(self):
        from pipeline.screeners.breadth_signals import evaluate
        frame = _frame([{'date': '2026-07-29', **_bull_row(t2108=85.0)}])
        v = evaluate(frame, _health_stub())
        assert v['env'] == 'OVERBOUGHT'

    def test_churn_day_noted(self):
        from pipeline.screeners.breadth_signals import evaluate
        frame = _frame([{'date': '2026-07-29', **_row(up_4pct=400, down_4pct=380)}])
        v = evaluate(frame, _health_stub())
        assert any('churn' in n.lower() or 'volatile' in n.lower() for n in v['notes'])

    def test_health_none_degrades(self):
        from pipeline.screeners.breadth_signals import evaluate
        frame = _frame([{'date': '2026-07-29', **_bull_row()}])
        v = evaluate(frame, None)
        assert v['spy_state'] is None and v['alignment'] is None
        assert v['warn_total'] == 0 and v['risk'] == 'Low'
        assert any('price signals unavailable' in n.lower() for n in v['notes'])
        assert v['votes']['spy_danger'] == 'neutral'

    def test_mixed_day_and_disagreement_named(self):
        from pipeline.screeners.breadth_signals import evaluate
        # Genuinely split tape: 3 bull votes (ratio_10d, 13/34 spread, bench),
        # 3 bear votes (qtr spread, mcclellan, nh_nl), rest neutral -> score 0.
        frame = _frame([{'date': '2026-07-29',
                         **_row(ratio_5d=0.6, ratio_10d=1.2,
                                up_25pct_qtr=200, down_25pct_qtr=300,
                                up_13pct_34d=500, down_13pct_34d=400,
                                mcclellan_osc=-5.0, new_highs=10, new_lows=20,
                                pct_above_200sma=45.0, t2108=50.0)}])
        v = evaluate(frame, _health_stub(spy_count=2, qqq_count=3))
        assert v['env'] == 'MIXED'
        assert 'Inconclusive' in v['confirmation']
        assert 'disagree' in v['confirmation']

    def test_prefix_purity(self):
        """A prefix's verdict must not change when later rows exist (Spec 3 replay guard)."""
        from pipeline.screeners.breadth_signals import evaluate
        prefix_rows = [{'date': '2026-07-27', **_bull_row()},
                       {'date': '2026-07-28', **_bull_row()}]
        v_alone = evaluate(_frame(prefix_rows), None)
        # Same prefix sliced out of a longer frame that ends with a bear day
        full = _frame(prefix_rows + [{'date': '2026-07-29', **_bear_row()}])
        v_sliced = evaluate(full.iloc[:2].reset_index(drop=True), None)
        assert v_alone == v_sliced
        assert v_alone['env'] == 'BULLISH'   # the later bear row leaked nothing

    def test_evaluate_matches_replay_via_truncate_health(self):
        """Spec 3 replay guard: evaluating a prefix directly with the full health
        dict must equal evaluating the same prefix against a pre-truncated
        health dict (the shape Time Machine hands in for historical replay)."""
        from pipeline.screeners.breadth_signals import (
            evaluate, market_health, truncate_health,
        )
        prefix_rows = [{'date': '2026-07-27', **_bull_row()},
                       {'date': '2026-07-28', **_bull_row()},
                       {'date': '2026-07-29', **_bear_row()}]
        prefix_frame = _frame(prefix_rows)
        prefix_last_date = prefix_rows[-1]['date']

        # hists run longer than the prefix (through 2026-07-31)
        spy = _ohlc([100.0 + i * 0.1 for i in range(250)], end='2026-07-31')
        qqq = _ohlc([200.0 + i * 0.2 for i in range(250)], end='2026-07-31')
        full_health = market_health(spy, qqq, days=130)

        v_full = evaluate(prefix_frame, full_health)
        v_truncated = evaluate(prefix_frame, truncate_health(full_health, prefix_last_date))
        assert v_full == v_truncated


class TestPercentileContext:
    def test_ranks_on_known_frame(self):
        from pipeline.screeners.breadth_signals import percentile_context
        rows = [{'date': f'2026-07-{d:02d}', **_row(down_4pct=d * 10)} for d in range(1, 11)]
        frame = _frame(rows)   # down_4pct: 10..100, today = 100 -> 100th pctile
        ctx = percentile_context(frame)
        assert ctx['down_4pct'] == 100
        assert 0 <= ctx['t2108'] <= 100
        assert 'qtr_spread' in ctx and 'nh_nl_net' in ctx

    def test_missing_today_value_omitted(self):
        from pipeline.screeners.breadth_signals import percentile_context
        rows = [{'date': '2026-07-28', **_row()},
                {'date': '2026-07-29', **_row(mcclellan_osc=None)}]
        ctx = percentile_context(_frame(rows))
        assert 'mcclellan_osc' not in ctx

    def test_nan_row_excluded_from_denominator(self):
        """A NaN row must not count in the ranking denominator (FINDING F):
        rank against dropna(), not the raw series (which would deflate the
        percentile by counting the NaN as a member with an undefined order)."""
        from pipeline.screeners.breadth_signals import percentile_context
        rows = [{'date': f'2026-07-{d:02d}', **_row(down_4pct=d * 10)} for d in range(1, 5)]
        rows.append({'date': '2026-07-05', **_row(down_4pct=None)})
        rows.append({'date': '2026-07-06', **_row(down_4pct=40)})
        frame = _frame(rows)  # non-NaN down_4pct values: 10,20,30,40(today),40
        ctx = percentile_context(frame)
        # denominator excludes the NaN row: 5 non-NaN values, today (40) ties
        # the max -> 100th percentile either way here, so pin count via mean directly
        non_nan = pd.to_numeric(frame['down_4pct'], errors='coerce').dropna()
        expected = int(round(float((non_nan <= 40).mean()) * 100))
        assert ctx['down_4pct'] == expected
        assert len(non_nan) == 5  # confirms the NaN row was excluded from ranking


class TestAnnotateRows:
    def test_rows_get_codes_matching_prefix_evaluate(self):
        from pipeline.screeners.breadth_signals import annotate_rows, evaluate
        rows_data = [{'date': '2026-07-27', **_bull_row()},
                     {'date': '2026-07-28', **_bear_row()},
                     {'date': '2026-07-29', **_bull_row()}]
        frame = _frame(rows_data)
        json_rows = [dict(r) for r in rows_data]
        annotate_rows(json_rows, frame, None)
        for i, jr in enumerate(json_rows):
            expect = evaluate(frame.iloc[:i + 1].reset_index(drop=True), None)
            assert jr['v'] == {'env': expect['env'], 'risk': expect['risk'],
                               'warn': expect['warn_total']}

    def test_unknown_date_gets_none(self):
        from pipeline.screeners.breadth_signals import annotate_rows
        frame = _frame([{'date': '2026-07-29', **_bull_row()}])
        json_rows = [{'date': '1999-01-01'}]
        annotate_rows(json_rows, frame, None)
        assert json_rows[0]['v'] is None


class TestRunSignals:
    def _breadth_result(self, rows):
        return {'history': {'rows': [dict(r) for r in rows]}, 'mm': {}, 'breadth': {}}

    def test_attaches_verdict_context_and_row_codes(self):
        from pipeline.screeners.breadth_signals import run_signals
        rows = [{'date': '2026-07-28', **_bull_row()},
                {'date': '2026-07-29', **_bull_row()}]
        frame = _frame(rows)
        spy = _ohlc([100.0 + i * 0.1 for i in range(250)])
        qqq = _ohlc([200.0 + i * 0.2 for i in range(250)])
        result = self._breadth_result(rows)
        health = run_signals(result, frame, spy, qqq)
        assert health is not None and 'spy' in health and 'qqq' in health
        assert result['verdict']['env'] in ('BULLISH', 'MIXED', 'BEARISH',
                                            'OVERSOLD', 'OVERBOUGHT')
        assert 'context' in result['verdict']
        assert all('v' in r for r in result['history']['rows'])

    def test_none_history_degrades(self):
        from pipeline.screeners.breadth_signals import run_signals
        rows = [{'date': '2026-07-29', **_bull_row()}]
        result = self._breadth_result(rows)
        health = run_signals(result, _frame(rows), None, None)
        assert health is None
        assert result['verdict']['spy_state'] is None
        assert any('unavailable' in n for n in result['verdict']['notes'])


class TestSignalsHistory:
    def test_shape_and_keys(self):
        from pipeline.screeners.breadth_signals import signals_history
        closes = [100.0 + (i % 9) - 4 for i in range(220)]
        hist = _hist(closes)
        sh = signals_history(hist, days=130)
        assert len(sh) == 130
        assert set(sh[0]) == {'date', 'signals', 'count'}
        assert set(sh[0]['signals']) == {'below_20sma', 'stoch_cross', 'stoch_down',
                                         'lower_lows', 'close_below_lows'}
        assert all(s['count'] == sum(s['signals'].values()) for s in sh)
        assert sh[-1]['date'] == hist.index[-1].strftime('%Y-%m-%d')

    def test_days_none_returns_all_sessions(self):
        from pipeline.screeners.breadth_signals import signals_history
        hist = _hist([100.0 + (i % 5) for i in range(210)])
        assert len(signals_history(hist, days=None)) == 210

    def test_matches_danger_at_for_each_date(self):
        """The history entry for date D must equal danger_at(hist, D)."""
        from pipeline.screeners.breadth_signals import signals_history, danger_at
        hist = _hist([100.0 + (i % 11) - 5 for i in range(230)])
        sh = signals_history(hist, days=None)
        for entry in (sh[-1], sh[-40], sh[-100]):
            da = danger_at(hist, entry['date'])
            assert da['signals'] == entry['signals']
            assert da['count'] == entry['count']
            assert da['date'] == entry['date']

    def test_market_health_includes_signals_history(self):
        from pipeline.screeners.breadth_signals import market_health
        spy = _ohlc([100.0 + i * 0.1 for i in range(250)])
        qqq = _ohlc([200.0 + i * 0.2 for i in range(250)])
        health = market_health(spy, qqq, days=130)
        for key in ('spy', 'qqq'):
            sh = health[key]['signals_history']
            assert len(sh) == 130 == len(health[key]['candles'])
            assert sh[-1]['date'] == health[key]['candles'][-1]['date']


class TestRunSignalsAtomicity:
    def test_breadth_result_untouched_when_annotate_fails(self, monkeypatch):
        from pipeline.screeners import breadth_signals as bs
        rows = [{'date': '2026-07-29', **_bull_row()}]
        frame = _frame(rows)
        result = {'history': {'rows': [dict(r) for r in rows]}, 'mm': {}, 'breadth': {}}

        def boom(*args, **kwargs):
            raise RuntimeError('annotate exploded')

        monkeypatch.setattr(bs, 'annotate_rows', boom)
        with pytest.raises(RuntimeError):
            bs.run_signals(result, frame, None, None)
        assert 'verdict' not in result
        assert all('v' not in r for r in result['history']['rows'])

    def test_success_path_unchanged(self):
        from pipeline.screeners.breadth_signals import run_signals
        rows = [{'date': '2026-07-28', **_bull_row()},
                {'date': '2026-07-29', **_bull_row()}]
        frame = _frame(rows)
        result = {'history': {'rows': [dict(r) for r in rows]}, 'mm': {}, 'breadth': {}}
        spy = _ohlc([100.0 + i * 0.1 for i in range(250)])
        qqq = _ohlc([200.0 + i * 0.2 for i in range(250)])
        health = run_signals(result, frame, spy, qqq)
        assert health is not None
        assert 'context' in result['verdict']
        assert all(r.get('v') for r in result['history']['rows'])


class TestBuildReplay:
    def _frame_and_hists(self, n=12):
        rows = []
        for i in range(n):
            body = _bull_row() if i % 2 == 0 else _bear_row()
            rows.append({'date': f'2026-07-{i + 1:02d}', **body})
        frame = _frame(rows)
        spy = _ohlc([100.0 + i * 0.1 for i in range(260)], end='2026-07-12')
        qqq = _ohlc([200.0 + i * 0.2 for i in range(260)], end='2026-07-12')
        return frame, spy, qqq

    def test_top_level_shape(self):
        from pipeline.screeners.breadth_signals import build_replay
        frame, spy, qqq = self._frame_and_hists()
        r = build_replay(frame, spy, qqq)
        assert set(r) == {'dates', 'rows', 'verdicts', 'health'}
        assert r['dates'] == list(frame['date'])
        assert set(r['rows']) == set(r['dates']) == set(r['verdicts'])
        for key in ('spy', 'qqq'):
            assert set(r['health'][key]) == {'candles', 'sma20', 'sma50',
                                             'sma200', 'signals_history'}

    def test_no_peek_every_date_matches_independent_evaluate(self):
        """The no-peek rule: every stored verdict equals a fresh prefix evaluate."""
        from pipeline.screeners.breadth_signals import (
            build_replay, evaluate, percentile_context, market_health)
        frame, spy, qqq = self._frame_and_hists()
        r = build_replay(frame, spy, qqq)
        health = market_health(spy, qqq, days=None)
        for i, d in enumerate(r['dates']):
            prefix = frame.iloc[:i + 1].reset_index(drop=True)
            expected = evaluate(prefix, health)
            expected['context'] = percentile_context(prefix)
            assert r['verdicts'][d] == expected, d

    def test_rows_are_json_safe(self):
        import json
        import numpy as np
        from pipeline.screeners.breadth_signals import build_replay
        frame, spy, qqq = self._frame_and_hists()
        frame.loc[0, 'mcclellan_osc'] = np.nan
        r = build_replay(frame, spy, qqq)
        assert r['rows'][r['dates'][0]]['mcclellan_osc'] is None
        json.dumps(r)  # must not raise

    def test_health_none_degrades(self):
        from pipeline.screeners.breadth_signals import build_replay
        frame, _, _ = self._frame_and_hists()
        r = build_replay(frame, None, None)
        assert r['health'] is None
        first = r['verdicts'][r['dates'][0]]
        assert first['spy_state'] is None
        assert any('unavailable' in n.lower() for n in first['notes'])

    def test_health_spans_full_history(self):
        from pipeline.screeners.breadth_signals import build_replay
        frame, spy, qqq = self._frame_and_hists()
        r = build_replay(frame, spy, qqq)
        # days=None -> every session of the input history, not just 130
        assert len(r['health']['spy']['candles']) == len(spy)
        assert len(r['health']['spy']['signals_history']) == len(spy)
