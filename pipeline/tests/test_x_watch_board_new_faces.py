"""候选闸「新进」判据切「新面孔人数」版(T-0927-66,README 09-25d·3 裁决)。

build_board.py `highlights()` 的「新进」判据原来是 `n >= 2 and o == 0`(昨天 0 人)。
09-27 起改成「新面孔人数」:今天≥2 人,且今天的人里至少 1 个不在昨天名单上。
两个方向都要验红:
  ① 漏改——总人数在降、且人是纯子集没换过(假设形状,⚠️ 不是 09-25 `$AMD` 的真实
     数据——那天真实数据里来了 1 位新面孔,新面孔版仍会选中它,理由是新面孔不是
     被排除),不该判新进。
  ② 改了但接错——总人数没涨甚至没变,但人全部或部分换了(09-14 `$GOOGL` 2→2、
     09-26 `$SMH` 1→2 的形状),该判新进却被漏掉。
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "data/content/x_watch/tools/build_board.py"
_spec = importlib.util.spec_from_file_location("x_watch_build_board_newfaces", _SRC)
bb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bb)


def _ticker(sym, days, cash=True, idx=False):
    return {"sym": sym, "cash": cash, "idx": idx, "days": days, "st": {}, "wall": []}


def _days(spec: dict[str, list[str]]) -> dict[str, dict]:
    return {d: {"p": sorted(p), "n": len(p), "v": 0} for d, p in spec.items()}


def _data(tickers, dates):
    return {"dates": dates, "tickers": tickers, "wall": []}


def _fresh_marks(data, sym):
    return [h["k"] for h in bb.highlights(data) if h["sym"] == sym]


# ── ① 漏改:降温但没换人,不该被判「新进」 ──────────────────────────────
def test_cooldown_same_people_shrinking_count_is_not_flagged_fresh():
    """纯降温假设形状(⚠️ 不是 09-25 `$AMD` 真实数据,那天真实数据带 1 位新面孔):
    昨天 {a,b,c} 3 人,今天剩 {a,b}(Δ-1,n 仍 >=2),没有新面孔。"""
    data = _data([_ticker("AMD", _days({
        "2026-09-24": ["a", "b", "c"],
        "2026-09-25": ["a", "b"],
    }))], ["2026-09-24", "2026-09-25"])
    assert _fresh_marks(data, "AMD") == []


def test_flat_count_same_people_is_not_flagged_fresh():
    """人数没变、人也没换(Δ=0,新面孔=0)——同样不该判新进。"""
    data = _data([_ticker("XYZ", _days({
        "2026-09-24": ["a", "b"],
        "2026-09-25": ["a", "b"],
    }))], ["2026-09-24", "2026-09-25"])
    assert _fresh_marks(data, "XYZ") == []


# ── ② 改了但接错:换人不换数,该判「新进」却被漏掉 ──────────────────────
def test_flat_growth_shape_all_new_faces_is_flagged_fresh():
    """09-26 `$SMH` 形状(此处换一个不在 INDEX 集合里的代码,避免撞上真实 ETF 过滤):
    前天/昨天都是 1 人(p),今天变成 2 个全新的人(q,r)。"""
    data = _data([_ticker("NEWCO", _days({
        "2026-09-24": ["p"],
        "2026-09-25": ["p"],
        "2026-09-26": ["q", "r"],
    }))], ["2026-09-24", "2026-09-25", "2026-09-26"])
    assert _fresh_marks(data, "NEWCO") == ["新进"]


def test_googl_shape_flat_total_all_turnover_is_flagged_fresh():
    """09-14 `$GOOGL` 真实案例形状:昨天 2 人,今天 2 个完全不同的人,总数没变。"""
    data = _data([_ticker("GOOGL", _days({
        "2026-09-13": ["Venu_7_", "ZaStocks"],
        "2026-09-14": ["Jake__Wujastyk", "TheProfInvestor"],
    }))], ["2026-09-13", "2026-09-14"])
    assert _fresh_marks(data, "GOOGL") == ["新进"]


def test_partial_overlap_with_one_new_face_is_flagged_fresh():
    """部分重叠也该算:昨天 {a,b},今天 {a,c}(c 是新面孔)。"""
    data = _data([_ticker("PARTIAL", _days({
        "2026-09-24": ["a", "b"],
        "2026-09-25": ["a", "c"],
    }))], ["2026-09-24", "2026-09-25"])
    assert _fresh_marks(data, "PARTIAL") == ["新进"]


def test_index_ticker_with_new_faces_is_labeled_index_entry_not_fresh():
    """指数/ETF 走「指数进场」标签,不是「新进」——判据切换不改变这条既有分支。"""
    data = _data([_ticker("SPY", _days({
        "2026-09-24": ["a"],
        "2026-09-25": ["b", "c"],
    }), idx=True)], ["2026-09-24", "2026-09-25"])
    assert _fresh_marks(data, "SPY") == ["指数进场"]


def test_first_day_with_no_prior_data_treats_everyone_as_new_faces():
    """首日(无昨天数据)人人都是新面孔,与旧「昨天 0 人」判据等价地触发新进。"""
    data = _data([_ticker("FIRSTDAY", _days({"2026-09-24": ["a", "b"]}))],
                ["2026-09-24"])
    assert _fresh_marks(data, "FIRSTDAY") == ["新进"]
