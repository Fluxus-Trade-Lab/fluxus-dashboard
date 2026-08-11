"""The calendar's job is to be checkable, and to admit when it cannot answer."""
from __future__ import annotations

import json

import pytest

from pipeline.reference import events as EV

SRC = "https://example.invalid/schedule"


def _rows(*specs):
    return [EV.entry(date=d, time=t, event=e, name=e, source=SRC)
            for d, t, e in specs]


CPI = _rows(("2026-07-14", "08:30", "CPI"), ("2026-08-12", "08:30", "CPI"),
            ("2026-09-11", "08:30", "CPI"))


def test_entry_refuses_an_unsourced_date():
    with pytest.raises(ValueError, match="source is required"):
        EV.entry(date="2026-08-12", event="CPI", name="CPI", source="")


def test_entry_refuses_an_unknown_event_key():
    with pytest.raises(ValueError, match="unknown event key"):
        EV.entry(date="2026-08-12", event="GDP", name="GDP", source=SRC)


def test_entry_refuses_a_malformed_date():
    with pytest.raises(ValueError):
        EV.entry(date="Aug 12 2026", event="CPI", name="CPI", source=SRC)


def test_a_later_row_corrects_an_earlier_one(tmp_path):
    p = tmp_path / "events.jsonl"
    EV.append(EV.entry(date="2026-02-11", event="CPI", name="CPI", source=SRC), p)
    EV.append(EV.entry(date="2026-02-13", event="CPI", name="CPI (moved)",
                       source=SRC), p)
    rows = EV.load(p)
    # Both dates survive as distinct rows -- a reschedule is a new date, not an
    # edit -- and neither is silently dropped.
    assert [r["date"] for r in rows] == ["2026-02-11", "2026-02-13"]

    # A true duplicate, though, collapses to the last one written.
    EV.append(EV.entry(date="2026-02-13", event="CPI", name="CPI (final)",
                       source=SRC), p)
    rows = EV.load(p)
    assert len(rows) == 2
    assert rows[-1]["name"] == "CPI (final)"


def test_load_of_a_missing_file_is_empty_not_an_error(tmp_path):
    assert EV.load(tmp_path / "nope.jsonl") == []


# --- the distinction the module exists for -------------------------------


def test_a_day_inside_coverage_that_is_not_the_event_is_a_mismatch():
    got = EV.check_claim("CPI day — expect continued chop", "2026-08-11", CPI)
    assert len(got) == 1
    assert got[0]["event"] == "CPI"
    assert got[0]["verdict"] == "mismatch"
    assert got[0]["nearest"]["date"] == "2026-08-12"
    assert got[0]["nearest"]["days_out"] == 1


def test_the_actual_event_day_is_confirmed():
    got = EV.check_claim("CPI day", "2026-08-12", CPI)
    assert got[0]["verdict"] == "confirmed"


def test_an_untracked_event_is_unknown_and_never_no():
    got = EV.check_claim("payroll Friday, expect a range", "2026-08-11", CPI)
    assert [g["event"] for g in got] == ["NFP"]
    assert got[0]["verdict"] == "unknown"
    assert "no NFP dates at all" in got[0]["note"]


def test_a_date_outside_the_stored_span_is_unknown_not_a_mismatch():
    # We hold July-September. Asking about June is a question we cannot answer,
    # and answering "not a CPI day" would be a fabrication.
    got = EV.check_claim("CPI day", "2026-06-10", CPI)
    assert got[0]["verdict"] == "unknown"
    assert "2026-07-14..2026-09-11" in got[0]["note"]


def test_covers_is_false_with_no_rows():
    assert EV.covers("CPI", "2026-08-12", []) is False


def test_a_rationale_naming_nothing_produces_nothing():
    assert EV.check_claim("spot above the flip, dealers long gamma",
                          "2026-08-11", CPI) == []


# --- text matching -------------------------------------------------------


def test_mentions_needs_a_word_boundary():
    assert EV.mentions("post-opex drift") == ["OPEX"]
    # "cpi" must not be conjured out of a longer token.
    assert EV.mentions("the cpix basket") == []


def test_mentions_matches_chinese_aliases():
    assert EV.mentions("明天非农，今天先观望") == ["NFP"]
    assert EV.mentions("议息会议前不动") == ["FOMC"]


def test_mentions_dedupes_one_event_named_two_ways():
    assert EV.mentions("nonfarm payroll") == ["NFP"]


# --- reporting -----------------------------------------------------------


def test_upcoming_carries_days_out_and_includes_today():
    got = EV.upcoming("2026-08-12", within=40, rows=CPI)
    assert [(r["date"], r["days_out"]) for r in got] == [
        ("2026-08-12", 0), ("2026-09-11", 30)]


def test_summary_names_what_it_can_speak_for():
    line = EV.summary("2026-08-11", rows=CPI)
    assert "nothing scheduled" in line
    assert "CPI +1d" in line
    # Without this, a line listing CPI alone reads as "CPI is all there is".
    assert "tracking CPI" in line


def test_summary_says_so_when_it_holds_nothing():
    assert "no event data held" in EV.summary("2026-08-11", rows=[])


def test_the_real_seeded_file_answers_the_day_this_module_was_built():
    """A guard on the shipped data, not just the logic."""
    rows = EV.load()
    if not rows:
        pytest.skip("calendar not seeded in this checkout")
    got = EV.check_claim("CPI day", "2026-08-11", rows)
    assert got[0]["verdict"] == "mismatch"
    assert got[0]["nearest"]["date"] == "2026-08-12"
    assert all(r["source"] for r in rows), "every row must carry provenance"
