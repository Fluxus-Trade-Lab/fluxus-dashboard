"""X 台账的结构三列（RS 评级 · 距 50 日线% · 所属 ETF 篮子）与 `data/output/x_heat.json`。

三列全部是 dashboard 管线已经算好的字段，这里只做 join，**不新算指标**。所以测试钉住的
不是算术，是三件会悄悄坏掉的事：

* **查不到就写「无」，永不写 0** —— RS 评级 0 分是一个真读数（全市场最弱），
  「我们没查到这只票」是另一件事。两者一旦混成同一个格子，就再也分不开，
  而筛「RS ≥ 80」时它们表现得完全一样（都被筛掉），没有任何东西会报红。
* **多篮子全留** —— 一只票同时属于 4 个 ETF 篮子（09-23 实测 `$TSLA`）。取第一个会让
  同一只票在不同跑次里换篮子，而「它在几个篮子里」本身就是读数。
* **x_heat 的人数是跨日去重的人，不是日人数相加** —— 同一个人连说 7 天不是 7 个人。
  这一列将来要上 dashboard 个股页，读它的人不会回来看这份口径。
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "data/content/x_watch/tools/build_board.py"
_spec = importlib.util.spec_from_file_location("x_watch_build_board_struct", _SRC)
bb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bb)


def _write(tmp_path: Path, universe=None, signals=None, groups=None):
    u, s, g = tmp_path / "universe.json", tmp_path / "signals.json", tmp_path / "groups.json"
    if universe is not None:
        u.write_text(json.dumps({"rows": universe}))
    if signals is not None:
        s.write_text(json.dumps({"rows": signals}))
    if groups is not None:
        g.write_text(json.dumps({"themes": groups}))
    return u, s, g


def _days(spec: dict[str, list[str]]) -> dict[str, dict]:
    """{日期: [handle…]} → build() 里 days 的形状。"""
    return {d: {"p": sorted(p), "n": len(p), "v": 0} for d, p in spec.items()}


# ── 三列各自从哪个字段来 ──────────────────────────────────────────────────
def test_rs_and_dist50_come_from_universe_fields(tmp_path):
    u, s, g = _write(
        tmp_path,
        universe=[{"ticker": "AAA", "rs_rating": 97, "sma50_dist": 0.1406}],
        groups=[])
    idx = bb.load_structure(u, s, g)
    assert idx["AAA"]["rs"] == 97
    assert idx["AAA"]["d50"] == 0.1406
    assert bb.rs_cell(idx["AAA"]["rs"]) == "97"
    # 小数 → 百分比，带符号；这是唯一的换算，没有别的加工
    assert bb.d50_cell(idx["AAA"]["d50"]) == "+14.06%"


def test_baskets_come_from_groups_themes_with_method_etf(tmp_path):
    u, s, g = _write(
        tmp_path, universe=[],
        groups=[{"group": "Cloud Software", "method": "etf", "tickers": ["AAA", "BBB"]},
                {"group": "Semis", "method": "etf", "tickers": ["AAA"]},
                # 行业组和规则组不是「ETF 篮子」，不许混进这一列
                {"group": "Oil Refining", "method": "industry", "tickers": ["AAA"]},
                {"group": "Growth Factor", "method": "rule", "tickers": ["AAA"]}])
    idx = bb.load_structure(u, s, g)
    assert idx["AAA"]["bask"] == ["Cloud Software", "Semis"]
    assert "Oil Refining" not in idx["AAA"]["bask"]


def test_index_etfs_fall_back_to_asset_signals_for_dist50(tmp_path):
    """SPY/QQQ 不在 universe 里，距 50 日线走 asset_signals 的同名字段。"""
    u, s, g = _write(tmp_path, universe=[],
                     signals=[{"ticker": "SPY", "sma50_dist": 0.0192}], groups=[])
    idx = bb.load_structure(u, s, g)
    assert idx["SPY"]["d50"] == 0.0192
    assert idx["SPY"]["rs"] is None          # 那份没有 RS 评级 → 无，不许造一个


def test_universe_wins_over_signals_for_a_ticker_in_both(tmp_path):
    u, s, g = _write(tmp_path,
                     universe=[{"ticker": "AAA", "rs_rating": 91, "sma50_dist": 0.10}],
                     signals=[{"ticker": "AAA", "sma50_dist": 0.99}], groups=[])
    assert bb.load_structure(u, s, g)["AAA"]["d50"] == 0.10


# ── 缺字段一律「无」，不是 0 ──────────────────────────────────────────────
def test_missing_fields_render_as_none_not_zero(tmp_path):
    u, s, g = _write(tmp_path, universe=[{"ticker": "AAA"}], groups=[])
    idx = bb.load_structure(u, s, g)
    assert (idx["AAA"]["rs"], idx["AAA"]["d50"], idx["AAA"]["bask"]) == (None, None, [])
    assert bb.rs_cell(None) == "无"
    assert bb.d50_cell(None) == "无"
    assert bb.bask_cell([]) == "无"


def test_zero_rs_is_a_reading_and_must_not_read_as_missing(tmp_path):
    """阳性对照：RS 真的是 0 时必须印出 0，不能被「无」吞掉。"""
    assert bb.rs_cell(0) == "0"
    assert bb.d50_cell(0.0) == "+0.00%"


def test_ticker_absent_everywhere_gets_all_three_as_missing(tmp_path):
    u, s, g = _write(tmp_path, universe=[{"ticker": "AAA", "rs_rating": 80}], groups=[])
    rows = [{"sym": "ZZZ", "days": {}}]
    bb.attach_structure(rows, u, s, g)
    assert rows[0] == {"sym": "ZZZ", "days": {}, "rs": None, "d50": None, "bask": []}


def test_absent_files_do_not_crash_the_board(tmp_path):
    """data/output 还没生成时，看板要照出，三列全「无」。"""
    idx = bb.load_structure(tmp_path / "nope.json", tmp_path / "nope2.json",
                            tmp_path / "nope3.json")
    assert idx == {}


# ── 多归属 ────────────────────────────────────────────────────────────────
def test_multi_basket_membership_keeps_every_basket_sorted(tmp_path):
    u, s, g = _write(
        tmp_path, universe=[],
        groups=[{"group": "Semis", "method": "etf", "tickers": ["TSLA"]},
                {"group": "EV", "method": "etf", "tickers": ["TSLA"]},
                {"group": "Tech Mega Caps", "method": "etf", "tickers": ["TSLA"]},
                {"group": "High Octane", "method": "etf", "tickers": ["TSLA"]}])
    bask = bb.load_structure(u, s, g)["TSLA"]["bask"]
    assert bask == ["EV", "High Octane", "Semis", "Tech Mega Caps"]   # 四个都在，排序固定
    assert bb.bask_cell(bask) == "EV / High Octane / Semis / Tech Mega Caps"


def test_same_basket_listed_twice_is_not_double_counted(tmp_path):
    u, s, g = _write(tmp_path, universe=[],
                     groups=[{"group": "Semis", "method": "etf", "tickers": ["AAA", "AAA"]},
                             {"group": "Semis", "method": "etf", "tickers": ["AAA"]}])
    assert bb.load_structure(u, s, g)["AAA"]["bask"] == ["Semis"]


# ── x_heat.json 的形状 ────────────────────────────────────────────────────
def _data(tickers, dates):
    return {"dates": dates, "tickers": tickers}


def test_x_heat_shape_and_required_keys():
    data = _data([{"sym": "AAA", "cash": True, "idx": False,
                   "days": _days({"2026-09-22": ["a", "b"]})}], ["2026-09-22"])
    h = bb.x_heat(data, window=7)
    assert set(h) == {"window_days", "window", "count", "source", "note", "rows"}
    assert h["window_days"] == 7 and h["count"] == 1
    assert h["window"] == {"start": "2026-09-22", "end": "2026-09-22"}
    assert set(h["rows"][0]) == {"ticker", "people_7d", "posts_7d", "days_7d",
                                 "peak_day", "peak_people", "is_index"}


def test_x_heat_people_are_deduped_across_days_not_summed():
    """同一个人连说三天是 1 个人，不是 3 个。"""
    data = _data([{"sym": "AAA", "cash": True, "idx": False,
                   "days": _days({"2026-09-20": ["a"], "2026-09-21": ["a"],
                                  "2026-09-22": ["a", "b"]})}],
                 ["2026-09-20", "2026-09-21", "2026-09-22"])
    r = bb.x_heat(data)["rows"][0]
    assert r["people_7d"] == 2          # {a, b}
    assert r["days_7d"] == 3
    assert r["peak_people"] == 2


def test_x_heat_window_cuts_to_the_last_n_days():
    days = _days({f"2026-09-{d:02d}": ["a"] for d in range(10, 23)})
    dates = sorted(days)
    data = _data([{"sym": "AAA", "cash": True, "idx": False, "days": days}], dates)
    h = bb.x_heat(data, window=7)
    assert h["window"] == {"start": dates[-7], "end": dates[-1]}
    assert h["rows"][0]["days_7d"] == 7          # 窗口外那 6 天不算进来


def test_x_heat_peak_day_ties_go_to_the_earliest_day():
    data = _data([{"sym": "AAA", "cash": True, "idx": False,
                   "days": _days({"2026-09-21": ["a", "b"], "2026-09-20": ["c", "d"]})}],
                 ["2026-09-20", "2026-09-21"])
    assert bb.x_heat(data)["rows"][0]["peak_day"] == "2026-09-20"


def test_x_heat_skips_bare_codes_and_tickers_with_no_mentions_in_window():
    data = _data([{"sym": "RS", "cash": False, "idx": False,        # 裸代码噪声
                   "days": _days({"2026-09-22": ["a"]})},
                  {"sym": "OLD", "cash": True, "idx": False,        # 提及全在窗口外
                   "days": _days({"2026-08-01": ["a"]})},
                  {"sym": "AAA", "cash": True, "idx": False,
                   "days": _days({"2026-09-22": ["a"]})}],
                 ["2026-09-22"])
    assert [r["ticker"] for r in bb.x_heat(data)["rows"]] == ["AAA"]


def test_x_heat_sorted_by_people_desc():
    data = _data([{"sym": "LOW", "cash": True, "idx": False,
                   "days": _days({"2026-09-22": ["a"]})},
                  {"sym": "HIGH", "cash": True, "idx": False,
                   "days": _days({"2026-09-22": ["a", "b", "c"]})}],
                 ["2026-09-22"])
    assert [r["ticker"] for r in bb.x_heat(data)["rows"]] == ["HIGH", "LOW"]
