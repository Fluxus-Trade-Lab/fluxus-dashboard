"""Archive invariants (pipeline/tools/audit_archives.py)."""
from __future__ import annotations

import datetime as dt
import json

import pandas as pd

from pipeline.tools import audit_archives as A

LAST = dt.date(2026, 8, 18)   # a Tuesday; 2026-08-19 is the (untraded) next day


def _write(tmp_path, name, rows):
    p = tmp_path / name
    pd.DataFrame(rows).to_csv(p, index=False)
    return p


def test_clean_archives_pass(tmp_path):
    _write(tmp_path, "breadth_archive.csv", [
        {"date": "2026-08-17", "spx_close": 7745.06}, {"date": "2026-08-18", "spx_close": 7691.76}])
    _write(tmp_path, "leaders_log.csv", [{"date": "2026-08-18", "ticker": "A"}, {"date": "2026-08-18", "ticker": "B"}])
    out = A.run(tmp_path, last_done=LAST, output=None)
    assert out["ok"] and out["violations"] == 0


def test_future_row_identical_spx_and_dupes_are_violations_and_repairable(tmp_path):
    p = _write(tmp_path, "breadth_archive.csv", [
        {"date": "2026-08-17", "spx_close": 7745.06}, {"date": "2026-08-18", "spx_close": 7691.76},
        {"date": "2026-08-19", "spx_close": 7691.76}])                     # the 08-19 premarket row
    q = _write(tmp_path, "leaders_log.csv", [
        {"date": "2026-08-18", "ticker": "A"}, {"date": "2026-08-18", "ticker": "A"},   # dup
        {"date": "2026-08-16", "ticker": "B"}])                                         # Sunday
    out = A.run(tmp_path, last_done=LAST, output=None)
    assert not out["ok"]
    by = {r["archive"]: r for r in out["archives"]}
    assert any(v.startswith("I1 2026-08-19") for v in by["breadth_archive.csv"]["violations"])
    assert any(v.startswith("I3 2026-08-19") for v in by["breadth_archive.csv"]["violations"])
    assert any(v.startswith("I1 2026-08-16") for v in by["leaders_log.csv"]["violations"])
    assert any(v.startswith("I2 1 duplicate") for v in by["leaders_log.csv"]["violations"])
    out2 = A.run(tmp_path, do_repair=True, last_done=LAST, output=None)
    assert not out2["ok"]          # this pass reports what it removed
    assert A.run(tmp_path, last_done=LAST, output=None)["ok"]
    assert (tmp_path / "breadth_archive.csv.bak").exists()
    assert pd.read_csv(p).date.tolist() == ["2026-08-17", "2026-08-18"]
    assert len(pd.read_csv(q)) == 1


def test_count_collapse_and_staleness_are_warnings_not_violations(tmp_path):
    rows = [{"date": f"2026-07-{d:02d}", "ticker": t} for d in (20, 21, 22, 23, 24, 27, 28) for t in "ABCDEFGHIJ"]
    rows += [{"date": "2026-07-29", "ticker": "A"}]       # 1 row vs median 10
    _write(tmp_path, "leaders_log.csv", rows)
    out = A.run(tmp_path, last_done=LAST, output=None)
    assert out["ok"]
    w = {r["archive"]: r["warnings"] for r in out["archives"]}["leaders_log.csv"]
    assert any(x.startswith("I4 2026-07-29") for x in w) and any(x.startswith("I5") for x in w)


# ---------------------------------------------------------------------------
# I6 (reconcile) and I7 (ticker shells) had NO tests at all: every case above
# calls run(..., output=None), so the whole reconcile() body was never entered.
# I6a is the check that stopped the 2026-08-25 publish (ADR gate wired into
# only one of two writers, DATA_CONTRACTS §十一) -- i.e. the repo's most
# expensive guard to date was the one nothing pinned.
#
# Found by pipeline/tools/audit_mutation_sweep.py: `!=` -> `==` on the count
# comparison, `not p.exists()` -> `p.exists()`, and `>` -> `>=` on the shell
# rate all left the suite green. Each test below is written so that the
# corresponding mutation turns it red; the sweep re-run is the receipt.
# ---------------------------------------------------------------------------

DATE = "2026-08-18"


def _wl(panels, date=DATE):
    """A watchlist.json with one zone, whichever panels are handed in."""
    return {"date": date, "zones": [{"key": "z", "label": "Z", "panels": panels}]}


def _out(tmp_path, **files):
    d = tmp_path / "output"
    d.mkdir(exist_ok=True)
    for name, payload in files.items():
        (d / f"{name}.json").write_text(json.dumps(payload))
    return d


def _rep(out, archive):
    return {r["archive"]: r for r in out["archives"]}[archive]


class TestReconcileI6a:
    """watchlist.json panel counts vs watchlist_hits.csv rows, same date."""

    def _fixture(self, tmp_path, json_count, n_hit_rows, measured=True, hits_date=DATE):
        _write(tmp_path, "watchlist_hits.csv",
               [{"date": hits_date, "panel": "vcs", "ticker": f"T{i}"} for i in range(n_hit_rows)])
        out_dir = _out(tmp_path, watchlist=_wl([{"key": "vcs", "measured": measured,
                                                "count": json_count}]))
        return A.run(tmp_path, last_done=LAST, output=out_dir)

    def test_counts_agree_is_not_a_violation(self, tmp_path):
        out = self._fixture(tmp_path, json_count=3, n_hit_rows=3)
        assert _rep(out, "reconcile(I6)")["violations"] == []

    def test_counts_disagree_is_a_violation(self, tmp_path):
        # the positive control: this is the 08-25 shape, page says 4, archive has 8
        out = self._fixture(tmp_path, json_count=4, n_hit_rows=8)
        v = _rep(out, "reconcile(I6)")["violations"]
        assert any(x.startswith(f"I6a {DATE} vcs") for x in v), v
        assert "4" in v[0] and "8" in v[0]
        assert not out["ok"]

    def test_unmeasured_panels_are_not_reconciled(self, tmp_path):
        # a panel that says it did not measure itself cannot disagree with anything
        out = self._fixture(tmp_path, json_count=4, n_hit_rows=8, measured=False)
        assert _rep(out, "reconcile(I6)")["violations"] == []

    def test_hits_from_another_session_do_not_count_as_this_one(self, tmp_path):
        # rows exist, but for a different date -- reconciling against them would
        # compare today's page with yesterday's archive
        out = self._fixture(tmp_path, json_count=4, n_hit_rows=4, hits_date="2026-08-17")
        r = _rep(out, "reconcile(I6)")
        assert r["violations"] == []
        assert any(x.startswith("I6a no watchlist_hits rows") for x in r["warnings"]), r["warnings"]


class TestReconcileI6b:
    """screener JSON row counts vs ticker_events.csv rows for the newest date."""

    def _fixture(self, tmp_path, csv_tickers, json_tickers, newest=DATE, write_json=True):
        rows = [{"date": "2026-08-17", "ticker": "OLD", "screener": "gainers_4pct"}]
        rows += [{"date": newest, "ticker": t, "screener": "gainers_4pct"} for t in csv_tickers]
        _write(tmp_path, "ticker_events.csv", rows)
        files = {"gainers_4pct": {"tickers": [{"ticker": t} for t in json_tickers]}} if write_json else {}
        return A.run(tmp_path, last_done=LAST, output=_out(tmp_path, **files))

    def test_counts_agree_is_not_a_violation(self, tmp_path):
        out = self._fixture(tmp_path, ["A", "B"], ["A", "B"])
        assert [v for v in _rep(out, "reconcile(I6)")["violations"] if v.startswith("I6b")] == []

    def test_counts_disagree_is_a_violation(self, tmp_path):
        out = self._fixture(tmp_path, ["A", "B"], ["A", "B", "C"])
        v = [x for x in _rep(out, "reconcile(I6)")["violations"] if x.startswith("I6b")]
        assert v and "3 rows vs ticker_events 2" in v[0], v

    def test_a_screener_with_no_json_is_skipped_not_reconciled_against_zero(self, tmp_path):
        # the file is absent, not empty -- treating absent as 0 rows would fire
        # I6b on every screener we do not export
        out = self._fixture(tmp_path, ["A", "B"], [], write_json=False)
        assert [v for v in _rep(out, "reconcile(I6)")["violations"] if v.startswith("I6b")] == []

    def test_only_the_newest_session_is_reconciled(self, tmp_path):
        # 08-17 has one row and no matching JSON count; it must not be compared
        out = self._fixture(tmp_path, ["A"], ["A"])
        assert [v for v in _rep(out, "reconcile(I6)")["violations"] if v.startswith("I6b")] == []


class TestReconcileI6c:
    """breadth_archive universe_size vs universe.json rows -- a warning."""

    def _fixture(self, tmp_path, size, n_rows):
        _write(tmp_path, "breadth_archive.csv",
               [{"date": "2026-08-17", "spx_close": 7745.06, "universe_size": size - 1},
                {"date": DATE, "spx_close": 7691.76, "universe_size": size}])
        return A.run(tmp_path, last_done=LAST,
                     output=_out(tmp_path, universe={"rows": [{"t": i} for i in range(n_rows)]}))

    def test_agree_is_silent(self, tmp_path):
        r = _rep(self._fixture(tmp_path, 100, 100), "reconcile(I6)")
        assert [w for w in r["warnings"] if w.startswith("I6c")] == []

    def test_disagree_is_a_warning_not_a_violation(self, tmp_path):
        out = self._fixture(tmp_path, 100, 97)
        r = _rep(out, "reconcile(I6)")
        assert any(w.startswith("I6c breadth universe_size 100") for w in r["warnings"]), r["warnings"]
        assert r["violations"] == []


class TestTickerShellsI7:
    """Empty-shell rate in data/output/tickers/."""

    def _dir(self, tmp_path, n_full, n_shell, extra_underscore=0):
        d = tmp_path / "output" / "tickers"
        d.mkdir(parents=True, exist_ok=True)
        for i in range(n_full):
            (d / f"F{i}.json").write_text(json.dumps({"ohlc_2y": [{"c": 1}]}))
        for i in range(n_shell):
            (d / f"S{i}.json").write_text(json.dumps({"ohlc_2y": []}))
        for i in range(extra_underscore):
            (d / f"_bench{i}.json").write_text(json.dumps({}))
        return tmp_path / "output"

    def test_no_shells_is_silent(self, tmp_path):
        r = A.ticker_shells(self._dir(tmp_path, 20, 0))
        assert r["violations"] == [] and r["warnings"] == [] and r["rows"] == 20

    def test_rate_at_the_threshold_is_a_warning(self, tmp_path):
        r = A.ticker_shells(self._dir(tmp_path, 18, 2))       # exactly 10%
        assert r["violations"] == []
        assert any(w.startswith("I7 2/20 empty shells") for w in r["warnings"]), r["warnings"]

    def test_rate_above_the_threshold_is_a_violation(self, tmp_path):
        r = A.ticker_shells(self._dir(tmp_path, 17, 3))       # 15%
        assert any(v.startswith("I7 3/20 empty shells") for v in r["violations"]), r
        assert r["warnings"] == []

    def test_a_file_with_no_ohlc_key_at_all_is_a_shell(self, tmp_path):
        d = self._dir(tmp_path, 19, 0)
        (d / "tickers" / "X.json").write_text(json.dumps({"info": {"name": "X"}}))
        r = A.ticker_shells(d, max_rate=0.0)
        assert any("X" in v for v in r["violations"]), r

    def test_unreadable_files_count_as_shells(self, tmp_path):
        d = self._dir(tmp_path, 19, 0)
        (d / "tickers" / "BAD.json").write_text("{not json")
        r = A.ticker_shells(d, max_rate=0.0)
        assert any("BAD" in v for v in r["violations"]), r

    def test_underscore_files_are_not_ticker_files(self, tmp_path):
        r = A.ticker_shells(self._dir(tmp_path, 10, 0, extra_underscore=5))
        assert r["rows"] == 10 and r["violations"] == []

    def test_missing_directory_is_a_warning(self, tmp_path):
        r = A.ticker_shells(tmp_path / "nope")
        assert r["warnings"] == ["I7 skipped: no tickers dir"] and r["violations"] == []


def test_main_prints_bad_for_the_archives_that_have_violations(tmp_path, capsys, monkeypatch):
    """The CLI's OK/BAD flag is the only thing a human reads in the CI log."""
    _write(tmp_path, "breadth_archive.csv", [
        {"date": "2026-08-17", "spx_close": 7745.06}, {"date": "2026-08-18", "spx_close": 7745.06}])
    # chdir so main()'s default output=Path("data/output") resolves to nothing:
    # a test must not read the real archives, let alone reconcile against them
    # (2026-08-23: a test wrote into data/history/quality and blunted a guard).
    monkeypatch.chdir(tmp_path)
    rc = A.main(["--history", str(tmp_path)])
    printed = capsys.readouterr().out
    assert rc == 1
    bad = [ln for ln in printed.splitlines() if "breadth_archive.csv" in ln]
    assert bad and bad[0].startswith("BAD"), printed


# ---------------------------------------------------------------------------
# I4 (per-session row counts) and I5 (freshness) are the WARNING tier: they do
# not fail CI, they decide what a human is told to look at. The mutation sweep
# left every one of their boundaries alive -- `<` vs `<=` on the floor, `>` vs
# `>=` on the ceiling, `>= 6` on the minimum history, `<` on staleness -- so a
# guard could have been one comparison off in either direction and stayed
# green. Also pinned here: I3 only applies to breadth, and the dedupe of
# drop_dates between I1 and I3.
#
# SESSIONS below are real trading days; 2026-07-25/26 (weekend) are skipped so
# I1 does not fire and drown out what these cases are about.
# ---------------------------------------------------------------------------

SESSIONS = ["2026-07-20", "2026-07-21", "2026-07-22", "2026-07-23", "2026-07-24",
            "2026-07-27", "2026-07-28", "2026-07-29", "2026-07-30", "2026-07-31"]


def _counted(tmp_path, per_day, name="leaders_log.csv"):
    """`per_day` = row count for each session, oldest first."""
    rows = [{"date": d, "ticker": f"T{i}"} for d, n in zip(SESSIONS, per_day) for i in range(n)]
    _write(tmp_path, name, rows)
    out = A.run(tmp_path, last_done=LAST, output=None)
    return [w for w in {r["archive"]: r for r in out["archives"]}[name]["warnings"]
            if w.startswith("I4")], out


class TestI4CountBounds:
    """Trailing median is over every session but the newest; floor 0.30x, ceiling 3.0x."""

    def test_steady_counts_raise_nothing(self, tmp_path):
        w, _ = _counted(tmp_path, [10] * 6)
        assert w == []

    def test_exactly_at_the_floor_is_not_a_warning(self, tmp_path):
        # median 10, floor 0.30 x 10 = 3 -- three rows is ON the floor, not under it
        w, _ = _counted(tmp_path, [10] * 5 + [3])
        assert w == []

    def test_one_row_under_the_floor_is_a_warning(self, tmp_path):
        w, _ = _counted(tmp_path, [10] * 5 + [2])
        assert w and "2 rows vs trailing median 10" in w[0], w

    def test_exactly_at_the_ceiling_is_not_a_warning(self, tmp_path):
        # ceiling 3.0 x 10 = 30
        w, _ = _counted(tmp_path, [10] * 5 + [30])
        assert w == []

    def test_one_row_over_the_ceiling_is_a_warning(self, tmp_path):
        w, _ = _counted(tmp_path, [10] * 5 + [31])
        assert w and "31 rows vs trailing median 10" in w[0], w

    def test_six_sessions_is_enough_history_to_judge(self, tmp_path):
        w, _ = _counted(tmp_path, [10] * 5 + [1])
        assert w, "six sessions (five of history) must be enough to call a collapse"

    def test_five_sessions_is_not_enough(self, tmp_path):
        # with four days of history the median is guesswork; stay quiet
        w, _ = _counted(tmp_path, [10] * 4 + [1])
        assert w == []

    def test_an_archive_that_is_not_count_checked_is_never_judged(self, tmp_path):
        # universe_quality is one row per session by construction; running I4
        # on it would warn on every normal day
        _write(tmp_path, "universe_quality.csv",
               [{"date": d, "x": i} for d, n in zip(SESSIONS, [10] * 5 + [1]) for i in range(n)])
        out = A.run(tmp_path, last_done=LAST, output=None)
        w = {r["archive"]: r for r in out["archives"]}["universe_quality.csv"]["warnings"]
        assert [x for x in w if x.startswith("I4")] == [], w


class TestI5Freshness:
    def test_newest_equals_the_last_completed_session_is_silent(self, tmp_path):
        _write(tmp_path, "leaders_log.csv", [{"date": LAST.isoformat(), "ticker": "A"}])
        out = A.run(tmp_path, last_done=LAST, output=None)
        w = {r["archive"]: r for r in out["archives"]}["leaders_log.csv"]["warnings"]
        assert [x for x in w if x.startswith("I5")] == [], w

    def test_one_session_behind_is_a_warning(self, tmp_path):
        _write(tmp_path, "leaders_log.csv", [{"date": "2026-08-17", "ticker": "A"}])
        out = A.run(tmp_path, last_done=LAST, output=None)
        w = {r["archive"]: r for r in out["archives"]}["leaders_log.csv"]["warnings"]
        assert any(x.startswith("I5 newest session 2026-08-17") for x in w), w

    def test_a_header_only_archive_does_not_reach_the_freshness_check(self, tmp_path):
        # no rows -> no dates -> nothing to compare; asking for max() of nothing
        # is how this used to crash (the run_all smoke found the sibling case)
        p = tmp_path / "leaders_log.csv"
        p.write_text("date,ticker\n")
        out = A.run(tmp_path, last_done=LAST, output=None)
        r = {x["archive"]: x for x in out["archives"]}["leaders_log.csv"]
        assert r["violations"] == [] and [x for x in r["warnings"] if x.startswith("I5")] == []


class TestI3IsBreadthOnly:
    def test_an_identical_close_on_a_valid_session_is_flagged_and_repaired(self, tmp_path):
        # both dates are real sessions, so I1 never touches them: this pins the
        # I3 path on its own, and the drop_dates append that I1 usually shadows
        p = _write(tmp_path, "breadth_archive.csv", [
            {"date": "2026-08-17", "spx_close": 7745.06},
            {"date": "2026-08-18", "spx_close": 7745.06}])
        out = A.run(tmp_path, last_done=LAST, output=None)
        assert not out["ok"]
        A.run(tmp_path, do_repair=True, last_done=LAST, output=None)
        assert pd.read_csv(p).date.tolist() == ["2026-08-17"]

    def test_another_archive_with_an_spx_close_column_is_not_breadth(self, tmp_path):
        _write(tmp_path, "leaders_log.csv", [
            {"date": "2026-08-17", "ticker": "A", "spx_close": 7745.06},
            {"date": "2026-08-18", "ticker": "B", "spx_close": 7745.06}])
        out = A.run(tmp_path, last_done=LAST, output=None)
        assert out["ok"], [r["violations"] for r in out["archives"]]


# ----------------------------------------------------------- 2026-09-02
def test_every_archive_on_disk_is_registered_or_named_as_an_exception():
    """An archive missing from ARCHIVES is not audited by anything.

    This guard passes such a file the way it passes a file it read and liked --
    silently, and for the opposite reason. Nothing in this suite was asking the
    question, so the answer had never been written down.

    Three files are unregistered today. They are listed here rather than
    registered, because registering one changes what the nightly gate checks
    and can turn it red on main; that is the data side's call, not a test's.
    The point of the list is that adding a FOURTH now fails here instead of
    joining them unnoticed. All three carry a date column, so none of them is
    obviously out of scope.

    → routed to DATA ALEX / OPS, night report 2026-09-02.
    """
    from pathlib import Path

    from pipeline.tools.audit_archives import ARCHIVES

    UNREGISTERED_ON_2026_09_02 = {
        "shortlist_feedback.csv",   # pulled_at, ticker, ... 18 rows
        "shortlist_seat_log.csv",   # date, seat, ticker, ... 42 rows
        "theme_ladder.csv",         # date, rung, measurable, ... 10 rows
    }

    history = Path("data/history")
    if not history.is_dir():                     # not a full checkout
        import pytest
        pytest.skip("data/history not present")

    on_disk = {p.name for p in history.glob("*.csv")}
    unregistered = on_disk - set(ARCHIVES) - UNREGISTERED_ON_2026_09_02
    assert not unregistered, (
        f"archives that nothing audits: {sorted(unregistered)}. "
        "Register them in ARCHIVES, or add them to the dated list in this test "
        "with a reason.")

    # and the exemption list must not rot: a file that got registered, or
    # deleted, should leave the list rather than sit there looking like a debt.
    stale = {n for n in UNREGISTERED_ON_2026_09_02
             if n in ARCHIVES or n not in on_disk}
    assert not stale, f"exemptions no longer needed, delete them: {sorted(stale)}"


class TestSessionClassification:
    """_sessions() decides, per date string, whether a row is a real session,
    a future date, or a date it could not read. Four of its mutants survived
    the corrected sweep on 2026-09-02: the whole unparsable branch, and the
    slice that turns a timestamp into a date."""

    def test_a_date_it_cannot_read_is_reported_as_unparsable(self):
        """Kills the three booleans on the unparsable record. Calling it a
        session, or a future date, both hide it behind a different message --
        and 'not a trading session' is a sentence someone would shrug at."""
        info = A._sessions(pd.Series(["not-a-date"]), LAST)
        row = info.iloc[0]
        assert bool(row.unparsable) is True
        assert bool(row.session) is False
        assert bool(row.future) is False

    def test_an_unparsable_date_is_flagged_with_that_reason(self, tmp_path):
        _write(tmp_path, "leaders_log.csv",
               [{"date": "2026-08-18", "ticker": "A"}, {"date": "garbage", "ticker": "B"}])
        out = A.run(tmp_path, last_done=LAST, output=None)
        text = " ".join(v for r in out["archives"] for v in r["violations"])
        assert "unparsable" in text, text

    def test_a_timestamp_is_read_as_its_date(self):
        """`d[:10]`. One character more and 2026-08-18T09:30 stops parsing, so
        a perfectly good session gets reported as an unreadable date."""
        info = A._sessions(pd.Series(["2026-08-18T09:30:00"]), LAST)
        row = info.iloc[0]
        assert bool(row.unparsable) is False
        assert bool(row.session) is True, "2026-08-18 is a Tuesday"
        assert bool(row.future) is False

    def test_the_day_after_the_last_completed_session_is_future(self):
        info = A._sessions(pd.Series(["2026-08-18", "2026-08-19"]), LAST)
        by = {r.date: r for r in info.itertuples()}
        assert bool(by["2026-08-18"].future) is False
        assert bool(by["2026-08-19"].future) is True
