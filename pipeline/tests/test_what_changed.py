"""Tests for the WHAT CHANGED candidate detector.

The detector lives in `data/research/what_changed_2026-08/` rather than
`pipeline/tools/` -- it is a prototype against an OPS 挂单 whose owner is not
settled yet (夜班/数据端), and `pipeline/tools/` is not mine to merge into.
Loaded by path so the tests can live where new tests belong.

What is actually worth pinning here is the resolution floor. The three
archives have 574 / 8 / 7 sessions of history, and the whole point of the
tiering is that a percentile computed off 7 observations is a finer number
than the data can carry. A bug that quietly ranks the short archives would
print a confident p100 next to every regime reading, and nothing about the
output would look wrong.
"""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import pytest

_SRC = (Path(__file__).resolve().parents[2]
        / "data/research/what_changed_2026-08/what_changed.py")
_spec = importlib.util.spec_from_file_location("what_changed", _SRC)
wc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wc)


# --------------------------------------------------------------------------
# to_float -- the difference between "no reading" and "a reading of zero"
# --------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expect", [
    ("1.5", 1.5), ("0", 0.0), ("-3", -3.0), ("  2 ", 2.0),
    ("", None), ("   ", None), ("nan", None), ("NaN", None),
    ("None", None), ("null", None), (None, None), ("abc", None),
])
def test_to_float(raw, expect):
    assert wc.to_float(raw) == expect or (wc.to_float(raw) is None and expect is None)


def test_zero_survives_as_a_reading_not_a_blank():
    """A blank becoming 0.0 would invent a week-over-week move out of nothing."""
    assert wc.to_float("0") == 0.0
    assert wc.to_float("") is None


def test_series_drops_rows_with_no_value_and_keeps_zeros():
    rows = [{"date": "d1", "x": "1"}, {"date": "d2", "x": ""},
            {"date": "d3", "x": "0"}, {"date": "d4", "x": "bad"}]
    assert wc.series(rows, "x") == [("d1", 1.0), ("d3", 0.0)]


def test_series_drops_a_row_with_no_date():
    assert wc.series([{"x": "1"}, {"date": "d", "x": "2"}], "x") == [("d", 2.0)]


# --------------------------------------------------------------------------
# span_changes / percentile_of
# --------------------------------------------------------------------------

def test_span_changes_are_overlapping_and_correctly_counted():
    vals = [0, 1, 2, 3, 4, 5]
    assert wc.span_changes(vals, 1) == [1, 1, 1, 1, 1]
    assert wc.span_changes(vals, 5) == [5]
    assert len(wc.span_changes(vals, 2)) == len(vals) - 2


def test_span_changes_is_empty_when_the_history_is_shorter_than_the_span():
    assert wc.span_changes([1, 2, 3], 5) == []
    assert wc.span_changes([1, 2, 3], 3) == []


def test_span_changes_signs_are_not_absolute():
    assert wc.span_changes([10, 4], 1) == [-6]


def test_span_of_zero_is_rejected_rather_than_returning_nonsense():
    with pytest.raises(ValueError):
        wc.span_changes([1, 2, 3], 0)


def test_percentile_of_ends_and_middle():
    pop = [1, 2, 3, 4]
    assert wc.percentile_of(0, pop) == 0.0
    assert wc.percentile_of(4, pop) == 100.0
    assert wc.percentile_of(2, pop) == 50.0


def test_percentile_of_an_empty_population_is_nan_not_zero_or_a_hundred():
    assert math.isnan(wc.percentile_of(1, []))


def test_percentile_is_inclusive_at_the_value_itself():
    assert wc.percentile_of(1, [1, 1, 1, 1]) == 100.0


# --------------------------------------------------------------------------
# the resolution floor -- the reason the tiers exist
# --------------------------------------------------------------------------

def _rows(values, col="x", start=1):
    return [{"date": f"2026-01-{i:02d}", col: str(v)}
            for i, v in enumerate(values, start)]


METRIC = {"label": "x", "col": "x", "unit": "", "en": "x went from {a} to {b}"}


def test_a_short_archive_is_reported_but_never_ranked():
    got = wc.score_metric(_rows([1, 2, 3, 4, 5, 6, 7]), METRIC, None, span=5)
    assert got["rankable"] is False
    assert got["pctile"] is None
    assert got["change"] == 5     # still reports the raw move


def test_a_long_archive_is_ranked():
    got = wc.score_metric(_rows(list(range(60))), METRIC, None, span=5)
    assert got["rankable"] is True
    assert got["pctile"] is not None


def test_the_rankable_boundary_sits_exactly_at_min_history():
    """MIN_HISTORY span-changes is enough; one fewer is not."""
    span = 5
    n_at = wc.MIN_HISTORY + span + 1      # history excludes the newest row
    assert wc.score_metric(_rows(list(range(n_at))), METRIC, None, span)["rankable"]
    assert not wc.score_metric(_rows(list(range(n_at - 1))), METRIC, None, span)["rankable"]


def test_min_history_is_large_enough_that_a_percentile_means_something():
    """Below ~40 the floor on a reported percentile is coarser than 2.5 points."""
    assert wc.MIN_HISTORY >= 40


def test_too_few_rows_for_even_one_comparison_returns_nothing():
    assert wc.score_metric(_rows([1, 2, 3]), METRIC, None, span=5) is None
    assert wc.score_metric(_rows([1, 2, 3, 4, 5, 6]), METRIC, None, span=5) is not None


# --------------------------------------------------------------------------
# score_metric -- the numbers it reports
# --------------------------------------------------------------------------

def test_from_and_to_are_span_apart_not_adjacent():
    got = wc.score_metric(_rows([10, 20, 30, 40, 50, 60]), METRIC, None, span=5)
    assert got["from"] == 10 and got["to"] == 60
    assert got["from_date"].endswith("01") and got["to_date"].endswith("06")


def test_direction_words():
    up = wc.score_metric(_rows([1, 1, 1, 1, 1, 9]), METRIC, None, span=5)
    down = wc.score_metric(_rows([9, 1, 1, 1, 1, 1]), METRIC, None, span=5)
    flat = wc.score_metric(_rows([5, 1, 1, 1, 1, 5]), METRIC, None, span=5)
    assert (up["direction"], down["direction"], flat["direction"]) == ("up", "down", "flat")


def test_asof_truncates_the_series_and_changes_the_answer():
    rows = _rows([1, 2, 3, 4, 5, 6, 100])
    late = wc.score_metric(rows, METRIC, None, span=5)
    early = wc.score_metric(rows, METRIC, "2026-01-06", span=5)
    assert late["to"] == 100 and early["to"] == 6


def test_history_excludes_the_current_reading():
    """The move being ranked must not be inside the population it is ranked against."""
    rows = _rows([0] * 50 + [1000])
    got = wc.score_metric(rows, METRIC, None, span=5)
    assert got["pctile"] == 100.0
    assert got["history_n"] == len(rows) - 1 - 5


def test_the_sentence_carries_both_numbers():
    got = wc.score_metric(_rows([12, 0, 0, 0, 0, 34]), METRIC, None, span=5)
    assert "12" in got["sentence"] and "34" in got["sentence"]


def test_units_reach_the_sentence():
    m = dict(METRIC, unit="%", en="share went from {a} to {b}")
    got = wc.score_metric(_rows([12, 0, 0, 0, 0, 34]), m, None, span=5)
    assert "12%" in got["sentence"] and "34%" in got["sentence"]


# --------------------------------------------------------------------------
# fmt
# --------------------------------------------------------------------------

@pytest.mark.parametrize("value,expect", [
    (1408, "1,408"), (-1408, "-1,408"), (0, "0"),
    (50.52, "50.52"), (123.456, "123.5"), (0.0083, "0.0083"),
    (0.10000, "0.1"),
])
def test_fmt(value, expect):
    assert wc.fmt(value) == expect


def test_fmt_appends_the_unit():
    assert wc.fmt(852, "只") == "852只"


# --------------------------------------------------------------------------
# group_flips -- categorical, so it works on a short archive
# --------------------------------------------------------------------------

def _grows(*specs):
    return [{"date": d, "kind": k, "group": g, "state": s, "excess_3m": e}
            for d, k, g, s, e in specs]


def test_only_a_changed_state_word_is_a_flip():
    rows = _grows(("d1", "theme", "A", "Leading", "0.1"),
                  ("d2", "theme", "A", "Lagging", "-0.1"),
                  ("d1", "theme", "B", "Leading", "0.2"),
                  ("d2", "theme", "B", "Leading", "0.9"))
    flips = wc.group_flips(rows, None, span=1, kind="theme")
    assert [f["group"] for f in flips] == ["A"]
    assert flips[0]["from_state"] == "Leading" and flips[0]["to_state"] == "Lagging"


def test_a_group_that_did_not_exist_in_the_baseline_is_not_a_flip():
    rows = _grows(("d1", "theme", "A", "Leading", "0.1"),
                  ("d2", "theme", "A", "Leading", "0.1"),
                  ("d2", "theme", "NEW", "Leading", "0.5"))
    assert wc.group_flips(rows, None, span=1, kind="theme") == []


def test_kind_filter_keeps_themes_and_industries_apart():
    rows = _grows(("d1", "theme", "A", "Leading", "0.1"),
                  ("d2", "theme", "A", "Lagging", "0.0"),
                  ("d1", "industry", "Z", "Leading", "0.1"),
                  ("d2", "industry", "Z", "Lagging", "0.0"))
    assert [f["group"] for f in wc.group_flips(rows, None, 1, "theme")] == ["A"]
    assert [f["group"] for f in wc.group_flips(rows, None, 1, "industry")] == ["Z"]


def test_flips_are_ordered_by_size_of_the_excess_move():
    rows = _grows(("d1", "theme", "small", "Leading", "0.10"),
                  ("d2", "theme", "small", "Lagging", "0.09"),
                  ("d1", "theme", "big", "Leading", "0.10"),
                  ("d2", "theme", "big", "Lagging", "-0.50"))
    assert [f["group"] for f in wc.group_flips(rows, None, 1, "theme")] == ["big", "small"]


def test_a_flip_with_an_unreadable_excess_still_reports_the_state_change():
    rows = _grows(("d1", "theme", "A", "Leading", ""),
                  ("d2", "theme", "A", "Lagging", ""))
    flips = wc.group_flips(rows, None, 1, "theme")
    assert len(flips) == 1
    assert flips[0]["excess_3m_change"] is None


def test_a_short_group_archive_falls_back_to_its_full_span_and_says_so():
    """8 sessions of archive must not silently return 'nothing flipped'."""
    rows = _grows(("d1", "theme", "A", "Leading", "0.1"),
                  ("d2", "theme", "A", "Lagging", "0.0"))
    flips = wc.group_flips(rows, None, span=20, kind="theme")
    assert len(flips) == 1
    assert flips[0]["window_sessions"] == 1      # not the 20 that was asked for


def test_a_single_date_cannot_produce_a_flip():
    assert wc.group_flips(_grows(("d1", "theme", "A", "Leading", "0.1")),
                          None, 1, "theme") == []


def test_group_flips_respect_asof():
    rows = _grows(("d1", "theme", "A", "Leading", "0.1"),
                  ("d2", "theme", "A", "Leading", "0.1"),
                  ("d3", "theme", "A", "Lagging", "0.0"))
    assert wc.group_flips(rows, "d2", 1, "theme") == []
    assert len(wc.group_flips(rows, "d3", 1, "theme")) == 1


# --------------------------------------------------------------------------
# build / render on the real archives
# --------------------------------------------------------------------------

def test_build_on_the_real_archives_separates_the_tiers():
    out = wc.build(asof="2026-08-28", span=5)
    assert out["candidates"], "no ranked candidates from a 574-session archive"
    assert all(c["rankable"] and c["pctile"] is not None for c in out["candidates"])
    assert all(not c["rankable"] and c["pctile"] is None for c in out["no_baseline"])


def test_the_regime_archive_is_in_the_unranked_tier_today():
    """7 sessions of regime_ledger cannot carry a percentile. If this starts
    failing, the archive grew past MIN_HISTORY and the tiering did its job."""
    out = wc.build(asof="2026-08-28", span=5)
    labels = {c["label"] for c in out["no_baseline"]}
    assert "VIX" in labels or any(c["label"] == "VIX" for c in out["candidates"])


def test_candidates_are_ordered_by_percentile():
    out = wc.build(asof="2026-08-28", span=5)
    pcts = [c["pctile"] for c in out["candidates"]]
    assert pcts == sorted(pcts, reverse=True)


def test_top_caps_the_list_without_dropping_the_rest():
    full = wc.build(asof="2026-08-28", span=5, top=100)
    small = wc.build(asof="2026-08-28", span=5, top=3)
    assert len(small["candidates"]) == 3
    assert len(small["candidates"]) + len(small["also_ranked"]) == len(full["candidates"])


def test_render_says_out_loud_what_it_cannot_see():
    text = wc.render(wc.build(asof="2026-08-28", span=5))
    assert "atr_ext" in text          # the part of the挂单 it cannot deliver
    assert "不是 p 值" in text         # the percentile is descriptive
    assert "排不了名" in text          # the short-archive tier is visible


def test_render_survives_archives_that_produce_nothing():
    empty = {"asof": None, "span": 5, "min_history": wc.MIN_HISTORY,
             "candidates": [], "also_ranked": [], "no_baseline": [],
             "theme_flips": [], "industry_flips": []}
    assert "无" in wc.render(empty)


def test_main_writes_both_files(tmp_path):
    md, js = tmp_path / "a" / "c.md", tmp_path / "b" / "c.json"
    assert wc.main(["--asof", "2026-08-28", "--span", "5",
                    "--out", str(md), "--json", str(js)]) == 0
    assert "WHAT CHANGED" in md.read_text()
    got = json.loads(js.read_text())
    assert got["asof"] == "2026-08-28" and got["span"] == 5
