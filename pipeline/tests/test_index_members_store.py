"""成员台账:抓漏保护、变动流水、按日回放。

这个文件的主张是**抓漏保护**。Finviz 的成员页要翻 ~26 页,翻到一半失败会返回一个
**结构完好但内容残缺**的集合 —— 行数、类型、字段全都正常,只是少了几十只。
没有保护时那一晚会在台账里刻下「80 只同时被剔除」的假历史,第二晚它们又「加回来」。
所以每道闸都先注入对应的坏输入,确认它真的拦得住。
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from pipeline.adapters import index_members_store as ims


def _members(n: int, prefix: str = "T") -> set[str]:
    return {f"{prefix}{i:04d}" for i in range(n)}


@pytest.fixture
def paths(tmp_path: Path):
    return tmp_path / "roster.json", tmp_path / "log.csv"


def test_first_build_writes_everyone_without_tripping_the_churn_gate(paths):
    """首夜:503 只全是「新进」,变动量必然超阈值 —— 但不该被拦。

    ⚠️ 如果这条红了,说明台账**永远建不起来**:第一晚就被自己的闸挡住。
    """
    roster, log = paths
    cur = _members(503)
    out = ims.update(cur, "2026-09-10", roster, log)
    assert out["first_build"] is True
    assert out["members"] == 503
    assert len(out["added"]) == 503 and out["dropped"] == []
    assert len(ims.load_roster(roster)) == 503
    assert not log.exists(), "首建是快照不是 503 次变动,流水不该有行"


def test_normal_churn_is_recorded_in_the_log(paths):
    """正常换手:一进一出,流水记两行,名单更新。"""
    roster, log = paths
    ims.update(_members(503), "2026-09-10", roster, log)

    nxt = (_members(503) - {"T0000"}) | {"NEWCO"}
    out = ims.update(nxt, "2026-09-21", roster, log)
    assert out["added"] == ["NEWCO"] and out["dropped"] == ["T0000"]

    rows = list(csv.DictReader(log.open()))
    assert {(r["date"], r["action"], r["ticker"]) for r in rows} == {
        ("2026-09-21", "add", "NEWCO"), ("2026-09-21", "drop", "T0000")}


def test_first_seen_is_preserved_across_updates(paths):
    """老成员的 first_seen 不许被后来的日期覆盖 —— 那是它进指数的时间。"""
    roster, log = paths
    ims.update(_members(503), "2026-09-10", roster, log)
    ims.update((_members(503) - {"T0000"}) | {"NEWCO"}, "2026-09-21", roster, log)
    r = ims.load_roster(roster)
    assert r["T0001"] == "2026-09-10", "老成员保持原始日期"
    assert r["NEWCO"] == "2026-09-21", "新成员记新日期"


def test_a_truncated_scrape_is_rejected_and_changes_nothing(paths):
    """阳性对照:抓到 420 只(翻页翻一半失败)必须被拒,且**什么都不写**。"""
    roster, log = paths
    ims.update(_members(503), "2026-09-10", roster, log)
    before = ims.load_roster(roster)

    with pytest.raises(ims.MembershipRejected, match="抓漏"):
        ims.update(_members(420), "2026-09-11", roster, log)

    assert ims.load_roster(roster) == before, "名单必须原封不动"
    assert not log.exists(), "流水不许留下假的大换血"


def test_a_mass_churn_within_plausible_size_is_still_rejected(paths):
    """更阴的一种:名单**规模正常**(500 只),但换了 40 只。

    规模闸放行,只有变动量闸拦得住 —— 真实换手 ~22 只/年,一晚 40 只不是市场事件。
    """
    roster, log = paths
    ims.update(_members(503), "2026-09-10", roster, log)
    swapped = (_members(503) - _members(40)) | _members(40, prefix="X")
    with pytest.raises(ims.MembershipRejected, match="单晚变动"):
        ims.update(swapped, "2026-09-11", roster, log)


def test_churn_just_under_the_limit_passes(paths):
    """反向对照:阈值内的变动必须放行,否则这道闸会把真实调仓也拦掉。"""
    roster, log = paths
    ims.update(_members(503), "2026-09-10", roster, log)
    ok = (_members(503) - _members(7)) | _members(7, prefix="X")   # 进 7 出 7 = 14 <= 15
    out = ims.update(ok, "2026-09-11", roster, log)
    assert len(out["added"]) == 7 and len(out["dropped"]) == 7


def test_members_on_replays_history_instead_of_using_todays_list(paths):
    """按日回放:问 09-15 的名单,答案必须是**那天**的,不是今天的。

    这是存台账的理由之一 —— 没有它,任何历史回填都带幸存者偏差。
    """
    roster, log = paths
    ims.update(_members(503), "2026-09-10", roster, log)
    ims.update((_members(503) - {"T0000"}) | {"NEWCO"}, "2026-09-21", roster, log)

    now = ims.members_on("2026-09-30", log, roster)
    assert "NEWCO" in now and "T0000" not in now

    then = ims.members_on("2026-09-15", log, roster)
    assert "NEWCO" not in then, "09-15 时 NEWCO 还没进指数"
    assert "T0000" in then, "09-15 时 T0000 还在指数里"


def test_members_on_returns_none_before_the_log_starts(paths):
    """流水开始之前的日期:返回 None,不许拿今天的名单冒充。"""
    roster, log = paths
    ims.update(_members(503), "2026-09-10", roster, log)
    ims.update((_members(503) - {"T0000"}) | {"NEWCO"}, "2026-09-21", roster, log)
    assert ims.members_on("2026-01-01", log, roster) is None


def test_no_change_writes_no_log_row(paths):
    """名单没变的那些晚上不该在流水里留行 —— 流水是变动流水,不是心跳。"""
    roster, log = paths
    ims.update(_members(503), "2026-09-10", roster, log)
    n_before = len(list(csv.DictReader(log.open()))) if log.exists() else 0
    ims.update(_members(503), "2026-09-11", roster, log)
    n_after = len(list(csv.DictReader(log.open()))) if log.exists() else 0
    assert n_after == n_before


def test_unreadable_roster_is_treated_as_empty_not_a_crash(paths):
    """台账文件损坏时当空处理(重建),不许掀翻整晚产线。"""
    roster, log = paths
    roster.write_text("{ this is not json")
    assert ims.load_roster(roster) == {}
