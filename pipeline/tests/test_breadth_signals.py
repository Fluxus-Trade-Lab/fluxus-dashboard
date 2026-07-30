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
    idx = pd.bdate_range(end=end, periods=n)
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
