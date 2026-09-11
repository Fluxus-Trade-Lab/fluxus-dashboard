"""audit_events_vs_bars 的测试。

两条体例要求（这个仓库都栽过）：
  * **真阳性对照** —— 往真归档里注射一场真重放，闸必须红并且把帧指对。
    一条只会绿的断言是装饰（`pitfall_red_for_the_wrong_reason`）。
  * **不读自己的常量** —— 阈值、字段名、判定线全部写死在断言里，不引 `A.TOL` / `A.OK_RATE`；
    否则改了常量测试跟着动，永远不会红（`pitfall_a_test_that_reads_its_own_constant`）。
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from pipeline.tools import audit_events_vs_bars as A

HEAD = ["date", "ticker", "screener", "group", "change_pct",
        "rel_volume", "volume", "sector", "atr_ext"]

# 三个交易日的合成 K 线。收盘价选成每天涨跌都不一样，免得「配错一天」也偶然对上。
BARS = {
    "AAA": [("2026-09-01", 100.0), ("2026-09-02", 110.0), ("2026-09-03", 99.0)],
    "BBB": [("2026-09-01", 50.0), ("2026-09-02", 52.0), ("2026-09-03", 62.4)],
    "CCC": [("2026-09-01", 20.0), ("2026-09-02", 19.0), ("2026-09-03", 20.9)],
    "DDD": [("2026-09-01", 8.0), ("2026-09-02", 8.8), ("2026-09-03", 8.36)],
    "EEE": [("2026-09-01", 300.0), ("2026-09-02", 285.0), ("2026-09-03", 313.5)],
    "FFF": [("2026-09-01", 12.0), ("2026-09-02", 13.2), ("2026-09-03", 12.54)],
    "GGG": [("2026-09-01", 45.0), ("2026-09-02", 49.5), ("2026-09-03", 44.55)],
    "HHH": [("2026-09-01", 7.0), ("2026-09-02", 7.7), ("2026-09-03", 8.47)],
    "III": [("2026-09-01", 90.0), ("2026-09-02", 81.0), ("2026-09-03", 89.1)],
    "JJJ": [("2026-09-01", 33.0), ("2026-09-02", 36.3), ("2026-09-03", 34.485)],
    "KKK": [("2026-09-01", 61.0), ("2026-09-02", 67.1), ("2026-09-03", 63.745)],
    "LLL": [("2026-09-01", 5.0), ("2026-09-02", 5.5), ("2026-09-03", 5.225)],
    "MMM": [("2026-09-01", 210.0), ("2026-09-02", 199.5), ("2026-09-03", 219.45)],
    "NNN": [("2026-09-01", 17.0), ("2026-09-02", 18.7), ("2026-09-03", 17.765)],
    "OOO": [("2026-09-01", 76.0), ("2026-09-02", 68.4), ("2026-09-03", 75.24)],
    "PPP": [("2026-09-01", 29.0), ("2026-09-02", 31.9), ("2026-09-03", 30.305)],
    "QQQ": [("2026-09-01", 140.0), ("2026-09-02", 154.0), ("2026-09-03", 146.3)],
    "RRR": [("2026-09-01", 3.0), ("2026-09-02", 3.3), ("2026-09-03", 3.135)],
}
TICKERS = sorted(BARS)


def _store(tmp_path: Path, bars=BARS) -> Path:
    d = tmp_path / "tickers"
    d.mkdir()
    for t, series in bars.items():
        blob = {"ticker": t, "ohlc_2y": [
            {"date": day, "open": c, "high": c, "low": c, "close": c, "volume": 1000}
            for day, c in series]}
        (d / f"{t}.json").write_text(json.dumps(blob))
    return d


def _pct(t: str, day: str) -> float:
    series = BARS[t]
    i = [x[0] for x in series].index(day)
    return series[i][1] / series[i - 1][1] - 1.0


def _archive(tmp_path: Path, rows: list[dict], name: str = "events.csv") -> Path:
    p = tmp_path / name
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=HEAD)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in HEAD})
    return p


def _rows_for(day: str, values_from: str, screener="gainers_4pct") -> list[dict]:
    """day 这一场的行，change_pct 取自 values_from 那一天的真实涨跌幅。"""
    return [{"date": day, "ticker": t, "screener": screener,
             "change_pct": f"{_pct(t, values_from):.4f}", "volume": "1000"}
            for t in TICKERS]


# --------------------------------------------------------------------------- 合成

def test_a_day_whose_values_match_its_own_bars_passes(tmp_path):
    res = A.audit(_archive(tmp_path, _rows_for("2026-09-02", "2026-09-02")),
                  _store(tmp_path), declared={})
    assert res["violations"] == []
    assert res["judged"]["2026-09-02"]["rate"] == 1.0
    assert res["judged"]["2026-09-02"]["n"] == 18


def test_a_replayed_day_is_reported_and_the_frame_is_named(tmp_path):
    """09-03 这场记的是 09-02 的涨跌幅 —— 闸必须红，并且把帧指向 09-02。"""
    rows = _rows_for("2026-09-02", "2026-09-02") + _rows_for("2026-09-03", "2026-09-02")
    res = A.audit(_archive(tmp_path, rows), _store(tmp_path), declared={})
    assert len(res["violations"]) == 1
    assert "2026-09-03" in res["violations"][0]
    assert res["judged"]["2026-09-03"]["frame"] == "2026-09-02"
    # 18 只合成票里有 1 只两天的涨跌幅恰好落在容差内 —— 这正是「配得上一成」的噪声底
    assert res["judged"]["2026-09-03"]["rate"] < 0.10
    # 而没被重放的那一天照样绿
    assert res["judged"]["2026-09-02"]["rate"] == 1.0


def test_the_frame_is_not_named_when_no_candidate_dominates(tmp_path):
    """把每只票的值换成别的票的涨跌幅：真的坏，但**配不上任何一天**。

    这是 2026-08-17 的形状。闸要敢说「我不知道它来自哪一天」，
    而不是把一个刚过噪声底的候选说成机制。
    """
    shuffled = TICKERS[1:] + TICKERS[:1]
    rows = [{"date": "2026-09-03", "ticker": t, "screener": "gainers_4pct",
             "change_pct": f"{_pct(other, '2026-09-03'):.4f}", "volume": "1000"}
            for t, other in zip(TICKERS, shuffled)]
    res = A.audit(_archive(tmp_path, rows), _store(tmp_path), declared={})
    assert len(res["violations"]) == 1
    assert "配不上任何单日" in res["violations"][0]
    assert res["judged"]["2026-09-03"]["frame"] is None
    assert res["judged"]["2026-09-03"]["frames"]  # 候选表还是要打出来


def test_a_day_with_too_few_comparable_rows_is_unjudgeable_not_green(tmp_path):
    rows = _rows_for("2026-09-03", "2026-09-02")[:5]      # 5 行，全是错的
    res = A.audit(_archive(tmp_path, rows), _store(tmp_path), declared={})
    assert res["violations"] == []                        # 不判红
    assert "2026-09-03" not in res["judged"]              # 也不判绿
    assert ("2026-09-03", 5) in res["unjudgeable"]
    assert "查不了" in A._fmt(res)


def test_rows_that_never_carry_change_pct_are_skipped_not_counted_as_agreeing(tmp_path):
    """healthy_charts 这类筛子全史写 0.0。若把它们算进分母，坏日会被稀释成绿。"""
    rows = ([{"date": "2026-09-03", "ticker": t, "screener": "healthy_charts",
              "change_pct": "0.0", "volume": "1000"} for t in TICKERS]
            + _rows_for("2026-09-03", "2026-09-02")[:5])
    res = A.audit(_archive(tmp_path, rows), _store(tmp_path), declared={})
    assert ("2026-09-03", 5) in res["unjudgeable"]        # 分母是 5 不是 23


def test_a_declared_day_is_green_but_still_printed_in_full(tmp_path):
    rows = _rows_for("2026-09-03", "2026-09-02")
    declared = {"2026-09-03": ("DATA ALEX", "2026-09-11", "合成的欠条")}
    res = A.audit(_archive(tmp_path, rows), _store(tmp_path), declared=declared)
    assert res["violations"] == []
    out = A._fmt(res)
    assert "[declared] 2026-09-03" in out
    assert "合成的欠条" in out
    assert "声明是欠条，不是结案。" in out


def test_an_undeclared_bad_day_makes_main_exit_one(tmp_path, monkeypatch):
    rows = _rows_for("2026-09-03", "2026-09-02")
    archive = _archive(tmp_path, rows)
    monkeypatch.setattr(A, "STORE_DIR", _store(tmp_path))
    monkeypatch.setattr(A, "DECLARED", {})
    assert A.main([str(archive)]) == 1


def test_a_missing_archive_is_two_not_one(tmp_path, capsys):
    """文件不在 ≠ 数据坏了。别把「没跑成」混进 E1（红得不是地方）。"""
    assert A.main([str(tmp_path / "nope.csv")]) == 2


def test_an_empty_bar_store_is_two_not_zero(tmp_path, monkeypatch):
    """没有 K 线库时闸没有结论 —— 尤其不能因为「零违规」而报绿。"""
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setattr(A, "STORE_DIR", empty)
    assert A.main([str(_archive(tmp_path, _rows_for("2026-09-02", "2026-09-02")))]) == 2


def test_four_decimal_rounding_still_matches(tmp_path):
    """写入方 round(...,4)。这点往返误差不许把干净日判红。"""
    rows = [{"date": "2026-09-02", "ticker": t, "screener": "gainers_4pct",
             "change_pct": f"{round(_pct(t, '2026-09-02'), 4)}", "volume": "1000"}
            for t in TICKERS]
    res = A.audit(_archive(tmp_path, rows), _store(tmp_path), declared={})
    assert res["judged"]["2026-09-02"]["rate"] == 1.0


def test_a_half_percent_error_is_inside_tolerance_and_a_two_percent_one_is_not(tmp_path):
    """容差的边界要被断言钉住，且两个方向都测 —— 单向的检查另一个方向永远是绿的。"""
    def day(bump):
        return [{"date": "2026-09-02", "ticker": t, "screener": "gainers_4pct",
                 "change_pct": f"{_pct(t, '2026-09-02') + bump:.4f}", "volume": "1000"}
                for t in TICKERS]
    inside = A.audit(_archive(tmp_path, day(0.004), "a.csv"), _store(tmp_path), declared={})
    assert inside["judged"]["2026-09-02"]["rate"] == 1.0
    outside = A.audit(_archive(tmp_path, day(0.02), "b.csv"),
                      tmp_path / "tickers", declared={})
    assert outside["judged"]["2026-09-02"]["rate"] == 0.0


def test_the_previous_close_comes_from_the_tickers_own_last_bar(tmp_path):
    """某票在 09-02 停牌没有 bar：09-03 的前收必须回退到 09-01，而不是当它没数据。"""
    bars = {t: list(s) for t, s in BARS.items()}
    bars["AAA"] = [("2026-09-01", 100.0), ("2026-09-03", 99.0)]
    store = _store(tmp_path, bars)
    rows = [{"date": "2026-09-03", "ticker": "AAA", "screener": "gainers_4pct",
             "change_pct": "-0.0100", "volume": "1000"}]
    res = A.audit(_archive(tmp_path, rows), store, declared={})
    # n<MIN_N 所以不判，但可比性本身要成立：单只票的读数拿得到
    cal = A.calendar(A.load_store(store))
    got = A._bar_pct(A.load_store(store), {d: i for i, d in enumerate(cal)}, cal,
                     "AAA", "2026-09-03")
    assert got == pytest.approx(99.0 / 100.0 - 1.0)
    assert res["unjudgeable"] == [("2026-09-03", 1)]


# --------------------------------------------------------------------------- 真归档

REAL_ARCHIVE = A.ARCHIVE
REAL_STORE = A.STORE_DIR
_real = pytest.mark.skipif(
    not (REAL_ARCHIVE.exists() and REAL_STORE.exists()),
    reason="真归档或本地 K 线库不在这棵树上")


@_real
def test_the_real_archive_puts_08_07_on_the_previous_sessions_frame():
    """真阳性对照之一：08-07 这一天不是合成的，它真的偏了一整场。"""
    res = A.audit()
    rec = res["judged"]["2026-08-07"]
    assert rec["rate"] < 0.10
    assert rec["frame"] == "2026-08-06"
    assert res["violations"] == []          # 它已被声明；棘轮今天该是绿的


@_real
def test_the_real_archive_refuses_to_name_a_frame_for_08_17():
    """08-17 是「坏，但说不出来自哪一天」那一类。闸不许替它编一个机制。"""
    rec = A.audit()["judged"]["2026-08-17"]
    assert rec["rate"] < 0.50
    assert rec["frame"] is None


@_real
def test_the_real_archive_is_otherwise_clean_and_the_gap_is_wide():
    """阴性对照 + 分辨率：干净日和坏日之间要有实测空档，判定线才不是拍的。"""
    res = A.audit()
    bad = set(res["bad"])
    assert bad == {"2026-08-07", "2026-08-17"}
    clean = [r["rate"] for d, r in res["judged"].items() if d not in bad]
    assert min(clean) > 0.90                       # 最差的干净日
    assert max(res["judged"][d]["rate"] for d in bad) < 0.50   # 最好的坏日


@_real
def test_injecting_a_replay_into_the_real_archive_turns_it_red(tmp_path):
    """真阳性对照之二：拿真归档最近一场，把 change_pct 换成前一场的，闸必须红。

    这一条回答的是「这把尺子在**今天的真数据**上还有没有分辨率」——
    合成夹具证明不了这件事（我量的数也会过期）。
    """
    with open(REAL_ARCHIVE, newline="") as fh:
        rows = list(csv.DictReader(fh))
        head = list(rows[0].keys())
    # 注入到**K 线库覆盖得到的**最新一场，而不是归档的最后一场：
    # cron 写完归档时，K 线库常常还停在上一场（2026-09-11 实测：归档到 09-10、库到 09-09），
    # 那一场本来就是「查不了」—— 往查不了的日子里注入，闸不红是对的，不能算它瞎。
    covered = set(A.calendar(A.load_store(REAL_STORE)))
    days = sorted({r["date"] for r in rows} & covered)
    last, prev = days[-1], days[-2]
    prev_pct = {r["ticker"]: r["change_pct"] for r in rows if r["date"] == prev}
    hit = 0
    for r in rows:
        if r["date"] == last and r["ticker"] in prev_pct:
            r["change_pct"] = prev_pct[r["ticker"]]
            hit += 1
    assert hit > 50, "注射本身没生效，下面的红就没有意义"
    p = tmp_path / "injected.csv"
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=head)
        w.writeheader()
        w.writerows(rows)
    res = A.audit(p, REAL_STORE, declared={})
    assert last in res["bad"], f"注射了一场重放，闸却没报 {last}"
    assert any(last in v for v in res["violations"])
