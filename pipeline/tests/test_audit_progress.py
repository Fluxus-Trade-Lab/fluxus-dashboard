"""audit_progress 的测试 —— 每条恒等式先证明它能报阳性，再信它的阴性。

阳性对照分两种，两种都要：
  · 合成的：往干净档里注射一条已知的坏，闸必须响（下面 P1/P2/P3 各一组）；
  · 真实的：档案自己留下的 2026-08-17（已知坏日，`DATA_RELIABILITY` §六.7），
    本闸用完全不同的判据独立报出来 —— 见 test_real_archive_*。

合成用例注入一个「每一个日历日都是交易日」的假日历，所以
days_since 该等于的值就是 (as_of - ep_date).days。这样测的是判定逻辑，
不是 pandas 交易日历。

⚠️ 本文件里最要紧的两条：
  · test_a_column_that_changed_does_not_excuse_a_frozen_counter ——
    2026-09-02 那天 `today_relvol` 36/36 都变了（最大 +46.4%），
    任何问「变没变」的闸都会放行。
  · test_real_archive_catches_2026_08_20_which_differencing_cannot ——
    第一版 P1 是按相邻场差分写的，在真档案上漏掉整整一天：
    赤字一旦形成就持续，之后每天 Δ 都是正常的 +1。绝对重算才看得见。
"""
import csv
import datetime as dt

import pytest

from pipeline.tools import audit_progress as ap

HEADER = ["as_of", "ticker", "ep_date", "days_since", "close", "base_high",
          "today_relvol"]

# 假日历：每一天都是交易日。合成用例只想测判定，不想测 pandas。
ALL_DAYS = lambda d: True                                   # noqa: E731
EP_DATE = "2026-08-20"
SESSIONS = ("2026-09-01", "2026-09-02", "2026-09-03")


def _expected(as_of, ep_date=EP_DATE):
    return (dt.date.fromisoformat(as_of) - dt.date.fromisoformat(ep_date)).days


def _row(as_of, ticker, days_since, close, base_high, relvol="1.0",
         ep_date=EP_DATE):
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
    """3 只票 × 3 场：days_since 与日历一致，收盘价每天都动，base_high 不降。"""
    out = []
    for i, t in enumerate(("AAA", "BBB", "CCC")):
        for j, d in enumerate(SESSIONS):
            out.append(_row(d, t, _expected(d), round(10 + i + 0.5 * j, 2),
                            round(20 + i + j, 2), relvol=str(1.0 + 0.01 * j)))
    return out


def _audit(path):
    return ap.audit(path, is_trading_day=ALL_DAYS)


def _codes(res):
    return sorted(c for c, _ in res["violations"])


# ---------- 阴性：干净档必须零违规 ----------

def test_clean_archive_has_no_violations(tmp_path):
    res = _audit(_write(tmp_path, _clean()))
    assert res["violations"] == []
    assert res["tracks"] == 3
    assert res["rows"] == 9


def test_render_survives_a_clean_archive(tmp_path):
    assert "零违规" in ap.render(_audit(_write(tmp_path, _clean())))


# ---------- P1：帧与日历对不上 ----------

def test_p1_fires_when_one_row_disagrees_with_the_calendar(tmp_path):
    rows = _clean()
    for r in rows:
        if r["ticker"] == "BBB" and r["as_of"] == "2026-09-03":
            r["days_since"] = str(int(r["days_since"]) - 1)
    res = _audit(_write(tmp_path, rows))
    assert _codes(res) == ["P1"]
    hit = res["p1"]["2026-09-03"][0]
    assert hit["ticker"] == "BBB" and hit["got"] == hit["expected"] - 1


def test_p1_counts_only_the_bad_rows_not_the_whole_session(tmp_path):
    rows = _clean()
    for r in rows:
        if r["ticker"] == "BBB" and r["as_of"] == "2026-09-03":
            r["days_since"] = "1"
    res = _audit(_write(tmp_path, rows))
    assert len(res["p1"]["2026-09-03"]) == 1
    assert res["per_session"]["2026-09-03"] == 3


def test_p1_is_absolute_so_a_deficit_that_persists_is_still_caught(tmp_path):
    """这条是第一版漏掉一整天的原因：差分只看得见赤字**形成**的那一场。

    BBB 在第 2 场少了一根，第 3 场照常 +1 —— 差分口径在第 3 场是干净的，
    绝对口径两场都报。
    """
    rows = _clean()
    for r in rows:
        if r["ticker"] == "BBB" and r["as_of"] in ("2026-09-02", "2026-09-03"):
            r["days_since"] = str(int(r["days_since"]) - 1)
    res = _audit(_write(tmp_path, rows))
    assert len(res["p1"]["2026-09-02"]) == 1
    assert len(res["p1"]["2026-09-03"]) == 1          # ← 差分口径在这里是空的
    d2 = res["p1"]["2026-09-02"][0]
    d3 = res["p1"]["2026-09-03"][0]
    assert d2["got"] - d2["expected"] == -1
    assert d3["got"] - d3["expected"] == -1


def test_a_row_ahead_of_the_calendar_is_also_p1(tmp_path):
    rows = _clean()
    for r in rows:
        if r["ticker"] == "AAA" and r["as_of"] == "2026-09-03":
            r["days_since"] = str(int(r["days_since"]) + 3)
    res = _audit(_write(tmp_path, rows))
    assert _codes(res) == ["P1"]
    assert res["p1"]["2026-09-03"][0]["got"] > res["p1"]["2026-09-03"][0]["expected"]


def test_a_holiday_in_the_calendar_shifts_what_is_expected(tmp_path):
    """日历不是摆设：同一份数据，换一个把 09-02 当假日的日历就该报违规。"""
    rows = _clean()
    clean_res = ap.audit(_write(tmp_path, rows), is_trading_day=ALL_DAYS)
    assert clean_res["violations"] == []
    holiday = lambda d: d.isoformat() != "2026-09-02"      # noqa: E731
    res = ap.audit(_write(tmp_path, rows, "again.csv"), is_trading_day=holiday)
    # 09-02 不算交易日 => 09-02 与 09-03 的期望值各少 1，6 行全报
    assert len(res["p1"]["2026-09-02"]) == 3
    assert len(res["p1"]["2026-09-03"]) == 3


def test_ghost_rows_are_flagged_when_the_fix_leaves_the_scan_window(tmp_path):
    """修正后落在 delayed_ep_scan 的 3..15 窗口之外 = 那一行本不该在归档里。"""
    rows = [_row("2026-09-03", "AAA", 15, 10.0, 20.0, ep_date="2026-08-18")]
    res = _audit(_write(tmp_path, rows))
    hit = res["p1"]["2026-09-03"][0]
    assert hit["expected"] == 16 and hit["ghost"] is True
    assert "本不该在归档里" in res["violations"][0][1]


def test_a_row_still_inside_the_window_after_the_fix_is_not_a_ghost(tmp_path):
    rows = [_row("2026-09-03", "AAA", 9, 10.0, 20.0, ep_date="2026-08-24")]
    res = _audit(_write(tmp_path, rows))
    hit = res["p1"]["2026-09-03"][0]
    assert hit["expected"] == 10 and hit["ghost"] is False


# ---------- P2：整场复制品，且必须和 P1 区分开 ----------

def test_p2_fires_when_every_row_is_off_and_close_repeats(tmp_path):
    rows = _clean()
    prev = {r["ticker"]: r for r in rows if r["as_of"] == "2026-09-02"}
    for r in rows:
        if r["as_of"] == "2026-09-03":
            r["days_since"] = prev[r["ticker"]]["days_since"]
            r["close"] = prev[r["ticker"]]["close"]
    res = _audit(_write(tmp_path, rows))
    assert _codes(res) == ["P2"]                    # 不再另报 P1
    assert res["p2"] == ["2026-09-03"]


def test_all_rows_off_but_prices_moved_is_p1_not_p2(tmp_path):
    """2026-08-17 的形状：帧对不上日历，价格却更新了 —— 那不是整场复制品。"""
    rows = _clean()
    prev = {r["ticker"]: r for r in rows if r["as_of"] == "2026-09-02"}
    for r in rows:
        if r["as_of"] == "2026-09-03":
            r["days_since"] = prev[r["ticker"]]["days_since"]   # close 保持不同
    res = _audit(_write(tmp_path, rows))
    assert _codes(res) == ["P1"]
    assert res["p2"] == []


def test_one_bad_row_with_a_frozen_close_is_still_only_p1(tmp_path):
    """P2 要的是**整场**，不是「凡对不上的都冻了 close」。"""
    rows = _clean()
    prev = {r["ticker"]: r for r in rows if r["as_of"] == "2026-09-02"}
    for r in rows:
        if r["as_of"] == "2026-09-03" and r["ticker"] == "BBB":
            r["days_since"] = prev["BBB"]["days_since"]
            r["close"] = prev["BBB"]["close"]
    res = _audit(_write(tmp_path, rows))
    assert _codes(res) == ["P1"]
    assert res["p2"] == []


def test_all_off_but_only_one_close_repeated_is_p1_not_p2(tmp_path):
    """把 all() 写成 any() 的实现会在这里错判整场复制。"""
    rows = _clean()
    prev = {r["ticker"]: r for r in rows if r["as_of"] == "2026-09-02"}
    for r in rows:
        if r["as_of"] == "2026-09-03":
            r["days_since"] = prev[r["ticker"]]["days_since"]
            if r["ticker"] == "AAA":
                r["close"] = prev["AAA"]["close"]
    res = _audit(_write(tmp_path, rows))
    assert _codes(res) == ["P1"]
    assert res["p2"] == []
    assert sum(x["close_frozen"] for x in res["p1"]["2026-09-03"]) == 1


def test_a_column_that_changed_does_not_excuse_a_frozen_counter(tmp_path):
    """09-02 的真实伪装：relvol 36/36 都变了（最大 +46.4%），「变没变」全绿。"""
    rows = _clean()
    prev = {r["ticker"]: r for r in rows if r["as_of"] == "2026-09-02"}
    for r in rows:
        if r["as_of"] == "2026-09-03":
            r["days_since"] = prev[r["ticker"]]["days_since"]
            r["close"] = prev[r["ticker"]]["close"]
            r["today_relvol"] = str(float(prev[r["ticker"]]["today_relvol"]) * 1.464)
    res = _audit(_write(tmp_path, rows))
    assert res["p2"] == ["2026-09-03"]              # 有列变了，照样抓到


# ---------- P3：累积极值降了 ----------

def test_p3_fires_when_base_high_drops(tmp_path):
    rows = _clean()
    for r in rows:
        if r["ticker"] == "CCC" and r["as_of"] == "2026-09-03":
            r["base_high"] = "1.00"
    res = _audit(_write(tmp_path, rows))
    assert _codes(res) == ["P3"]
    assert res["p3"][0]["ticker"] == "CCC"


def test_p3_tolerates_an_exactly_equal_base_high(tmp_path):
    rows = _clean()
    prev = {r["ticker"]: r for r in rows if r["as_of"] == "2026-09-02"}
    for r in rows:
        if r["as_of"] == "2026-09-03":
            r["base_high"] = prev[r["ticker"]]["base_high"]
    assert _audit(_write(tmp_path, rows))["violations"] == []


def test_p3_is_scoped_to_one_track_not_across_tickers(tmp_path):
    """AAA 的 base_high 低于 BBB 的，这不是违规 —— 恒等式是每条轨迹内部的。"""
    assert _audit(_write(tmp_path, _clean()))["p3"] == []


# ---------- 不许静默报绿 ----------

def test_a_missing_column_raises_instead_of_reporting_clean(tmp_path):
    rows = [{k: v for k, v in r.items() if k != "base_high"} for r in _clean()]
    p = tmp_path / "short.csv"
    with p.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=[c for c in HEADER if c != "base_high"])
        w.writeheader()
        w.writerows(rows)
    with pytest.raises(KeyError) as e:
        _audit(p)
    # 「红得不是地方」:少一列时 dict 取值本来就会抛 KeyError,
    # 所以只断言类型的测试对「删掉守卫」这个改动是绿的。断言它说出了列名。
    assert "base_high" in str(e.value)
    assert "缺列" in str(e.value)


def test_a_missing_file_exits_two_not_zero(tmp_path):
    assert ap.main([str(tmp_path / "nope.csv")]) == 2


def test_main_returns_one_when_there_are_violations(tmp_path):
    rows = _clean()
    for r in rows:
        if r["ticker"] == "BBB" and r["as_of"] == "2026-09-03":
            r["days_since"] = "1"
    assert ap.main([str(_write(tmp_path, rows))]) == 1


def test_main_returns_zero_on_a_clean_archive(tmp_path):
    """main 走真日历 —— 所以合成档的日期必须挑成周内连续交易日。"""
    rows = []
    for i, t in enumerate(("AAA", "BBB")):
        for j, d in enumerate(("2026-09-02", "2026-09-03", "2026-09-04")):
            rows.append(_row(d, t, 9 + j, 10.0 + i + j, 20.0 + i + j,
                             ep_date="2026-08-20"))
    assert ap.main([str(_write(tmp_path, rows))]) == 0


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
    assert len(res["p1"]["2026-08-17"]) == 12
    assert [x["ticker"] for x in res["p3"]] == ["CORT"]


def test_real_archive_catches_2026_08_20_which_differencing_cannot():
    """按相邻场差分写的第一版在这一天全绿：赤字已形成，Δ 恢复成正常的 +1。"""
    res = _real()
    assert len(res["p1"]["2026-08-20"]) == 8


def test_real_archive_deficits_are_all_minus_one():
    res = _real()
    assert {x["got"] - x["expected"]
            for s in res["p1"] for x in res["p1"][s]} == {-1}


def test_real_archive_ghost_rows_should_have_been_outside_the_scan_window():
    """修正后 days_since=16 > --max-days 15 —— 这些行本不该被写进归档。"""
    res = _real()
    ghosts = {(s, x["ticker"]) for s in res["p1"] for x in res["p1"][s] if x["ghost"]}
    assert len(ghosts) == 10
    assert {s for s, _ in ghosts} == {"2026-08-19", "2026-08-20"}


def test_real_archive_the_frozen_cohort_repeats_across_the_three_august_days():
    res = _real()
    a = {x["ticker"] for x in res["p1"]["2026-08-17"]}
    b = {x["ticker"] for x in res["p1"]["2026-08-19"]}
    c = {x["ticker"] for x in res["p1"]["2026-08-20"]}
    assert len(a & b) == 11
    assert c <= (a | b)                    # 08-20 那批没有新面孔


def test_real_archive_august_rows_had_moving_prices_so_they_are_not_p2():
    """判别力的真实版：八月那三天的坏行，close 一行都没冻 —— 所以不是 P2。"""
    res = _real()
    for s in ("2026-08-17", "2026-08-19", "2026-08-20"):
        assert sum(x["close_frozen"] for x in res["p1"][s]) == 0
        assert s not in res["p2"]


def test_real_archive_has_exactly_these_five_violations():
    assert _codes(_real()) == ["P1", "P1", "P1", "P2", "P3"]


# ---------- --sweep：不需要日历、不需要计数器、不需要懂这张表 ----------

def _clean6():
    """--sweep 要求共同键 ≥ MIN_KEYS(5)，所以这一组用 6 只票。"""
    out = []
    for i, t in enumerate(("AAA", "BBB", "CCC", "DDD", "EEE", "FFF")):
        for j, d in enumerate(SESSIONS):
            out.append(_row(d, t, _expected(d), round(10 + i + 0.5 * j, 2),
                            round(20 + i + j, 2), relvol=str(1.0 + 0.01 * j)))
    return out


def _sweep_rows(rows, date_col="as_of", key=("ticker",)):
    return ap.frozen_columns(rows, date_col, key)


def test_sweep_counts_a_column_frozen_only_when_every_key_repeats(tmp_path):
    rows = _clean6()
    prev = {r["ticker"]: r for r in rows if r["as_of"] == "2026-09-02"}
    for r in rows:                       # 只冻 AAA 的 close —— 不算这一列冻住
        if r["as_of"] == "2026-09-03" and r["ticker"] == "AAA":
            r["close"] = prev["AAA"]["close"]
    hit = [x for x in _sweep_rows(rows) if x["session"] == "2026-09-03"][0]
    assert hit["frozen"] == 1            # 只有 ep_date 一列本来就恒定
    assert hit["columns"] == 5           # 6 列减掉键列 ticker —— 键列按定义就冻着
    assert hit["keys"] == 6


def test_sweep_column_view_sees_a_replay_that_the_row_view_reports_as_zero(tmp_path):
    """本文件里最要紧的对照：同一份数据，逐行比 0%、逐列比 80%。

    这就是 2026-09-02 的形状 —— 16 个非键列里 2 列带着供应商修订回来，
    整行比法从此全废，而整列比法还看得见 14/16。
    """
    rows = _clean6()
    prev = {r["ticker"]: r for r in rows if r["as_of"] == "2026-09-02"}
    for r in rows:
        if r["as_of"] == "2026-09-03":
            for c in ("days_since", "close", "base_high"):
                r[c] = prev[r["ticker"]][c]
            r["today_relvol"] = str(float(prev[r["ticker"]]["today_relvol"]) * 1.464)

    cols = [c for c in HEADER if c != "as_of"]
    a = {r["ticker"]: r for r in rows if r["as_of"] == "2026-09-02"}
    b = {r["ticker"]: r for r in rows if r["as_of"] == "2026-09-03"}
    identical_rows = sum(all(a[t][c] == b[t][c] for c in cols) for t in a)
    assert identical_rows == 0                     # ← 逐行比法：0%

    hit = [x for x in _sweep_rows(rows) if x["session"] == "2026-09-03"][0]
    assert hit["frozen"] == 4 and hit["columns"] == 5   # ← 逐列比法：4/5
    assert hit["share"] > 0.75


def test_sweep_skips_pairs_with_too_few_common_keys(tmp_path):
    rows = [_row("2026-09-01", "AAA", 12, 10.0, 20.0),
            _row("2026-09-02", "AAA", 13, 11.0, 21.0)]
    assert _sweep_rows(rows) == []                 # 1 个共同键 < MIN_KEYS


def test_sweep_on_the_real_archives_puts_2026_09_02_first_by_a_wide_margin():
    hist = ap.ARCHIVE.parent
    if not (hist / "delayed_ep_log.csv").exists():
        pytest.skip("归档不在这棵树上")
    rows = ap.sweep(hist)
    top = rows[0]
    assert top["archive"] == "delayed_ep_log.csv" and top["session"] == "2026-09-02"
    assert top["frozen"] == 14 and top["columns"] == 16
    # 断层写死（实测 37.5pp）：塌到 20pp 以内就说明这个读法不再有分辨率，该有人看一眼
    assert (top["share"] - rows[1]["share"]) > 0.20


def test_sweep_reports_and_never_gates(tmp_path):
    """只报不判：阈值是拿唯一一个阳性凑的，所以退出码永远 0。"""
    assert ap.main(["--sweep", str(ap.ARCHIVE.parent)]) == 0


def test_sweep_says_so_when_there_is_nothing_to_compare(tmp_path):
    out = ap.render_sweep([])
    assert "没有结论" in out and "不是绿" in out
