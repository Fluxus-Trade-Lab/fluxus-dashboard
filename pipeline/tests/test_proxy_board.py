"""主题板的口径测试 —— 每条都对着「会怎么坏」造，不是对着「什么都没做」造。"""
import datetime as dt

import pandas as pd
import pytest

from pipeline.constants.theme_proxies import (RETIRED_FROM_BOARD, SCREEN_ONLY,
                                              THEME_PROXIES)
from pipeline.themes import proxy_board as PB


def mkseries(start="2026-06-01", n=140, step=0.0):
    idx = pd.bdate_range(start, periods=n)
    return pd.Series([100 * (1 + step) ** i for i in range(n)], index=idx)


def test_classify_puts_zero_momentum_on_the_positive_side():
    # 实测：他的 3383 行里有 3 行动能正好是 0，全部归 leading/improving。
    assert PB.classify(1.0, 0.0) == "leading"
    assert PB.classify(-1.0, 0.0) == "improving"
    assert PB.classify(1.0, -0.01) == "weakening"
    assert PB.classify(-1.0, -0.01) == "lagging"
    assert PB.classify(None, 1.0) is None


def test_buckets_are_14_calendar_days_not_10_sessions():
    bench = mkseries()
    anchor = bench.index[-1].date()
    edges = PB.bucket_edges(anchor, bench)
    # 每个桶界与锚点相差 14 的整数倍天（落到交易日后允许最多 4 天回退）
    for k, e in enumerate(edges):
        assert e is not None
        gap = (anchor - e).days
        assert 14 * k <= gap <= 14 * k + 4, (k, gap)


def test_edges_fall_back_to_the_last_trading_day_before_a_holiday():
    idx = pd.to_datetime(["2026-08-24", "2026-08-25", "2026-09-04", "2026-09-08",
                          "2026-09-21", "2026-09-22"])
    bench = pd.Series([1, 2, 3, 4, 5, 6], index=idx)
    # 锚点 09-22，往前 14 天是 09-08（在），28 天是 08-25（在）
    edges = PB.bucket_edges(dt.date(2026, 9, 22), bench, n=2)
    assert edges[:3] == [dt.date(2026, 9, 22), dt.date(2026, 9, 8), dt.date(2026, 8, 25)]


def test_excess_is_theme_minus_benchmark_over_the_same_window():
    idx = pd.to_datetime(["2026-09-08", "2026-09-22"])
    etf = pd.Series([100.0, 110.0], index=idx)     # +10%
    bench = pd.Series([100.0, 104.0], index=idx)   # +4%
    got = PB.excess(etf, bench, dt.date(2026, 9, 22), dt.date(2026, 9, 8))
    assert got == pytest.approx(10 / 1 - 4 / 1, abs=1e-9)


def test_build_marks_leading_when_this_bucket_beats_the_last():
    idx = pd.to_datetime(["2026-08-11", "2026-08-25", "2026-09-08", "2026-09-22"])
    bench = pd.Series([100.0, 100.0, 100.0, 100.0], index=idx)
    # 前一桶 +1%，本桶 +5% -> level>0 且 momentum>0 -> leading
    etf = pd.Series([100.0, 100.0, 101.0, 106.05], index=idx)
    out = PB.build({"T": "E"}, {"E": etf, "SPY": bench}, {"SPY": bench},
                   {"T": []}, {"T": "Weakening"}, anchor=dt.date(2026, 9, 22))
    row = out["themes"][0]
    assert row["state"] == "leading"
    assert row["state_prev"] == "Weakening"        # 并排期的旧读数要带着
    assert row["buckets"][0]["from"] == "2026-09-08"


def test_build_refuses_to_publish_without_the_benchmark():
    # 09-05 事故的形状：限流把 SPY 冲掉，板子不能"少个分母照样出"
    with pytest.raises(ValueError):
        PB.build({"T": "E"}, {"E": mkseries()}, {}, {"T": []}, {})


def test_member_distribution_counts_members_not_the_proxy():
    idx = pd.to_datetime(["2026-08-25", "2026-09-08", "2026-09-22"])
    bench = pd.Series([100.0, 100.0, 100.0], index=idx)
    up = pd.Series([100.0, 100.0, 110.0], index=idx)     # 本桶强、前桶平 -> leading
    down = pd.Series([100.0, 100.0, 90.0], index=idx)    # -> lagging
    edges = [dt.date(2026, 9, 22), dt.date(2026, 9, 8), dt.date(2026, 8, 25)]
    dist = PB.member_distribution(["A", "B", "C"], {"A": up, "B": down}, bench, edges)
    assert dist["leading"] == 1 and dist["lagging"] == 1
    assert dist["n/a"] == 1          # C 没有价格，要单独计，不能悄悄漏掉


def test_proxy_map_covers_the_taxonomy_exactly():
    from pipeline.themes.taxonomy import THEMES
    names = {t.name for t in THEMES}
    covered = set(THEME_PROXIES) | set(RETIRED_FROM_BOARD) | set(SCREEN_ONLY)
    assert names == covered, f"未处置的主题: {sorted(names ^ covered)}"


def test_retired_themes_are_not_on_the_board():
    for name in list(RETIRED_FROM_BOARD) + list(SCREEN_ONLY):
        assert name not in THEME_PROXIES


# ---- screener 层：个股对自己主题代理的相对强弱（只发原料，页面做减法）----

def test_plain_return_does_not_subtract_any_benchmark():
    idx = pd.to_datetime(["2026-09-08", "2026-09-22"])
    s = pd.Series([100.0, 110.0], index=idx)
    got = PB.plain_return(s, dt.date(2026, 9, 22), dt.date(2026, 9, 8))
    assert got == pytest.approx(10.0)          # 不是超额，是涨幅本身


def test_member_returns_are_keyed_by_ticker_not_by_theme_pair():
    """同一只票属于两个主题时只存一份——这正是不发 9,674 组配对的理由。"""
    idx = pd.to_datetime(["2026-08-25", "2026-09-08", "2026-09-22"])
    bench = pd.Series([100.0, 100.0, 100.0], index=idx)
    etf = pd.Series([100.0, 100.0, 105.0], index=idx)
    dual = pd.Series([100.0, 100.0, 120.0], index=idx)
    out = PB.build({"T1": "E", "T2": "E"}, {"E": etf, "SPY": bench},
                   {"DUAL": dual, "SPY": bench},
                   {"T1": ["DUAL"], "T2": ["DUAL"]}, {},
                   anchor=dt.date(2026, 9, 22))
    assert list(out["member_returns"]) == ["DUAL"]          # 一份，不是两份
    assert out["member_returns"]["DUAL"][0] == pytest.approx(20.0)
    for row in out["themes"]:
        assert row["proxy_ret"][0] == pytest.approx(5.0)    # 两个主题各自带代理涨幅


def test_the_two_primitives_reproduce_the_relative_reading():
    """页面那一次减法：票 20% − 代理 5% = 对主题超额 15pp。"""
    idx = pd.to_datetime(["2026-08-25", "2026-09-08", "2026-09-22"])
    bench = pd.Series([100.0, 100.0, 100.0], index=idx)
    etf = pd.Series([100.0, 102.0, 107.1], index=idx)     # 本桶 +5%，前桶 +2%
    stock = pd.Series([100.0, 101.0, 121.2], index=idx)   # 本桶 +20%，前桶 +1%
    out = PB.build({"T": "E"}, {"E": etf, "SPY": bench}, {"S": stock, "SPY": bench},
                   {"T": ["S"]}, {}, anchor=dt.date(2026, 9, 22))
    row = out["themes"][0]
    mr = out["member_returns"]["S"]
    excess_now = mr[0] - row["proxy_ret"][0]
    excess_prev = mr[1] - row["proxy_ret"][1]
    assert excess_now == pytest.approx(15.0, abs=0.02)
    assert PB.classify(excess_now, excess_now - excess_prev) == "leading"


def test_a_member_with_no_price_is_left_out_not_zero_filled():
    idx = pd.to_datetime(["2026-08-25", "2026-09-08", "2026-09-22"])
    bench = pd.Series([100.0, 100.0, 100.0], index=idx)
    etf = pd.Series([100.0, 100.0, 105.0], index=idx)
    out = PB.build({"T": "E"}, {"E": etf, "SPY": bench}, {"SPY": bench},
                   {"T": ["GHOST"]}, {}, anchor=dt.date(2026, 9, 22))
    assert "GHOST" not in out["member_returns"]   # 缺价的票不许以 0 出现在排名里
