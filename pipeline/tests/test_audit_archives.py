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


# --- I7: a series that has always been there wrote nothing -------------------
# The change_pct incident (Finviz renamed `Change` -> `Change %` on 2026-08-07,
# fixed a week later in e8ac440): gainers_4pct and vol_up_gainers wrote ZERO
# rows on 08-07/11/12/13 while the file's total row count stayed at 0.68-1.17x
# its trailing median, and is_plausible_day saw 4 of 7 screeners reporting and
# said yes. Nothing in the pipeline noticed for four sessions.

_BANDS = {"archives": {"ticker_events.csv": {"series": {
    "gainers_4pct":   {"kind": "reliable", "presence": 0.96, "median_rows": 180.0},
    "vol_up_gainers": {"kind": "reliable", "presence": 0.96, "median_rows": 46.0},
    "episodic_pivot": {"kind": "sparse",   "presence": 0.93, "median_rows": 4.0},
    "vcp":            {"kind": "sparse",   "presence": 1.00, "median_rows": 19.0,
                       "band": {"floor": 0.27, "ceil": 2.96}},
}}}}


def _events(tmp_path, day_counts):
    """day_counts: {date: {screener: n}} -> ticker_events.csv"""
    rows = [{"date": d, "ticker": f"T{i}", "screener": scr}
            for d, per in day_counts.items() for scr, n in per.items() for i in range(n)]
    return _write(tmp_path, "ticker_events.csv", rows)


def test_reliable_screener_writing_nothing_is_a_violation(tmp_path):
    _events(tmp_path, {
        "2026-08-17": {"gainers_4pct": 200, "vol_up_gainers": 50, "vcp": 19},
        "2026-08-18": {"vcp": 19, "episodic_pivot": 3},          # the two died
    })
    out = A.run(tmp_path, last_done=LAST, output=None, bands=_BANDS)
    assert not out["ok"]
    v = {r["archive"]: r["violations"] for r in out["archives"]}["ticker_events.csv"]
    assert any(x.startswith("I7 2026-08-18 gainers_4pct") for x in v)
    assert any(x.startswith("I7 2026-08-18 vol_up_gainers") for x in v)


def test_sparse_series_writing_nothing_says_nothing(tmp_path):
    _events(tmp_path, {
        "2026-08-17": {"gainers_4pct": 200, "vol_up_gainers": 50, "episodic_pivot": 4},
        "2026-08-18": {"gainers_4pct": 190, "vol_up_gainers": 44},   # episodic_pivot gone
    })
    out = A.run(tmp_path, last_done=LAST, output=None, bands=_BANDS)
    assert out["ok"] and out["violations"] == 0


def test_series_count_outside_its_own_band_is_a_warning(tmp_path):
    _events(tmp_path, {
        "2026-08-18": {"gainers_4pct": 190, "vol_up_gainers": 44, "vcp": 90},   # 4.7x its median
    })
    out = A.run(tmp_path, last_done=LAST, output=None, bands=_BANDS)
    assert out["ok"]
    w = {r["archive"]: r["warnings"] for r in out["archives"]}["ticker_events.csv"]
    assert any(x.startswith("I4s 2026-08-18 vcp") for x in w)


def test_measured_total_band_is_used_when_the_registry_has_one(tmp_path):
    rows = [{"date": f"2026-07-{d:02d}", "ticker": t} for d in (20, 21, 22, 23, 24, 27, 28) for t in "ABCDEFGHIJ"]
    rows += [{"date": "2026-07-29", "ticker": t} for t in "ABCD"]      # 4 rows = 0.4x median 10
    _write(tmp_path, "leaders_log.csv", rows)
    loose = {"archives": {}}                                          # default band 0.30/3.0
    assert not any(x.startswith("I4 2026-07-29") for r in A.run(
        tmp_path, last_done=LAST, output=None, bands=loose)["archives"]
        for x in r["warnings"])
    tight = {"archives": {"leaders_log.csv": {"total": {"floor": 0.58, "ceil": 2.45}}}}
    assert any(x.startswith("I4 2026-07-29") for r in A.run(
        tmp_path, last_done=LAST, output=None, bands=tight)["archives"]
        for x in r["warnings"])
