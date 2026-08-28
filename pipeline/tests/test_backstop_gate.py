"""The backstop gate's date test must survive a late trigger.

`.github/workflows/daily-data-update.yml` carries a second cron, `30 1 * * 2-6`,
whose only job is to notice that the 21:30 UTC main run never landed. It decides
by comparing the newest session in `data/output/breadth.json` against the date it
believes it is looking for (`WANT`).

`WANT` used to be `TZ=America/New_York date +%F` -- the ET date of the moment the
step actually executes. ET midnight is 04:00 UTC (EDT), so a 01:30 UTC schedule
has exactly 150 minutes of slack. GitHub's scheduled runs are late as a matter of
course (this workflow's own comment: 49 business days, median 63 min late, worst
213; and run 33145206555 on the main schedule fired 485 minutes past due). Past
150 minutes `WANT` rolls over to the NEXT calendar day -- a date that can never
appear in `breadth.json` -- so the gate opens unconditionally and the backstop
re-runs a night that already landed.

These tests execute the REAL `run:` script out of the workflow YAML. They do not
keep a copy of it: a copy would stay green while the YAML regressed, which is the
one thing a regression test must not do. The only edit made to the script is
substituting the `${{ github.event.schedule }}` expression that GitHub would have
expanded.

Verified to report POSITIVE before being trusted: on the pre-fix YAML,
`test_late_trigger_does_not_reopen_a_landed_session` fails with run=true.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
WORKFLOW = REPO / ".github" / "workflows" / "daily-data-update.yml"
BACKSTOP_CRON = "30 1 * * 2-6"
MAIN_CRON = "30 21 * * 1-5"
SCHEDULE_EXPR = "${{ github.event.schedule }}"


# ---------------------------------------------------------------- the script

def _decide_script_via_yaml(text: str) -> str | None:
    try:
        import yaml
    except ModuleNotFoundError:
        return None
    doc = yaml.safe_load(text)
    steps = doc["jobs"]["gate"]["steps"]
    hits = [s for s in steps if s.get("id") == "decide"]
    # Count, don't take [0]: two steps sharing an id means the workflow changed
    # shape under us and we would be testing whichever one happened to be first.
    assert len(hits) == 1, f"expected exactly one gate step with id=decide, found {len(hits)}"
    return hits[0]["run"]


def _decide_script_via_text(text: str) -> str:
    """PyYAML-free fallback. Still reads the real file, never a copy."""
    lines = text.splitlines()
    starts = [i for i, ln in enumerate(lines) if ln.strip() == "- id: decide"]
    assert len(starts) == 1, f"expected exactly one '- id: decide' line, found {len(starts)}"
    i = starts[0]
    while i < len(lines) and lines[i].strip() not in ("run: |", "run: |-"):
        i += 1
    assert i < len(lines), "no block-scalar `run:` under the decide step"
    body_indent = None
    body: list[str] = []
    for ln in lines[i + 1:]:
        if not ln.strip():
            body.append("")
            continue
        indent = len(ln) - len(ln.lstrip())
        if body_indent is None:
            body_indent = indent
        elif indent < body_indent:
            break
        body.append(ln[body_indent:])
    assert body, "decide step's run: block is empty"
    return "\n".join(body).rstrip() + "\n"


def decide_script() -> str:
    text = WORKFLOW.read_text(encoding="utf-8")
    return _decide_script_via_yaml(text) or _decide_script_via_text(text)


# ------------------------------------------------------------------ GNU date

def _is_gnu_date(cmd: str | None) -> bool:
    if not cmd:
        return False
    try:
        out = subprocess.run(
            [cmd, "-d", "@0", "+%F"],
            capture_output=True, text=True,
            env={**os.environ, "TZ": "UTC"}, timeout=10,
        )
    except OSError:
        return False
    return out.returncode == 0 and out.stdout.strip() == "1970-01-01"


@pytest.fixture(scope="module")
def gnu_date_path(tmp_path_factory) -> str:
    """A PATH on which `date` understands `-d @epoch`, or skip saying why.

    The runner is ubuntu (GNU coreutils), so the workflow may use `date -d`. On
    macOS `/bin/date` is BSD and cannot; if Homebrew coreutils' `gdate` is
    present we shim it in as `date`, otherwise these behavioural cases skip.
    `test_gate_reads_the_now_override` below never skips -- the GATE_NOW_EPOCH
    seam itself stays covered on any machine.
    """
    if _is_gnu_date(shutil.which("date")):
        return os.environ.get("PATH", "")
    gdate = shutil.which("gdate")
    if _is_gnu_date(gdate):
        shim = tmp_path_factory.mktemp("gnu_date_shim")
        (shim / "date").symlink_to(gdate)
        return f"{shim}{os.pathsep}{os.environ.get('PATH', '')}"
    pytest.skip(
        "no GNU date on this machine: `date -d @<epoch>` is unsupported by BSD "
        "date and `gdate` (Homebrew coreutils, `brew install coreutils`) is not "
        "installed either. The workflow itself runs on ubuntu-latest where GNU "
        "date is guaranteed; only this local execution of its script is skipped."
    )


# -------------------------------------------------------------------- runner

def _epoch(iso_utc: str) -> int:
    return int(datetime.strptime(iso_utc, "%Y-%m-%dT%H:%M:%SZ")
               .replace(tzinfo=timezone.utc).timestamp())


def _breadth(*dates: str) -> str:
    return json.dumps({"conditions": {"history": [{"date": d} for d in dates]}})


def run_gate(tmp_path, path, *, now=None, breadth=None, schedule=BACKSTOP_CRON):
    """Execute the real decide script; return (run_flag, completed_process)."""
    script = decide_script()
    assert SCHEDULE_EXPR in script, (
        "the decide script no longer references ${{ github.event.schedule }}; "
        "this test would be exercising the wrong branch"
    )
    script = script.replace(SCHEDULE_EXPR, schedule)
    leftover = re.findall(r"\$\{\{.*?\}\}", script)
    assert not leftover, f"unexpanded GitHub expressions in the script: {leftover}"

    work = tmp_path / "work"
    (work / "data" / "output").mkdir(parents=True, exist_ok=True)
    if breadth is not None:
        (work / "data" / "output" / "breadth.json").write_text(breadth, encoding="utf-8")

    gh_output = tmp_path / "github_output"
    gh_output.write_text("", encoding="utf-8")

    env = {**os.environ, "PATH": path, "GITHUB_OUTPUT": str(gh_output)}
    env.pop("TZ", None)
    env.pop("GATE_NOW_EPOCH", None)
    if now is not None:
        env["GATE_NOW_EPOCH"] = str(_epoch(now))

    proc = subprocess.run(["bash", "-e", "-c", script], cwd=work, env=env,
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, f"gate step failed:\n{proc.stdout}\n{proc.stderr}"

    flags = re.findall(r"^run=(\S+)$", gh_output.read_text(encoding="utf-8"), re.M)
    assert len(flags) == 1, f"expected exactly one run= line, got {flags}"
    return flags[0], proc


# --------------------------------------------------------------------- tests

def test_on_time_trigger_skips_a_landed_session(tmp_path, gnu_date_path):
    """01:30 UTC exactly, 2026-08-27 already in the file -> nothing to do."""
    flag, proc = run_gate(
        tmp_path, gnu_date_path,
        now="2026-08-28T01:30:00Z",
        breadth=_breadth("2026-08-25", "2026-08-26", "2026-08-27"),
    )
    assert flag == "false", proc.stdout
    assert "2026-08-27" in proc.stdout


@pytest.mark.parametrize("trigger,late_min", [
    ("2026-08-28T03:59:00Z", 149),   # inside the OLD 150-minute margin
    ("2026-08-28T04:01:00Z", 151),   # one minute past it: the old code rolled over
    ("2026-08-28T05:35:19Z", 245),   # the shape that actually happens
    ("2026-08-28T09:59:00Z", 509),   # still inside the new 8h30m margin
])
def test_late_trigger_does_not_reopen_a_landed_session(tmp_path, gnu_date_path,
                                                       trigger, late_min):
    """THE REGRESSION CASE.

    Same landed session, same schedule -- only the wall clock moved. Before the
    fix every row past 150 minutes returned run=true and the backstop would have
    recomputed a night that was already on disk.
    """
    flag, proc = run_gate(
        tmp_path, gnu_date_path,
        now=trigger,
        breadth=_breadth("2026-08-26", "2026-08-27"),
    )
    assert flag == "false", (
        f"gate opened on a session that already landed, {late_min} min late "
        f"({trigger}):\n{proc.stdout}"
    )


def test_genuinely_missed_session_still_fires(tmp_path, gnu_date_path):
    """The backstop must keep working -- 08-27 is missing, so run it."""
    flag, proc = run_gate(
        tmp_path, gnu_date_path,
        now="2026-08-28T01:30:00Z",
        breadth=_breadth("2026-08-25", "2026-08-26"),
    )
    assert flag == "true", proc.stdout


def test_late_trigger_still_fires_on_a_genuinely_missed_session(tmp_path, gnu_date_path):
    """Lateness must not make the gate blind in the other direction either."""
    flag, proc = run_gate(
        tmp_path, gnu_date_path,
        now="2026-08-28T05:35:19Z",
        breadth=_breadth("2026-08-25", "2026-08-26"),
    )
    assert flag == "true", proc.stdout


@pytest.mark.parametrize("payload", [
    None,                                   # file absent
    "{ not json at all",                    # unparseable
    '{"conditions": {}}',                   # right file, wrong shape
    '{"conditions": {"history": []}}',      # shape ok, empty
])
def test_broken_breadth_fails_open(tmp_path, gnu_date_path, payload):
    """A broken breadth.json is exactly when the backstop must not sit out."""
    flag, proc = run_gate(
        tmp_path, gnu_date_path,
        now="2026-08-28T01:30:00Z",
        breadth=payload,
    )
    assert flag == "true", proc.stdout


@pytest.mark.parametrize("schedule", [MAIN_CRON, ""])
def test_main_schedule_and_dispatch_always_run(tmp_path, gnu_date_path, schedule):
    """The gate only ever judges the backstop cron; everything else runs."""
    flag, proc = run_gate(
        tmp_path, gnu_date_path,
        now="2026-08-28T05:35:19Z",
        breadth=_breadth("2026-08-27"),
        schedule=schedule,
    )
    assert flag == "true", proc.stdout
    assert "main schedule or manual dispatch" in proc.stdout


def test_gate_reads_the_now_override():
    """The GATE_NOW_EPOCH seam is what makes the cases above testable at all.

    Deliberately free of GNU date and of bash, so that it still runs on a
    machine where the behavioural cases skip: without this, a BSD-date box
    could drop the whole file and report green.
    """
    script = decide_script()
    assert re.search(r'GATE_NOW_EPOCH:-\$\(date -u \+%s\)', script), (
        "the decide script must read NOW from ${GATE_NOW_EPOCH:-$(date -u +%s)} "
        "-- the override is the test seam, the default is production"
    )
    assert "NOW_EPOCH" in script and "21600" in script, (
        "WANT must be computed from the override-able epoch minus 6 hours, not "
        "from the wall clock"
    )
