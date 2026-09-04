"""Tests for the auditor that asks what the wired test run actually runs.

Every violation code below has a positive control: a fixture that makes it
fire. A check nobody has seen report an aberration is not evidence when it
stays quiet -- and the first draft of this tool proved the point by reading
`pip install pytest PyYAML` as a test invocation.
"""

import textwrap

import pytest

from pipeline.tools import audit_ci_test_coverage as cov


# ---------- reading the workflow ----------

WF_HEAD = textwrap.dedent("""\
    name: tests
    on:
      push:
      pull_request:
    jobs:
      pytest:
        runs-on: ubuntu-latest
        steps:
    """)


def _wf(steps: str, checkout: str = "      - uses: actions/checkout@v4\n") -> str:
    return WF_HEAD + checkout + textwrap.dedent(steps)


def test_no_fetch_depth_means_depth_one_not_unspecified():
    assert cov.checkout_depth("      - uses: actions/checkout@v4\n") == 1


def test_fetch_depth_zero_is_full_history():
    assert cov.checkout_depth(
        "      - uses: actions/checkout@v4\n"
        "        with:\n"
        "          fetch-depth: 0\n") == 0


def test_a_workflow_that_checks_nothing_out_reports_none():
    assert cov.checkout_depth("jobs:\n  a:\n    steps:\n      - run: echo hi\n") is None


def test_two_checkouts_report_the_shallow_one_not_the_deep_one():
    """Over-reporting is the safe direction; under-reporting says all is well."""
    text = ("      - uses: actions/checkout@v4\n"
            "        with:\n"
            "          fetch-depth: 0\n"
            "      - uses: actions/checkout@v4\n")
    assert cov.checkout_depth(text) == 1


def test_fetch_depth_belonging_to_a_later_step_is_not_borrowed():
    text = ("      - uses: actions/checkout@v4\n"
            "      - uses: actions/setup-python@v6\n"
            "        with:\n"
            "          fetch-depth: 0\n")
    assert cov.checkout_depth(text) == 1


# ---------- naming pytest is not running it ----------

def test_pip_install_pytest_is_not_a_test_run():
    """The bug this tool shipped with: `\\bpytest\\b` matched the install step."""
    assert cov._invocation("pip install -r req.txt pytest PyYAML") is None


def test_python_dash_m_pytest_is_a_test_run():
    assert cov._invocation("python -m pytest pipeline/tests -q") == \
        ["pipeline/tests", "-q"]


def test_bare_pytest_is_a_test_run():
    assert cov._invocation("pytest -q") == ["-q"]


def test_leading_env_assignments_are_stripped():
    assert cov._invocation("PYTHONPATH=. pytest tests") == ["tests"]


def test_a_comment_mentioning_pytest_is_not_a_test_run():
    assert cov._invocation("echo 'run pytest later'") is None


# ---------- the marker expression ----------

@pytest.mark.parametrize("expr,expected", [
    ("not slow", {"slow"}),
    ("not slow and not flaky", {"slow", "flaky"}),
])
def test_negated_markers_are_understood(expr, expected):
    got, understood = cov.negated_markers(expr)
    assert understood and got == expected


@pytest.mark.parametrize("expr", ["slow or flaky", "not (slow or flaky)", "slow"])
def test_an_expression_we_cannot_model_says_so_instead_of_guessing(expr):
    _, understood = cov.negated_markers(expr)
    assert not understood


def test_an_unmodelled_marker_expression_becomes_an_unmodelled_option():
    _, markers, unmodelled = cov.parse_pytest_args(["-m", "slow or flaky"])
    assert markers == set() and unmodelled


def test_dash_k_is_reported_as_unmodelled_and_eats_its_argument():
    targets, _, unmodelled = cov.parse_pytest_args(["-k", "overwrite", "tests"])
    assert unmodelled == ["-k"] and targets == ["tests"]


def test_tb_short_does_not_swallow_the_target_after_it():
    targets, _, unmodelled = cov.parse_pytest_args(["--tb=short", "tests"])
    assert targets == ["tests"] and not unmodelled


def test_the_real_workflow_command_parses_to_one_excluded_marker():
    targets, markers, unmodelled = cov.parse_pytest_args(
        ["pipeline/tests", "-q", "-m", "not slow", "--tb=short"])
    assert targets == ["pipeline/tests"] and markers == {"slow"} and not unmodelled


# ---------- reading the suite ----------

def _write_suite(tmp_path, rel, body):
    d = tmp_path / rel
    d.mkdir(parents=True, exist_ok=True)
    (d / "test_x.py").write_text(textwrap.dedent(body))
    return tmp_path


def test_a_marker_on_a_test_is_seen(tmp_path):
    _write_suite(tmp_path, "pipeline/tests", """\
        import pytest
        @pytest.mark.slow
        def test_a(): pass
        def test_b(): pass
        """)
    got = {t["name"]: t for t in cov.suite_tests(tmp_path)}
    assert got["test_a"]["markers"] == {"slow"} and got["test_b"]["markers"] == set()


def test_a_module_level_pytestmark_reaches_every_test(tmp_path):
    _write_suite(tmp_path, "tests", """\
        import pytest
        pytestmark = pytest.mark.slow
        def test_a(): pass
        """)
    assert cov.suite_tests(tmp_path)[0]["markers"] == {"slow"}


def test_a_skipif_on_repository_history_is_flagged(tmp_path):
    _write_suite(tmp_path, "pipeline/tests", """\
        import pytest
        def _has(r): return True
        @pytest.mark.skipif(not _has("abc"), reason="shallow checkout")
        def test_a(): pass
        def test_b(): pass
        """)
    got = {t["name"]: t["history_gated"] for t in cov.suite_tests(tmp_path)}
    assert got == {"test_a": True, "test_b": False}


def test_skipif_is_not_mistaken_for_a_marker_name(tmp_path):
    _write_suite(tmp_path, "pipeline/tests", """\
        import pytest
        @pytest.mark.skipif(False, reason="x")
        def test_a(): pass
        """)
    assert cov.suite_tests(tmp_path)[0]["markers"] == set()


# ---------- the comparison ----------

def _tests(*specs):
    out = []
    for f, name, markers, hist in specs:
        out.append({"file": f, "root": f.split("/")[0] if "/" in f else f,
                    "name": name, "line": 1, "markers": set(markers),
                    "history_gated": hist})
    return out


def _step(targets=("pipeline/tests",), markers=(), depth=1, unmodelled=()):
    return {"workflow": "tests.yml", "command": "pytest", "depth": depth,
            "targets": list(targets), "markers": set(markers),
            "unmodelled": list(unmodelled)}


def test_a_test_root_no_step_targets_is_excluded():
    t = _tests(("tests/a/test_x.py", "test_a", (), False))
    t[0]["root"] = "tests"
    buckets = cov.excluded_tests(t, [_step()])
    assert list(buckets) == ["tests"]


def test_a_marked_test_inside_a_targeted_root_is_excluded_by_the_marker():
    t = _tests(("pipeline/tests/test_x.py", "test_a", ("slow",), False))
    assert list(cov.excluded_tests(t, [_step(markers=("slow",))])) == ["marker:slow"]


def test_a_history_gated_test_runs_when_the_checkout_is_full():
    t = _tests(("pipeline/tests/test_x.py", "test_a", (), True))
    assert cov.excluded_tests(t, [_step(depth=0)]) == {}


def test_a_history_gated_test_is_excluded_by_a_shallow_checkout():
    t = _tests(("pipeline/tests/test_x.py", "test_a", (), True))
    assert list(cov.excluded_tests(t, [_step(depth=1)])) == ["shallow-checkout"]


def test_a_test_one_step_skips_and_another_runs_is_not_excluded():
    t = _tests(("pipeline/tests/test_x.py", "test_a", ("slow",), False))
    steps = [_step(markers=("slow",)), _step()]
    assert cov.excluded_tests(t, steps) == {}


def test_a_bare_pytest_with_no_target_covers_the_whole_tree():
    t = _tests(("tests/test_x.py", "test_a", (), False))
    t[0]["root"] = "tests"
    assert cov.excluded_tests(t, [_step(targets=())]) == {}


def test_a_target_prefix_does_not_match_a_sibling_directory():
    t = _tests(("pipeline/tests_extra/test_x.py", "test_a", (), False))
    t[0]["root"] = "pipeline/tests_extra"
    assert list(cov.excluded_tests(t, [_step()])) == ["pipeline/tests_extra"]


# ---------- the violation codes, each with a positive control ----------

DECL = {"tests": ("owner", "reason", "2026-09-05")}


def test_t1_fires_when_an_exclusion_is_undeclared():
    t = _tests(("tests/test_x.py", "test_a", (), False))
    t[0]["root"] = "tests"
    res = cov.check(t, [_step()], declared={})
    assert [c for c, _ in res["violations"]] == ["T1"]


def test_t1_is_silent_once_that_exclusion_is_declared():
    t = _tests(("tests/test_x.py", "test_a", (), False))
    t[0]["root"] = "tests"
    res = cov.check(t, [_step()], declared=DECL)
    assert res["violations"] == []


def test_t2_fires_when_a_declared_exclusion_no_longer_excludes_anything():
    """The anti-rot half: fixing it forces you to delete the excuse."""
    t = _tests(("pipeline/tests/test_x.py", "test_a", (), False))
    res = cov.check(t, [_step()], declared=DECL)
    assert ("T2", "declared exclusion 'tests' excludes nothing now "
                  "-- delete the entry") in res["violations"]


def test_t3_fires_when_a_declared_marker_is_on_no_test():
    t = _tests(("pipeline/tests/test_x.py", "test_a", ("slow",), False))
    decl = {"marker:slow": ("o", "r", "d"), "marker:ghost": ("o", "r", "d")}
    res = cov.check(t, [_step(markers=("slow",))], declared=decl)
    assert any(c == "T3" and "ghost" in m for c, m in res["violations"])


def test_t4_fires_when_a_declared_entry_has_no_owner():
    t = _tests(("tests/test_x.py", "test_a", (), False))
    t[0]["root"] = "tests"
    res = cov.check(t, [_step()], declared={"tests": ("", "reason", "d")})
    assert any(c == "T4" for c, _ in res["violations"])


def test_t5_fires_on_an_option_the_parser_does_not_model():
    res = cov.check([], [_step(unmodelled=["-k"])], declared={})
    assert any(c == "T5" for c, _ in res["violations"])


def test_t6_fires_when_nothing_runs_pytest_automatically():
    res = cov.check([], [], declared={})
    assert any(c == "T6" for c, _ in res["violations"])


# ---------- against this repository ----------

def test_the_real_repository_is_green_on_its_declared_set():
    """If this goes red, either a new blind spot opened or an old one closed.

    Both mean the same thing: edit DECLARED. It is not allowed to drift.
    """
    tests = cov.suite_tests(cov.ROOT)
    steps = cov.pytest_steps(cov.ROOT / ".github" / "workflows")
    res = cov.check(tests, steps)
    assert res["violations"] == [], cov.render(res)


def test_the_repository_really_does_have_a_second_untriggered_test_root():
    """The finding this tool was written for, pinned so it cannot quietly go away."""
    steps = cov.pytest_steps(cov.ROOT / ".github" / "workflows")
    assert steps, "no automatic trigger runs pytest at all"
    targets = {t for s in steps for t in s["targets"]}
    assert (cov.ROOT / "tests").is_dir()
    if "tests" not in targets and not any(not s["targets"] for s in steps):
        buckets = cov.excluded_tests(cov.suite_tests(cov.ROOT), steps)
        assert len(buckets.get("tests", [])) > 100


def test_render_names_the_owner_of_every_bucket_it_prints():
    tests = cov.suite_tests(cov.ROOT)
    steps = cov.pytest_steps(cov.ROOT / ".github" / "workflows")
    text = cov.render(cov.check(tests, steps))
    assert text.count("owner:") == len(cov.excluded_tests(tests, steps))  # one per bucket


# ---------- the control that matters: can it see the fix? ----------

FIXED_WORKFLOW = """\
name: tests
on:
  push:
jobs:
  pytest:
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - run: python -m pytest pipeline/tests tests -q
"""


def test_the_fixed_workflow_leaves_nothing_excluded(tmp_path):
    """Positive control on the whole tool, in the direction that matters.

    Everything else here proves it can report a hole. This proves it can
    report the hole CLOSING -- otherwise the declared table would be a place
    entries go to live forever, and its green would mean nothing.
    """
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "tests.yml").write_text(FIXED_WORKFLOW)
    steps = cov.pytest_steps(wf)
    assert len(steps) == 1 and steps[0]["depth"] == 0 and not steps[0]["markers"]

    tests = cov.suite_tests(cov.ROOT)
    assert cov.excluded_tests(tests, steps) == {}

    res = cov.check(tests, steps)
    codes = sorted({c for c, _ in res["violations"]})
    assert codes == ["T2"], cov.render(res)
    assert len(res["violations"]) == len(cov.DECLARED)
