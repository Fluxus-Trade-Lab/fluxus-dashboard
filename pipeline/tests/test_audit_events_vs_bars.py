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


FROZEN = Path(__file__).parent / "fixtures" / "events_vs_bars"


@_real
def test_the_08_07_rows_as_first_written_sit_on_the_previous_sessions_frame():
    """真阳性对照之一，已冻成夹具。2026-09-13 DATA ALEX 按 ET 场次重挑快照、重算了该日
    preset 行，真归档里不再有这一天的坏行 —— 原样冻结，免得对照随修复一起消失
    （pitfall_positive_control_vanished_when_vendor_healed）。"""
    res = A.audit(FROZEN / "ticker_events_2026-08-07_as_written.csv", declared={})
    rec = res["judged"]["2026-08-07"]
    assert rec["rate"] < 0.10
    assert rec["frame"] == "2026-08-06"
    assert res["violations"], "未声明的坏日必须判红"


@_real
def test_the_08_17_rows_as_first_written_get_no_invented_frame():
    """08-17 是「坏，但说不出来自哪一天」那一类。闸不许替它编一个机制。（同上，已冻成夹具）"""
    rec = A.audit(FROZEN / "ticker_events_2026-08-17_as_written.csv", declared={})["judged"]["2026-08-17"]
    assert rec["rate"] < 0.50
    assert rec["frame"] is None


@_real
def test_the_real_archive_is_clean_and_the_gap_to_the_frozen_bad_days_is_wide():
    """阴性对照 + 分辨率：真归档今天没有坏日；它最差的一天和冻结的坏日之间要有实测空档，
    判定线才不是拍的。"""
    res = A.audit()
    assert set(res["bad"]) == set()
    assert min(r["rate"] for r in res["judged"].values()) > 0.90      # 最差的干净日
    worst_bad = max(A.audit(FROZEN / f"ticker_events_{d}_as_written.csv", declared={})["judged"][d]["rate"]
                    for d in ("2026-08-07", "2026-08-17"))
    assert worst_bad < 0.50                                           # 最好的坏日


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


# --------------------------------------------------------------------------- 第二条恒等式：volume
#
# 合成成交量：三天的量彼此差得远（×1.5、×0.6），免得「配错一天」偶然落进带里。

VOLS = {t: {"2026-09-01": 1000.0 * (k + 1), "2026-09-02": 1500.0 * (k + 1),
            "2026-09-03": 900.0 * (k + 1)} for k, t in enumerate(TICKERS)}


def _store_v(tmp_path: Path, name: str = "tickers_v") -> Path:
    d = tmp_path / name
    d.mkdir()
    for t, series in BARS.items():
        blob = {"ticker": t, "ohlc_2y": [
            {"date": day, "open": c, "high": c, "low": c, "close": c, "volume": VOLS[t][day]}
            for day, c in series]}
        (d / f"{t}.json").write_text(json.dumps(blob))
    return d


def _vol_rows(day: str, values_from: str, scale: float = 1.0, screener="momentum_97") -> list[dict]:
    """change_pct 写 0.0（momentum_97 那类「本列不填」的筛子），volume 取自 values_from 那天 × scale。"""
    return [{"date": day, "ticker": t, "screener": screener, "change_pct": "0.0",
             "volume": f"{VOLS[t][values_from] * scale:.1f}"} for t in TICKERS]


def test_a_day_without_change_pct_is_judged_by_volume_not_left_blind(tmp_path):
    """Finviz 改名那一周的形状：change_pct 整列为空。以前判「查不了」，现在由 volume 判。"""
    res = A.audit(_archive(tmp_path, _vol_rows("2026-09-02", "2026-09-02")),
                  _store_v(tmp_path), declared={})
    assert ("2026-09-02", 0) in res["unjudgeable"]            # change_pct 那条仍然判不了
    assert res["volume"]["judged"]["2026-09-02"]["rate"] == 1.0
    assert res["volume"]["judged"]["2026-09-02"]["n"] == 18
    assert res["blind"] == []
    assert res["violations"] == []
    out = A._fmt(res)
    assert "改由 volume 判" in out
    assert "两条恒等式可比读数都" not in out


def test_a_volume_replay_is_red_and_the_frame_is_named(tmp_path):
    """09-03 这场记的是 09-02 的成交量，change_pct 为空 —— 以前这一天会静默，现在必须红并指对帧。"""
    rows = _vol_rows("2026-09-02", "2026-09-02") + _vol_rows("2026-09-03", "2026-09-02")
    res = A.audit(_archive(tmp_path, rows), _store_v(tmp_path), declared={})
    assert len(res["violations"]) == 1
    assert "2026-09-03" in res["violations"][0] and "volume" in res["violations"][0]
    rec = res["volume"]["judged"]["2026-09-03"]
    assert rec["rate"] == 0.0
    assert rec["frame"] == "2026-09-02"
    assert res["volume"]["judged"]["2026-09-02"]["rate"] == 1.0
    assert "[UNDECLARED] 2026-09-03: volume" in A._fmt(res)


def test_a_volume_shuffle_is_red_without_an_invented_frame(tmp_path):
    shuffled = TICKERS[1:] + TICKERS[:1]
    rows = [{"date": "2026-09-03", "ticker": t, "screener": "momentum_97", "change_pct": "0.0",
             "volume": f"{VOLS[other]['2026-09-03']:.1f}"} for t, other in zip(TICKERS, shuffled)]
    res = A.audit(_archive(tmp_path, rows), _store_v(tmp_path), declared={})
    assert len(res["violations"]) == 1
    assert "配不上任何单日" in res["violations"][0]
    assert res["volume"]["judged"]["2026-09-03"]["frame"] is None


@pytest.mark.parametrize("scale,inside", [
    (0.91, True), (0.89, False),      # 下沿宽：Finviz 少记 9% 仍算同一天，少记 11% 不算
    (1.009, True), (1.02, False),     # 上沿紧：多记 2% 就不算 —— 两个方向都钉住
])
def test_the_volume_band_is_one_sided_and_both_edges_are_pinned(tmp_path, scale, inside):
    res = A.audit(_archive(tmp_path, _vol_rows("2026-09-02", "2026-09-02", scale)),
                  _store_v(tmp_path), declared={})
    assert res["volume"]["judged"]["2026-09-02"]["rate"] == (1.0 if inside else 0.0)


def test_identical_readings_vote_once_and_different_readings_each_vote(tmp_path):
    """同票同量抄十遍只算一票；同票不同量各算一票、且与行序无关。

    3 只票各有一个坏量（抄 10 遍）+ 18 只票的好量 → 21 个读数、15+3 命中… 不：
    坏量 3 个不命中、好量 18 个命中 → hit 18 / n 21。把坏行挪到后面，读数必须不变
    （旧的「首行胜出」在 08-14 真数据上会在 0.925 和 0.975 之间翻）。"""
    rows = _vol_rows("2026-09-02", "2026-09-02")
    bad = [{"date": "2026-09-02", "ticker": t, "screener": f"preset:s{i}", "change_pct": "0.0",
            "volume": "1.0"} for t in TICKERS[:3] for i in range(10)]
    first = A.audit(_archive(tmp_path, bad + rows, "a.csv"), _store_v(tmp_path), declared={})
    last = A.audit(_archive(tmp_path, rows + bad, "b.csv"), tmp_path / "tickers_v", declared={})
    for res in (first, last):
        rec = res["volume"]["judged"]["2026-09-02"]
        assert (rec["hit"], rec["n"]) == (18, 21)


def test_non_finite_and_non_numeric_volumes_are_skipped(tmp_path):
    dirty = [{"date": "2026-09-02", "ticker": t, "screener": "vcp", "change_pct": "0.0", "volume": val}
             for t in TICKERS for val in ("nan", "inf", "-5", "abc", "1e400")]
    res = A.audit(_archive(tmp_path, dirty + _vol_rows("2026-09-02", "2026-09-02")),
                  _store_v(tmp_path), declared={})
    rec = res["volume"]["judged"]["2026-09-02"]
    assert (rec["hit"], rec["n"]) == (18, 18)


def test_zero_volume_rows_are_skipped_not_counted_as_misses(tmp_path):
    """写 0 的 volume 是「本列不填」，不是成交量为零。算进分母会把干净日稀释成红。"""
    zeros = [{"date": "2026-09-02", "ticker": t, "screener": "vcp", "change_pct": "0.0",
              "volume": "0.0"} for t in TICKERS]
    res = A.audit(_archive(tmp_path, zeros + _vol_rows("2026-09-02", "2026-09-02")),
                  _store_v(tmp_path), declared={})
    assert res["volume"]["judged"]["2026-09-02"]["hit"] == 18
    assert res["volume"]["judged"]["2026-09-02"]["n"] == 18


def test_a_day_half_of_whose_volumes_come_from_another_frame_is_red(tmp_path):
    """判定线从两边钉住：整场换帧在真数据上最高也能偶然配上 0.304，而部分重放要尽量早报。
    一半换帧（9/18）红；换掉 5 只（13/18 = 0.72）也红；换掉 3 只（15/18 = 0.83）绿。"""
    store = _store_v(tmp_path)

    def replaced(k: int, name: str):
        rows = [dict(r, volume=f"{VOLS[r['ticker']]['2026-09-01']:.1f}") if i < k else r
                for i, r in enumerate(_vol_rows("2026-09-02", "2026-09-02"))]
        return A.audit(_archive(tmp_path, rows, name), store, declared={})["volume"]

    half = replaced(9, "half.csv")
    assert half["judged"]["2026-09-02"]["rate"] == 0.5 and "2026-09-02" in half["bad"]
    five = replaced(5, "five.csv")
    assert five["judged"]["2026-09-02"]["hit"] == 13 and "2026-09-02" in five["bad"]
    three = replaced(3, "three.csv")
    assert three["judged"]["2026-09-02"]["hit"] == 15 and three["bad"] == {}


def test_a_declared_day_silences_the_volume_identity_too(tmp_path):
    rows = _vol_rows("2026-09-03", "2026-09-02")
    declared = {"2026-09-03": ("DATA ALEX", "2026-09-14", "合成的欠条")}
    res = A.audit(_archive(tmp_path, rows), _store_v(tmp_path), declared=declared)
    assert res["violations"] == []
    out = A._fmt(res)
    assert "[declared] 2026-09-03: volume" in out
    assert "合成的欠条" in out


def test_both_identities_blind_is_still_unjudgeable_not_green(tmp_path):
    rows = _vol_rows("2026-09-03", "2026-09-02")[:5]
    res = A.audit(_archive(tmp_path, rows), _store_v(tmp_path), declared={})
    assert res["violations"] == []
    assert "2026-09-03" not in res["volume"]["judged"]
    assert res["blind"] == [("2026-09-03", 0)]
    assert "两条恒等式可比读数都" in A._fmt(res)


@_real
def test_the_08_07_rows_as_first_written_are_red_on_volume_and_point_at_08_06():
    """冻结坏行在第二条恒等式上也要红，而且帧指向同一天 —— 两条不共用算术的尺子说同一句话。"""
    rec = A.audit(FROZEN / "ticker_events_2026-08-07_as_written.csv", declared={})["volume"]["judged"]["2026-08-07"]
    assert rec["rate"] < 0.30
    assert rec["frame"] == "2026-08-06"


@_real
def test_the_08_17_rows_as_first_written_are_red_on_volume_with_no_frame():
    rec = A.audit(FROZEN / "ticker_events_2026-08-17_as_written.csv", declared={})["volume"]["judged"]["2026-08-17"]
    assert rec["rate"] < 0.50
    assert rec["frame"] is None


@_real
def test_the_finviz_rename_week_is_no_longer_blind_and_is_clean():
    """阴性对照 + 覆盖：08-07、08-11/12/13 在 change_pct 上判不了，volume 必须能判且判绿。"""
    res = A.audit()
    vj = res["volume"]["judged"]
    for d in ("2026-08-07", "2026-08-11", "2026-08-12", "2026-08-13"):
        assert d in vj, f"{d} 仍然是盲的"
        assert vj[d]["rate"] > 0.90, (d, vj[d])
    assert res["volume"]["bad"] == {}
    assert min(r["rate"] for r in vj.values()) > 0.85                 # 最差的干净日（实测 0.929）
    # 只管 K 线库覆盖得到的日子：归档常比库新一场（盲区 5），那一场两条都是 n=0，不是本闸退化
    covered = set(A.calendar(A.load_store(REAL_STORE)))
    assert {d for d, _ in res["blind"] if d in covered} <= {"2026-03-12", "2026-03-13"}


@_real
def test_injecting_a_volume_replay_into_the_real_archive_turns_it_red(tmp_path):
    """真阳性对照：把 K 线库覆盖得到的最新一场的 volume 换成前一场的，volume 恒等式必须红。"""
    with open(REAL_ARCHIVE, newline="") as fh:
        rows = list(csv.DictReader(fh))
        head = list(rows[0].keys())
    covered = set(A.calendar(A.load_store(REAL_STORE)))
    days = sorted({r["date"] for r in rows} & covered)
    last, prev = days[-1], days[-2]
    prev_vol = {}
    for r in rows:
        if r["date"] == prev and r["volume"]:
            prev_vol.setdefault(r["ticker"], r["volume"])
    hit = 0
    for r in rows:
        if r["date"] == last and r["ticker"] in prev_vol and r["volume"]:
            r["volume"] = prev_vol[r["ticker"]]
            hit += 1
    assert hit > 50, "注射本身没生效，下面的红就没有意义"
    p = tmp_path / "injected_v.csv"
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=head)
        w.writeheader()
        w.writerows(rows)
    res = A.audit(p, REAL_STORE, declared={})
    assert last in res["volume"]["bad"], f"注射了一场成交量重放，volume 恒等式却没报 {last}"
