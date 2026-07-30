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
