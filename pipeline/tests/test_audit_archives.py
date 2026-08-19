"""Archive invariants (pipeline/tools/audit_archives.py)."""
from __future__ import annotations

import datetime as dt

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
