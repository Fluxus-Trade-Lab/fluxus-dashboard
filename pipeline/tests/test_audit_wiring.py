"""Can this auditor report red -- and does it discriminate?

An audit that has never been seen to fire is not evidence of anything. Two
kinds of test live here:

  * POSITIVE CONTROLS -- one per violation class (W1..W4), each building a
    tree where the answer is known to be BAD and asserting we say BAD.
  * DISCRIMINATION -- the four things a grep would get wrong. Each pairs a
    "looks wired but isn't" tree against a "genuinely wired" tree and asserts
    the two come out different. A detector that says "wired" to both is
    useless in exactly the direction that hurts: it under-reports.

The last test asserts the REAL repository is green. That is the ratchet: the
known-unwired table below `audit_wiring` may only shrink, and if a new guard
lands with nobody calling it, this file turns red.
"""

import textwrap
from pathlib import Path

import pytest

from pipeline.tools import audit_wiring as W


def tree(root: Path, guards=(), workflows=None, prod=None):
    """Minimal repo: guard modules, workflow files, production python."""
    (root / "pipeline" / "tools").mkdir(parents=True, exist_ok=True)
    for g in guards:
        (root / "pipeline" / "tools" / f"{g}.py").write_text("def check():\n    return {}\n")
    wf = root / ".github" / "workflows"
    wf.mkdir(parents=True, exist_ok=True)
    for name, body in (workflows or {}).items():
        (wf / name).write_text(textwrap.dedent(body))
    for name, body in (prod or {}).items():
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(body))
    return root


SCHEDULED = """\
    name: nightly
    on:
      schedule:
        - cron: '30 21 * * 1-5'
    jobs:
      go:
        runs-on: ubuntu-latest
        steps:
          - run: |
              {cmd}
    """


def run(root, exempt=None, known=None):
    f = W.collect(root)
    return W.check(f["guards"], f["ci"], f["prod"],
                   exempt=exempt or {}, known=known or {})


# ---------- positive controls: each violation class can fire ----------

def test_w1_a_new_guard_nobody_calls_is_red(tmp_path):
    """The 2026-08-31 shape: a guard exists, nothing runs it, nobody declared it."""
    out = run(tree(tmp_path, guards=["audit_lonely"]))
    assert not out["ok"]
    assert any(v.startswith("W1 audit_lonely") for v in out["violations"])
    assert out["status"]["audit_lonely"][0] == "UNWIRED"


def test_w2_fixing_a_guard_forces_you_to_delete_the_excuse(tmp_path):
    """Anti-rot: the table may not outlive the problem it describes."""
    root = tree(tmp_path, guards=["audit_x"],
                workflows={"n.yml": SCHEDULED.format(
                    cmd="python -m pipeline.tools.audit_x")})
    out = run(root, known={"audit_x": ("ALEX", "2026-09-03", "why")})
    assert not out["ok"]
    assert any(v.startswith("W2 audit_x") for v in out["violations"])


def test_w3_an_entry_for_a_module_that_no_longer_exists_is_red(tmp_path):
    out = run(tree(tmp_path, guards=["audit_x"]),
              known={"audit_ghost": ("ALEX", "2026-09-03", "why")})
    assert any(v.startswith("W3 audit_ghost") for v in out["violations"])


@pytest.mark.parametrize("entry", [("", "2026-09-03", "why"),
                                   ("ALEX", "2026-09-03", "")])
def test_w4_an_entry_without_an_owner_or_a_reason_is_red(tmp_path, entry):
    out = run(tree(tmp_path, guards=["audit_x"]), known={"audit_x": entry})
    assert any(v.startswith("W4 audit_x") for v in out["violations"])


def test_an_exemption_without_a_reason_is_red(tmp_path):
    out = run(tree(tmp_path, guards=["audit_x"]), exempt={"audit_x": "   "})
    assert any(v.startswith("W4 audit_x") for v in out["violations"])


# ---------- discrimination: the four things a grep gets wrong ----------

def test_a_mention_inside_a_run_block_comment_is_not_a_call(tmp_path):
    """`grep audit_archives .github/workflows/` gets 4 hits; 2 are comments."""
    named = tree(tmp_path / "commented", guards=["audit_x"],
                 workflows={"n.yml": SCHEDULED.format(
                     cmd="# python -m pipeline.tools.audit_x   (disabled)\n              echo hi")})
    called = tree(tmp_path / "called", guards=["audit_x"],
                  workflows={"n.yml": SCHEDULED.format(
                      cmd="python -m pipeline.tools.audit_x")})
    assert run(named)["status"]["audit_x"][0] == "UNWIRED"
    assert run(called)["status"]["audit_x"][0] == "ci"


def test_workflow_dispatch_alone_is_a_human_pressing_a_button(tmp_path):
    manual = tree(tmp_path / "manual", guards=["audit_x"], workflows={"n.yml": """\
        name: n
        on: [workflow_dispatch]
        jobs:
          go:
            runs-on: ubuntu-latest
            steps:
              - run: python -m pipeline.tools.audit_x
        """})
    assert run(manual)["status"]["audit_x"][0] == "UNWIRED"


def test_importing_a_lookup_table_is_not_invoking_the_gate(tmp_path):
    """pipeline/no_downgrade.py:85 imports STATUS_RANK and never calls the gate."""
    table = tree(tmp_path / "table", guards=["audit_x"], prod={"pipeline/p.py": """\
        from pipeline.tools.audit_x import STATUS_RANK

        def rank(s):
            return STATUS_RANK.get(s.lower())
        """})
    call = tree(tmp_path / "call", guards=["audit_x"], prod={"pipeline/p.py": """\
        from pipeline.tools.audit_x import check

        def go():
            return check()
        """})
    assert run(table)["status"]["audit_x"][0] == "UNWIRED"
    assert run(call)["status"]["audit_x"][0] == "prod"


def test_a_docstring_that_names_the_module_is_not_a_call(tmp_path):
    doc = tree(tmp_path / "doc", guards=["audit_x"], prod={"pipeline/p.py": '''\
        """See pipeline/tools/audit_x.py for the invariants."""

        def go():
            return 1
        '''})
    sub = tree(tmp_path / "sub", guards=["audit_x"], prod={"pipeline/p.py": '''\
        import subprocess

        def go():
            return subprocess.run(["python", "-m", "pipeline.tools.audit_x"])
        '''})
    assert run(doc)["status"]["audit_x"][0] == "UNWIRED"
    assert run(sub)["status"]["audit_x"][0] == "prod"


# ---------- the ratchet ----------

def test_the_real_repository_is_green():
    """New guard with no caller, or a stale excuse, turns this red."""
    root = Path(__file__).resolve().parents[2]
    facts = W.collect(root)
    out = W.check(facts["guards"], facts["ci"], facts["prod"])
    assert out["ok"], "\n".join(out["violations"])
    assert facts["guards"], "found no guards at all -- the glob is broken"


def test_the_two_guards_we_believe_are_wired_still_are():
    """Independently verified 2026-09-04: these two run from the nightly data
    workflow. If either drops off, that is the 08-31 shape returning."""
    root = Path(__file__).resolve().parents[2]
    ci = W.ci_invocations(root / ".github" / "workflows")
    assert "audit_archives" in ci
    assert "audit_ledger" in ci
