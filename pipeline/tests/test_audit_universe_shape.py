"""Tests for audit_universe_shape.

The load-bearing property of this guard is stated as a test, not as a comment:
`test_it_fires_when_the_row_count_does_not_move_at_all` builds two sessions with
IDENTICAL row counts where one is truncated, because that is the exact case
every count-based check in this repo misses (2026-06-26 had MORE rows than the
day before it).
"""
from __future__ import annotations

import pytest

from pipeline.tools.audit_universe_shape import check, share_after

AL = [f"A{i:03d}" for i in range(50)]      # all sort before 'L'
MZ = [f"W{i:03d}" for i in range(50)]      # all sort after 'L'


def healthy(n_days: int, start_day: int = 1) -> dict[str, list[str]]:
    """Sessions that are ~50/50 either side of 'L'."""
    return {f"2026-06-{start_day + i:02d}": AL + MZ for i in range(n_days)}


def test_share_after_is_what_it_says():
    assert share_after(AL + MZ) == pytest.approx(0.5)
    assert share_after(AL) == 0.0
    assert share_after(MZ) == 1.0
    assert share_after([]) is None
    assert share_after(["  ", ""]) is None


def test_lowercase_symbols_are_not_a_different_alphabet():
    assert share_after(["aapl", "wmt"]) == pytest.approx(0.5)


# ------------------------------------------------------------------- green

def test_a_stable_archive_is_silent():
    out = check(healthy(10))
    assert out["ok"], out["violations"]


def test_ordinary_mix_drift_inside_tolerance_is_silent():
    by = healthy(8)
    by["2026-06-09"] = AL + MZ[:40]        # 44% vs 50% baseline
    out = check(by)
    assert out["ok"], out["violations"]


# --------------------------------------------------------------------- U2

def test_u2_a_hard_zero_is_a_truncation():
    by = healthy(8)
    by["2026-06-09"] = AL * 2              # 100 rows, none after 'L'
    out = check(by)
    assert not out["ok"]
    assert any(v.startswith("U2 2026-06-09") and "truncation" in v
               for v in out["violations"])


def test_u2_fires_on_the_other_end_too():
    by = healthy(8)
    by["2026-06-09"] = MZ * 2
    assert any(v.startswith("U2 2026-06-09") for v in check(by)["violations"])


def test_u2_ignores_a_zero_that_is_just_a_small_sample():
    # Three names on a quiet day, all before 'L', is not evidence of anything.
    by = healthy(8)
    by["2026-06-09"] = AL[:3]
    out = check(by)
    assert not any(v.startswith("U2") for v in out["violations"])


# --------------------------------------------------------------- the point

def test_it_fires_when_the_row_count_does_not_move_at_all():
    """The whole reason this file exists.

    2026-06-26 lost half the universe and gained rows (1,613 vs 965), so every
    count-based guard stayed green. Here both sessions have exactly 100 rows
    and only the coverage changes."""
    by = healthy(8)
    normal_n = len(by["2026-06-01"])
    by["2026-06-09"] = AL * 2
    assert len(by["2026-06-09"]) == normal_n     # identical row count
    out = check(by)
    assert not out["ok"]
    assert out["rows"][-1]["rows"] == normal_n


# --------------------------------------------------------------------- U1

def test_u1_catches_a_drift_that_is_not_a_hard_zero():
    by = healthy(8)
    by["2026-06-09"] = AL + MZ[:5]        # 9% vs 50%
    out = check(by)
    assert any(v.startswith("U1 2026-06-09") for v in out["violations"])


def test_tolerance_is_where_it_says_it_is():
    by = healthy(8)
    by["2026-06-09"] = AL * 2 + MZ * 2    # exactly 0.50 -> no move
    assert check(by)["ok"]
    by["2026-06-09"] = AL * 10 + MZ * 3   # 3/13 = 0.231, moved 27pp
    assert not check(by, tolerance=0.15)["ok"]
    assert check(by, tolerance=0.30)["ok"]


# --------------------------------------------------------------------- U3

def test_the_first_sessions_are_not_judged_they_are_flagged():
    out = check(healthy(3))
    assert out["ok"]
    assert len(out["warnings"]) == 3
    assert all(w.startswith("U3") for w in out["warnings"])


def test_a_truncation_in_the_first_sessions_still_fires():
    # U3 means "no baseline to compare against", which must not become a free
    # pass for a hard zero -- an archive that starts truncated is the worst
    # case, because the baseline it poisons is every later session's.
    by = {"2026-06-01": AL * 2, "2026-06-02": AL * 2}
    out = check(by)
    assert not out["ok"]
    assert all(v.startswith("U2") for v in out["violations"])


# ------------------------------------------------------------ configurable

def test_the_split_letter_is_not_baked_in():
    by = {f"2026-06-{d:02d}": [f"A{i}" for i in range(50)] + [f"C{i}" for i in range(50)]
          for d in range(1, 9)}
    assert check(by, split="B")["ok"]         # 50% after 'B', stable
    out = check(by, split="L")                # 0% after 'L' on every session
    assert not out["ok"]
    assert all(v.startswith("U2") for v in out["violations"])


def test_empty_archive_is_not_a_pass():
    out = check({})
    assert out["sessions"] == 0
    assert out["rows"] == [] and out["warnings"] == []
    # ok is vacuously true here; main() is what refuses an empty file, and the
    # next test pins that contract so it cannot quietly change.
    assert out["ok"]


def test_main_refuses_an_empty_archive(tmp_path):
    from pipeline.tools.audit_universe_shape import main
    p = tmp_path / "empty.csv"
    p.write_text("date,ticker\n")
    assert main([str(p)]) == 1
