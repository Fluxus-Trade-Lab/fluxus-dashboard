"""第7章「5日涨≥20%」家数脚本的口径测试（T-1003-68）。

脚本在 data/research/course_ch07/count_5d20.py，不是包，按路径加载。
"""
import importlib.util
from pathlib import Path

import pandas as pd

_SCRIPT = Path(__file__).resolve().parents[2] / "data/research/course_ch07/count_5d20.py"
_spec = importlib.util.spec_from_file_location("count_5d20", _SCRIPT)
count_5d20 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(count_5d20)


def _panel(prices: dict[str, list[float]], volume: float = 1e7):
    idx = pd.bdate_range("2024-01-02", periods=len(next(iter(prices.values()))))
    close = pd.DataFrame(prices, index=idx)
    vol = pd.DataFrame(volume, index=idx, columns=close.columns)
    return close, vol


def test_five_bar_gain_at_boundary_counts_and_below_does_not():
    # AAA: 第 6 根收盘 121，相对 5 根前的 100 为 +21%（计入）；BBB 为 +19%（不计）；
    # CCC 恰好 +20%（计入，口径是 ≥）
    close, vol = _panel({
        "AAA": [100, 100, 100, 100, 100, 121],
        "BBB": [100, 100, 100, 100, 100, 119],
        "CCC": [100, 100, 100, 100, 100, 120],
    })
    out = count_5d20.daily_counts(close, vol, cap={"AAA": 2e9, "BBB": 2e9, "CCC": 2e9})
    last = out.iloc[-1]
    assert last["n_hit_all"] == 2
    assert out.iloc[0]["n_valid"] == 0  # 前 5 根没有回看价，不计入分母


def test_cap_gate_only_counts_one_billion_and_up():
    close, vol = _panel({
        "BIG": [100, 100, 100, 100, 100, 130],
        "SMALL": [100, 100, 100, 100, 100, 130],
    })
    out = count_5d20.daily_counts(close, vol, cap={"BIG": 5e9, "SMALL": 5e8})
    last = out.iloc[-1]
    assert last["n_hit_all"] == 2
    assert last["n_hit_cap1b"] == 1


def test_liquid_subset_needs_price_five_and_twenty_day_dollar_volume():
    # 低价票 +30% 但收盘 $3，不进流动性子集；成交额不足的票进不了
    prices = [10] * 25 + [13]
    close, vol = _panel({"HI": prices, "LOWPX": [3 * p / 10 for p in prices],
                         "THIN": prices}, volume=1e7)
    vol["THIN"] = 1e4  # 20 日均额 = 10 × 1e4 = 1e5 < 5e6
    out = count_5d20.daily_counts(close, vol, cap={})
    last = out.iloc[-1]
    assert last["n_hit_all"] == 3
    assert last["n_hit_liquid"] == 1
