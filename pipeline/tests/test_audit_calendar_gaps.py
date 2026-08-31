"""Tests for audit_calendar_gaps.

The point of this file is not that the auditor turns red on 2026-08-28. It is
that it turns red for the RIGHT REASON on each check independently, and that it
turns GREEN on a clean feed -- a guard nobody has watched go green is not a
guard, it is an alarm that is always on.

`pitfall_red_for_the_wrong_reason`: a check that fails because of a KeyError is
not a positive control. Every red case below is a feed that is well-formed and
wrong in exactly one way.
"""
from __future__ import annotations

import datetime as dt

import pytest

from pipeline.tools.audit_calendar_gaps import check, reconcile, trading_grid

# 2026-08-24..08-28 is a plain Mon-Fri week with no holiday in it.
START = dt.date(2026, 8, 24)
END = dt.date(2026, 8, 28)
WEEK = ["2026-08-24", "2026-08-25", "2026-08-26", "2026-08-27", "2026-08-28"]
NAMES = [f"T{i}" for i in range(10)]


def feed(sessions, tickers=NAMES):
    return {t: set(sessions) for t in tickers}


def test_the_week_we_test_against_is_really_five_sessions():
    # If this ever fails the rest of the file is testing a fiction.
    assert trading_grid(START, END) == WEEK


# --------------------------------------------------------------- green

def test_clean_feed_is_green():
    out = check(feed(WEEK), START, END, END)
    assert out["ok"], out["violations"]
    assert out["violations"] == [] and out["warnings"] == []
    assert out["sessions_expected"] == 5


def test_green_when_the_window_ends_before_the_last_complete_session():
    # Auditing Mon-Wed while Friday has already closed must not invent gaps.
    out = check(feed(WEEK[:3]), START, dt.date(2026, 8, 26), END)
    assert out["ok"], out["violations"]


# ----------------------------------------------------------------- C1/C4

def test_c1_universal_gap_is_a_violation():
    out = check(feed([d for d in WEEK if d != "2026-08-28"]), START, END, END)
    assert not out["ok"]
    assert any(v.startswith("C1 2026-08-28") for v in out["violations"])
    assert "FEED LOST A SESSION" in " ".join(out["violations"])
    gap = next(g for g in out["gaps"] if g["session"] == "2026-08-28")
    assert gap["universal"] and gap["missing"] == 10


def test_c4_sporadic_gap_is_only_a_warning():
    # One name did not trade on Thursday. That is a halt, not a feed outage,
    # and it must NOT fail the build.
    present = feed(WEEK)
    present["T3"] = set(WEEK) - {"2026-08-27"}
    out = check(present, START, END, END)
    assert out["ok"], out["violations"]
    assert any("C1 2026-08-27" in w and "sporadic" in w for w in out["warnings"])
    assert not next(g for g in out["gaps"] if g["session"] == "2026-08-27")["universal"]


def test_c4_threshold_is_where_it_says_it_is():
    # 8 of 10 missing == the 0.80 default, which is fatal; 7 of 10 is not.
    present = feed(WEEK)
    for t in NAMES[:8]:
        present[t] = set(WEEK) - {"2026-08-26"}
    assert not check(present, START, END, END)["ok"]

    present = feed(WEEK)
    for t in NAMES[:7]:
        present[t] = set(WEEK) - {"2026-08-26"}
    assert check(present, START, END, END)["ok"]


def test_c1_names_the_survivors_so_the_gap_can_be_diagnosed():
    # On 2026-08-28 exactly one of 90 names still carried anything. Naming it
    # is what let the claim "FBRX is the survivor" be checked -- and refuted:
    # FBRX had been halted since 07-20 and its bar was a zero-volume stale
    # quote (see C5). The list is here to be doubted, not to be trusted.
    present = feed([d for d in WEEK if d != "2026-08-28"])
    present["T7"] = set(WEEK)
    out = check(present, START, END, END)
    gap = next(g for g in out["gaps"] if g["session"] == "2026-08-28")
    assert gap["still_present"] == ["T7"]


# -------------------------------------------------------------------- C2

def test_c2_bar_past_the_last_completed_session_is_a_violation():
    # Mid-session on Friday: the feed hands back a live Friday bar while only
    # Thursday has actually closed.
    out = check(feed(WEEK), START, END, dt.date(2026, 8, 27))
    assert not out["ok"]
    assert any(v.startswith("C2 2026-08-28") for v in out["violations"])


def test_c2_does_not_fire_once_that_session_closes():
    assert check(feed(WEEK), START, END, END)["ok"]


# -------------------------------------------------------------------- C3

def test_c3_bar_on_a_non_trading_day_is_a_violation():
    # 2026-08-29 is a Saturday.
    out = check(feed(WEEK + ["2026-08-29"]), START, dt.date(2026, 8, 29), END)
    assert not out["ok"]
    assert any(v.startswith("C3 2026-08-29") for v in out["violations"])


# ------------------------------------------------- the failure being modelled

def test_it_reproduces_the_2026_08_28_shape_end_to_end():
    """Both real symptoms at once: Friday's close gone for all but one name,
    and a live Monday bar standing in the window while Friday is still the
    last completed session."""
    present = feed([d for d in WEEK if d != "2026-08-28"] + ["2026-08-31"])
    present["FBRX"] = set(WEEK) | {"2026-08-31"}
    out = check(present, START, dt.date(2026, 8, 31), END)
    kinds = {v.split()[0] for v in out["violations"]}
    assert kinds == {"C1", "C2"}
    assert next(g for g in out["gaps"]
                if g["session"] == "2026-08-28")["still_present"] == ["FBRX"]


@pytest.mark.parametrize("drop", WEEK)
def test_every_session_in_the_week_can_be_caught(drop):
    out = check(feed([d for d in WEEK if d != drop]), START, END, END)
    assert any(v.startswith(f"C1 {drop}") for v in out["violations"])


# ------------------------------------------------------------------------
# Added after a mutation sweep on this module returned 13/38. The survivors
# below were all inside check() -- lines where the auditor could have been
# wrong and nothing in this file would have said so.
# ------------------------------------------------------------------------

def test_the_counts_in_the_report_are_the_real_counts():
    # `missing`, `of` and `frac` are what a human reads to decide whether a gap
    # is an outage. A mutant that reports 8/10 as 9/10 survived until this.
    present = feed(WEEK)
    for t in NAMES[:6]:
        present[t] = set(WEEK) - {"2026-08-25"}
    gap = next(g for g in check(present, START, END, END)["gaps"]
               if g["session"] == "2026-08-25")
    assert (gap["missing"], gap["of"]) == (6, 10)
    assert gap["frac"] == pytest.approx(0.6)
    assert "6/10" in " ".join(check(present, START, END, END)["warnings"])


def test_c2_and_c3_report_how_many_tickers_carry_the_bad_bar():
    # One name printing a live bar is a listing quirk; all ten is the feed.
    # Nothing asserted `who` before, so both readings looked identical.
    present = {t: set(WEEK) for t in NAMES}
    present["T0"].add("2026-08-31")
    out = check(present, START, dt.date(2026, 8, 31), END)
    assert any("C2 2026-08-31: 1/10" in v for v in out["violations"])

    present = {t: set(WEEK) | {"2026-08-29"} for t in NAMES}   # a Saturday
    out = check(present, START, dt.date(2026, 8, 29), END)
    assert any("C3 2026-08-29: 10/10" in v for v in out["violations"])


def test_survivor_list_is_capped_so_one_outage_cannot_flood_the_report():
    # 20 names still have the session; the report shows five of them.
    names = [f"S{i:02d}" for i in range(26)]
    present = {t: set(WEEK) for t in names}
    for t in names[:6]:
        present[t] = set(WEEK) - {"2026-08-26"}
    gap = next(g for g in check(present, START, END, END, universal_frac=0.2)["gaps"]
               if g["session"] == "2026-08-26")
    assert gap["missing"] == 6 and gap["universal"]
    assert len(gap["still_present"]) == 5
    assert gap["still_present"] == sorted(names[6:])[:5]


def test_c3_only_looks_inside_the_audited_window():
    # A Saturday bar outside [start, end] is somebody else's problem; the
    # boundary is inclusive on both ends.
    present = {t: set(WEEK) | {"2026-08-22"} for t in NAMES}   # Sat before
    assert check(present, START, END, END)["ok"]
    out = check(present, dt.date(2026, 8, 22), END, END)
    assert any(v.startswith("C3 2026-08-22") for v in out["violations"])


def test_empty_ticker_set_does_not_pretend_the_feed_is_healthy():
    # Found while writing this file: check({}) used to return ok=True. Asking
    # about nothing and being told "no gaps" is the most expensive green there
    # is -- it is indistinguishable from a healthy feed at the call site.
    out = check({}, START, END, END)
    assert out["tickers"] == 0
    assert not out["ok"]
    assert any(v.startswith("C0") for v in out["violations"])


# ------------------------------------------------------------------------ C5

def test_c5_a_bar_that_is_not_a_session_is_a_violation():
    # Both real shapes: a null close beside a real-looking volume (a truncated
    # window handing back the live day under the missing day's date), and a
    # zero-volume O=H=L=C quote on a halted name.
    out = check(feed(WEEK), START, END, END,
                degenerate={"T0": {"2026-08-28"}, "T1": {"2026-08-28"}})
    assert not out["ok"]
    assert any(v.startswith("C5 2026-08-28: 2/10") for v in out["violations"])


def test_c5_is_silent_when_no_bar_quality_is_supplied():
    # Callers that cannot judge bar quality must not get a fabricated pass or
    # a fabricated failure -- C5 simply does not run.
    assert check(feed(WEEK), START, END, END, degenerate=None)["ok"]
    assert check(feed(WEEK), START, END, END, degenerate={})["ok"]


def test_c5_ignores_degenerate_bars_outside_the_window():
    out = check(feed(WEEK), START, END, END,
                degenerate={"T0": {"2026-07-01", "2026-09-15"}})
    assert out["ok"], out["violations"]


def test_c5_and_c1_are_different_failures_and_both_can_fire():
    # A day everyone lost AND a day one name fakes: the report must say both.
    present = feed([d for d in WEEK if d != "2026-08-27"])
    out = check(present, START, END, END, degenerate={"T4": {"2026-08-26"}})
    kinds = {v.split()[0] for v in out["violations"]}
    assert kinds == {"C1", "C5"}


# ------------------------------------------------------- three-way reconcile

def test_reconcile_is_quiet_when_all_three_agree():
    out = reconcile(feed(WEEK), set(WEEK), START, END, END)
    assert out["ok"] and out["findings"] == [] and out["warnings"] == []


def test_d1_archive_hole_the_market_traded_and_we_did_not_write_it():
    # `ticker_events.csv` shape: SPY has bars for 2026-04-07 / 06-08 / 07-14 /
    # 07-15 and our archive has no row for any of them.
    out = reconcile(feed(WEEK), set(WEEK) - {"2026-08-26"}, START, END, END)
    assert not out["ok"]
    assert any(v.startswith("D1 2026-08-26") and "ARCHIVE HOLE" in v
               for v in out["violations"])


def test_d2_calendar_wrong_is_a_warning_not_a_violation():
    # 2025-01-09 shape: marketcal says trading, no ticker has a bar, our
    # archive has no row. The calendar is the thing that is wrong, and an
    # ad-hoc closure must not fail anyone's build.
    out = reconcile(feed([d for d in WEEK if d != "2026-08-26"]),
                    set(WEEK) - {"2026-08-26"}, START, END, END)
    assert out["ok"], out["violations"]
    assert any(w.startswith("D2 2026-08-26") and "CALENDAR WRONG" in w
               for w in out["warnings"])


def test_d3_feed_regression_is_the_one_that_must_fail_loudly():
    # 2026-08-28 shape: our archive holds the session, the feed no longer
    # returns it. This is the only one of the three where data we already
    # consumed has gone missing underneath us.
    out = reconcile(feed([d for d in WEEK if d != "2026-08-28"]),
                    set(WEEK), START, END, END)
    assert not out["ok"]
    assert any(v.startswith("D3 2026-08-28") and "FEED REGRESSION" in v
               for v in out["violations"])


def test_d2_and_d3_are_indistinguishable_without_the_archive():
    """The point of the whole three-way. Feed and calendar see the same thing
    in both cases; only the archive tells them apart."""
    absent = feed([d for d in WEEK if d != "2026-08-26"])
    as_d2 = reconcile(absent, set(WEEK) - {"2026-08-26"}, START, END, END)
    as_d3 = reconcile(absent, set(WEEK), START, END, END)
    assert [f["kind"] for f in as_d2["findings"]] == ["D2"]
    assert [f["kind"] for f in as_d3["findings"]] == ["D3"]
    assert as_d2["ok"] and not as_d3["ok"]


def test_reconcile_refuses_an_empty_sample_too():
    out = reconcile({}, set(WEEK), START, END, END)
    assert not out["ok"] and any(v.startswith("C0") for v in out["violations"])


def test_d1_exempts_the_newest_session_because_the_writer_runs_after_the_close():
    # Found the moment the market closed on 2026-08-31: last_completed_session
    # flipped to today, tonight's cron had not run, and the reconcile reported
    # today's legitimate absence as an ARCHIVE HOLE. A gate that is red every
    # evening by design is a gate nobody reads.
    out = reconcile(feed(WEEK), set(WEEK) - {"2026-08-28"}, START, END, END)
    assert out["ok"], out["violations"]

    # ...but only the newest one. Yesterday's absence is still a hole.
    out = reconcile(feed(WEEK), set(WEEK) - {"2026-08-27"}, START, END, END)
    assert any(v.startswith("D1 2026-08-27") for v in out["violations"])


def test_grace_never_covers_d3():
    # A session the archive already holds cannot un-happen, so the vendor
    # deleting today's bar must fail even inside the grace window.
    out = reconcile(feed([d for d in WEEK if d != "2026-08-28"]),
                    set(WEEK), START, END, END)
    assert any(v.startswith("D3 2026-08-28") for v in out["violations"])


def test_grace_of_zero_reports_everything():
    out = reconcile(feed(WEEK), set(WEEK) - {"2026-08-28"}, START, END, END,
                    grace_sessions=0)
    assert any(v.startswith("D1 2026-08-28") for v in out["violations"])
