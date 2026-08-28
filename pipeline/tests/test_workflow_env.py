"""The workflow must give every step the env its own script reads.

2026-08-23 I inserted a new step between the ticker refresh and the one after
it, and the `env:` block that belonged to the refresh went with the new step.
The refresh then took its "credentials not configured" branch every night for
five nights, exited 0, and the run stayed GREEN while the OHLC store went from
47% frozen to 100% frozen. Nothing failed. The staleness report printed
"100.0% stale" into a log nobody reads.

This reads the workflow itself: any step whose `run:` mentions an env var must
declare it (or inherit it from the job). Parsed with a small hand-rolled
scanner rather than PyYAML -- pyyaml is not in pipeline/requirements.txt and a
test that silently skips is the same failure mode this file exists to catch.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

WORKFLOWS = sorted((Path(__file__).resolve().parents[2] / ".github/workflows").glob("*.yml"))
# vars a step's shell reads; GITHUB_* and standard runner vars are provided
TRACKED = re.compile(r"\$\{?([A-Z][A-Z0-9_]{3,})\b")
PROVIDED = {"GITHUB_TOKEN", "GITHUB_WORKSPACE", "GITHUB_ENV", "GITHUB_OUTPUT",
            "GITHUB_STEP_SUMMARY", "GITHUB_REF", "GITHUB_SHA", "HOME", "PATH",
            "RUNNER_OS", "RUNNER_TEMP", "CI"}


def _steps(text: str):
    """(name, run_block, env_names, job_env_names) per step. Indentation-based:
    steps sit at 6 spaces, their keys at 8."""
    job_env: set[str] = set()
    in_job_env = False
    for line in text.splitlines():
        if re.match(r"^    env:\s*$", line):
            in_job_env = True; continue
        if in_job_env:
            m = re.match(r"^      ([A-Z][A-Z0-9_]*):", line)
            if m:
                job_env.add(m.group(1)); continue
            if line.strip() and not line.startswith("      "):
                in_job_env = False

    steps, cur = [], None
    mode = None
    for line in text.splitlines():
        if re.match(r"^      - name:", line):
            if cur:
                steps.append(cur)
            cur = {"name": line.split("name:", 1)[1].strip(), "run": [], "env": set()}
            mode = None
            continue
        if cur is None:
            continue
        if re.match(r"^        run:", line):
            mode = "run"
            cur["run"].append(line.split("run:", 1)[1])
            continue
        if re.match(r"^        env:", line):
            mode = "env"
            continue
        if re.match(r"^        \w+:", line):        # any other step key
            mode = None
            continue
        if mode == "run":
            cur["run"].append(line)
        elif mode == "env":
            m = re.match(r"^          ([A-Z][A-Z0-9_]*):", line)
            if m:
                cur["env"].add(m.group(1))
            elif line.strip() and not line.startswith("          "):
                mode = None
    if cur:
        steps.append(cur)
    return steps, job_env


@pytest.mark.parametrize("wf", WORKFLOWS, ids=lambda p: p.name)
def test_every_step_declares_the_env_its_script_reads(wf):
    text = wf.read_text()
    steps, job_env = _steps(text)
    assert steps, f"{wf.name}: parsed no steps -- the scanner broke, not the workflow"
    missing = []
    for s in steps:
        used = {v for v in TRACKED.findall("\n".join(s["run"]))
                if v not in PROVIDED and not v.startswith("GITHUB_")}
        # only vars this repo actually injects somewhere are our problem
        used = {v for v in used if v in _ALL_INJECTED(text)}
        gap = used - s["env"] - job_env
        if gap:
            missing.append(f"{wf.name} :: {s['name']} reads {sorted(gap)} but declares {sorted(s['env']) or 'nothing'}")
    assert not missing, "step reads an env var it was never given:\n  " + "\n  ".join(missing)


def _ALL_INJECTED(text: str) -> set[str]:
    """Env names this workflow injects anywhere -- the set we can be wrong about."""
    return set(re.findall(r"^\s+([A-Z][A-Z0-9_]*):\s*\$\{\{", text, re.M)) | \
           set(re.findall(r"^\s+([A-Z][A-Z0-9_]*):\s*'", text, re.M))


def test_the_scanner_can_report_positive(tmp_path):
    """An unverified green is not evidence: give it the 2026-08-23 shape and
    confirm it fails."""
    bad = tmp_path / "bad.yml"
    bad.write_text(
        "jobs:\n  j:\n    steps:\n"
        "      - name: uses a secret it was not given\n"
        "        run: |\n"
        "          if [ -z \"$FLUXUS_GAS_URL\" ]; then exit 0; fi\n"
        "          echo go\n"
        "      - name: has it\n"
        "        run: echo $FLUXUS_GAS_URL\n"
        "        env:\n"
        "          FLUXUS_GAS_URL: ${{ secrets.FLUXUS_GAS_URL }}\n")
    with pytest.raises(AssertionError, match="never given"):
        test_every_step_declares_the_env_its_script_reads(bad)
