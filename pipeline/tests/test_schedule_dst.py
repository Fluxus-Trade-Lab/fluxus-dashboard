"""Every data cron must land OUTSIDE run_all's refusal window in BOTH seasons.

Andy 2026-09-17 (constitution, 「排程必须同时对夏令时和冬令时有效」): cron is UTC,
the market is ET, and ET slides an hour at the DST boundaries. The main schedule
`20 20 * * 1-5` is 16:20 EDT but 15:20 EST -- inside run_all.py's 04:00-16:15 ET
refusal window -- so from 2026-11-02 every on-time main run would refuse.

For each cron in the workflow and one EDT and one EST trading week, this test
runs the REAL gate script (test_backstop_gate.run_gate) at the cron's nominal
time with the session not yet landed. Whenever the gate lets the run through,
the ET wall clock at that moment must be outside the refusal window. It also
requires that, in each season, every ET weekday gets at least one main run that
the gate lets through at or after 16:15 ET -- so "skip everything" cannot pass.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from pipeline.tests.test_backstop_gate import (  # noqa: F401  (fixture re-export)
    BACKSTOP_CRON, WORKFLOW, _breadth, gnu_date_path, run_gate,
)

REPO = Path(__file__).resolve().parents[2]
ET = ZoneInfo("America/New_York")
# Literal on purpose; pinned to run_all.py's source by the test below.
REFUSE_FROM, REFUSE_UNTIL = (4, 0), (16, 15)
SEASONS = {  # Monday of a full trading week
    "EDT": datetime(2026, 9, 14, tzinfo=timezone.utc),
    "EST": datetime(2026, 11, 9, tzinfo=timezone.utc),
}


def _crons():
    return re.findall(r"^\s*-\s*cron:\s*'([^']+)'", WORKFLOW.read_text(encoding="utf-8"), re.M)


def _utc_days(dow_field: str) -> set[int]:
    """cron day-of-week (0=Sun) -> python weekday set (0=Mon)."""
    out = set()
    for part in dow_field.split(","):
        a, _, b = part.partition("-")
        for d in range(int(a), int(b or a) + 1):
            out.add((d - 1) % 7)
    return out


def _fires(cron: str, monday: datetime):
    minute, hour, _, _, dow = cron.split()
    days = _utc_days(dow)
    for i in range(8):
        day = monday + timedelta(days=i)
        if day.weekday() in days:
            yield day.replace(hour=int(hour), minute=int(minute))


def test_refusal_window_literal_matches_run_all():
    src = (REPO / "pipeline" / "screeners" / "run_all.py").read_text(encoding="utf-8")
    assert "(4, 0) <= (_now.hour, _now.minute) < (16, 15)" in src, (
        "run_all's refusal window changed; update REFUSE_FROM/REFUSE_UNTIL here")


@pytest.mark.parametrize("season", sorted(SEASONS))
def test_no_cron_the_gate_lets_through_lands_in_the_refusal_window(tmp_path, gnu_date_path, season):
    covered: set[int] = set()
    bad = []
    for k, cron in enumerate(_crons()):
        for fire in _fires(cron, SEASONS[season]):
            et = fire.astimezone(ET)
            prev_session = (et - timedelta(hours=6)).date() - timedelta(days=1)
            sub = tmp_path / f"{k}-{fire:%m%d}"
            sub.mkdir()
            flag, proc = run_gate(sub, gnu_date_path, now=fire.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                  breadth=_breadth(prev_session.isoformat()), schedule=cron)
            if flag != "true":
                continue
            hm = (et.hour, et.minute)
            if et.weekday() < 5 and REFUSE_FROM <= hm < REFUSE_UNTIL:
                bad.append(f"{cron} at {fire:%a %H:%MZ} = {et:%a %H:%M %Z}")
            if cron != BACKSTOP_CRON and hm >= REFUSE_UNTIL and et.weekday() < 5:
                covered.add(et.weekday())
    assert not bad, f"{season}: runs the gate lets through that run_all will refuse: {bad}"
    assert covered == {0, 1, 2, 3, 4}, f"{season}: ET weekdays with no usable main run: {sorted({0,1,2,3,4} - covered)}"
