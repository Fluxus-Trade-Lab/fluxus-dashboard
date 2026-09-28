"""候选闸判据 C(新面孔人数)——`compare_candidate_rules.py` 侧的实装验收(T-0927-66)。

Steve 09-27 裁决(README 09-25d·3):切「新面孔人数」版,不切字面版(判据 B,
只看 Δ人数≠0、不分方向)。两个方向都要验红:
  ① 漏改——降温且没换人(总数降、今天的人是昨天名单的纯子集),B 会误选,
    C 必须正确排除。⚠️ 这是纯假设形状,不是 09-25 `$AMD`/`$INTC` 的真实数据
    ——那两票当天各带 1 位新面孔,真实数据下 C 仍会选中它们(理由是新面孔,
    不是被排除);本窗口该形状的真实个案数是 0(见 `cooldown_scan`)。
  ② 改了但接错——换人不换数(09-14 `$GOOGL`、09-21/09-24 `$MU` 这类),
    A、字面 B 都接不住,C 必须靠「有新面孔」接住。
"""
from __future__ import annotations

import importlib.util
from datetime import date
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "data/content/x_watch/tools/compare_candidate_rules.py"
_spec = importlib.util.spec_from_file_location("x_watch_compare_candidate_rules", _SRC)
ccr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ccr)


def _row(d, sym, handle, stance="long", post_id=None):
    return {"date": d, "ticker": sym, "handle": handle, "stance": stance,
            "post_id": post_id or f"{d}-{sym}-{handle}"}


# ── ① 漏改:降温但没换人,C 必须排除(B 会误选) ──────────────────────────
def test_amd_cooldown_same_people_is_not_a_candidate_under_c():
    """纯降温假设形状:09-24 三人 long(a,b,c),09-25 剩 a,b(Δ-1,n 仍 >=2),
    没有新面孔。⚠️ 不是 09-25 `$AMD` 的真实数据(真实数据里那天来了 1 位新面孔,
    C 仍会选中它)——这里构造的是「一位新面孔都没有」的更极端边界,验证判据 C
    真的会因为「无新面孔」而排除,不是巧合地排除。"""
    rows = [
        _row("2026-09-24", "AMD", "a"), _row("2026-09-24", "AMD", "b"),
        _row("2026-09-24", "AMD", "c"),
        _row("2026-09-25", "AMD", "a"), _row("2026-09-25", "AMD", "b"),
    ]
    report = ccr.compare(rows, date(2026, 9, 24), date(2026, 9, 25))
    day = next(r for r in report if r["date"] == "2026-09-25")
    assert "AMD" not in day["c"], f"降温、无新面孔的票不该进判据 C 候选表,实际 {day['c']}"
    assert "AMD" in day["b"]  # 字面版(B)会把它误选——这正是切换判据的理由


def test_cooldown_scan_confirms_b_false_positive_c_correctly_excludes():
    rows = [
        _row("2026-09-24", "AMD", "a"), _row("2026-09-24", "AMD", "b"),
        _row("2026-09-24", "AMD", "c"),
        _row("2026-09-25", "AMD", "a"), _row("2026-09-25", "AMD", "b"),
    ]
    hits = ccr.cooldown_scan(rows, date(2026, 9, 24), date(2026, 9, 25))
    assert len(hits) == 1
    assert hits[0]["sym"] == "AMD"
    assert hits[0]["caught_by_b"] is True
    assert hits[0]["caught_by_c"] is False


# ── ② 改了但接错:换人不换数,C 必须接住(A、字面 B 都接不住) ────────────
def test_googl_turnover_shape_is_a_candidate_under_c_not_under_a_or_b():
    """09-14 `$GOOGL` 真实案例:09-13 两人,09-14 换成两个完全不同的人,总数没变(Δ=0)。"""
    rows = [
        _row("2026-09-13", "GOOGL", "Venu_7_"), _row("2026-09-13", "GOOGL", "ZaStocks"),
        _row("2026-09-14", "GOOGL", "Jake__Wujastyk"),
        _row("2026-09-14", "GOOGL", "TheProfInvestor"),
    ]
    report = ccr.compare(rows, date(2026, 9, 13), date(2026, 9, 14))
    day = next(r for r in report if r["date"] == "2026-09-14")
    assert "GOOGL" in day["c"], f"换人不换数的真新面孔该进判据 C 候选表,实际 {day['c']}"
    assert "GOOGL" not in day["b"]  # Δ=0,字面版(B)接不住
    # 判据 A:09-13 那天 GOOGL 已经是候选(2 人),09-14 因为「昨天已候选过」被 A 排除
    day13 = next(r for r in report if r["date"] == "2026-09-13")
    assert "GOOGL" in day13["a"]
    assert "GOOGL" not in day["a"]


def test_turnover_scan_all_full_turnover_cases_caught_by_c():
    rows = [
        _row("2026-09-13", "GOOGL", "Venu_7_"), _row("2026-09-13", "GOOGL", "ZaStocks"),
        _row("2026-09-14", "GOOGL", "Jake__Wujastyk"),
        _row("2026-09-14", "GOOGL", "TheProfInvestor"),
    ]
    hits = ccr.turnover_scan(rows, date(2026, 9, 13), date(2026, 9, 14))
    assert len(hits) == 1
    assert hits[0]["caught_by_a"] is False
    assert hits[0]["caught_by_b"] is False
    assert hits[0]["caught_by_c"] is True


def test_flat_growth_shape_with_new_faces_is_caught_by_c():
    """09-26 `$SMH` 形状(此处换一个不在 INDEX 集合里的代码,避免撞上真实 ETF 过滤):
    09-24/09-25 都是同一人 p(1 人,过不了闸),09-26 变成 2 个新人。"""
    rows = [
        _row("2026-09-24", "NEWCO", "p"),
        _row("2026-09-25", "NEWCO", "p"),
        _row("2026-09-26", "NEWCO", "q"), _row("2026-09-26", "NEWCO", "r"),
    ]
    report = ccr.compare(rows, date(2026, 9, 24), date(2026, 9, 26))
    day = next(r for r in report if r["date"] == "2026-09-26")
    assert "NEWCO" in day["c"]
    assert day["c"]["NEWCO"] == (2, 2)  # 2 人,2 个都是新面孔


def test_list_post_and_index_and_stance_filters_still_apply_to_candidate_c():
    """判据 C 复用与 A/B 相同的前三关(剔清单帖、剔指数、立场 long/watching),不是另起炉灶。"""
    rows = [
        _row("2026-09-24", "SPY", "a", stance="long"),
        _row("2026-09-24", "SPY", "b", stance="long"),  # 指数,剔
        _row("2026-09-24", "NFLX", "c", stance="recap"),
        _row("2026-09-24", "NFLX", "d", stance="recap"),  # 立场不合格,剔
    ]
    report = ccr.compare(rows, date(2026, 9, 24), date(2026, 9, 24))
    day = report[0]
    assert day["c"] == {}
