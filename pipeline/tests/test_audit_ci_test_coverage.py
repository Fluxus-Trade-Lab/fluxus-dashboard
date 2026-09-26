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
    res = cov.check(t, [_step()], declared={}, declared_triggers={})
    assert [c for c, _ in res["violations"]] == ["T1"]


def test_t1_is_silent_once_that_exclusion_is_declared():
    t = _tests(("tests/test_x.py", "test_a", (), False))
    t[0]["root"] = "tests"
    res = cov.check(t, [_step()], declared=DECL, declared_triggers={})
    assert res["violations"] == []


def test_t2_fires_when_a_declared_exclusion_no_longer_excludes_anything():
    """The anti-rot half: fixing it forces you to delete the excuse."""
    t = _tests(("pipeline/tests/test_x.py", "test_a", (), False))
    res = cov.check(t, [_step()], declared=DECL, declared_triggers={})
    assert ("T2", "declared exclusion 'tests' excludes nothing now "
                  "-- delete the entry") in res["violations"]


def test_t3_fires_when_a_declared_marker_is_on_no_test():
    t = _tests(("pipeline/tests/test_x.py", "test_a", ("slow",), False))
    decl = {"marker:slow": ("o", "r", "d"), "marker:ghost": ("o", "r", "d")}
    res = cov.check(t, [_step(markers=("slow",))], declared=decl,
                     declared_triggers={})
    assert any(c == "T3" and "ghost" in m for c, m in res["violations"])


def test_t4_fires_when_a_declared_entry_has_no_owner():
    t = _tests(("tests/test_x.py", "test_a", (), False))
    t[0]["root"] = "tests"
    res = cov.check(t, [_step()], declared={"tests": ("", "reason", "d")},
                     declared_triggers={})
    assert any(c == "T4" for c, _ in res["violations"])


def test_t7_fires_when_a_declared_trigger_filter_no_longer_narrows_anything():
    """T2's anti-rot half, for trigger filters."""
    decl_t = {"branches: [main]": ("o", "r", "d")}
    res = cov.check([], [_step()], declared={}, declared_triggers=decl_t)
    assert ("T7", "declared trigger filter 'branches: [main]' is not on any "
                  "workflow's trigger now -- delete the entry") in res["violations"]


def test_t7_is_silent_once_the_filter_is_still_on_the_trigger():
    step = _step()
    step["trigger_filters"] = ["branches: [main]"]
    decl_t = {"branches: [main]": ("o", "r", "d")}
    res = cov.check([], [step], declared={}, declared_triggers=decl_t)
    assert res["violations"] == []
    assert res["certified"]


def test_t8_fires_when_a_declared_trigger_filter_has_no_owner():
    step = _step()
    step["trigger_filters"] = ["branches: [main]"]
    decl_t = {"branches: [main]": ("", "r", "d")}
    res = cov.check([], [step], declared={}, declared_triggers=decl_t)
    assert any(c == "T8" for c, _ in res["violations"])


def test_an_undeclared_trigger_filter_still_trips_t5():
    """The escape hatch is per-line, not a blanket amnesty for narrowing."""
    step = _step()
    step["trigger_filters"] = ["paths: ['frontend/**']"]
    res = cov.check([], [step], declared={}, declared_triggers={})
    assert any(c == "T5" for c, _ in res["violations"])
    assert not res["certified"]


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


def test_a_skipif_that_asks_the_machine_nothing_is_not_history_gated(tmp_path):
    """The other half of the line above, and the half nothing was watching.

    `history_gated` decides whether a shallow checkout is allowed to excuse a
    test. Over-flagging is the expensive direction: a `skipif(False)` marked
    as history-gated gets written off as "shallow checkout skipped it", and
    the test stops being anybody's problem.

    Two survivors sat on this one expression (`and` -> `or`, `h in seg` ->
    `h not in seg`) and both of them turn this False into True. Neither was
    visible from the flagged side: `_has("abc")` keeps reading True under
    `not in` too, because a real condition never contains *every* hint.
    """
    _write_suite(tmp_path, "pipeline/tests", """\
        import pytest
        @pytest.mark.skipif(False, reason="x")
        def test_a(): pass
        """)
    assert cov.suite_tests(tmp_path)[0]["history_gated"] is False


def test_a_decorator_chain_that_ends_at_mark_is_read_without_crashing(tmp_path):
    """`@pytest.mark` with nothing after it: no marker, and no traceback.

    `i + 1 >= len(attr)` is the only thing standing between this decorator and
    an IndexError one line later. An auditor that raises on one malformed
    decorator reports nothing about the other 3,600 tests -- so the failure
    mode here is not a wrong number, it is no number at all.
    """
    _write_suite(tmp_path, "pipeline/tests", """\
        import pytest
        @pytest.mark
        def test_a(): pass
        @pytest.mark.slow
        def test_b(): pass
        """)
    got = {t["name"]: t["markers"] for t in cov.suite_tests(tmp_path)}
    assert got == {"test_a": set(), "test_b": {"slow"}}


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

    res = cov.check(tests, steps, declared_triggers={})
    codes = sorted({c for c, _ in res["violations"]})
    assert codes == ["T2"], cov.render(res)
    assert len(res["violations"]) == len(cov.DECLARED)


# ==========================================================================
# 2026-09-26 (T-0926-21) -- the holes the first mutation sweep of this file
# found. It is the largest guard in the repo (174 mutation sites) and had
# never been swept: `audit_mutation_sweep`'s workspace did not copy `tests/`,
# so the sweep's own baseline went red on this file's T3 ("declared path
# 'tests' does not exist") and it refused to run. Fixed in the same task.
#
# First reading: 126/174 killed (72%). 48 survivors, and they clustered in
# three places -- the `-m` parser (the guard's central input), `render()`
# (13 survivors, two tests), and `main()`'s exit code.
# ==========================================================================

# ---------- the exit code (third repository-wide instance) ----------

def _mini_repo(tmp_path, workflow, marked=False):
    """A whole repo the tool can be pointed at: two test roots, one workflow."""
    for rel in ("pipeline/tests", "tests"):
        d = tmp_path / rel
        d.mkdir(parents=True)
        body = ("import pytest\n\n@pytest.mark.slow\ndef test_a():\n    pass\n"
                if marked else "def test_a():\n    pass\n")
        (d / "test_x.py").write_text(body)
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "tests.yml").write_text(textwrap.dedent(workflow))
    return tmp_path


_CLEAN_WF = """\
    name: tests
    on:
      push:
    jobs:
      t:
        steps:
          - uses: actions/checkout@v4
            with:
              fetch-depth: 0
          - run: python -m pytest pipeline/tests tests -q
"""

_HOLED_WF = _CLEAN_WF.replace('pipeline/tests tests -q',
                              'pipeline/tests tests -q -m "not slow"')


def test_main_exits_zero_on_a_clean_repo_and_one_when_it_finds_a_hole(
        tmp_path, monkeypatch, capsys):
    """`return 1 if violations else 0` -- both branches, not just the loud one.

    The `0 -> 1` mutant on that line is the THIRD instance of one shape in
    this repository: it lived three weeks in `audit_archives` and in
    `audit_ledger` (both closed 2026-09-25, T-0925-11) and it was still open
    here. It is the worst-behaved mutant we know of, because what it breaks
    is the QUIET path: every clean night exits 1, CI goes red on a repo with
    nothing wrong with it, and the fix people reach for is to stop reading
    the check. "We tested main()" and "we tested both of main()'s exits" are
    not the same sentence -- three guards in a row proved it.
    """
    monkeypatch.setattr(cov, "DECLARED", {})
    monkeypatch.setattr(cov, "DECLARED_TRIGGERS", {})

    clean = _mini_repo(tmp_path / "clean", _CLEAN_WF)
    assert cov.main(["--repo", str(clean)]) == 0, capsys.readouterr().out

    holed = _mini_repo(tmp_path / "holed", _HOLED_WF, marked=True)
    assert cov.main(["--repo", str(holed)]) == 1, capsys.readouterr().out


# ---------- the `-m` parser: the guard's central input ----------

def test_the_marker_value_is_found_when_dash_m_is_the_last_flag():
    """`["-m", "not slow"]` with nothing after it.

    The one existing test of the real command puts `--tb=short` after the
    marker, which leaves `i + 1 < len(rest)` true under BOTH the real bound
    and the off-by-one. With `-m` second-to-last they disagree: the mutant
    reads no value at all and the excluded marker silently becomes the empty
    set -- a guard that reports "this run excludes nothing".
    """
    targets, markers, unmodelled = cov.parse_pytest_args(["-m", "not slow"])
    assert targets == [] and markers == {"slow"} and unmodelled == []


def test_the_marker_value_is_found_in_the_attached_spelling():
    """`-mnot slow`, which is what `-m"not slow"` becomes after shlex."""
    targets, markers, unmodelled = cov.parse_pytest_args(["-mnot slow", "tests"])
    assert targets == ["tests"] and markers == {"slow"} and unmodelled == []


def test_a_trailing_dash_m_with_no_value_is_reported_not_crashed_on():
    """A malformed command must go to T5, not to IndexError.

    An auditor that raises is an auditor that reports nothing, and this one
    runs inside the nightly gate.
    """
    targets, markers, unmodelled = cov.parse_pytest_args(["tests", "-m"])
    assert targets == ["tests"] and markers == set()
    assert unmodelled == ["-m ''"]


def test_a_token_that_only_starts_with_dash_m_is_not_read_as_a_marker():
    """`-mfoo=bar` is not `-m foo=bar`; the `=` is what tells them apart."""
    _, markers, unmodelled = cov.parse_pytest_args(["-mnot slow=1"])
    assert markers == set() and unmodelled == ["-mnot slow=1"]


def test_an_option_we_model_only_by_its_head_does_not_become_unmodelled():
    """`--maxfail=2`: the head is modelled, the whole token is not.

    Reading only the whole token makes every `=`-form option an unmodelled
    option, which trips T5 and makes the tool refuse to certify a run it
    understands perfectly well.
    """
    targets, _, unmodelled = cov.parse_pytest_args(["--maxfail=2", "tests"])
    assert targets == ["tests"] and unmodelled == []


def test_an_option_in_neither_table_is_still_reported():
    """The other direction of the same line: unknown means unknown."""
    targets, _, unmodelled = cov.parse_pytest_args(["--boom", "tests"])
    assert targets == ["tests"] and unmodelled == ["--boom"]


def test_an_inline_ignore_does_not_also_eat_the_next_token():
    """`--ignore=tests pipeline/tests` runs pipeline/tests -- it is a target.

    The separated spelling (`--ignore tests`) consumes its argument; the
    inline one already carries it. Swallowing one more token drops a whole
    test root out of the audit's view of the run.
    """
    targets, _, unmodelled = cov.parse_pytest_args(
        ["--ignore=tests", "pipeline/tests"])
    assert targets == ["pipeline/tests"] and unmodelled == ["--ignore=tests"]


def test_a_separated_modelled_option_does_eat_its_argument():
    """`-p no:cacheprovider tests` has exactly one target."""
    targets, _, unmodelled = cov.parse_pytest_args(
        ["-p", "no:cacheprovider", "tests"])
    assert targets == ["tests"] and unmodelled == []


def test_python_dash_m_something_else_is_not_a_pytest_run():
    """`python -X dev -m pytest` is a run; `python -m mypy` is not.

    The line names pytest either way, so `\\bpytest\\b` cannot tell them
    apart -- only the position of `-m pytest` can.
    """
    assert cov._invocation("python -X dev -m pytest tests") is None
    assert cov._invocation("python -m pytest tests") == ["tests"]


# ---------- the trigger block boundary ----------

def test_a_filter_outside_the_on_block_is_not_a_trigger_filter():
    """`branches:` under `jobs:` is a job's business, not the trigger's.

    Reporting it is a T5 on a workflow that has no trigger narrowing at all,
    and T5 blocks certification -- the audit would refuse to certify a run
    it had no complaint about.
    """
    text = ("  branches: [before]\n"
            "on:\n"
            "  push:\n"
            "    paths: ['pipeline/**']\n"
            "jobs:\n"
            "  t:\n"
            "    branches: [after]\n")
    assert cov.trigger_filters(text) == ["paths: ['pipeline/**']"]


def test_the_yaml_true_spelling_of_on_is_still_the_trigger_block():
    """YAML 1.1 reads a bare `on` key as the boolean true.

    A workflow round-tripped through a YAML writer comes back with `True:`
    where `on:` was, and a reader that only knows `on:` sees no trigger
    block at all -- and therefore no filters, which reads as full coverage.
    """
    text = "True:\n  push:\n    branches: [main]\njobs:\n  t:\n"
    assert cov.trigger_filters(text) == ["branches: [main]"]


# ---------- the checkout depth default ----------

def test_a_runtime_fetch_depth_expression_is_read_as_the_shallow_default():
    """`fetch-depth: ${{ inputs.depth }}` is unknowable statically.

    It is assumed to be 1 -- the checkout action's own default, and the
    direction that over-reports. Assuming anything deeper certifies history
    the job may not have.
    """
    text = ("jobs:\n  t:\n    steps:\n      - uses: actions/checkout@v4\n"
            "        with:\n          fetch-depth: ${{ inputs.depth }}\n")
    assert cov.checkout_depth(text) == 1


# ---------- the declared tables: T4 and T8 ----------

def test_t4_fires_on_a_missing_reason_and_not_on_a_missing_date():
    """The IOU must name an owner and a reason. The date it may forget.

    `not entry[1]` and `not entry[2]` are one character apart and the tests
    pinned neither: a table full of `("DATA ALEX", "", "2026-09-05")` -- an
    owner and no reason, which is the exact shape of an excuse nobody has to
    justify -- passed T4 unremarked.
    """
    t = _tests(("tests/test_x.py", "test_a", ("slow",), False))
    step = [_step(markers=("slow",))]
    no_reason = {"marker:slow": ("DATA ALEX", "", "2026-09-05")}
    codes = [c for c, _ in cov.check(t, step, declared=no_reason,
                                     declared_triggers={})["violations"]]
    assert "T4" in codes

    no_date = {"marker:slow": ("DATA ALEX", "because", "")}
    codes = [c for c, _ in cov.check(t, step, declared=no_date,
                                     declared_triggers={})["violations"]]
    assert "T4" not in codes


def test_t8_fires_on_a_missing_reason_and_not_on_a_missing_date():
    """T4's half for the trigger table, pinned the same way."""
    t = _tests(("tests/test_x.py", "test_a", (), False))
    step = [_step()]
    step[0]["trigger_filters"] = ["branches: [main]"]
    no_reason = {"branches: [main]": ("DATA ALEX", "", "2026-09-23")}
    codes = [c for c, _ in cov.check(t, step, declared={},
                                     declared_triggers=no_reason)["violations"]]
    assert "T8" in codes

    no_date = {"branches: [main]": ("DATA ALEX", "because", "")}
    codes = [c for c, _ in cov.check(t, step, declared={},
                                     declared_triggers=no_date)["violations"]]
    assert "T8" not in codes


# ---------- render(): 13 of the 48 survivors lived here ----------
#
# Two tests covered this function, and they asserted on one line each. The
# report is the entire product -- nothing else leaves this tool -- and its
# truncation arithmetic, its depth wording and its declared/UNDECLARED label
# were all free to be wrong.

def _res(**over):
    base = {"steps": [], "buckets": {}, "declared": {}, "declared_triggers": {},
            "violations": [], "total": 0, "certified": True}
    base.update(over)
    return base


def _bucket_items(n):
    return [{"file": f"tests/test_{i}.py", "name": f"test_{i}"} for i in range(n)]


def test_render_prints_three_examples_and_counts_the_rest():
    """`items[:3]` and `len(items) - 3` are the same 3 and must stay the same 3.

    The failure this pins is a report that says "... and 3 more" under four
    printed examples: the reader adds them up, gets a number that is not the
    bucket size, and stops trusting the page. Seven tests excluded, three
    shown, four more.
    """
    text = cov.render(_res(buckets={"marker:slow": _bucket_items(7)}, total=7))
    assert text.count("      e.g.   ") == 3
    assert "... and 4 more" in text


def test_render_does_not_say_and_zero_more_when_the_bucket_is_exactly_three():
    """The boundary of the same line: 3 printed, nothing left over."""
    text = cov.render(_res(buckets={"marker:slow": _bucket_items(3)}, total=3))
    assert text.count("      e.g.   ") == 3
    assert "more" not in text


def test_render_accounts_for_the_fourth_test_when_the_bucket_is_exactly_four():
    """One past the boundary -- the only width at which `> 3` and `> 4` differ.

    Seven and three were both measured; four was not, and `3 -> 4` on this
    comparison survived because of it. Under the mutant a four-test bucket
    prints three examples and stops: the header says 4, the body shows 3, and
    the missing one is silently the reader's problem.
    """
    text = cov.render(_res(buckets={"marker:slow": _bucket_items(4)}, total=4))
    assert text.count("      e.g.   ") == 3
    assert "... and 1 more" in text


@pytest.mark.parametrize("depth,expected", [
    (None, "no checkout"),
    (0, "full history"),
    (1, "depth 1 (shallow)"),
    (2, "depth 2 (shallow)"),
])
def test_render_words_the_checkout_depth_by_what_it_means(depth, expected):
    """0 is full history; None is no checkout at all; everything else is shallow.

    Three separate survivors sat on this one expression -- `is None` vs
    `is not None`, `== 0` vs `!= 0`, and the 0 itself. Getting it wrong
    prints "full history" over a depth-1 clone, which is the precise lie
    this whole guard was written to stop telling.
    """
    step = {"workflow": "tests.yml", "command": "pytest tests",
            "depth": depth, "markers": set(), "caveats": (),
            "trigger_filters": ()}
    assert f"checkout: {expected}" in cov.render(_res(steps=[step]))


def test_render_says_so_when_no_automatic_run_exists_at_all():
    """T6's shape, in the report. An empty step list is not an empty page."""
    assert "(no automatically triggered workflow runs pytest)" in \
        cov.render(_res())


def test_render_labels_declared_and_undeclared_buckets_differently():
    """The label is the whole point of the bucket list.

    Flipping it prints every open hole as `[declared]` -- a report in which
    an undeclared exclusion is indistinguishable from an owned one, which is
    the state this tool exists to end.
    """
    text = cov.render(_res(
        buckets={"marker:slow": _bucket_items(1), "tests": _bucket_items(1)},
        declared={"marker:slow": ("DATA ALEX", "because", "2026-09-05")},
        total=2))
    assert "[declared] marker:slow" in text
    assert "[UNDECLARED] tests" in text
    assert "owner: DATA ALEX" in text and "owner: ?" in text


def test_render_marks_a_declared_trigger_filter_as_claimed_not_as_a_warning():
    """And the undeclared one the other way round.

    Same line, both directions: a declared filter must stop shouting, and an
    undeclared one must not go quiet. Only the second half was tested.
    """
    step = {"workflow": "tests.yml", "command": "pytest tests", "depth": 0,
            "markers": set(), "caveats": (),
            "trigger_filters": ["branches: [main]", "paths:"]}
    text = cov.render(_res(steps=[step], declared_triggers={
        "branches: [main]": ("DATA ALEX", "email flood", "2026-09-23")}))
    assert "[declared trigger] branches: [main]: email flood" in text
    assert "trigger is narrowed by 'paths:'" in text
    assert "trigger is narrowed by 'branches: [main]'" not in text


def test_render_only_shouts_not_certified_when_it_was_told_it_was_not():
    """`res.get("certified", True)` -- the default is the load-bearing half.

    A res dict from an older caller has no `certified` key. Defaulting it to
    False stamps NOT CERTIFIED on every report, and a banner that is always
    on carries no information.
    """
    stale = _res()
    del stale["certified"]
    assert "NOT CERTIFIED" not in cov.render(stale)
    assert "NOT CERTIFIED" in cov.render(_res(certified=False))
