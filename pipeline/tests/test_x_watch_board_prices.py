"""X 台账的「提及峰值日后 T+k 相对 SPY」两列。

口径登记在 `data/reference/METRIC_SOURCES.md`（event study 的 market-adjusted
model，AR_it = R_it − R_mt）。这里钉住三件最容易悄悄坏掉的事：

* **峰值日并列取最早** —— 并列时如果随字典序/插入序漂，同一份数据换个读取顺序
  就会换一个锚点，两次跑出来的读数对不上，而没有任何东西会报红。
* **本地没有行情的票写「无价格」** —— 不是 0、不是空。0% 的意思是「跟上基准」，
  跟「我们没有这只票的价格」是两件事，混成一格就再也分不开。
* **基准缺失必须抛错** —— `method_denominator_is_not_optional`：分母不是可选输入。
  SPY 取不到时静默当 0，出来的每一格都会变成「个股的绝对收益」冒充相对收益。
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[2] / "data/content/x_watch/tools/build_board.py"
_spec = importlib.util.spec_from_file_location("x_watch_build_board", _SRC)
bb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bb)


# ── 一段固定的假行情：交易日历只有这 8 天（含一个周末缺口）────────────────
CAL = ["2026-09-04",  # 周五
       "2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11",
       "2026-09-14", "2026-09-15", "2026-09-16"]
SPY = {d: 100.0 for d in CAL}          # 基准一路走平，便于手算
SPY["2026-09-09"] = 101.0              # T+1 那天基准 +1%


def _write(tmp_path: Path, tickers: dict[str, dict], baskets: dict[str, dict]):
    td, bd = tmp_path / "tickers", tmp_path / "baskets"
    td.mkdir(parents=True); bd.mkdir(parents=True)
    for sym, closes in tickers.items():
        (td / f"{sym}.json").write_text(json.dumps(
            {"ohlc_2y": [{"date": d, "close": c} for d, c in sorted(closes.items())]}))
    for sym, closes in baskets.items():
        (bd / f"{sym}.json").write_text(json.dumps(
            {"bars": [{"date": d, "close": c} for d, c in sorted(closes.items())]}))
    return td, bd


def _days(spec: dict[str, int]) -> dict[str, dict]:
    """{日期: 人数} → build() 里 days 的形状。"""
    return {d: {"p": [f"h{i}" for i in range(n)], "n": n, "v": 0}
            for d, n in spec.items()}


# ── 峰值日 ────────────────────────────────────────────────────────────────
def test_peak_day_picks_the_single_max():
    assert bb.peak_day(_days({"2026-09-08": 1, "2026-09-09": 4, "2026-09-10": 2})) \
        == "2026-09-09"


def test_peak_day_breaks_ties_to_the_earliest_day():
    """三天并列 4 人 —— 必须是最早那天，而且插入顺序倒过来也一样。"""
    spec = {"2026-09-10": 4, "2026-09-08": 4, "2026-09-09": 4, "2026-09-04": 1}
    assert bb.peak_day(_days(spec)) == "2026-09-08"
    assert bb.peak_day(_days(dict(reversed(list(spec.items()))))) == "2026-09-08"


def test_peak_day_none_when_no_mention_day():
    assert bb.peak_day({}) is None
    assert bb.peak_day(_days({"2026-09-08": 0})) is None


# ── 相对收益的算术 ────────────────────────────────────────────────────────
def test_rel_is_stock_return_minus_bench_return():
    # 锚 09-08=100 → T+1 09-09 个股 110（+10%），基准 +1% ⇒ +9.00
    closes = dict.fromkeys(CAL, 100.0) | {"2026-09-09": 110.0}
    v, why = bb.rel_vs_bench(closes, SPY, CAL, "2026-09-08", 1)
    assert why == "ok"
    assert v == pytest.approx(9.0, abs=1e-9)


def test_rel_counts_trading_days_not_calendar_days():
    """09-04 是周五，T+1 必须是 09-08 而不是日历上的 09-05。"""
    closes = dict.fromkeys(CAL, 100.0) | {"2026-09-08": 105.0}
    v, why = bb.rel_vs_bench(closes, SPY, CAL, "2026-09-04", 1)
    assert (why, round(v, 9)) == ("ok", 5.0)


def test_anchor_is_the_last_close_at_or_before_a_non_trading_peak_day():
    """周末提及（09-06）锚在上周五 09-04 收盘，T+1 落到 09-08。"""
    closes = dict.fromkeys(CAL, 100.0) | {"2026-09-08": 105.0}
    assert bb.rel_vs_bench(closes, SPY, CAL, "2026-09-06", 1)[0] == pytest.approx(5.0)


def test_horizon_beyond_the_calendar_is_not_yet_due():
    closes = dict.fromkeys(CAL, 100.0)
    assert bb.rel_vs_bench(closes, SPY, CAL, "2026-09-15", 5) == (None, "未到期")


def test_peak_before_the_first_bar_has_no_anchor():
    closes = dict.fromkeys(CAL, 100.0)
    assert bb.rel_vs_bench(closes, SPY, CAL, "2026-08-01", 1) == (None, "无基准日")


def test_missing_bar_on_either_end_is_not_zero():
    closes = {d: 100.0 for d in CAL if d != "2026-09-09"}
    assert bb.rel_vs_bench(closes, SPY, CAL, "2026-09-08", 1) == (None, "缺K线")


# ── 缺价格 / 缺基准 ───────────────────────────────────────────────────────
def test_ticker_without_local_prices_is_labelled_not_zeroed(tmp_path):
    td, bd = _write(tmp_path, {"AAA": dict.fromkeys(CAL, 100.0)}, {"SPY": SPY})
    rows = [{"sym": "AAA", "days": _days({"2026-09-08": 2})},
            {"sym": "ZZZ", "days": _days({"2026-09-08": 2})}]   # 本地没有 ZZZ
    bb.attach_prices(rows, td, bd)
    assert rows[1]["rel"][1] == (None, "无价格")
    assert bb.price_cell(*rows[1]["rel"][1]) == "无价格"
    # AAA 走平而基准当天 +1% ⇒ −1.00%：有价格就写百分比，且分母真的在减
    assert bb.price_cell(*rows[0]["rel"][1]) == "-1.00%"


def test_missing_benchmark_raises_instead_of_silently_using_zero(tmp_path):
    td, bd = _write(tmp_path, {"AAA": dict.fromkeys(CAL, 100.0)}, {})  # 没有 SPY
    rows = [{"sym": "AAA", "days": _days({"2026-09-08": 2})}]
    with pytest.raises(RuntimeError, match="SPY"):
        bb.attach_prices(rows, td, bd)


def test_empty_benchmark_file_also_raises(tmp_path):
    """SPY 文件在、但 bars 是空的 —— 同样不许放行。"""
    td, bd = _write(tmp_path, {"AAA": dict.fromkeys(CAL, 100.0)}, {"SPY": {}})
    with pytest.raises(RuntimeError):
        bb.attach_prices([{"sym": "AAA", "days": _days({"2026-09-08": 2})}], td, bd)


def test_benchmark_is_read_from_baskets_and_used_as_the_denominator(tmp_path):
    """基准单独取、单独验：换掉 SPY 的数，每一格读数必须跟着变。"""
    stock = dict.fromkeys(CAL, 100.0) | {"2026-09-09": 110.0}
    td, bd = _write(tmp_path, {"AAA": stock}, {"SPY": SPY})
    rows = [{"sym": "AAA", "days": _days({"2026-09-08": 3})}]
    bb.attach_prices(rows, td, bd)
    assert rows[0]["peak"] == "2026-09-08"
    assert rows[0]["rel"][1][0] == pytest.approx(9.0)

    flat = dict.fromkeys(CAL, 100.0)
    td2, bd2 = _write(tmp_path / "b", {"AAA": stock}, {"SPY": flat})
    rows2 = [{"sym": "AAA", "days": _days({"2026-09-08": 3})}]
    bb.attach_prices(rows2, td2, bd2)
    assert rows2[0]["rel"][1][0] == pytest.approx(10.0)


def test_no_mention_day_reports_its_own_reason(tmp_path):
    """墙后独有的票（公开区零提及）没有峰值日，不能顶替成「无价格」。"""
    td, bd = _write(tmp_path, {"AAA": dict.fromkeys(CAL, 100.0)}, {"SPY": SPY})
    rows = [{"sym": "AAA", "days": {}}]
    bb.attach_prices(rows, td, bd)
    assert rows[0]["peak"] is None
    assert rows[0]["rel"][5] == (None, "无提及日")
