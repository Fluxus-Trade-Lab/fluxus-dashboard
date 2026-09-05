"""audit_event_agreement 的测试。

体例上要求自己做到两件，因为这个仓库栽过：
  * **真阳性对照** —— 注射一个真的分歧，闸必须红。一条只会绿的断言是装饰
    （协议：红得不是地方 / 注射了却全绿=那条断言是装饰）。
  * **不读自己的常量** —— 断言里写死字段名和数字，不引 `A.FIELDS`；
    否则改了常量测试跟着一起动，永远不会红
    （协议：读自己那个常量的测试永远不会红）。
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from pipeline.tools import audit_event_agreement as A

HEAD = ["date", "ticker", "screener", "group", "change_pct",
        "rel_volume", "volume", "sector", "atr_ext"]


def _write(tmp_path: Path, rows: list[dict], name: str = "events.csv") -> Path:
    p = tmp_path / name
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=HEAD)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in HEAD})
    return p


def _row(date, ticker, screener, **kw):
    return {"date": date, "ticker": ticker, "screener": screener, **kw}


CLEAN = [
    _row("2026-09-01", "AAA", "gainers_4pct", change_pct="0.0500", volume="1000000",
         sector="Technology", atr_ext="1.2"),
    _row("2026-09-01", "AAA", "preset:sugar_babies", change_pct="0.0500", volume="1000000",
         sector="Technology", atr_ext="1.2"),
    _row("2026-09-01", "BBB", "vcp", sector="Energy"),
    _row("2026-09-02", "AAA", "gainers_4pct", change_pct="0.0100", volume="900000",
         sector="Technology", atr_ext="0.8"),
]


# ---------- 阴性：干净的归档必须绿 ----------

def test_a_clean_archive_has_no_violations(tmp_path):
    res = A.audit(_write(tmp_path, CLEAN), declared={})
    assert res["violations"] == []
    assert res["disagreements"] == {}


def test_the_two_screeners_that_agree_still_count_as_compared(tmp_path):
    """闸必须真的比过 —— 否则「零违规」可能只是「零比较」。"""
    res = A.audit(_write(tmp_path, CLEAN), declared={})
    assert res["pairs_checked"] == 4   # AAA@09-01 的 change_pct / volume / sector / atr_ext


# ---------- 真阳性对照：注射一个分歧，必须红 ----------

def test_an_injected_disagreement_on_an_undeclared_date_goes_red(tmp_path):
    rows = CLEAN + [_row("2026-09-03", "CCC", "gainers_4pct", change_pct="0.0700"),
                    _row("2026-09-03", "CCC", "preset:pp_count", change_pct="0.0000")]
    res = A.audit(_write(tmp_path, rows), declared={})
    assert [c for c, _ in res["violations"]] == ["E1"]
    assert "2026-09-03" in res["violations"][0][1]


def test_the_positive_control_replays_the_real_08_17_numbers(tmp_path):
    """EROC 的真数：gainers_4pct +4.07%，preset 那边 +9.33%（= 它 08-14 的涨幅）。"""
    rows = [_row("2026-08-17", "EROC", "gainers_4pct", change_pct="0.0407"),
            _row("2026-08-17", "EROC", "preset:vol_up_gainers", change_pct="0.0933")]
    res = A.audit(_write(tmp_path, rows), declared={})
    assert [c for c, _ in res["violations"]] == ["E1"]
    bad = res["disagreements"]["2026-08-17"]
    assert [x["ticker"] for x in bad] == ["EROC"]
    assert sorted(bad[0]["readings"]) == [0.0407, 0.0933]


def test_the_positive_control_replays_the_real_08_14_volume(tmp_path):
    """NN 的真数：302 股 vs 2,244,694 股，同一天同一只票。"""
    rows = [_row("2026-08-14", "NN", "gainers_4pct", volume="302"),
            _row("2026-08-14", "NN", "preset:weekly_20_gainers", volume="2244694")]
    res = A.audit(_write(tmp_path, rows), declared={})
    assert [c for c, _ in res["violations"]] == ["E1"]
    assert res["disagreements"]["2026-08-14"][0]["field"] == "volume"


def test_a_disagreement_in_a_string_field_is_caught_too(tmp_path):
    rows = [_row("2026-09-03", "CCC", "vcp", sector="Energy"),
            _row("2026-09-03", "CCC", "healthy_charts", sector="Technology")]
    res = A.audit(_write(tmp_path, rows), declared={})
    assert res["disagreements"]["2026-09-03"][0]["field"] == "sector"


# ---------- 声明与棘轮 ----------

def test_a_declared_date_is_green(tmp_path):
    rows = CLEAN + [_row("2026-09-03", "CCC", "gainers_4pct", change_pct="0.0700"),
                    _row("2026-09-03", "CCC", "preset:pp_count", change_pct="0.0000")]
    res = A.audit(_write(tmp_path, rows),
                  declared={"2026-09-03": ("DATA ALEX", "2026-09-06", "为什么")})
    assert res["violations"] == []


def test_a_declared_date_that_is_now_clean_forces_you_to_delete_the_excuse(tmp_path):
    """E2 —— 防腐的那一半。修好了不删声明，这张表就变成永久豁免名单。"""
    res = A.audit(_write(tmp_path, CLEAN),
                  declared={"2026-09-01": ("DATA ALEX", "2026-09-06", "为什么")})
    assert [c for c, _ in res["violations"]] == ["E2"]


def test_a_declared_date_that_is_not_in_the_archive_is_a_violation(tmp_path):
    res = A.audit(_write(tmp_path, CLEAN),
                  declared={"2025-01-01": ("DATA ALEX", "2026-09-06", "为什么")})
    assert [c for c, _ in res["violations"]] == ["E3"]


@pytest.mark.parametrize("entry", [("", "2026-09-06", "为什么"),
                                   ("DATA ALEX", "2026-09-06", "")])
def test_a_declaration_without_an_owner_or_a_reason_is_a_violation(tmp_path, entry):
    res = A.audit(_write(tmp_path, CLEAN), declared={"2026-09-01": entry})
    assert [c for c, _ in res["violations"]] == ["E4"]


# ---------- 不该报红的那些 ----------

def test_the_same_number_written_two_ways_is_not_a_disagreement(tmp_path):
    rows = [_row("2026-09-03", "CCC", "gainers_4pct", change_pct="0.0400"),
            _row("2026-09-03", "CCC", "preset:pp_count", change_pct="0.04")]
    assert A.audit(_write(tmp_path, rows), declared={})["violations"] == []


def test_a_missing_value_is_not_a_disagreement(tmp_path):
    rows = [_row("2026-09-03", "CCC", "gainers_4pct", change_pct="0.0400"),
            _row("2026-09-03", "CCC", "preset:pp_count", change_pct="")]
    assert A.audit(_write(tmp_path, rows), declared={})["violations"] == []


def test_nan_is_treated_as_no_reading_not_as_a_value(tmp_path):
    rows = [_row("2026-09-03", "CCC", "gainers_4pct", change_pct="0.0400"),
            _row("2026-09-03", "CCC", "preset:pp_count", change_pct="nan")]
    assert A.audit(_write(tmp_path, rows), declared={})["violations"] == []


def test_one_screener_alone_is_never_a_disagreement(tmp_path):
    rows = [_row("2026-09-03", "CCC", "gainers_4pct", change_pct="0.0400")]
    res = A.audit(_write(tmp_path, rows), declared={})
    assert res["violations"] == [] and res["pairs_checked"] == 0


def test_group_is_deliberately_not_checked(tmp_path):
    """`group` 是**多义列**：momentum_97 往里写它自己的 RS 桶（97/98/99/100），
    别的筛子写别的东西 —— 实测 111 个日期上都分歧，其中 953 例差得远
    （healthy_charts 说 65、momentum_97 说 97）。同一个列名两个量。
    放进来闸会天天红，然后被人学会跳过。这条测试钉住那个选择。"""
    rows = [_row("2026-09-03", "CCC", "healthy_charts", group="65"),
            _row("2026-09-03", "CCC", "momentum_97", group="97")]
    assert A.audit(_write(tmp_path, rows), declared={})["violations"] == []


# ---------- 比法按字段定 ----------

def test_rel_volume_is_compared_at_the_coarser_recorded_precision(tmp_path):
    """`vol_up_gainers` 把 rel_volume 四舍五入到 2 位，预设那边写全精度。
    精确比之下 42.38% 的可比组「不一致」，而那全是精度不是分歧。"""
    rows = [_row("2026-03-16", "BELFA", "vol_up_gainers", rel_volume="1.96"),
            _row("2026-03-16", "BELFA", "preset:vol_up_gainers", rel_volume="1.963872")]
    assert A.audit(_write(tmp_path, rows), declared={})["violations"] == []


def test_rel_volume_still_catches_a_real_disagreement(tmp_path):
    """真数：2026-08-17 的 AIR，0.58 vs 3.3。按精度比也必须红 ——
    否则上一条就把这把闸对 rel_volume 变成了摆设。"""
    rows = [_row("2026-08-17", "AIR", "preset:pp_count", rel_volume="0.580454"),
            _row("2026-08-17", "AIR", "vol_up_gainers", rel_volume="3.3")]
    res = A.audit(_write(tmp_path, rows), declared={})
    assert [c for c, _ in res["violations"]] == ["E1"]
    assert res["disagreements"]["2026-08-17"][0]["field"] == "rel_volume"


def test_change_pct_is_NOT_compared_at_the_coarser_precision(tmp_path):
    """真数：2026-08-17 的 CHRD，一侧写 "0.0"（一位小数）、另一侧 "0.0405"。
    若按 1 位比，两边都成了 0.0 —— 实测这样会漏掉 6 例。所以没有全局容差。"""
    rows = [_row("2026-08-17", "CHRD", "preset:pp_count", change_pct="0.0"),
            _row("2026-08-17", "CHRD", "gainers_4pct", change_pct="0.0405")]
    res = A.audit(_write(tmp_path, rows), declared={})
    assert [c for c, _ in res["violations"]] == ["E1"]
    assert res["disagreements"]["2026-08-17"][0]["field"] == "change_pct"


# ---------- 覆盖面：这把闸自己看得见多少 ----------

def test_the_tool_reports_the_dates_it_cannot_see_at_all(tmp_path):
    """协议：has_X() 是个 bool，缺口住在集合里。闸必须自己说盲区在哪。"""
    rows = CLEAN + [_row("2026-09-09", "DDD", "momentum_97"),
                    _row("2026-09-09", "EEE", "ema21_watch")]
    cov = A.coverage(_write(tmp_path, rows))
    assert cov["dates_blind"] == ["2026-09-09"]
    assert cov["dates_seen"] == 2 and cov["dates_total"] == 3


# ---------- 「红得不是地方」 ----------

def test_a_missing_archive_is_not_reported_as_a_data_violation(tmp_path):
    """文件不在 ≠ 数据不自洽。用另一个退出码，别混进 E1。"""
    assert A.main([str(tmp_path / "nope.csv")]) == 2


def test_the_exit_code_is_1_only_when_there_is_a_real_violation(tmp_path, capsys):
    clean = _write(tmp_path, CLEAN, "clean.csv")
    dirty = _write(tmp_path, CLEAN + [
        _row("2026-09-03", "CCC", "gainers_4pct", change_pct="0.07"),
        _row("2026-09-03", "CCC", "preset:pp_count", change_pct="0.00")], "dirty.csv")
    monkey = A.DECLARED.copy()
    A.DECLARED.clear()
    try:
        assert A.main([str(clean)]) == 0
        assert A.main([str(dirty)]) == 1
    finally:
        A.DECLARED.update(monkey)


# ---------- 钉住字段表本身 ----------

def test_the_checked_fields_are_the_five_that_must_be_equal(tmp_path):
    """写死，不引 A.FIELDS —— 引了就跟着常量一起动，永远不会红。"""
    assert set(A.FIELDS) == {"change_pct", "volume", "sector", "atr_ext", "rel_volume"}
    assert set(A.PRECISION_AWARE) == {"rel_volume"}


# ---------- 真接线：这条测试就是这把闸今天的自动触发点 ----------

def test_the_real_archive_agrees_with_itself():
    """跑在**真归档**上。`tests.yml` 每次 push 都跑 `pytest pipeline/tests`，
    所以这条测试就是 `audit_event_agreement` 今天的自动执行点。

    ⚠️ `audit_wiring` 仍然把它记成 known-unwired，那**不是矛盾**：
    `prod_invocations` 明确跳过 `tests/` 目录（「a test calling it is not a run」），
    它数的是**生产调用**。真正能算生产接线的地方是 `pipeline/screeners/ticker_events.py`
    写完归档之后自查一次 —— 那是 DATA ALEX 的文件，夜间组不碰。
    所以 KNOWN_UNWIRED 里那条声明是**记账**，不是「它没在跑」。

    它红了怎么办：**不要来改这条测试。** 要么修那天的数据，
    要么在 `DECLARED` 里具名声明那一天（谁、何时发现、为什么）。
    """
    archive = Path("data/history/ticker_events.csv")
    if not archive.exists():                       # 别人的树里可能没有归档
        pytest.skip("no archive in this tree")
    res = A.audit(archive)
    assert res["violations"] == [], (
        "ticker_events 里出现了新的读数不一致 —— 同一天同一只票，两个筛子报了两个数。\n"
        "先跑 `python3 -m pipeline.tools.audit_event_agreement` 看是哪一天、哪些票。\n"
        + "\n".join(f"  {c} {m}" for c, m in res["violations"]))
