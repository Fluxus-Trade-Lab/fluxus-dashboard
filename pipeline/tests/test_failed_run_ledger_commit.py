"""A failed run's ledger line must reach origin/main.

`.github/workflows/daily-data-update.yml`, step "Commit the ledger even when a
gate failed", exists so that a run which trips a gate still leaves its
`run_ledger.jsonl` line (and the two audit JSONs) on main. On 2026-09-09 it
could not: the late main-schedule run failed after a manual dispatch had
already landed the session, and the dispatch had committed files -- e.g.
`data/output/trades/SOXL_2026-09-08_000.json` -- that the failed run had as
UNTRACKED copies in its own working tree. The step committed the three
bookkeeping files and ran `git rebase --autostash origin/main`; autostash
stashes tracked changes only, so all three attempts aborted with "untracked
working tree files would be overwritten" and the failure left no trace on
origin.

These tests build that situation in throwaway git repos -- a bare "origin",
a "dispatch" clone that lands first, a "runner" clone that fails -- and
execute the REAL `run:` script out of the workflow YAML (never a copy: a copy
stays green while the YAML regresses). The only edits made to the script are
`sleep 15` -> `sleep 0`, so the three-attempt failure path of the pre-fix
script finishes in seconds instead of 45.

Verified to report POSITIVE before being trusted: against the pre-fix YAML,
`test_untracked_collision_still_records_both_runs`,
`test_ledger_append_collision_records_both_lines` and
`test_line_committed_before_a_lost_push_is_still_recorded` fail (origin keeps
only the dispatch's line).
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
WORKFLOW = REPO / ".github" / "workflows" / "daily-data-update.yml"
STEP_NAME = "Commit the ledger even when a gate failed"

LEDGER = "data/history/run_ledger.jsonl"
AUDIT = "data/history/audit_last.json"
AUDIT_LEDGER = "data/history/audit_ledger_last.json"
BOOKKEEPING = {LEDGER, AUDIT, AUDIT_LEDGER}
TRADE = "data/output/trades/SOXL_2026-09-08_000.json"

L_OLD1 = '{"session": "2026-09-04", "started_utc": "2026-09-04T20:21:00+00:00", "run_id": "1"}'
L_OLD2 = '{"session": "2026-09-08", "started_utc": "2026-09-08T20:21:00+00:00", "run_id": "2"}'
L_DISPATCH = '{"session": "2026-09-09", "started_utc": "2026-09-09T22:18:53+00:00", "run_id": "34411547131"}'
L_FAILED = '{"session": "2026-09-09", "started_utc": "2026-09-09T22:37:51+00:00", "run_id": "34413142036"}'


# ---------------------------------------------------------------- the script

def _step_via_yaml(text: str):
    try:
        import yaml
    except ModuleNotFoundError:
        return None
    doc = yaml.safe_load(text)
    hits = [s for s in doc["jobs"]["update-data"]["steps"] if s.get("name") == STEP_NAME]
    assert len(hits) == 1, f"expected exactly one step named {STEP_NAME!r}, found {len(hits)}"
    return hits[0]


def _script_via_text(text: str) -> str:
    """PyYAML-free fallback. Still reads the real file, never a copy."""
    lines = text.splitlines()
    starts = [i for i, ln in enumerate(lines) if ln.strip() == f"- name: {STEP_NAME}"]
    assert len(starts) == 1, f"expected exactly one '- name: {STEP_NAME}' line, found {len(starts)}"
    i = starts[0] + 1
    while i < len(lines) and lines[i].strip() not in ("run: |", "run: |-"):
        assert not lines[i].strip().startswith("- name:"), "step has no block-scalar run:"
        i += 1
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
    assert body, "the ledger step's run: block is empty"
    return "\n".join(body).rstrip() + "\n"


def ledger_script() -> str:
    text = WORKFLOW.read_text(encoding="utf-8")
    step = _step_via_yaml(text)
    script = step["run"] if step is not None else _script_via_text(text)
    assert "sleep 15" in script, "retry sleep changed shape; update the test's substitution"
    script = script.replace("sleep 15", "sleep 0")
    leftover = re.findall(r"\$\{\{.*?\}\}", script)
    assert not leftover, (
        f"GitHub expressions inside the script body: {leftover} -- pass them "
        "through the step's env: so the script stays executable as-is"
    )
    return script


# ------------------------------------------------------------------- git rig

def _git(cwd: Path, *args: str, env: dict) -> str:
    out = subprocess.run(["git", *args], cwd=cwd, env=env, capture_output=True,
                         text=True, timeout=60)
    assert out.returncode == 0, f"git {' '.join(args)} failed in {cwd}:\n{out.stdout}\n{out.stderr}"
    return out.stdout


def _write(root: Path, rel: str, content: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


@pytest.fixture
def rig(tmp_path):
    """origin (bare) + dispatch clone + runner clone, all at the same base."""
    home = tmp_path / "home"
    home.mkdir()
    env = {
        **os.environ,
        "HOME": str(home),
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com",
        "GIT_CEILING_DIRECTORIES": str(tmp_path),
    }
    origin = tmp_path / "origin.git"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin), env=env)

    dispatch = tmp_path / "dispatch"
    _git(tmp_path, "clone", "-q", str(origin), str(dispatch), env=env)
    _git(dispatch, "checkout", "-q", "-b", "main", env=env)
    _write(dispatch, LEDGER, f"{L_OLD1}\n{L_OLD2}\n")
    _write(dispatch, AUDIT, '{"audit": "base"}\n')
    _write(dispatch, AUDIT_LEDGER, '{"audit_ledger": "base"}\n')
    _write(dispatch, "data/output/breadth.json", '{"v": "base"}\n')
    _git(dispatch, "add", "-A", env=env)
    _git(dispatch, "commit", "-q", "-m", "base", env=env)
    _git(dispatch, "push", "-q", "-u", "origin", "main", env=env)
    base = _git(dispatch, "rev-parse", "HEAD", env=env).strip()

    runner = tmp_path / "runner"
    _git(tmp_path, "clone", "-q", str(origin), str(runner), env=env)

    return {"tmp": tmp_path, "env": env, "origin": origin, "dispatch": dispatch,
            "runner": runner, "base": base}


def land_dispatch(rig, *, with_trade=True, ledger_line=True):
    """The run that got there first: commits the session to origin/main."""
    d, env = rig["dispatch"], rig["env"]
    if ledger_line:
        with (d / LEDGER).open("a", encoding="utf-8") as fh:
            fh.write(L_DISPATCH + "\n")
    _write(d, AUDIT, '{"audit": "dispatch"}\n')
    _write(d, "data/output/breadth.json", '{"v": "dispatch"}\n')
    if with_trade:
        _write(d, TRADE, '{"from": "dispatch"}\n')
    _git(d, "add", "-A", env=env)
    _git(d, "commit", "-q", "-m", "chore: market data 2026-09-09", env=env)
    _git(d, "push", "-q", "origin", "main", env=env)
    return _git(d, "rev-parse", "HEAD", env=env).strip()


def fail_the_run(rig, *, with_trade=True, ledger_line=True, touch_audit_ledger=True):
    """The run that tripped a gate: leaves its outputs lying in the tree."""
    r = rig["runner"]
    if ledger_line:
        with (r / LEDGER).open("a", encoding="utf-8") as fh:
            fh.write(L_FAILED + "\n")
    if touch_audit_ledger:
        _write(r, AUDIT_LEDGER, '{"audit_ledger": "failed run: regression"}\n')
    # audit_last.json deliberately left at the base version: this run did not
    # get that far, so its copy must NOT roll back the dispatch's newer one.
    _write(r, "data/output/breadth.json", '{"v": "failed run"}\n')        # tracked, modified
    _write(r, "data/output/failed_only.json", '{"v": "failed run"}\n')    # untracked, new
    if with_trade:
        _write(r, TRADE, '{"from": "failed run"}\n')                       # untracked here, tracked on origin


def run_step(rig, script=None):
    env = {**rig["env"], "BASE_SHA": rig["base"], "RUNNER_TEMP": str(rig["tmp"] / "runner_temp")}
    (rig["tmp"] / "runner_temp").mkdir(exist_ok=True)
    proc = subprocess.run(["bash", "-e", "-c", script or ledger_script()], cwd=rig["runner"],
                          env=env, capture_output=True, text=True, timeout=120)
    # continue-on-error in the workflow; a non-zero exit is still a bug here
    assert proc.returncode == 0, f"ledger step exited {proc.returncode}:\n{proc.stdout}\n{proc.stderr}"
    return proc


def origin_show(rig, rel: str) -> str | None:
    out = subprocess.run(["git", "show", f"main:{rel}"], cwd=rig["origin"], env=rig["env"],
                         capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else None


def origin_head(rig) -> str:
    return _git(rig["origin"], "rev-parse", "main", env=rig["env"]).strip()


def changed_between(rig, a: str, b: str) -> set[str]:
    return set(_git(rig["origin"], "diff", "--name-only", a, b, env=rig["env"]).split())


def _report(proc) -> str:
    return f"\n--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"


# --------------------------------------------------------------------- tests

def test_untracked_collision_still_records_both_runs(rig):
    """THE 09-09 CASE: the dispatch committed a file the failed run has untracked."""
    landed = land_dispatch(rig)
    fail_the_run(rig)
    proc = run_step(rig)

    ledger = origin_show(rig, LEDGER)
    assert ledger is not None
    assert ledger.splitlines() == [L_OLD1, L_OLD2, L_DISPATCH, L_FAILED], (
        "origin/main must carry the dispatch's line AND the failed run's line" + _report(proc))
    assert origin_show(rig, TRADE) == '{"from": "dispatch"}\n', "origin's copy of the trade file was replaced"
    assert origin_show(rig, AUDIT_LEDGER) == '{"audit_ledger": "failed run: regression"}\n'
    assert origin_show(rig, AUDIT) == '{"audit": "dispatch"}\n', (
        "an audit JSON the failed run never touched rolled main's newer copy back")
    assert origin_show(rig, "data/output/breadth.json") == '{"v": "dispatch"}\n'
    assert origin_show(rig, "data/output/failed_only.json") is None
    # plan B holds: the failed run's commit touches bookkeeping only
    assert changed_between(rig, landed, origin_head(rig)) == {LEDGER, AUDIT_LEDGER}
    assert "Ledger not recorded" not in proc.stdout


def test_ledger_append_collision_records_both_lines(rig):
    """Both runs appended to the append-only ledger; no untracked collision."""
    landed = land_dispatch(rig, with_trade=False)
    fail_the_run(rig, with_trade=False)
    proc = run_step(rig)

    assert (origin_show(rig, LEDGER) or "").splitlines() == [L_OLD1, L_OLD2, L_DISPATCH, L_FAILED], _report(proc)
    assert changed_between(rig, landed, origin_head(rig)) == {LEDGER, AUDIT_LEDGER}


def test_line_committed_before_a_lost_push_is_still_recorded(rig):
    """`Commit and push` committed tonight's data (ledger line included) and
    then lost the push race. HEAD now CONTAINS the line, so counting from HEAD
    would call it old; the step must count from the checkout commit."""
    landed = land_dispatch(rig, with_trade=False)
    fail_the_run(rig, with_trade=False)
    r, env = rig["runner"], rig["env"]
    _git(r, "add", "data/output/", "data/history/", env=env)
    _git(r, "commit", "-q", "-m", "chore: market data (push lost)", env=env)
    proc = run_step(rig)

    assert (origin_show(rig, LEDGER) or "").splitlines() == [L_OLD1, L_OLD2, L_DISPATCH, L_FAILED], _report(proc)
    assert changed_between(rig, landed, origin_head(rig)) == {LEDGER, AUDIT_LEDGER}


def test_no_changes_records_nothing(rig):
    """Nothing of the three changed -> say so, push nothing."""
    landed = land_dispatch(rig)
    fail_the_run(rig, ledger_line=False, touch_audit_ledger=False)
    proc = run_step(rig)

    assert "no ledger changes to record" in proc.stdout, _report(proc)
    assert origin_head(rig) == landed


def test_a_line_main_already_has_is_not_duplicated(rig):
    """If the tree's ledger already includes main's line past BASE (HEAD was
    rebased onto it before the push was lost), replay must not append it twice."""
    land_dispatch(rig, with_trade=False)
    r, env = rig["runner"], rig["env"]
    with (r / LEDGER).open("a", encoding="utf-8") as fh:
        fh.write(L_DISPATCH + "\n" + L_FAILED + "\n")
    proc = run_step(rig)

    assert (origin_show(rig, LEDGER) or "").splitlines() == [L_OLD1, L_OLD2, L_DISPATCH, L_FAILED], _report(proc)


def test_step_wiring():
    """BASE_SHA must be the checkout commit, and the step must stay
    failure-only and non-fatal. Needs PyYAML to read `env:`/`if:` reliably."""
    yaml = pytest.importorskip("yaml")
    step = _step_via_yaml(WORKFLOW.read_text(encoding="utf-8"))
    assert step is not None
    assert step.get("if") == "failure()"
    assert step.get("continue-on-error") is True
    assert (step.get("env") or {}).get("BASE_SHA") == "${{ github.sha }}"
    script = step["run"]
    assert not re.search(r"git\s+rebase", script), "the replay must not go back to rebasing"
    # stages the three bookkeeping paths and nothing wider
    assert not re.search(r"git add\s+(-A|\.|data/output)", script)
    assert "git commit -a" not in script
