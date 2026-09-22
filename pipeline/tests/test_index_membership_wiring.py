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


def _plausible(*tickers: str) -> set[str]:
    """把名单补到真实规模。

    ⚠️ 名单要能通过抓漏闸(>= MIN_PLAUSIBLE_MEMBERS)。用 2 只票做接线测试,
    测的其实是「残缺名单被拒」那条路径,而不是接线 —— 第一版就栽在这里。
    """
    return set(tickers) | {f"PAD{i:04d}" for i in range(520)}


@pytest.fixture(autouse=True)
def _store_in_tmp(tmp_path, monkeypatch):
    """台账写进 tmp,别在仓库里落文件。"""
    from pipeline.adapters import index_members_store as ims
    monkeypatch.setattr(ims, "ROSTER", tmp_path / "roster.json")
    monkeypatch.setattr(ims, "CHANGELOG", tmp_path / "log.csv")
    monkeypatch.setattr(ims, "NDX_ROSTER", tmp_path / "ndx_roster.json")
    monkeypatch.setattr(ims, "NDX_CHANGELOG", tmp_path / "ndx_log.csv")


def _plausible_ndx(*tickers: str) -> set[str]:
    """Nasdaq-100 台账的抓漏闸下限是 90,不是标普的 480。"""
    return set(tickers) | {f"NPAD{i:04d}" for i in range(90)}


def test_membership_lands_on_the_frame_breadth_reads(monkeypatch):
    """阳性对照的正面:抓到成员时,`universe` 本身必须带上这一列。"""
    monkeypatch.setattr('pipeline.adapters.finviz_adapter.FinvizAdapter',
                        _fake_adapter(_plausible('AAPL', 'MSFT')))
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
                        _fake_adapter(_plausible('AAPL')))
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
                        _fake_adapter(_plausible('AAPL', 'MSFT')))
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


def test_a_truncated_scrape_falls_back_to_the_stored_roster(monkeypatch, tmp_path):
    """抓漏的那一晚:沿用上一版名单继续算,而不是整晚读数变 NULL。

    这是存台账换来的新能力。在有台账之前,唯一的选择是 NULL(或者更糟 ——
    拿残缺名单硬算,静默给出一个偏掉的宽度读数)。
    """
    from pipeline.adapters import index_members_store as ims

    # 先建账:一个正常的名单
    good = _plausible('AAPL', 'MSFT')
    monkeypatch.setattr('pipeline.adapters.finviz_adapter.FinvizAdapter',
                        _fake_adapter(good))
    run_all.attach_index_membership(UNI.copy())
    assert len(ims.load_roster()) == len(good), "台账已建立"

    # 今晚翻页翻一半:只回来 3 只
    monkeypatch.setattr('pipeline.adapters.finviz_adapter.FinvizAdapter',
                        _fake_adapter({'AAPL', 'MSFT', 'PAD0001'}))
    uni = UNI.copy()
    run_all.attach_index_membership(uni)

    assert 'in_sp500' in uni.columns, "必须沿用上一版名单,不是放弃"
    assert uni['in_sp500'].tolist() == [True, True, False]
    assert len(ims.load_roster()) == len(good), "台账不许被残缺名单覆盖"


def test_no_stored_roster_and_a_bad_scrape_still_ships_null(monkeypatch):
    """没有台账可退时,残缺名单不许硬算 —— 宁可 NULL。

    反向对照:上一条的兜底不能变成「什么都放行」。
    """
    monkeypatch.setattr('pipeline.adapters.finviz_adapter.FinvizAdapter',
                        _fake_adapter({'AAPL', 'MSFT'}))
    uni = UNI.copy()
    run_all.attach_index_membership(uni)
    assert 'in_sp500' not in uni.columns


# ── Nasdaq-100 (T-0923-03: MCO/MCSI's standard pool) ─────────────────────
#
# Same shape as the S&P 500 tests above -- `attach_ndx_membership` is a
# separate function so these cannot regress the sp500 wiring, but the
# failure-domain and NULL-not-fallback guarantees must hold for it too.

def test_ndx_membership_lands_on_the_frame_breadth_reads(monkeypatch):
    monkeypatch.setattr('pipeline.adapters.finviz_adapter.FinvizAdapter',
                        _fake_adapter(_plausible_ndx('AAPL', 'MSFT')))
    uni = UNI.copy()
    run_all.attach_ndx_membership(uni)
    assert 'in_ndx' in uni.columns
    assert uni['in_ndx'].tolist() == [True, True, False]


def test_ndx_breadth_produces_ndx_columns_from_that_frame(monkeypatch):
    from pipeline.screeners import breadth_metrics

    monkeypatch.setattr('pipeline.adapters.finviz_adapter.FinvizAdapter',
                        _fake_adapter(_plausible_ndx('AAPL', 'MSFT')))
    uni = pd.DataFrame({
        'ticker': ['AAPL', 'MSFT', 'PENNY'],
        'change_pct': [1.0, -1.0, 0.5],
        'sma20_dist': [3.0, -2.0, 9.0],
        'sma40_dist': [3.0, -2.0, 9.0],
        'sma50_dist': [3.0, -2.0, 9.0],
        'sma200_dist': [3.0, 2.0, -9.0],
    })
    run_all.attach_ndx_membership(uni)
    snap = breadth_metrics.compute_snapshot(uni)

    assert snap['ndx_members'] == 2, "PENNY 不是 Nasdaq-100 成分股,不该进分母"
    assert snap['advances_ndx'] == 1   # AAPL up, MSFT down
    assert snap['declines_ndx'] == 1


def test_ndx_missing_column_ships_null_not_the_full_universe(monkeypatch):
    """反向对照:没有 in_ndx 列时必须 NULL,不能退回全池。"""
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
    for k in ('advances_ndx', 'declines_ndx', 'ndx_members'):
        assert snap[k] is None, f"{k} 应为 NULL,不是全池读数"


def test_ndx_fetch_failure_is_its_own_failure_domain(monkeypatch):
    class _Boom:
        def fetch_index_members(self, index):        # noqa: D102, ARG002
            raise RuntimeError("finviz down")
    monkeypatch.setattr('pipeline.adapters.finviz_adapter.FinvizAdapter', _Boom)
    uni = UNI.copy()
    run_all.attach_ndx_membership(uni)      # 不抛
    assert 'in_ndx' not in uni.columns


def test_ndx_empty_membership_leaves_the_column_absent(monkeypatch):
    monkeypatch.setattr('pipeline.adapters.finviz_adapter.FinvizAdapter',
                        _fake_adapter(set()))
    uni = UNI.copy()
    run_all.attach_ndx_membership(uni)
    assert 'in_ndx' not in uni.columns


def test_ndx_sp500_are_independent_columns(monkeypatch):
    """两条指数各自的失败域互不影响 —— 一个抓失败,另一个照样有值。"""
    calls = {}

    def _adapter(members_by_index):
        class _FA:
            def fetch_index_members(self, index):
                calls[index] = calls.get(index, 0) + 1
                return members_by_index[index]
        return _FA

    monkeypatch.setattr(
        'pipeline.adapters.finviz_adapter.FinvizAdapter',
        _adapter({'sp500': _plausible('AAPL'), 'ndx': _plausible_ndx('MSFT')}),
    )
    uni = UNI.copy()
    run_all.attach_index_membership(uni)
    run_all.attach_ndx_membership(uni)
    assert uni['in_sp500'].tolist() == [True, False, False]
    assert uni['in_ndx'].tolist() == [False, True, False]
