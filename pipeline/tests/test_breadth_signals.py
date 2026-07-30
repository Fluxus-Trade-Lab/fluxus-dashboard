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
