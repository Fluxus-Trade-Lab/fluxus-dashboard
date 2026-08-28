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
