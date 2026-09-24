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
        # a shell count it never took must read as zero, not as one (2026-09-25)
        assert r["rows"] == 0 and r["drop_dupes"] == 0


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


# --------------------------------------------------------------- 2026-09-25
# The registry at the top of audit_archives.py is not a list of names: the two
# booleans on each line decide WHICH checks that archive gets. Flip
# `"nightly": True` to False on ticker_events.csv and I5 quietly stops asking
# whether a writer died -- which is the single reason I5 exists (08-18,
# delayed_ep archived 0 rows on a throttled download). The mutation sweep
# found 19 survivors on those eleven lines: every flag except leaders_log's,
# which the fixtures above happen to lean on.
#
# Pinning them by reading the dict back (`assert spec["nightly"] is True`)
# would be the "read your own constant" test that has now been caught three
# times in this suite (09-23 pp, 09-24 U3, 09-24 HIGH). So each flag is asked
# behaviourally instead: build the archive that WOULD trip the check, and
# assert the warning appears exactly when the flag says it should.
# ---------------------------------------------------------------------------

import pytest                                                     # noqa: E402

KEY_COLUMNS = ["ticker", "panel", "screener", "kind", "group", "recipe", "seat"]


def _rows_for(spec, dates_and_counts):
    """Rows for any registered archive: the date column it declares, plus a
    unique value in every key column any archive uses, so I2 never fires."""
    rows, i = [], 0
    for d, n in dates_and_counts:
        for _ in range(n):
            i += 1
            rows.append({spec["date"]: d, **{c: f"{c[0].upper()}{i}" for c in KEY_COLUMNS}})
    return rows


def _warnings_for(tmp_path, name, rows, prefix):
    _write(tmp_path, name, rows)
    out = A.run(tmp_path, last_done=LAST, output=None)
    rep = {r["archive"]: r for r in out["archives"]}[name]
    # the fixture must not be tripping a DIFFERENT invariant: every date is a
    # real past session and no spx_close repeats. I2 is allowed through -- the
    # three archives keyed on date alone (breadth, universe_quality,
    # regime_ledger) are one row per session by construction, so a fixture
    # with ten rows a day IS a duplicate there. I2 and I4 read different
    # fields; it cannot lend or take away an I4 warning.
    assert [v for v in rep["violations"] if v[:2] in ("I1", "I3")] == [], rep["violations"]
    return [w for w in rep["warnings"] if w.startswith(prefix)]


# ⚠️ The expected flags live HERE, written out, not read back off A.ARCHIVES.
# First draft of these tests did `assert bool(w) is bool(spec["counts"])` --
# which is green for the real code AND for every mutant, because flipping the
# flag moves the expectation with it. 19 survivors, zero of them killed. It is
# the same defect as 09-23's `f'{0.2692*100:.0f}'` and 09-24's `dirty == 1`,
# wearing a parametrize decorator. A test that fetches its own answer from the
# thing under test is not asking a question.
#
# The cost of writing them out is that changing a flag now means editing this
# table. That cost is the feature: turning a check off for an archive is a
# decision (09-18: a check that stopped applying, and nobody logged it), and
# this is where it gets signed.
WATCHED_ON_2026_09_25 = {
    # archive                 (counts -> I4 applies, nightly -> I5 applies)
    "breadth_archive.csv":    (False, True),
    "ticker_events.csv":      (True,  True),
    "watchlist_hits.csv":     (True,  True),
    "leaders_log.csv":        (True,  True),
    "groups_archive.csv":     (True,  True),
    "momentum97_shadow.csv":  (False, True),
    "universe_quality.csv":   (False, True),
    "asset_signals.csv":      (True,  True),
    "shortlist_log.csv":      (False, True),
    "regime_ledger.csv":      (False, True),
    "delayed_ep_log.csv":     (True,  True),
}


def test_the_flag_table_in_this_file_covers_every_registered_archive():
    """Anti-rot: a newly registered archive must be signed into the table
    above, not inherit whatever the two tests below happen to assert."""
    assert set(WATCHED_ON_2026_09_25) == set(A.ARCHIVES), (
        f"only in ARCHIVES: {sorted(set(A.ARCHIVES) - set(WATCHED_ON_2026_09_25))}; "
        f"only in the table: {sorted(set(WATCHED_ON_2026_09_25) - set(A.ARCHIVES))}")


@pytest.mark.parametrize("name,counts", [(n, v[0]) for n, v in sorted(WATCHED_ON_2026_09_25.items())])
def test_only_the_archives_this_file_says_are_counted_can_raise_I4(tmp_path, name, counts):
    """A collapse day (1 row where the median is 10) raises I4 on exactly the
    archives this file lists as counted."""
    rows = _rows_for(A.ARCHIVES[name], list(zip(SESSIONS[:5], [10] * 5)) + [(SESSIONS[5], 1)])
    w = _warnings_for(tmp_path, name, rows, "I4")
    assert bool(w) is counts, f"{name}: this file says counts={counts}, I4 said {w}"


@pytest.mark.parametrize("name,nightly", [(n, v[1]) for n, v in sorted(WATCHED_ON_2026_09_25.items())])
def test_only_the_archives_this_file_says_are_nightly_can_raise_I5(tmp_path, name, nightly):
    """An archive whose newest row is a session old raises I5 on exactly the
    archives this file lists as nightly -- all eleven today, i.e. every one of
    them still gets its clock read."""
    rows = _rows_for(A.ARCHIVES[name], [("2026-08-17", 1)])
    w = _warnings_for(tmp_path, name, rows, "I5")
    assert bool(w) is nightly, f"{name}: this file says nightly={nightly}, I5 said {w}"


# --------------------------------------------------------------------------
# I4's trailing window: `per.iloc[-21:-1] if len(per) > 21 else per.iloc[:-1]`.
# Five mutants on that one line survived. Medians are immune to a single
# outlier (09-02), so a lopsided day cannot separate the windows -- the
# fixtures below are bimodal instead: ten 10s and ten 30s, where dropping or
# adding ONE session moves the median from 20 to 10 and flips the verdict.
# --------------------------------------------------------------------------

def _sessions_back(n, last=LAST):
    """The n trading sessions ending at `last`, oldest first."""
    from pipeline.marketcal import is_trading_day
    out, d = [], last
    while len(out) < n:
        if is_trading_day(d):
            out.append(d.isoformat())
        d -= dt.timedelta(days=1)
    return list(reversed(out))


class TestI4TrailingWindowShape:
    def test_the_median_skips_only_the_newest_session(self, tmp_path):
        """`per.iloc[:-1]` -- dropping two sessions instead of one takes the
        median from 10 to 6, and 2 rows stops being a collapse (floor 1.8)."""
        counts = [2, 2, 10, 10, 10, 2]
        rows = _rows_for(A.ARCHIVES["leaders_log.csv"], list(zip(SESSIONS, counts)))
        w = _warnings_for(tmp_path, "leaders_log.csv", rows, "I4")
        assert w and "2 rows vs trailing median 10" in w[0], w

    def test_past_21_sessions_the_median_is_the_trailing_20_not_everything(self, tmp_path):
        """With 22 sessions the real window is the 20 before the newest
        (median 20); reaching back one further, or falling through to
        `[:-1]`, makes it 21 sessions (median 10) and the collapse vanishes."""
        sess = _sessions_back(22)
        counts = [10] + [10] * 10 + [30] * 10 + [5]
        rows = _rows_for(A.ARCHIVES["leaders_log.csv"], list(zip(sess, counts)))
        w = _warnings_for(tmp_path, "leaders_log.csv", rows, "I4")
        assert w and "5 rows vs trailing median 20" in w[0], w

    def test_the_window_stops_one_short_of_the_newest_not_two(self, tmp_path):
        """`[-21:-1]` -- ending the window at -2 drops a 30 and the median
        falls to 10, which is the same disappearing-collapse as above but
        from the other end of the slice."""
        sess = _sessions_back(22)
        counts = [30] + [10] * 10 + [30] * 10 + [5]
        rows = _rows_for(A.ARCHIVES["leaders_log.csv"], list(zip(sess, counts)))
        w = _warnings_for(tmp_path, "leaders_log.csv", rows, "I4")
        assert w and "5 rows vs trailing median 20" in w[0], w


# --------------------------------------------------------------------------
# --repair writes over a production archive. Nothing was checking WHAT shape
# it writes back: `to_csv(index=False)` flipping to True adds an unnamed index
# column -- and a second repair pass would add another one on top. The tests
# above read `.date` off the repaired file, which keeps working with the extra
# column, which is why the mutant lived.
# --------------------------------------------------------------------------

def test_repair_writes_back_the_same_columns_it_read(tmp_path):
    p = _write(tmp_path, "leaders_log.csv", [
        {"date": "2026-08-18", "ticker": "A"},
        {"date": "2026-08-18", "ticker": "A"},           # dup -> repaired away
        {"date": "2026-08-16", "ticker": "B"}])           # Sunday -> repaired away
    before = list(pd.read_csv(p).columns)
    A.run(tmp_path, do_repair=True, last_done=LAST, output=None)
    after = list(pd.read_csv(p).columns)
    assert after == before == ["date", "ticker"], after
    assert list(pd.read_csv(tmp_path / "leaders_log.csv.bak").columns) == before


def test_a_clean_run_reports_zero_pending_dupes_on_every_archive(tmp_path):
    """`drop_dupes` is what --repair acts on. Initialising it to 1 makes every
    archive look like it has a duplicate waiting, and makes --repair open and
    re-dedupe files that were fine."""
    _write(tmp_path, "leaders_log.csv", [{"date": "2026-08-18", "ticker": "A"}])
    out = A.run(tmp_path, last_done=LAST, output=None)
    assert all(r["drop_dupes"] == 0 for r in out["archives"]), out["archives"]


def test_an_archive_that_is_not_there_yet_reports_zero_rows(tmp_path):
    """The `missing (not yet created)` branch: rows must be 0, not 1. A phantom
    row count is how a never-written archive passes for a thin one."""
    _write(tmp_path, "leaders_log.csv", [{"date": "2026-08-18", "ticker": "A"}])
    out = A.run(tmp_path, last_done=LAST, output=None)
    missing = _rep(out, "ticker_events.csv")
    assert missing["warnings"] == ["missing (not yet created)"]
    assert missing["rows"] == 0 and missing["drop_dupes"] == 0
    assert missing["violations"] == []


def test_an_unreadable_archive_is_a_violation_with_zero_rows(tmp_path):
    """A zero-byte archive -- a writer killed between open and flush. pandas
    raises, and the report must say so instead of counting rows it never read."""
    (tmp_path / "leaders_log.csv").write_bytes(b"")
    out = A.run(tmp_path, last_done=LAST, output=None)
    r = _rep(out, "leaders_log.csv")
    assert r["rows"] == 0 and r["drop_dupes"] == 0
    assert r["violations"] and r["violations"][0].startswith("unreadable:"), r
    assert not out["ok"]


def test_a_ticker_literally_named_NA_is_not_read_as_a_missing_value(tmp_path):
    """`keep_default_na=False`. pandas' default NA words include 'NA' and
    'NULL'; with them enabled, two different tickers both become NaN and I2
    reports a duplicate that does not exist -- and --repair would then delete a
    real row. The archives are read as text on purpose."""
    _write(tmp_path, "leaders_log.csv", [
        {"date": "2026-08-18", "ticker": "NA"},
        {"date": "2026-08-18", "ticker": "NULL"}])
    out = A.run(tmp_path, last_done=LAST, output=None)
    r = _rep(out, "leaders_log.csv")
    assert r["violations"] == [], r["violations"]
    assert r["rows"] == 2 and out["ok"]


def test_a_clean_repo_exits_zero(tmp_path, capsys, monkeypatch):
    """main()'s exit code is the whole CI contract: 1 blocks the commit. The
    violation case was pinned; the clean case was not, so `return 1 if ok`
    -- which fails every good night -- was invisible."""
    _write(tmp_path, "breadth_archive.csv", [
        {"date": "2026-08-17", "spx_close": 7745.06}, {"date": "2026-08-18", "spx_close": 7691.76}])
    monkeypatch.chdir(tmp_path)
    assert A.main(["--history", str(tmp_path)]) == 0
    assert "OK:" in capsys.readouterr().out


class TestReconcileReportShape:
    def test_the_reconcile_report_counts_no_rows_of_its_own(self, tmp_path):
        """reconcile() compares other people's rows; its own `rows` is 0 and
        it can never have a dupe to repair. Both were unpinned."""
        _write(tmp_path, "watchlist_hits.csv", [{"date": DATE, "panel": "vcs", "ticker": "T"}])
        out = A.run(tmp_path, last_done=LAST,
                    output=_out(tmp_path, watchlist=_wl([{"key": "vcs", "measured": True, "count": 1}])))
        r = _rep(out, "reconcile(I6)")
        assert r["rows"] == 0 and r["drop_dupes"] == 0

    def test_a_panel_with_no_archived_rows_at_all_still_disagrees(self, tmp_path):
        """The default in `per.get(key, 0)`. Defaulting to 1 instead means a
        panel that printed `1` on the page while archiving NOTHING reads as
        agreement -- the one count where a silent writer is most likely."""
        _write(tmp_path, "watchlist_hits.csv", [{"date": DATE, "panel": "other", "ticker": "T"}])
        out = A.run(tmp_path, last_done=LAST,
                    output=_out(tmp_path, watchlist=_wl([{"key": "vcs", "measured": True, "count": 1}])))
        v = _rep(out, "reconcile(I6)")["violations"]
        assert v and v[0] == (f"I6a {DATE} vcs: watchlist.json count 1 vs watchlist_hits 0"), v


class TestTickerShellsMessageTruncation:
    """The I7 line is read by a human deciding whether to keep yesterday's
    tickers. `shells[:12]` and `> 12` decide what that human sees; all three
    mutants on them survived."""

    def _msg(self, tmp_path, n_shell, n_full):
        d = tmp_path / "output" / "tickers"
        d.mkdir(parents=True, exist_ok=True)
        for i in range(n_full):
            (d / f"F{i}.json").write_text(json.dumps({"ohlc_2y": [{"c": 1}]}))
        for i in range(n_shell):
            (d / f"S{i:02d}.json").write_text(json.dumps({"ohlc_2y": []}))
        r = A.ticker_shells(tmp_path / "output", max_rate=0.0)
        assert len(r["violations"]) == 1, r
        return r["violations"][0]

    def test_twelve_shells_are_all_named_with_no_ellipsis(self, tmp_path):
        msg = self._msg(tmp_path, 12, 88)
        names = msg.split(": ", 1)[1]
        assert "…" not in msg, msg
        assert len(names.split(", ")) == 12, names

    def test_the_thirteenth_shell_becomes_an_ellipsis(self, tmp_path):
        msg = self._msg(tmp_path, 13, 87)
        names = msg.split(": ", 1)[1]
        assert msg.endswith("…"), msg
        assert len(names.rstrip("…").split(", ")) == 12, names
