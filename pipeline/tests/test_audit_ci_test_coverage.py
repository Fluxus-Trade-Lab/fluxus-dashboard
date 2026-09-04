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


def test_the_shallowest_of_two_shallow_checkouts_is_reported():
    """min, not max -- and a fixture that can tell them apart.

    The [0, 1] fixture above cannot: 0 is filtered out before the comparison,
    so min == max == 1 and swapping them changes nothing. This one fails if
    `min` becomes `max`.
    """
    text = ("      - uses: actions/checkout@v4\n"
            "        with:\n"
            "          fetch-depth: 5\n"
            "      - uses: actions/checkout@v4\n"
            "        with:\n"
            "          fetch-depth: 50\n")
    assert cov.checkout_depth(text) == 5


@pytest.mark.parametrize("value", ["0", "'0'", '"0"'])
def test_a_quoted_zero_is_still_full_history(value):
    assert cov.checkout_depth("      - uses: actions/checkout@v4\n"
                              "        with:\n"
                              f"          fetch-depth: {value}\n") == 0


def test_fetch_depth_is_found_past_the_seventh_line():
    """Six sibling keys are enough to push it out of a fixed-size window."""
    text = ("      - uses: actions/checkout@v4\n"
            "        with:\n"
            "          repository: a\n          ref: b\n          token: c\n"
            "          path: d\n          clean: true\n          submodules: false\n"
            "          fetch-depth: 0\n")
    assert cov.checkout_depth(text) == 0


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


@pytest.mark.parametrize("opt", ["--ignore=tests", "--deselect", "-k",
                                 "--collect-only", "--co", "--ignore-glob"])
def test_every_selector_we_do_not_model_is_reported(opt):
    """`-k` was the only one with a test; `--ignore` is the likelier addition.

    `--collect-only` is in here because it is the one option that looks like a
    test run and executes nothing -- modelling it as harmless let a
    `pytest tests --collect-only` step empty a bucket, after which the audit
    printed T2 and told a human to delete the entry.
    """
    _, _, unmodelled = cov.parse_pytest_args([opt, "tests"])
    assert unmodelled, f"{opt} silently modelled"


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


@pytest.mark.parametrize("depth", [1, 5, 50, None])
def test_a_history_gated_test_is_excluded_by_any_shallow_checkout(depth):
    """Any depth but 0 is shallow.

    Testing only depth 1 let `!= 0` be rewritten as `== 1` with every test
    still green -- and a `fetch-depth: 50` checkout would then have read as
    full history, which is the under-report direction.
    """
    t = _tests(("pipeline/tests/test_x.py", "test_a", (), True))
    assert list(cov.excluded_tests(t, [_step(depth=depth)])) == ["shallow-checkout"]


def test_ignore_in_its_space_separated_form_does_not_leave_a_fake_target():
    """`--ignore tests` must not turn `tests` into a covered target path.

    Reported-as-unmodelled is only half the job: the option also has to eat its
    argument. If it does not, `pytest pipeline/tests --ignore tests` reads as
    covering BOTH roots -- the exclusion becomes coverage.
    """
    targets, _, unmodelled = cov.parse_pytest_args(
        ["pipeline/tests", "--ignore", "tests"])
    assert unmodelled and targets == ["pipeline/tests"]


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
    """The finding this tool was written for, pinned so it cannot quietly go away.

    The first version wrapped the real assertion in an `if`, so a change that
    made the condition false left the test asserting nothing and still green.
    Now the two outcomes are both spelled out and neither is silence.
    """
    steps = cov.pytest_steps(cov.ROOT / ".github" / "workflows")
    assert steps, "no automatic trigger runs pytest at all"
    assert (cov.ROOT / "tests").is_dir()
    targets = {t for s in steps for t in s["targets"]}
    covered = "tests" in targets or any(not s["targets"] for s in steps)
    buckets = cov.excluded_tests(cov.suite_tests(cov.ROOT), steps)
    if covered:
        # The day this becomes true, the finding is fixed -- and DECLARED must
        # lose its entry, which is T2's job. Say so instead of going quiet.
        assert not buckets.get("tests"), \
            "tests/ is a CI target but still reported as excluded"
        assert "tests" not in cov.DECLARED, \
            "tests/ now runs in CI -- delete the DECLARED entry (T2)"
    else:
        assert len(buckets.get("tests", [])) > 100, \
            "tests/ is not a CI target, so it must show up as excluded"


ONLY_DISPATCH = """\
name: t
on:
  workflow_dispatch:
jobs:
  pytest:
    steps:
      - uses: actions/checkout@v4
      - run: python -m pytest pipeline/tests tests -q
"""


def test_a_workflow_only_a_human_can_press_is_not_an_automatic_trigger(tmp_path):
    """T6's foundation had no coverage: deleting the trigger filter kept 41 green."""
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "t.yml").write_text(ONLY_DISPATCH)
    assert cov.pytest_steps(wf) == []
    res = cov.check([], cov.pytest_steps(wf), declared={})
    assert any(c == "T6" for c, _ in res["violations"])


# ---------- the four shapes that moved an exclusion off the command line ----

def _wf_file(tmp_path, text):
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True, exist_ok=True)
    (wf / "tests.yml").write_text(text)
    return wf


_ON = "name: t\non:\n  push:\n  pull_request:\n"
_CHECKOUT = "jobs:\n  pytest:\n    steps:\n      - uses: actions/checkout@v4\n"


def test_an_if_on_the_pytest_step_is_not_certifiable(tmp_path):
    """`if: false` ran zero tests and the first version reported no violations."""
    wf = _wf_file(tmp_path, _ON + _CHECKOUT +
                  "      - name: pytest\n        if: false\n"
                  '        run: |\n          python -m pytest pipeline/tests -q\n')
    res = cov.check(cov.suite_tests(cov.ROOT), cov.pytest_steps(wf))
    assert not res["certified"] and any(c == "T5" for c, _ in res["violations"])


def test_an_if_on_the_job_taints_every_step_under_it(tmp_path):
    wf = _wf_file(tmp_path, _ON +
                  "jobs:\n  pytest:\n    if: github.event_name == 'schedule'\n"
                  "    steps:\n      - uses: actions/checkout@v4\n"
                  "      - name: pytest\n"
                  '        run: |\n          python -m pytest pipeline/tests -q\n')
    res = cov.check(cov.suite_tests(cov.ROOT), cov.pytest_steps(wf))
    assert not res["certified"]


def test_an_if_on_an_unrelated_step_does_not_cry_wolf(tmp_path):
    """This repository's real tests.yml has `if: always()` on its audit step.

    An audit that went red on that would be ignored inside a week, and being
    ignored is the disease this whole file is about.
    """
    wf = _wf_file(tmp_path, _ON + _CHECKOUT +
                  "      - name: pytest\n"
                  '        run: |\n          python -m pytest pipeline/tests tests -q\n'
                  "      - name: audit\n        if: always()\n"
                  "        continue-on-error: true\n"
                  "        run: |\n          python -m pipeline.tools.audit_wiring\n")
    res = cov.check(cov.suite_tests(cov.ROOT), cov.pytest_steps(wf))
    assert res["certified"], cov.render(res)


def test_an_argument_built_at_runtime_is_not_certifiable(tmp_path):
    """`$PYTEST_ARGS` was read as a target PATH; an --ignore inside it vanished."""
    wf = _wf_file(tmp_path, _ON + _CHECKOUT +
                  "      - name: pytest\n        run: |\n"
                  "          PYTEST_ARGS='--ignore=pipeline/tests'\n"
                  "          python -m pytest pipeline/tests $PYTEST_ARGS -q\n")
    res = cov.check(cov.suite_tests(cov.ROOT), cov.pytest_steps(wf))
    assert not res["certified"]


def test_a_paths_filtered_trigger_is_not_certifiable(tmp_path):
    """`_triggers` reads key names, never the filters under them."""
    wf = _wf_file(tmp_path,
                  "name: t\non:\n  push:\n    paths: ['frontend/**']\n" + _CHECKOUT +
                  "      - name: pytest\n"
                  '        run: |\n          python -m pytest pipeline/tests tests -q\n')
    res = cov.check(cov.suite_tests(cov.ROOT), cov.pytest_steps(wf))
    assert not res["certified"]


def test_collect_only_does_not_get_to_empty_a_bucket(tmp_path):
    """The worst one: the tool used to instruct a human into a false green.

    A `pytest tests --collect-only` step emptied the `tests` bucket, and the
    audit then printed T2 -- "declared exclusion 'tests' excludes nothing now,
    delete the entry". Following its own advice produced 0 violations with 607
    tests never run.
    """
    wf = _wf_file(tmp_path, _ON + _CHECKOUT +
                  "      - name: pytest\n"
                  '        run: |\n          python -m pytest pipeline/tests -q\n'
                  "      - name: collect\n"
                  '        run: |\n          python -m pytest tests --collect-only -q\n')
    res = cov.check(cov.suite_tests(cov.ROOT), cov.pytest_steps(wf))
    assert not res["certified"]
    assert any(c == "T5" and "--collect-only" in m for c, m in res["violations"])


def test_render_shouts_when_it_could_not_read_the_run(tmp_path):
    wf = _wf_file(tmp_path, _ON + _CHECKOUT +
                  "      - name: pytest\n        if: false\n"
                  '        run: |\n          python -m pytest pipeline/tests -q\n')
    text = cov.render(cov.check(cov.suite_tests(cov.ROOT), cov.pytest_steps(wf)))
    assert "NOT CERTIFIED" in text and "LOWER BOUND" in text


# ---------- markers the ast pass used to miss ----------

def test_a_bare_mark_import_is_still_a_marker(tmp_path):
    _write_suite(tmp_path, "pipeline/tests", """\
        from pytest import mark
        @mark.slow
        def test_a(): pass
        """)
    assert cov.suite_tests(tmp_path)[0]["markers"] == {"slow"}


def test_a_marker_on_the_class_reaches_its_methods(tmp_path):
    _write_suite(tmp_path, "pipeline/tests", """\
        import pytest
        @pytest.mark.slow
        class TestThing:
            def test_a(self): pass
        """)
    assert cov.suite_tests(tmp_path)[0]["markers"] == {"slow"}


def test_an_annotated_pytestmark_still_reaches_every_test(tmp_path):
    _write_suite(tmp_path, "tests", """\
        import pytest
        pytestmark: list = [pytest.mark.slow]
        def test_a(): pass
        """)
    assert cov.suite_tests(tmp_path)[0]["markers"] == {"slow"}


def test_a_skipif_that_asks_the_machine_counts_even_without_the_keywords(tmp_path):
    """`shutil.which("git") is None` reached for the environment and read as free."""
    _write_suite(tmp_path, "pipeline/tests", """\
        import pytest, shutil
        @pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
        def test_a(): pass
        """)
    assert cov.suite_tests(tmp_path)[0]["history_gated"] is True


def test_t3_uses_the_repo_it_was_given_not_the_module_constant(tmp_path):
    """`--repo` was half-honoured: T3 went and asked the real repository."""
    res = cov.check([], [], declared={"tests": ("o", "r", "d")}, repo=tmp_path)
    assert any(c == "T3" and "tests" in m for c, m in res["violations"])


def test_render_names_the_owner_of_every_bucket_it_prints():
    """It must print the OWNER, not the string "owner:".

    The first version counted occurrences of the literal `owner:`, which a
    render that printed `owner: ?` for every bucket passed just as happily --
    the shape of pitfall_a_test_that_reads_its_own_constant.
    """
    tests = cov.suite_tests(cov.ROOT)
    steps = cov.pytest_steps(cov.ROOT / ".github" / "workflows")
    res = cov.check(tests, steps)
    text = cov.render(res)
    assert text.count("owner:") == len(res["buckets"])
    assert "?" not in [cov.DECLARED[k][0] for k in res["buckets"]]
    for key in res["buckets"]:
        assert cov.DECLARED[key][0] in text
        assert cov.DECLARED[key][2] in text        # the date it was found


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
