"""Scheduled-run windows -- was a cron run DROPPED, or is it only late?

Three lines called the same thing "dropped" within 72 hours, and none of them
was:

  - Plumber Joe 09-12 22:28Z: "09-11 主排程第 4 次被丢弃 (08-27/09-08/09-09/09-11)".
    The run appeared at 22:40:02Z -- 140 minutes late. 09-08 and 09-09 had
    fired too (145 / 137 minutes late); the count of four was a count of
    "not there when I looked".
  - 数据哨兵 09-14 21:47Z: "排程被 GitHub 丢弃 4+ 个窗口". It counted windows
    (02:04Z, 09-13, 09-14 06:xx) that neither cron expression contains.
  - Nighty Zac 09-15 晨报 (~21:48Z): "20:20Z 正班又被 GitHub 丢了" -- 88 minutes
    past due.

Measured over every window since 2026-08-01 (gh run list --event schedule):
since 09-01 the main schedule fires 102-153 minutes late and the backstop
269-295 minutes late, every single time. The worst lateness on record is 485
minutes (08-27). A window with no run at 130 minutes is the normal state of
this repository's scheduler, not an outage -- and "dropped" is what feeds the
tally that mechanism proposals get built on.

So the question this tool answers is not "is there a run yet" but "is it past
the point where a run can still arrive". It reads the cron expressions from the
workflow file itself (so a schedule change cannot leave it checking the old
times), lists every expected window, pairs each scheduled run to the latest
unpaired window at or before it, and classifies:

  fired    a run was created for the window (lateness in minutes)
  pending  no run yet, and the window is younger than --drop-after
  dropped  no run, and the window is at least --drop-after old  -> VIOLATION

--drop-after defaults to 600 minutes: above the 485-minute worst case, below
the 20h10m to the next window of the same cron.

Pairing caveat: GitHub does not say which cron a scheduled run belongs to. If
a main run is so late it lands after the backstop's window, the two labels
can swap. The NUMBER of windows left without a run is still right, and that
is what `dropped` counts.

If the run list cannot be read the tool exits 2, never 0 -- not being able to
look is not the same as finding nothing.

    python -m pipeline.tools.audit_schedule_windows
    python -m pipeline.tools.audit_schedule_windows --runs-json runs.json --now 2026-09-14T22:30:00Z
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

WORKFLOW = ".github/workflows/daily-data-update.yml"
DROP_AFTER_MIN = 600
LOOKBACK_DAYS = 10

_CRON_LINE = re.compile(r"""^\s*-\s*cron:\s*['"]([^'"]+)['"]""")


def parse_crons(text: str) -> List[str]:
    """Cron expressions under `on.schedule` (commented-out lines don't match)."""
    return [m.group(1).strip() for line in text.splitlines()
            if (m := _CRON_LINE.match(line))]


def _field(expr: str, lo: int, hi: int) -> set:
    if expr == "*":
        return set(range(lo, hi + 1))
    out: set = set()
    for part in expr.split(","):
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    if any(v < lo or v > hi for v in out):
        raise ValueError(f"cron field {expr!r} outside {lo}-{hi}")
    return out


def cron_windows(cron: str, start: datetime, end: datetime) -> List[datetime]:
    """Every UTC time in [start, end] the cron names.

    Only the shape this repo uses is supported (fixed minutes/hours, `*` for
    day-of-month and month, a day-of-week list/range). Anything else raises --
    silently mis-expanding a schedule would report windows that don't exist,
    which is exactly the mistake this tool was written to stop.
    """
    parts = cron.split()
    if len(parts) != 5 or parts[2] != "*" or parts[3] != "*" or "/" in cron:
        raise ValueError(f"unsupported cron expression: {cron!r}")
    minutes = _field(parts[0], 0, 59)
    hours = _field(parts[1], 0, 23)
    dows = {d % 7 for d in _field(parts[4], 0, 7)}  # cron: 0 and 7 are Sunday
    out = []
    day = start.date() - timedelta(days=1)
    while day <= end.date():
        if (day.weekday() + 1) % 7 in dows:  # python Monday=0 -> cron Monday=1
            for h in sorted(hours):
                for m in sorted(minutes):
                    w = datetime(day.year, day.month, day.day, h, m, tzinfo=timezone.utc)
                    if start <= w <= end:
                        out.append(w)
        day += timedelta(days=1)
    return out


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def check(crons: Sequence[str], runs: Sequence[Dict[str, Any]], now: datetime,
          since: datetime, drop_after_min: int = DROP_AFTER_MIN) -> Dict[str, Any]:
    horizon = timedelta(minutes=drop_after_min)
    # Windows up to one horizon BEFORE `since` take part in pairing but are not
    # reported: a late run created just after `since` belongs to one of them
    # (09-05 05:59Z was the 01:30Z backstop, and the cron change is 03:39Z).
    windows = sorted(((w, c) for c in crons for w in cron_windows(c, since - horizon, now)),
                     key=lambda x: x[0])
    paired: Dict[int, Dict[str, Any]] = {}
    orphans = []
    for run in sorted(runs, key=lambda r: r["createdAt"]):
        t = _ts(run["createdAt"])
        if t < since:
            continue
        cands = [i for i, (w, _) in enumerate(windows)
                 if i not in paired and w <= t and t - w <= horizon]
        if not cands:
            orphans.append(run)
            continue
        paired[max(cands, key=lambda i: windows[i][0])] = run

    rows = []
    for i, (w, cron) in enumerate(windows):
        if w < since:
            continue
        row: Dict[str, Any] = {"window": w.isoformat().replace("+00:00", "Z"), "cron": cron}
        if i in paired:
            row.update(status="fired", run_id=paired[i].get("databaseId"),
                       late_min=int((_ts(paired[i]["createdAt"]) - w).total_seconds() // 60))
        else:
            age = int((now - w).total_seconds() // 60)
            row.update(status="dropped" if age >= drop_after_min else "pending", age_min=age)
        rows.append(row)

    stats = {}
    for cron in crons:
        late = [r["late_min"] for r in rows if r["cron"] == cron and r["status"] == "fired"]
        stats[cron] = ({"n": len(late), "p50": statistics.median(late), "max": max(late)}
                       if late else {"n": 0})
    violations = [r for r in rows if r["status"] == "dropped"]
    warnings = [r for r in rows if r["status"] == "pending"
                and stats[r["cron"]].get("max") is not None
                and r["age_min"] > stats[r["cron"]]["max"]]
    return {"now": now.isoformat().replace("+00:00", "Z"),
            "since": since.isoformat().replace("+00:00", "Z"),
            "drop_after_min": drop_after_min, "rows": rows, "stats": stats,
            "orphans": orphans, "violations": violations, "warnings": warnings}


def render(res: Dict[str, Any]) -> str:
    lines = [f"schedule windows {res['since']} -> {res['now']} (dropped = no run after "
             f"{res['drop_after_min']} min)"]
    for r in res["rows"]:
        st = res["stats"][r["cron"]]
        if r["status"] == "fired":
            lines.append(f"  fired    {r['window']}  [{r['cron']}]  +{r['late_min']} min")
        else:
            ref = (f"this cron p50 {st['p50']:g} / max {st['max']} over {st['n']}"
                   if st.get("n") else "no fired window in range to compare")
            tag = "DROPPED " if r["status"] == "dropped" else "PENDING "
            lines.append(f"  {tag} {r['window']}  [{r['cron']}]  {r['age_min']} min past due ({ref})")
    for o in res["orphans"]:
        lines.append(f"  WARN orphan run {o.get('databaseId')} at {o['createdAt']} matches no window")
    for w in res["warnings"]:
        lines.append(f"  WARN {w['window']} is later than any fired window of [{w['cron']}] -- "
                     f"not dropped yet, but outside what this range has seen")
    verdict = "BAD" if res["violations"] else "OK"
    pend = sum(1 for r in res["rows"] if r["status"] == "pending")
    lines.append(f"{verdict}: {len(res['violations'])} dropped, {pend} pending, "
                 f"{len(res['warnings'])} warnings")
    return "\n".join(lines)


def fetch_runs(repo: Path, workflow: str) -> Optional[List[Dict[str, Any]]]:
    try:
        r = subprocess.run(["gh", "run", "list", "--workflow", Path(workflow).name,
                            "--event", "schedule", "-L", "100",
                            "--json", "createdAt,databaseId,conclusion"],
                           cwd=str(repo), capture_output=True, text=True, timeout=60)
    except Exception:  # noqa: BLE001 -- unreadable is reported as exit 2 below
        return None
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


def cron_changed_at(repo: Path, workflow: str) -> Optional[datetime]:
    """Commit time of the last change to a `cron:` line -- windows before it used other times."""
    try:
        r = subprocess.run(["git", "-C", str(repo), "log", "-1", "-G", "cron:",
                            "--format=%cI", "--", workflow],
                           capture_output=True, text=True, timeout=20)
    except Exception:  # noqa: BLE001
        return None
    s = r.stdout.strip()
    return _ts(s) if r.returncode == 0 and s else None


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=".", type=Path)
    ap.add_argument("--workflow", default=WORKFLOW)
    ap.add_argument("--runs-json", type=Path, help="gh run list --json createdAt,databaseId output")
    ap.add_argument("--now", help="ISO UTC time (default: now)")
    ap.add_argument("--since", help="ISO UTC start (default: lookback, clamped to last cron change)")
    ap.add_argument("--lookback-days", type=float, default=LOOKBACK_DAYS)
    ap.add_argument("--drop-after", type=int, default=DROP_AFTER_MIN)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args(argv)

    crons = parse_crons((a.repo / a.workflow).read_text(encoding="utf-8"))
    if not crons:
        print(f"ERROR: no cron lines in {a.workflow}")
        return 2
    now = _ts(a.now) if a.now else datetime.now(timezone.utc)
    if a.since:
        since = _ts(a.since)
    else:
        since = now - timedelta(days=a.lookback_days)
        changed = cron_changed_at(a.repo, a.workflow)
        if changed and changed > since:
            since = changed
    runs = (json.loads(a.runs_json.read_text(encoding="utf-8")) if a.runs_json
            else fetch_runs(a.repo, a.workflow))
    if runs is None:
        print("ERROR: could not read scheduled runs (gh) -- cannot tell late from dropped")
        return 2
    res = check(crons, runs, now, since, a.drop_after)
    print(render(res))
    if a.json:
        a.json.write_text(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    return 1 if res["violations"] else 0


if __name__ == "__main__":
    sys.exit(main())
