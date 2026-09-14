"""Late vs dropped scheduled runs (pipeline/tools/audit_schedule_windows.py).

The fixture is the real week: createdAt values copied from
`gh run list --workflow daily-data-update.yml --event schedule` for
2026-09-10 -> 09-12, and the 09-14 20:20Z main window that had no run at
22:30Z -- the moment two lines called it dropped.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from pipeline.tools import audit_schedule_windows as S

MAIN = "20 20 * * 1-5"
BACKSTOP = "30 1 * * 2-6"
CRONS = [MAIN, BACKSTOP]
REPO = Path(__file__).resolve().parents[2]

REAL_RUNS = [
    {"createdAt": "2026-09-10T06:14:18Z", "databaseId": 34444326236},
    {"createdAt": "2026-09-10T22:40:20Z", "databaseId": 34538593920},
    {"createdAt": "2026-09-11T06:17:46Z", "databaseId": 34569325506},
    {"createdAt": "2026-09-11T22:40:02Z", "databaseId": 34654994500},
    {"createdAt": "2026-09-12T06:04:25Z", "databaseId": 34677184393},
]
SINCE = "2026-09-10T00:00:00Z"


def utc(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def test_reads_the_crons_the_workflow_actually_has():
    text = (REPO / S.WORKFLOW).read_text(encoding="utf-8")
    assert S.parse_crons(text) == CRONS


def test_commented_cron_is_not_a_schedule():
    assert S.parse_crons("    # - cron: '0 0 * * *'\n    - cron: '20 20 * * 1-5'") == [MAIN]


def test_day_of_week_is_cron_numbering_not_python():
    wk0, wk1 = utc("2026-09-07T00:00:00Z"), utc("2026-09-13T23:59:00Z")  # Mon..Sun
    assert [w.day for w in S.cron_windows(MAIN, wk0, wk1)] == [7, 8, 9, 10, 11]
    assert [w.day for w in S.cron_windows(BACKSTOP, wk0, wk1)] == [8, 9, 10, 11, 12]
    assert [w.day for w in S.cron_windows("0 12 * * 0", wk0, wk1)] == [13]
    assert [w.day for w in S.cron_windows("0 12 * * 7", wk0, wk1)] == [13]


@pytest.mark.parametrize("bad", ["*/5 * * * *", "0 0 1 * *", "0 0 * 9 1", "0 0 * *"])
def test_unsupported_cron_raises_instead_of_guessing(bad):
    with pytest.raises(ValueError):
        S.cron_windows(bad, utc("2026-09-07T00:00:00Z"), utc("2026-09-08T00:00:00Z"))


def test_real_week_all_fired_and_0914_is_pending_not_dropped():
    res = S.check(CRONS, REAL_RUNS, utc("2026-09-14T22:30:00Z"), utc(SINCE))
    got = [(r["window"], r["status"], r.get("late_min", r.get("age_min"))) for r in res["rows"]]
    assert got == [
        ("2026-09-10T01:30:00Z", "fired", 284),
        ("2026-09-10T20:20:00Z", "fired", 140),
        ("2026-09-11T01:30:00Z", "fired", 287),
        ("2026-09-11T20:20:00Z", "fired", 140),
        ("2026-09-12T01:30:00Z", "fired", 274),
        ("2026-09-14T20:20:00Z", "pending", 130),
    ]
    assert res["violations"] == [] and res["warnings"] == [] and res["orphans"] == []
    assert res["stats"][MAIN] == {"n": 2, "p50": 140, "max": 140}


def test_the_0912_morning_call_was_pending():
    """Joe 09-12 22:28Z: no run for 09-11 20:20Z yet. The run came at 22:40:02Z."""
    runs = [r for r in REAL_RUNS if r["createdAt"] < "2026-09-11T22:28:00Z"]
    res = S.check(CRONS, runs, utc("2026-09-11T22:28:00Z"), utc(SINCE))
    last = res["rows"][-1]
    assert (last["window"], last["status"], last["age_min"]) == ("2026-09-11T20:20:00Z", "pending", 128)
    assert res["violations"] == []


@pytest.mark.parametrize("age,status", [(599, "pending"), (600, "dropped"), (601, "dropped")])
def test_drop_threshold_boundary(age, status):
    now = utc("2026-09-14T20:20:00Z") + timedelta(minutes=age)
    res = S.check([MAIN], [], now, utc("2026-09-14T00:00:00Z"))
    assert [r["status"] for r in res["rows"]] == [status]
    assert len(res["violations"]) == (status == "dropped")


def test_positive_control_a_real_drop_goes_red(tmp_path, capsys):
    """Remove the 09-11 main run and look the next morning: that window must be BAD."""
    runs = [r for r in REAL_RUNS if r["databaseId"] != 34654994500]
    f = tmp_path / "runs.json"
    f.write_text(json.dumps(runs))
    rc = S.main(["--repo", str(REPO), "--runs-json", str(f), "--since", SINCE,
                 "--now", "2026-09-12T10:00:00Z"])
    out = capsys.readouterr().out
    assert rc == 1
    assert "DROPPED  2026-09-11T20:20:00Z" in out
    assert "BAD: 1 dropped" in out


def test_overlap_still_counts_one_empty_window():
    """Main dropped, backstop fires: labels may swap, the count of empty windows may not."""
    runs = [{"createdAt": "2026-09-11T06:04:00Z", "databaseId": 1}]
    res = S.check(CRONS, runs, utc("2026-09-11T20:00:00Z"), utc("2026-09-10T20:00:00Z"))
    assert [r["status"] for r in res["rows"]] == ["dropped", "fired"]


def test_run_beyond_horizon_is_an_orphan_not_a_late_fire():
    runs = [{"createdAt": "2026-09-15T08:00:00Z", "databaseId": 9}]  # 700 min after 09-14 20:20Z
    res = S.check([MAIN], runs, utc("2026-09-15T09:00:00Z"), utc("2026-09-14T00:00:00Z"),
                  drop_after_min=600)
    assert [r["status"] for r in res["rows"]] == ["dropped"]
    assert [o["databaseId"] for o in res["orphans"]] == [9]


def test_late_run_of_a_window_before_since_is_not_an_orphan():
    """Real: cron change 09-05 03:39:32Z; the 01:30Z backstop's run came at 05:59:38Z."""
    runs = [{"createdAt": "2026-09-05T05:59:38Z", "databaseId": 33948611359}]
    res = S.check(CRONS, runs, utc("2026-09-05T12:00:00Z"), utc("2026-09-05T03:39:32Z"))
    assert res["orphans"] == [] and res["rows"] == []


def test_pending_older_than_anything_seen_warns():
    runs = [{"createdAt": "2026-09-10T22:40:00Z", "databaseId": 1}]
    res = S.check([MAIN], runs, utc("2026-09-11T23:00:00Z"), utc("2026-09-10T00:00:00Z"))
    assert [r["status"] for r in res["rows"]] == ["fired", "pending"]
    assert len(res["warnings"]) == 1 and res["violations"] == []


def test_unreadable_run_list_exits_2_not_green(monkeypatch, capsys):
    monkeypatch.setattr(S, "fetch_runs", lambda repo, wf: None)
    assert S.main(["--repo", str(REPO), "--since", SINCE, "--now", "2026-09-14T22:30:00Z"]) == 2
    assert "cannot tell late from dropped" in capsys.readouterr().out
