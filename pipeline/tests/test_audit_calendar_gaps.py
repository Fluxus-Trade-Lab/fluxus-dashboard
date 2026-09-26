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
import textwrap

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


def test_c2_for_the_session_in_progress_is_a_warning_not_a_violation():
    # 2026-09-15 04:3x JST the real tool went red mid-session on a healthy
    # feed. The live bar of the session that is open is what every mid-session
    # download looks like; red there reports the clock, not the feed.
    out = check(feed(WEEK), START, END, dt.date(2026, 8, 27),
                in_progress=dt.date(2026, 8, 28))
    assert out["ok"], out["violations"]
    assert out["violations"] == []
    assert any(w.startswith("C2 2026-08-28: 10/10") and "in progress" in w
               for w in out["warnings"])


def test_c2_past_the_session_in_progress_is_still_a_violation():
    # Friday is open; a bar dated Monday is not Friday's live bar.
    present = feed(WEEK + ["2026-08-31"])
    out = check(present, START, dt.date(2026, 8, 31), dt.date(2026, 8, 27),
                in_progress=dt.date(2026, 8, 28))
    assert not out["ok"]
    assert [v.split(":")[0] for v in out["violations"]] == ["C2 2026-08-31"]
    assert any(w.startswith("C2 2026-08-28") for w in out["warnings"])


class TestSessionInProgress:
    ET = dt.timezone(dt.timedelta(hours=-4))   # EDT, no DST edge in September

    def _at(self, y, m, d, hh, mm):
        return dt.datetime(y, m, d, hh, mm, tzinfo=self.ET)

    def test_mid_session_monday_is_in_progress(self):
        from pipeline.tools.audit_calendar_gaps import session_in_progress
        # the exact moment the false red was seen
        assert session_in_progress(self._at(2026, 9, 14, 15, 31)) == dt.date(2026, 9, 14)

    def test_premarket_counts_as_in_progress(self):
        from pipeline.tools.audit_calendar_gaps import session_in_progress
        assert session_in_progress(self._at(2026, 9, 14, 5, 0)) == dt.date(2026, 9, 14)

    def test_after_the_close_nothing_is_in_progress(self):
        from pipeline.tools.audit_calendar_gaps import session_in_progress
        assert session_in_progress(self._at(2026, 9, 14, 16, 0)) is None
        assert session_in_progress(self._at(2026, 9, 14, 15, 59)) == dt.date(2026, 9, 14)

    def test_weekend_and_holiday_are_never_in_progress(self):
        from pipeline.tools.audit_calendar_gaps import session_in_progress
        assert session_in_progress(self._at(2026, 9, 12, 12, 0)) is None   # Saturday
        assert session_in_progress(self._at(2026, 9, 7, 12, 0)) is None    # Labor Day


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


# ----------------------------------------------------------- 2026-09-02
# classify_bar was lifted out of fetch() so it could be reached at all. The
# mutation sweep had 17 of this module's 52 survivors sitting on its four
# lines: every boolean in the check was unpinned, including the one that tells
# a halted-but-still-quoted name from a live one. Each test below names the
# mutant it kills.

NAN = float("nan")


def _bar(o=None, h=None, lo=None, c=None, v=None):
    return {"Open": o, "High": h, "Low": lo, "Close": c, "Volume": v}


class TestClassifyBar:
    """The FBRX shape and its neighbours.

    2026-09-01 read FBRX's O=H=L=C=76.99 / Volume=0 row as "the one ticker that
    still had data" -- it was a stale-price placeholder for a name halted since
    07-20. `having a row is not having data`, and this is the function that
    knows the difference."""

    def test_an_ordinary_session_is_good(self):
        from pipeline.tools.audit_calendar_gaps import classify_bar
        assert classify_bar(_bar(10.0, 11.0, 9.5, 10.5, 1_000_000)) == "good"

    def test_the_fbrx_shape_is_bad(self):
        """Flat OHLC and zero volume: quoted, not traded."""
        from pipeline.tools.audit_calendar_gaps import classify_bar
        assert classify_bar(_bar(76.99, 76.99, 76.99, 76.99, 0)) == "bad"

    def test_flat_but_traded_is_good_not_bad(self):
        """A real session can print flat OHLC on a thin name. Volume is what
        separates it from the placeholder -- kills L292 `== 0` -> `!= 0`."""
        from pipeline.tools.audit_calendar_gaps import classify_bar
        assert classify_bar(_bar(5.0, 5.0, 5.0, 5.0, 4_200)) == "good"

    def test_moving_but_zero_volume_is_good(self):
        """Zero volume alone is not the signal; flatness AND zero volume is.
        Kills L292 `and` -> `or`."""
        from pipeline.tools.audit_calendar_gaps import classify_bar
        assert classify_bar(_bar(10.0, 11.0, 9.5, 10.5, 0)) == "good"

    def test_a_null_close_with_volume_is_bad(self):
        """Something claims a session happened while the price is missing."""
        from pipeline.tools.audit_calendar_gaps import classify_bar
        assert classify_bar(_bar(None, None, None, None, 900)) == "bad"
        assert classify_bar(_bar(c=NAN, v=900)) == "bad"

    def test_one_share_still_counts_as_volume(self):
        """`float(vol) > 0`, not `> 1`. A single share printed against a null
        close is still something claiming a session happened, and the boundary
        is where a guard is worth pinning -- 900 and 5 pass either way."""
        from pipeline.tools.audit_calendar_gaps import classify_bar
        assert classify_bar(_bar(c=None, v=1)) == "bad"

    def test_a_wholly_empty_row_is_padding_not_a_finding(self):
        """The calendar pads non-sessions. Padding must not be reported --
        kills L287 `> 0` -> `>= 0` and `0` -> `1`."""
        from pipeline.tools.audit_calendar_gaps import classify_bar
        assert classify_bar(_bar()) == "padding"
        assert classify_bar(_bar(c=NAN, v=0)) == "padding"
        assert classify_bar(_bar(c=NAN, v=NAN)) == "padding"

    def test_nan_volume_is_not_a_number_it_is_an_absence(self):
        """`vol == vol` is the NaN test. Flip it and every NaN volume is
        treated as a value -- kills L287/L292 `==` -> `!=`."""
        from pipeline.tools.audit_calendar_gaps import classify_bar
        # flat bar, NaN volume: we cannot say it was quoted-but-not-traded
        assert classify_bar(_bar(5.0, 5.0, 5.0, 5.0, NAN)) == "good"
        # null close, NaN volume: nothing claims a session -- padding
        assert classify_bar(_bar(c=None, v=NAN)) == "padding"

    def test_a_null_close_is_none_or_nan_and_nothing_else(self):
        """`close is None or close != close`. Kills L283's `or` -> `and`,
        `is` -> `is not`, and `!=` -> `==`."""
        from pipeline.tools.audit_calendar_gaps import classify_bar
        # None close, volume present -> the null branch fires
        assert classify_bar(_bar(c=None, v=5)) == "bad"
        # NaN close, volume present -> the null branch fires too
        assert classify_bar(_bar(c=NAN, v=5)) == "bad"
        # a real close never takes the null branch, even at zero
        assert classify_bar(_bar(0.0, 1.0, 0.0, 0.0, 5)) == "good"

    def test_flatness_compares_all_four_legs(self):
        """`o == h == lo == close`. Each `==` is load-bearing: break any one
        and a bar that moved on that leg gets called a placeholder."""
        from pipeline.tools.audit_calendar_gaps import classify_bar
        for bar in (_bar(9.0, 10.0, 10.0, 10.0, 0),     # open differs
                    _bar(10.0, 11.0, 10.0, 10.0, 0),    # high differs
                    _bar(10.0, 10.0, 9.0, 10.0, 0),     # low differs
                    _bar(10.0, 10.0, 10.0, 9.0, 0)):    # close differs
            assert classify_bar(bar) == "good", bar


# ----------------------------------------------------------- 2026-09-27
# `read_archive_dates` and `main` had no tests at all. 19 of this module's 37
# surviving mutants sat on those two functions -- the whole `--archive` entry
# path and the exit code. Each test below names the mutant it kills, and each
# one was run against that mutant before it was written down.

from pipeline.tools import audit_calendar_gaps as acg   # noqa: E402


def _csv(tmp_path, text, name="a.csv"):
    p = tmp_path / name
    p.write_text(textwrap.dedent(text))
    return p


class TestReadArchiveDates:
    """The function that turns one of our CSV archives into a set of sessions.

    It is the only thing standing between `--archive` and a three-way
    reconcile built on the wrong column. Reading zero dates out of a healthy
    archive does not look like a crash -- it looks like D1 firing on every
    session we ever wrote.
    """

    def test_it_finds_the_as_of_column(self, tmp_path):
        """The ordinary case, and the one that pins `column or next(...)`.

        `or` -> `and` turns a call with no explicit column into `None`, and
        then into SystemExit "cannot find a date column" on a file that has
        one. Kills L358 `Or -> And`.
        """
        p = _csv(tmp_path, """\
            as_of,ticker
            2026-08-24,SPY
            2026-08-25,SPY
            """)
        assert acg.read_archive_dates(p) == {"2026-08-24", "2026-08-25"}

    def test_it_falls_through_to_the_next_candidate_column(self, tmp_path):
        """No `as_of`, but a `date`. `if c in rows[0]` is what walks the list.

        Flip it to `not in` and the first candidate always wins, so `col`
        becomes a column the file does not have -- and then `r.get(col)` is
        None for every row and the archive reads as EMPTY, silently.
        Kills L359 `In -> NotIn`.
        """
        p = _csv(tmp_path, """\
            date,close
            2026-08-26,1
            """)
        assert acg.read_archive_dates(p) == {"2026-08-26"}

    @pytest.mark.parametrize("col", ["as_of", "date", "session", "Date"])
    def test_all_four_declared_candidates_are_really_tried(self, tmp_path, col):
        p = _csv(tmp_path, f"{col},x\n2026-08-27,1\n")
        assert acg.read_archive_dates(p) == {"2026-08-27"}

    def test_a_single_row_archive_is_read_not_indexed_past(self, tmp_path):
        """Header detection reads `rows[0]`; `rows[1]` on a one-row file is an
        IndexError. Kills L359 `0 -> 1`."""
        p = _csv(tmp_path, "as_of\n2026-08-24\n")
        assert acg.read_archive_dates(p) == {"2026-08-24"}

    def test_a_findable_column_does_not_raise(self, tmp_path):
        """`if col is None: raise`. Flip it to `is not None` and every healthy
        archive exits with "cannot find a date column". Kills L360
        `Is -> IsNot`."""
        p = _csv(tmp_path, "session\n2026-08-24\n")
        acg.read_archive_dates(p)          # must not raise

    def test_an_unnameable_column_raises_instead_of_guessing(self, tmp_path):
        """The other side of the same line: positive control on the SystemExit."""
        p = _csv(tmp_path, "when,x\n2026-08-24,1\n")
        with pytest.raises(SystemExit):
            acg.read_archive_dates(p)

    def test_an_explicit_column_overrides_the_candidates(self, tmp_path):
        """Both `as_of` and `stamp` are present; `--date-col stamp` must win."""
        p = _csv(tmp_path, "as_of,stamp\n2026-08-24,2026-08-30\n")
        assert acg.read_archive_dates(p, "stamp") == {"2026-08-30"}

    def test_an_empty_archive_is_empty_not_an_indexerror(self, tmp_path):
        """`if not rows: return set()`. Drop the `not` and a healthy archive
        returns nothing while an empty one crashes on `rows[0]` -- both
        directions wrong. Kills L356 `drop not`."""
        assert acg.read_archive_dates(_csv(tmp_path, "as_of\n")) == set()

    def test_a_timestamp_is_truncated_to_the_session_date(self, tmp_path):
        """`[:10]`, not `[:11]`. An 11-character slice keeps the `T` and every
        date stops matching the calendar grid, so D1 fires on all of them.
        Kills L362 `10 -> 11`."""
        p = _csv(tmp_path, "as_of\n2026-08-24T09:30:00-04:00\n")
        assert acg.read_archive_dates(p) == {"2026-08-24"}

    def test_a_blank_cell_is_skipped_not_sliced(self, tmp_path):
        p = _csv(tmp_path, "as_of,x\n2026-08-24,1\n,2\n")
        assert acg.read_archive_dates(p) == {"2026-08-24"}


class TestMain:
    """The entry point: exit code, window wording, and the `--archive` branch.

    `main` had no test of any kind. The one that matters most is the exit
    code: `return 0 if out["ok"] else 1` inverted is a guard that goes red on
    every clean night, and the thing people learn from a check that is always
    red is to stop reading it. That shape has now been found in
    `audit_archives`, `audit_ledger`, `audit_ci_test_coverage` and here --
    fourth time, so it gets pinned rather than noted.
    """

    def _run(self, monkeypatch, capsys, argv=("--days", "4"), dates=WEEK,
             degenerate=None, last=END, tickers=("A", "B")):
        seen = {}

        def fake_fetch(names, start, end):
            seen["call"] = (list(names), start, end)
            per = dates if isinstance(dates, dict) else {t: set(dates) for t in names}
            return per, (degenerate or {})

        monkeypatch.setattr(acg, "fetch", fake_fetch)
        monkeypatch.setattr(acg, "last_completed_session", lambda *a, **k: last)
        monkeypatch.setattr(acg, "session_in_progress", lambda *a, **k: None)
        code = acg.main(["--tickers", ",".join(tickers), *argv])
        return code, capsys.readouterr().out, seen

    def test_a_clean_feed_exits_zero(self, monkeypatch, capsys):
        """Kills L423 `0 -> 1`: the always-red guard nobody reads."""
        code, out, _ = self._run(monkeypatch, capsys)
        assert code == 0
        assert "OK: 0 violations" in out

    def test_a_lost_session_exits_one(self, monkeypatch, capsys):
        """Positive control on the same line, in the direction it is for."""
        code, out, _ = self._run(monkeypatch, capsys,
                                 dates=[d for d in WEEK if d != "2026-08-26"])
        assert code == 1
        assert "VIOLATIONS" in out and "C1 2026-08-26" in out

    def test_a_feed_that_returns_nothing_says_so_before_auditing(
            self, monkeypatch, capsys):
        """`if not present` guards the whole audit. Kills L393 `drop not`
        (which turns every healthy feed into "returned nothing") and L395
        `1 -> 2` (the exit code for it)."""
        code, out, _ = self._run(monkeypatch, capsys, dates={})
        assert code == 1
        assert "feed returned nothing at all" in out
        # and the audit itself never ran, so no C-code is reported
        assert "C0" not in out and "C1" not in out

    def test_the_window_is_printed_start_then_end(self, monkeypatch, capsys):
        """`out['window'][0]` is the start. Printing [1]..[0] reverses the
        window on every line of every report. Kills L407 `0 -> 1` / `1 -> 2`."""
        _, out, _ = self._run(monkeypatch, capsys)
        assert "window 2026-08-24..2026-08-28" in out

    def test_the_archive_branch_prints_the_same_window_the_same_way(
            self, monkeypatch, capsys, tmp_path):
        """The `--archive` path has its own copy of that line. Kills L401
        `0 -> 1` / `1 -> 2`."""
        arc = tmp_path / "a.csv"
        arc.write_text("as_of\n" + "\n".join(WEEK) + "\n")
        code, out, _ = self._run(monkeypatch, capsys,
                                 argv=("--days", "4", "--archive", str(arc)))
        assert "window 2026-08-24..2026-08-28" in out
        assert str(arc) in out and code == 0

    def test_the_default_window_is_thirty_days(self, monkeypatch, capsys):
        """`--days` default 30, not 31. Kills L368 `30 -> 31`.

        Asserted through the printed window rather than the parser's default,
        so it still says something if the arithmetic moves.
        """
        _, out, _ = self._run(monkeypatch, capsys, argv=())
        assert f"window {END - dt.timedelta(days=30)}..{END}" in out

    def test_the_feed_is_asked_three_days_past_the_window(
            self, monkeypatch, capsys):
        """C2 can only see a bar past the last session if the fetch reached
        past it. Kills L392 `3 -> 4` -- and a 4th day would put a Tuesday bar
        inside the sample that C3 then reports as a calendar disagreement."""
        _, _, seen = self._run(monkeypatch, capsys)
        assert seen["call"][2] == END + dt.timedelta(days=3)

    def test_the_c5_hint_is_only_printed_under_a_universal_gap(
            self, monkeypatch, capsys):
        """`g["universal"] and g["still_present"]`. Under `or`, every sporadic
        gap gets the "check C5 before calling these survivors" line appended to
        a warning that has no survivors to check. Kills L415 `And -> Or`."""
        names = [f"T{i}" for i in range(10)]
        dates = {t: set(WEEK) for t in names}
        dates["T0"] = set(WEEK) - {"2026-08-26"}       # 1/10 -> sporadic
        code, out, _ = self._run(monkeypatch, capsys, dates=dates,
                                 tickers=tuple(names))
        assert "sporadic" in out                        # the gap was reported
        assert "check C5" not in out                    # but not as a survivor list
        assert code == 0

    def test_a_universal_gap_with_survivors_does_get_the_hint(
            self, monkeypatch, capsys):
        """The other side: 9/10 missing is universal, and the 10th is exactly
        the FBRX shape this hint exists to warn about."""
        names = [f"T{i}" for i in range(10)]
        dates = {t: set(WEEK) - {"2026-08-26"} for t in names}
        dates["T9"] = set(WEEK)
        _, out, _ = self._run(monkeypatch, capsys, dates=dates,
                              tickers=tuple(names))
        assert "2026-08-26 still has a bar for: T9" in out
        assert "check C5" in out

    def test_the_grace_window_is_one_session_not_two(
            self, monkeypatch, capsys, tmp_path):
        """`--grace-sessions` default 1: the nightly writer runs after the
        close, so today's absence from the archive is normal and yesterday's
        is not. Kills L381 `1 -> 2`, which would swallow a real missed night.
        """
        arc = tmp_path / "a.csv"
        arc.write_text("as_of\n" + "\n".join(WEEK[:-2]) + "\n")   # 08-27/28 absent
        code, out, _ = self._run(monkeypatch, capsys,
                                 argv=("--days", "4", "--archive", str(arc)))
        assert code == 1
        assert "2026-08-27" in out                  # not exempt
        assert "D1 2026-08-28" not in out           # exempt by the grace window

    def test_the_json_report_is_the_report(self, monkeypatch, capsys, tmp_path):
        out_path = tmp_path / "r.json"
        code, _, _ = self._run(monkeypatch, capsys,
                               argv=("--days", "4", "--json", str(out_path)))
        import json as _json
        got = _json.loads(out_path.read_text())
        assert got["window"] == ["2026-08-24", "2026-08-28"]
        assert got["ok"] is True and code == 0
