"""Stockbee Market Monitor readings on the author's own definitions (2026-09-18).

Andy 2026-09-18, verbatim: 「全部按原文，9 用课程版，12 注册 EP Stockbee和 EP
Qullamaggie 然后我们以后可以测试下。」

Primary sources, checked word for word on 2026-09-18:
  * scans -- https://stockbee.blogspot.com/2014/08/how-i-get-market-monitor-numbers.html
    (TC2000 v12.4 block; "Universe: US Common Stocks")
  * ratio -- https://stockbee.blogspot.com/p/mm.html, Pradeep Bonde's own replies:
    "It is ratio of 5 days of 4% b/o /5 days 4% b/d same for 10 days using 10 day
    data." (2017-03-09) and "total of 5 days 4% b/o divided by total of 5 days 4%
    b/d" (2018-08-30)
  * 10-day line -- https://stockbee.blogspot.com/2010/05/what-you-need-to-know-about-market.html
    "When the 10 day ratio goes above 2 after market has been in bearish phase for
    sometime, it indicates bullish breadth thrust" / "goes below .5 after market
    has been bullish for sometime, it indicates a bearish thrust"

Each block: one positive case (the author's rule counts / votes) and one negative
case (the rule we used to run would have said something else).
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from pipeline.adapters.yfinance_adapter import stockbee_mm_inputs
from pipeline.screeners.breadth_metrics import compute_snapshot, _build_output
from pipeline.screeners.breadth_signals import breadth_votes, vote_detail, THRESHOLDS
from pipeline.screeners.breadth_store import derive, BREADTH_COLUMNS
from pipeline.screeners.state_board import state_board


# ── per-ticker inputs from the daily bars ────────────────────────────

def _hist(closes, vol=100_000):
    idx = pd.bdate_range(end='2026-09-17', periods=len(closes))
    c = pd.Series(closes, index=idx, dtype=float)
    return pd.DataFrame({'Open': c, 'High': c, 'Low': c, 'Close': c,
                         'Volume': float(vol)}, index=idx)


class TestPerTickerInputs:
    def test_quarter_is_anchored_at_the_65_day_lowest_close(self):
        # 100 bars: 20 flat at 12, falls to 10, then climbs to 13. Point to
        # point over 63 bars is +8.3% (12 -> 13); from MINC65 it is +30%.
        closes = [12.0] * 60 + [10.0] + list(np.linspace(10.5, 13.0, 39))
        r = stockbee_mm_inputs(_hist(closes))
        want = 100 * ((13.0 + .01) - (10.0 + .01)) / (10.0 + .01)
        assert r['sb_pct_from_minc65'] == pytest.approx(want)
        assert r['sb_pct_from_minc65'] >= 25
        p2p = 100 * (13.0 / closes[-63] - 1)
        assert p2p < 25          # the old point-to-point rule would not count it

    def test_down_direction_is_anchored_at_the_65_day_highest_close(self):
        closes = [20.0] * 40 + [30.0] + [22.0] * 59
        r = stockbee_mm_inputs(_hist(closes))
        want = 100 * ((22.0 + .01) - (30.0 + .01)) / (30.0 + .01)
        assert r['sb_pct_from_maxc65'] == pytest.approx(want)

    def test_34_day_window_and_20_bar_month(self):
        closes = list(np.linspace(8.0, 11.0, 80))
        r = stockbee_mm_inputs(_hist(closes, vol=50_000))
        c = pd.Series(closes)
        assert r['sb_pct_from_minc34'] == pytest.approx(
            100 * ((c.iloc[-1] + .01) - (c.iloc[-34:].min() + .01)) / (c.iloc[-34:].min() + .01))
        assert r['sb_c20'] == pytest.approx(c.iloc[-21])            # TC2000 C20
        assert r['sb_pct_chg_20'] == pytest.approx(100 * (c.iloc[-1] - c.iloc[-21]) / c.iloc[-21])
        assert r['sb_avg_dollar_vol_20'] == pytest.approx(c.iloc[-20:].mean() * 50_000)

    def test_short_history_is_null_not_zero(self):
        r = stockbee_mm_inputs(_hist([10.0] * 30))
        assert r['sb_pct_from_minc65'] is None and r['sb_pct_from_maxc65'] is None
        assert r['sb_pct_from_minc34'] is None
        assert r['sb_c20'] is not None


# ── cross-sectional counts ───────────────────────────────────────────

def _uni(rows):
    base = dict(change_pct=0.0, perf_1m=0.0, perf_3m=0.0, perf_34d=0.0,
                sma20_dist=0.0, sma40_dist=0.0, sma50_dist=0.0, sma200_dist=0.0,
                high_52w=-0.2, low_52w=0.2, industry='Software',
                sb_pct_from_minc65=0.0, sb_pct_from_maxc65=0.0,
                sb_pct_from_minc34=0.0, sb_pct_from_maxc34=0.0,
                sb_pct_chg_20=0.0, sb_c20=20.0, sb_avg_dollar_vol_20=1_000_000.0)
    return pd.DataFrame([{**base, 'ticker': f'T{i}', **r} for i, r in enumerate(rows)])


class TestAuthorCounts:
    def test_quarter_counts_need_the_liquidity_leg(self):
        s = compute_snapshot(_uni([
            dict(sb_pct_from_minc65=30.0),                                  # counts
            dict(sb_pct_from_minc65=30.0, sb_avg_dollar_vol_20=249_999.0),  # illiquid
            dict(sb_pct_from_minc65=30.0, industry='Shell Companies'),     # not common stock
            dict(sb_pct_from_maxc65=-26.0),                                 # down side
        ]))
        assert s['up_25pct_qtr_stockbee'] == 1
        assert s['down_25pct_qtr_stockbee'] == 1

    def test_quarter_count_ignores_the_point_to_point_column(self):
        s = compute_snapshot(_uni([dict(perf_3m=0.40, sb_pct_from_minc65=10.0)]))
        assert s['up_25pct_qtr'] == 1                   # old column unchanged
        assert s['up_25pct_qtr_stockbee'] == 0          # author's anchor says no

    def test_13_in_34(self):
        s = compute_snapshot(_uni([
            dict(sb_pct_from_minc34=13.0), dict(sb_pct_from_minc34=12.9),
            dict(sb_pct_from_maxc34=-13.0), dict(sb_pct_from_maxc34=-13.0, sb_avg_dollar_vol_20=1000.0),
        ]))
        assert s['up_13pct_34d_stockbee'] == 1
        assert s['down_13pct_34d_stockbee'] == 1

    def test_month_needs_c20_of_five_dollars(self):
        s = compute_snapshot(_uni([
            dict(sb_pct_chg_20=60.0, sb_c20=5.0),     # up 25 and up 50
            dict(sb_pct_chg_20=60.0, sb_c20=4.99),    # penny stock: out
            dict(sb_pct_chg_20=30.0, sb_c20=10.0),    # up 25 only
            dict(sb_pct_chg_20=-55.0, sb_c20=10.0),   # down 25 and down 50
        ]))
        assert s['up_25pct_month_stockbee'] == 2
        assert s['up_50pct_month_stockbee'] == 1
        assert s['down_25pct_month_stockbee'] == 1
        assert s['down_50pct_month_stockbee'] == 1

    def test_missing_inputs_are_null_not_zero(self):
        u = _uni([dict()]).drop(columns=['sb_pct_from_minc65', 'sb_pct_from_maxc65',
                                         'sb_pct_from_minc34', 'sb_pct_from_maxc34',
                                         'sb_pct_chg_20', 'sb_c20', 'sb_avg_dollar_vol_20'])
        s = compute_snapshot(u)
        for k in ('up_25pct_qtr_stockbee', 'down_13pct_34d_stockbee', 'up_50pct_month_stockbee'):
            assert s[k] is None

    def test_new_columns_are_in_the_archive_schema(self):
        for k in ('up_25pct_qtr_stockbee', 'down_25pct_qtr_stockbee',
                  'up_13pct_34d_stockbee', 'down_13pct_34d_stockbee',
                  'up_25pct_month_stockbee', 'down_25pct_month_stockbee',
                  'up_50pct_month_stockbee', 'down_50pct_month_stockbee',
                  'ratio_5d_stockbee', 'ratio_10d_stockbee'):
            assert k in BREADTH_COLUMNS


# ── ratios ───────────────────────────────────────────────────────────

def _archive(up_sb, dn_sb, up=None, dn=None):
    n = len(up_sb)
    return pd.DataFrame({
        'date': [f'2026-09-{i + 1:02d}' for i in range(n)],
        'advances': 100, 'declines': 100,
        'up_4pct': up or [500] * n, 'down_4pct': dn or [100] * n,
        'up_4pct_stockbee': up_sb, 'down_4pct_stockbee': dn_sb,
    })


class TestStockbeeRatios:
    def test_five_and_ten_day_sums_of_his_count(self):
        f = derive(_archive([float(x) for x in range(1, 11)], [5.0] * 10))
        assert f['ratio_5d_stockbee'].iloc[-1] == pytest.approx((6 + 7 + 8 + 9 + 10) / 25)
        assert f['ratio_10d_stockbee'].iloc[-1] == pytest.approx(55 / 50)
        assert f['ratio_5d'].iloc[-1] == pytest.approx(5.0)     # price-only column untouched

    def test_window_missing_a_session_is_unmeasurable(self):
        up = [None] * 3 + [100.0] * 7
        f = derive(_archive(up, [50.0] * 3 + [50.0] * 7))
        assert pd.isna(f['ratio_10d_stockbee'].iloc[-1])      # 3 of 10 missing
        assert f['ratio_5d_stockbee'].iloc[-1] == pytest.approx(2.0)

    def test_zero_decliners_is_unmeasurable_not_the_up_sum(self):
        f = derive(_archive([10.0] * 5, [0.0] * 5))
        assert pd.isna(f['ratio_5d_stockbee'].iloc[-1])


# ── votes ────────────────────────────────────────────────────────────

def _row(**kw):
    base = dict(ratio_5d=1.2, ratio_10d=1.1,
                ratio_5d_stockbee=1.2, ratio_10d_stockbee=1.1,
                up_25pct_qtr=400, down_25pct_qtr=300,
                up_25pct_qtr_stockbee=400, down_25pct_qtr_stockbee=300,
                up_13pct_34d=500, down_13pct_34d=400,
                up_13pct_34d_stockbee=500, down_13pct_34d_stockbee=400,
                new_highs=30, new_lows=10, new_highs_common=30, new_lows_common=10,
                mcclellan_osc=10.0, pct_above_200sma=55.0, t2108=65.0)
    base.update(kw)
    return base


class TestVotesReadTheAuthorColumns:
    def test_ten_day_bull_line_is_two(self):
        assert THRESHOLDS['ratio_10d']['bull'] == 2.0
        assert breadth_votes(_row(ratio_10d_stockbee=2.01))['ratio_10d'] == 'bull'
        # 1.5 was a bull vote under the self-made 1.0 line
        assert breadth_votes(_row(ratio_10d_stockbee=1.5))['ratio_10d'] == 'neutral'
        assert breadth_votes(_row(ratio_10d_stockbee=2.0))['ratio_10d'] == 'neutral'   # "goes above 2"
        assert breadth_votes(_row(ratio_10d_stockbee=0.49))['ratio_10d'] == 'bear'
        assert breadth_votes(_row(ratio_10d_stockbee=0.5))['ratio_10d'] == 'neutral'   # "below .5"

    def test_five_day_vote_reads_his_count_not_the_price_only_one(self):
        v = breadth_votes(_row(ratio_5d=1.5, ratio_5d_stockbee=0.4))
        assert v['ratio_5d'] == 'bear'
        v = breadth_votes(_row(ratio_5d=0.3, ratio_5d_stockbee=1.1))
        assert v['ratio_5d'] == 'bull'

    def test_ratio_without_his_count_is_unmeasurable(self):
        row = _row(ratio_5d=3.0, ratio_10d=3.0, ratio_5d_stockbee=None, ratio_10d_stockbee=float('nan'))
        v = breadth_votes(row)
        assert v['ratio_5d'] == 'neutral' and v['ratio_10d'] == 'neutral'
        d = {x['key']: x for x in vote_detail(row, v)}
        assert d['ratio_5d']['measurable'] is False
        assert d['ratio_10d']['measurable'] is False

    def test_spreads_read_the_author_columns(self):
        v = breadth_votes(_row(up_25pct_qtr=900, down_25pct_qtr=100,
                               up_25pct_qtr_stockbee=100, down_25pct_qtr_stockbee=900,
                               up_13pct_34d=900, down_13pct_34d=100,
                               up_13pct_34d_stockbee=100, down_13pct_34d_stockbee=900))
        assert v['qtr_spread'] == 'bear' and v['spread_13_34'] == 'bear'

    def test_spread_without_author_columns_is_unmeasurable(self):
        row = _row(up_25pct_qtr_stockbee=None, down_25pct_qtr_stockbee=None,
                   up_13pct_34d_stockbee=None, down_13pct_34d_stockbee=None)
        v = breadth_votes(row)
        assert v['qtr_spread'] == 'neutral' and v['spread_13_34'] == 'neutral'
        d = {x['key']: x for x in vote_detail(row, v)}
        assert d['qtr_spread']['measurable'] is False
        assert d['spread_13_34']['measurable'] is False

    def test_nh_nl_reads_the_common_stock_counts(self):
        # 2026-09-17: raw 28/30, common 4/28
        v = breadth_votes(_row(new_highs=40, new_lows=30, new_highs_common=4, new_lows_common=28))
        assert v['nh_nl'] == 'bear'
        d = {x['key']: x for x in vote_detail(_row(new_highs_common=None), v)}
        assert d['nh_nl']['measurable'] is False


# ── board ────────────────────────────────────────────────────────────

def _board_frame(**over):
    base = dict(_row(), up_4pct=231, down_4pct=288, pct_above_20sma=40.7,
                net_advances=-336, up_4pct_stockbee=159, down_4pct_stockbee=246)
    base.update(over)
    return pd.DataFrame([dict(base, down_4pct=637) for _ in range(5)] + [base])


def _board_row(board, key):
    return next(r for r in board if r['key'] == key)


class TestBoardReadsTheAuthorColumns:
    def test_damage_uses_his_quarter_counts(self):
        b = state_board(_board_frame(up_25pct_qtr=900, down_25pct_qtr=100,
                                     up_25pct_qtr_stockbee=100, down_25pct_qtr_stockbee=900))
        assert _board_row(b, 'damage')['level'] == 1
        b = state_board(_board_frame(up_25pct_qtr_stockbee=None, down_25pct_qtr_stockbee=None))
        assert _board_row(b, 'damage')['level'] is None

    def test_extremes_use_common_stock_counts(self):
        b = state_board(_board_frame(new_highs=90, new_lows=10, new_highs_common=4, new_lows_common=28))
        assert _board_row(b, 'extremes')['level'] == 0
        b = state_board(_board_frame(new_highs_common=float('nan')))
        assert _board_row(b, 'extremes')['level'] is None

    def test_confirmation_uses_his_five_day_ratio(self):
        b = state_board(_board_frame(ratio_5d=3.0, ratio_5d_stockbee=0.8, net_advances=100))
        assert _board_row(b, 'confirmation')['level'] == 0
        b = state_board(_board_frame(ratio_5d=3.0, ratio_5d_stockbee=None))
        assert _board_row(b, 'confirmation')['level'] is None


# ── breadth.json ─────────────────────────────────────────────────────

def test_breadth_json_carries_the_author_readings():
    f = pd.DataFrame([_row(date='2026-09-17', universe_size=5600,
                           up_25pct_month_stockbee=12, down_50pct_month_stockbee=3)])
    out = _build_output(f, {'stale': False}, {'universe_size': 5600}, None)
    for k in ('ratio_5d_stockbee', 'ratio_10d_stockbee', 'up_25pct_qtr_stockbee',
              'down_25pct_qtr_stockbee', 'up_13pct_34d_stockbee', 'down_13pct_34d_stockbee',
              'up_25pct_month_stockbee', 'down_25pct_month_stockbee',
              'up_50pct_month_stockbee', 'down_50pct_month_stockbee'):
        assert k in out['mm']
    assert out['mm']['up_25pct_month_stockbee'] == 12
    assert out['breadth']['new_highs_common'] == 30
    assert out['breadth']['new_lows_common'] == 10
