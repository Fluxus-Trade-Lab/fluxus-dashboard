"""The internal learning loop: falsifiable entries, and cohort comparison."""
import pytest

from pipeline.reference import learning_log as LG
from pipeline.reference.scorecard import compare_cohorts


def test_entry_requires_a_falsifier():
    # An entry with no way to be wrong is an opinion, and the log refuses it.
    with pytest.raises(ValueError, match="falsifier"):
        LG.entry("hypothesis", "confluence strikes are special", "   ")


def test_entry_rejects_unknown_kinds_and_classes():
    with pytest.raises(ValueError, match="kind"):
        LG.entry("vibe", "x", "y")
    with pytest.raises(ValueError, match="error class"):
        LG.entry("error", "x", "y", error_class="oopsie")


def test_roundtrip(tmp_path):
    p = tmp_path / "log.jsonl"
    LG.append(LG.entry("error", "vega off by 100x", "recompute vs a known case",
                       error_class="unit_convention", ref="commit abc"), p)
    rows = LG.read(p)
    assert rows[0]["class"] == "unit_convention" and rows[0]["ref"] == "commit abc"


def test_error_pattern_surfaces_the_recurring_failure_mode():
    rows = [LG.entry("error", "a", "f", error_class="wrong_reference"),
            LG.entry("error", "b", "f", error_class="wrong_reference"),
            LG.entry("error", "c", "f", error_class="arithmetic"),
            LG.entry("hypothesis", "d", "f")]          # not an error, excluded
    p = LG.error_pattern(rows)
    assert p["total"] == 3 and p["top"] == "wrong_reference"
    assert p["counts"]["wrong_reference"] == 2


def test_open_items_lists_only_unsettled_hypotheses():
    rows = [LG.entry("hypothesis", "a", "f"),
            LG.entry("hypothesis", "b", "f", status="settled", outcome="false"),
            LG.entry("error", "c", "f", error_class="plumbing")]
    assert [r["claim"] for r in LG.open_items(rows)] == ["a"]


# ------------------------------------------------------- cohort comparison

def _res(flag, verdict, n=1):
    return [{"level_name": "x", "verdict": verdict, "flagged": flag} for _ in range(n)]


def test_cohort_comparison_refuses_a_verdict_on_thin_samples():
    res = _res(True, "held", 5) + _res(False, "broke", 5)
    c = compare_cohorts(res, lambda r: r["flagged"])
    # The rates are 100 vs 0 — and it still declines to call it.
    assert c["edge_pct"] == 100.0
    assert "inconclusive" in c["verdict"]


def test_cohort_comparison_calls_a_winner_once_both_samples_are_deep():
    res = (_res(True, "held", 40) + _res(True, "broke", 10)
           + _res(False, "held", 20) + _res(False, "broke", 30))
    c = compare_cohorts(res, lambda r: r["flagged"])
    assert c["flagged"]["held_pct"] == pytest.approx(80.0)
    assert c["unflagged"]["held_pct"] == pytest.approx(40.0)
    assert c["verdict"] == "flagged held more often"


def test_cohort_comparison_reports_no_difference_when_rates_match():
    res = (_res(True, "held", 30) + _res(True, "broke", 30)
           + _res(False, "held", 31) + _res(False, "broke", 29))
    c = compare_cohorts(res, lambda r: r["flagged"])
    # A flag that does not separate the outcomes is decoration.
    assert c["verdict"] == "no measurable difference"


def test_untested_observations_do_not_count_toward_cohort_depth():
    res = _res(True, "untested", 100) + _res(False, "untested", 100)
    c = compare_cohorts(res, lambda r: r["flagged"])
    assert c["tested_total"] == 0 and "inconclusive" in c["verdict"]
