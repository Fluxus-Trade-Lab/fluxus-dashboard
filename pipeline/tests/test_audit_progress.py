"""audit_progress 的测试 —— 每条恒等式先证明它能报阳性，再信它的阴性。

阳性对照分两种，两种都要：
  · 合成的：往干净档里注射一条已知的坏，闸必须响（下面 P1/P2/P3 各一组）；
  · 真实的：档案自己留下的 2026-08-17（已知坏日，`DATA_RELIABILITY` §六.7）
    与 2026-09-02，本闸独立地报出来 —— 见 test_real_archive_*。

最要紧的一条是 test_a_column_that_changed_does_not_excuse_a_frozen_counter：
2026-09-02 那天 `today_relvol` **36/36 都变了**，任何问「变没变」的闸都会放行。
本闸问的是「往前走了没有」，所以别的列变不变与它无关。这条测试钉的就是这个差别。
"""
import csv

import pytest

from pipeline.tools import audit_progress as ap

HEADER = ["as_of", "ticker", "ep_date", "days_since", "close", "base_high",
          "today_relvol"]


def _row(as_of, ticker, ep_date, days_since, close, base_high, relvol="1.0"):
    return dict(zip(HEADER, [as_of, ticker, ep_date, str(days_since),
                             str(close), str(base_high), str(relvol)]))


def _write(tmp_path, rows, name="log.csv"):
    p = tmp_path / name
    with p.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)
    return p


def _clean():
    """3 只票 × 3 场，计数器逐场 +1，收盘价每天都动，base_high 不降。"""
    out = []
    for i, t in enumerate(("AAA", "BBB", "CCC")):
        for j, d in enumerate(("2026-09-01", "2026-09-02", "2026-09-03")):
            out.append(_row(d, t, "2026-08-20", 5 + j,
                            round(10 + i + 0.5 * j, 2), round(20 + i + j, 2),
                            relvol=str(1.0 + 0.01 * j)))
    return out


def _codes(res):
    return sorted(c for c, _ in res["violations"])


# ---------- 阴性：干净档必须零违规 ----------

def test_clean_archive_has_no_violations(tmp_path):
    res = ap.audit(_write(tmp_path, _clean()))
    assert res["violations"] == []
    assert res["tracks"] == 3
    assert res["pairs"] == 6


def test_render_survives_a_clean_archive(tmp_path):
    assert "零违规" in ap.render(ap.audit(_write(tmp_path, _clean())))


# ---------- P1：单只票的计数器冻住 ----------

def test_p1_fires_when_one_track_counter_does_not_advance(tmp_path):
    rows = _clean()
    for r in rows:                      # BBB 的第 3 场停在第 2 场的计数上
        if r["ticker"] == "BBB" and r["as_of"] == "2026-09-03":
            r["days_since"] = "6"
    res = ap.audit(_write(tmp_path, rows))
    assert _codes(res) == ["P1"]
    assert res["p1"]["2026-09-03"][0]["ticker"] == "BBB"


def test_p1_counts_only_the_frozen_tracks_not_the_whole_session(tmp_path):
    rows = _clean()
    for r in rows:
        if r["ticker"] == "BBB" and r["as_of"] == "2026-09-03":
            r["days_since"] = "6"
    res = ap.audit(_write(tmp_path, rows))
    assert len(res["p1"]["2026-09-03"]) == 1
    assert res["comparable"]["2026-09-03"] == 3


def test_a_counter_going_backwards_is_also_p1(tmp_path):
    rows = _clean()
    for r in rows:
        if r["ticker"] == "AAA" and r["as_of"] == "2026-09-03":
            r["days_since"] = "4"
    assert _codes(ap.audit(_write(tmp_path, rows))) == ["P1"]


def test_a_gap_of_two_is_legal(tmp_path):
    """冻住之后追平会出现 +2；那是恢复，不是违规。"""
    rows = _clean()
    for r in rows:
        if r["ticker"] == "AAA" and r["as_of"] == "2026-09-03":
            r["days_since"] = "8"
    assert ap.audit(_write(tmp_path, rows))["violations"] == []


# ---------- P2：整场复制品，且必须和 P1 区分开 ----------

def test_p2_fires_when_every_track_freezes_and_close_repeats(tmp_path):
    rows = _clean()
    prev = {r["ticker"]: r for r in rows if r["as_of"] == "2026-09-02"}
    for r in rows:
        if r["as_of"] == "2026-09-03":
            r["days_since"] = prev[r["ticker"]]["days_since"]
            r["close"] = prev[r["ticker"]]["close"]
    res = ap.audit(_write(tmp_path, rows))
    assert _codes(res) == ["P2"]                    # 不再另报 P1
    assert res["p2"] == ["2026-09-03"]


def test_all_frozen_but_prices_moved_is_p1_not_p2(tmp_path):
    """2026-08-17 的形状：帧没前进，价格却更新了 —— 那不是整场复制品。"""
    rows = _clean()
    prev = {r["ticker"]: r for r in rows if r["as_of"] == "2026-09-02"}
    for r in rows:
        if r["as_of"] == "2026-09-03":
            r["days_since"] = prev[r["ticker"]]["days_since"]   # close 保持不同
    res = ap.audit(_write(tmp_path, rows))
    assert _codes(res) == ["P1"]
    assert res["p2"] == []


def test_one_frozen_track_with_a_frozen_close_is_still_only_p1(tmp_path):
    """P2 要的是**整场**，不是「凡冻住的都冻了 close」。

    这里 3 条轨迹只冻 1 条、且那条的 close 也冻住 —— 判 P1。
    去掉「全部轨迹都冻住」这个条件的实现会在这里错判 P2。
    """
    rows = _clean()
    prev = {r["ticker"]: r for r in rows if r["as_of"] == "2026-09-02"}
    for r in rows:
        if r["as_of"] == "2026-09-03" and r["ticker"] == "BBB":
            r["days_since"] = prev["BBB"]["days_since"]
            r["close"] = prev["BBB"]["close"]
    res = ap.audit(_write(tmp_path, rows))
    assert _codes(res) == ["P1"]
    assert res["p2"] == []


def test_all_frozen_but_only_one_close_repeated_is_p1_not_p2(tmp_path):
    """P2 要的是**每一条**冻住的轨迹 close 都重复，不是有一条重复就算。

    把 all() 写成 any() 的实现会在这里错判整场复制。
    """
    rows = _clean()
    prev = {r["ticker"]: r for r in rows if r["as_of"] == "2026-09-02"}
    for r in rows:
        if r["as_of"] == "2026-09-03":
            r["days_since"] = prev[r["ticker"]]["days_since"]
            if r["ticker"] == "AAA":
                r["close"] = prev["AAA"]["close"]
    res = ap.audit(_write(tmp_path, rows))
    assert _codes(res) == ["P1"]
    assert res["p2"] == []
    assert sum(x["close_frozen"] for x in res["p1"]["2026-09-03"]) == 1


def test_a_column_that_changed_does_not_excuse_a_frozen_counter(tmp_path):
    """09-02 的真实伪装：供应商修订了 relvol，于是「变没变」这类闸全绿。"""
    rows = _clean()
    prev = {r["ticker"]: r for r in rows if r["as_of"] == "2026-09-02"}
    for r in rows:
        if r["as_of"] == "2026-09-03":
            r["days_since"] = prev[r["ticker"]]["days_since"]
            r["close"] = prev[r["ticker"]]["close"]
            r["today_relvol"] = str(float(prev[r["ticker"]]["today_relvol"]) + 1e-5)
    res = ap.audit(_write(tmp_path, rows))
    assert res["p2"] == ["2026-09-03"]              # 有列变了，照样抓到


# ---------- P3：累积极值降了 ----------

def test_p3_fires_when_base_high_drops(tmp_path):
    rows = _clean()
    for r in rows:
        if r["ticker"] == "CCC" and r["as_of"] == "2026-09-03":
            r["base_high"] = "1.00"
    res = ap.audit(_write(tmp_path, rows))
    assert _codes(res) == ["P3"]
    assert res["p3"][0]["ticker"] == "CCC"


def test_p3_tolerates_an_exactly_equal_base_high(tmp_path):
    rows = _clean()
    prev = {r["ticker"]: r for r in rows if r["as_of"] == "2026-09-02"}
    for r in rows:
        if r["as_of"] == "2026-09-03":
            r["base_high"] = prev[r["ticker"]]["base_high"]
    assert ap.audit(_write(tmp_path, rows))["violations"] == []


def test_p3_is_scoped_to_one_track_not_across_tickers(tmp_path):
    """AAA 的 base_high 低于 BBB 的，这不是违规 —— 恒等式是每条轨迹内部的。"""
    assert ap.audit(_write(tmp_path, _clean()))["p3"] == []


# ---------- 不许静默报绿 ----------

def test_a_missing_column_raises_instead_of_reporting_clean(tmp_path):
    rows = [{k: v for k, v in r.items() if k != "base_high"} for r in _clean()]
    p = tmp_path / "short.csv"
    with p.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=[c for c in HEADER if c != "base_high"])
        w.writeheader()
        w.writerows(rows)
    with pytest.raises(KeyError) as e:
        ap.audit(p)
    # 「红得不是地方」:少一列时 dict 取值本来就会抛 KeyError,
    # 所以只断言类型的测试对「删掉守卫」这个改动是绿的。断言它说出了列名。
    assert "base_high" in str(e.value)
    assert "缺列" in str(e.value)


def test_a_missing_file_exits_two_not_zero(tmp_path, capsys):
    assert ap.main([str(tmp_path / "nope.csv")]) == 2


def test_main_returns_one_when_there_are_violations(tmp_path):
    rows = _clean()
    for r in rows:
        if r["ticker"] == "BBB" and r["as_of"] == "2026-09-03":
            r["days_since"] = "6"
    assert ap.main([str(_write(tmp_path, rows))]) == 1


def test_main_returns_zero_on_a_clean_archive(tmp_path):
    assert ap.main([str(_write(tmp_path, _clean()))]) == 0


# ---------- 真实档案上的阳性对照（不是我注射的，是档案自己留下的）----------

def _real():
    if not ap.ARCHIVE.exists():
        pytest.skip("delayed_ep_log.csv 不在这棵树上")
    return ap.audit(ap.ARCHIVE)


def test_real_archive_reports_2026_09_02_as_a_duplicated_session():
    assert _real()["p2"] == ["2026-09-02"]


def test_real_archive_independently_finds_the_known_bad_2026_08_17():
    """08-17 是 DATA_RELIABILITY §六.7 已经立案的坏日（65bbb080 用了 08-14 的 bars）。"""
    res = _real()
    assert "2026-08-17" in res["p1"]
    assert len(res["p1"]["2026-08-17"]) == 12
    assert [x["ticker"] for x in res["p3"]] == ["CORT"]


def test_real_archive_also_finds_2026_08_19_which_no_other_guard_reported():
    res = _real()
    assert len(res["p1"]["2026-08-19"]) == 12
    # 08-17 与 08-19 冻住的是几乎同一批票 —— 写死这个重合度，它变了就该有人看一眼
    a = {x["ticker"] for x in res["p1"]["2026-08-17"]}
    b = {x["ticker"] for x in res["p1"]["2026-08-19"]}
    assert len(a & b) == 11


def test_real_archive_frozen_tracks_on_08_17_had_moving_prices():
    """判别力的真实版：08-17 冻住的 12 只，close 一只都没冻 —— 所以它不是 P2。"""
    res = _real()
    assert sum(x["close_frozen"] for x in res["p1"]["2026-08-17"]) == 0
    assert "2026-08-17" not in res["p2"]


def test_real_archive_has_exactly_these_four_violations():
    assert _codes(_real()) == ["P1", "P1", "P2", "P3"]
