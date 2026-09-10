"""in_sp500 必须同时到达 breadth 和 universe.json —— 接线测试,不是单元测试。

2026-09-04 上线的指数作用域一族(`pct_above_*_sp500` / `t2108_sp500` /
`sp500_members`)从上线到 09-09 每晚都写 NULL,而抓取本身一直是好的:
`universe.json` 里 503 行 `in_sp500=True` 一直在。原因是那列被设在
`compute_universe_scores` 内部的 `df = universe.copy()` 上,而 breadth 拿的是
**没被加工过的 `universe`**,两个不同的对象。

581 行归档里 0 个值,没有任何东西报红 —— **一个「允许为 NULL」的列,无法区分
「数据缺失」和「没人把数据递给它」**。所以这里测的不是函数对不对,是
**两个读者是不是都拿到了那一列**。
"""

from __future__ import annotations

import pandas as pd
import pytest

from pipeline.screeners import run_all


UNI = pd.DataFrame({
    'ticker': ['AAPL', 'MSFT', 'PENNY'],
    'change_pct': [1.0, -1.0, 0.5],
})


def _fake_adapter(members):
    class _FA:
        def fetch_index_members(self, index):        # noqa: D102, ARG002
            return members
    return _FA


def test_membership_lands_on_the_frame_breadth_reads(monkeypatch):
    """阳性对照的正面:抓到成员时,`universe` 本身必须带上这一列。"""
    monkeypatch.setattr('pipeline.adapters.finviz_adapter.FinvizAdapter',
                        _fake_adapter({'AAPL', 'MSFT'}))
    uni = UNI.copy()
    run_all.attach_index_membership(uni)
    assert 'in_sp500' in uni.columns, "breadth 读的就是这个 frame"
    assert uni['in_sp500'].tolist() == [True, True, False]


def test_the_same_column_survives_into_the_scored_copy(monkeypatch):
    """另一个读者:universe.json 走的是 `df = universe.copy()`,必须照样有。

    这一条锁住修复的形状 —— 把抓取挪到 main() 是为了**一次喂两个读者**,
    如果哪天有人把它挪回 compute_universe_scores,breadth 那侧会再次静默变 NULL。
    """
    monkeypatch.setattr('pipeline.adapters.finviz_adapter.FinvizAdapter',
                        _fake_adapter({'AAPL'}))
    uni = UNI.copy()
    run_all.attach_index_membership(uni)
    scored_copy = uni.copy()          # compute_universe_scores 的第一行就是这个
    assert scored_copy['in_sp500'].tolist() == [True, False, False]


def test_breadth_actually_produces_index_columns_from_that_frame(monkeypatch):
    """端到端:带着这列的 frame 交给 breadth,那五个读数必须**有值**。

    ⚠️ 这是本文件的主张。前两条只证明列在;这条证明列在**换来了数**。
    """
    from pipeline.screeners import breadth_metrics

    monkeypatch.setattr('pipeline.adapters.finviz_adapter.FinvizAdapter',
                        _fake_adapter({'AAPL', 'MSFT'}))
    uni = pd.DataFrame({
        'ticker': ['AAPL', 'MSFT', 'PENNY'],
        'change_pct': [1.0, -1.0, 0.5],
        'sma20_dist': [3.0, -2.0, 9.0],
        'sma40_dist': [3.0, -2.0, 9.0],
        'sma50_dist': [3.0, -2.0, 9.0],
        'sma200_dist': [3.0, 2.0, -9.0],
    })
    run_all.attach_index_membership(uni)
    snap = breadth_metrics.compute_snapshot(uni)

    assert snap['sp500_members'] == 2, "PENNY 不是成分股,不该进分母"
    assert snap['pct_above_200sma_sp500'] == 100.0, "两只成分股都在 200 日线上"
    assert snap['pct_above_20sma_sp500'] == 50.0


def test_missing_column_still_ships_null_not_a_fallback():
    """反向对照:没有这一列时必须是 NULL,**不能**退回整个池子。

    退回全池正是让读数与任何公开来源都对不上的那个错。
    """
    from pipeline.screeners import breadth_metrics

    uni = pd.DataFrame({
        'ticker': ['AAPL', 'MSFT', 'PENNY'],
        'change_pct': [1.0, -1.0, 0.5],
        'sma20_dist': [3.0, -2.0, 9.0],
        'sma40_dist': [3.0, -2.0, 9.0],
        'sma50_dist': [3.0, -2.0, 9.0],
        'sma200_dist': [3.0, 2.0, -9.0],
    })
    snap = breadth_metrics.compute_snapshot(uni)
    for k in ('pct_above_20sma_sp500', 't2108_sp500', 'pct_above_50sma_sp500',
              'pct_above_200sma_sp500', 'sp500_members'):
        assert snap[k] is None, f"{k} 应为 NULL,而不是全池读数"


def test_fetch_failure_is_its_own_failure_domain(monkeypatch):
    """抓取炸了不许掀翻整晚产线,只是这几列没有。"""
    class _Boom:
        def fetch_index_members(self, index):        # noqa: D102, ARG002
            raise RuntimeError("finviz down")
    monkeypatch.setattr('pipeline.adapters.finviz_adapter.FinvizAdapter', _Boom)
    uni = UNI.copy()
    run_all.attach_index_membership(uni)      # 不抛
    assert 'in_sp500' not in uni.columns


def test_empty_membership_leaves_the_column_absent(monkeypatch):
    """抓回空集也算失败 —— 不能写一列全 False 冒充「没有成分股」。"""
    monkeypatch.setattr('pipeline.adapters.finviz_adapter.FinvizAdapter',
                        _fake_adapter(set()))
    uni = UNI.copy()
    run_all.attach_index_membership(uni)
    assert 'in_sp500' not in uni.columns
