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


# ----------------------------------------------------------- 2026-09-02
# Four lines the suite believed it pinned and did not. They were reported as
# killed by the mutation sweep for four nights, while the sweep was executing
# some mutants with the previous mutant's bytecode (fixed in deb7a0f5). With
# the instrument corrected they came back as survivors:
#   L56  WINDOW = 20 -> 21        the trailing window this guard averages over
#   L117 `or` -> `and`            date extraction in load()
#   L117 [:10] -> [:11]           the date/timestamp truncation
#   L96  *100 -> *101             the pp figure in the U1 message
# Each test below is written so the named mutant fails it, not merely so it
# passes today.

def test_the_trailing_window_is_twenty_sessions_not_twenty_one():
    """WINDOW is how far back the baseline looks. Off by one and it keeps a
    session it was meant to have forgotten.

    Making 20 and 21 disagree takes care: the baseline is a MEDIAN, so one
    ancient outlier cannot move it -- the first draft of this test asserted a
    difference that was not there, and its own precondition said so. What does
    move a median is which side of the split gets the extra vote. The 20 recent
    sessions are 10 low and 10 high, so a 20-session memory sits at the midpoint
    between them; adding one more high session tips the count to 11 high and the
    median lands ON the high value.
    """
    from pipeline.tools.audit_universe_shape import check

    LOW = AL + MZ[:10]        # share 10/60  = 0.1667
    HIGH = AL[:5] + MZ        # share 50/55  = 0.9091

    by = {"2026-06-01": HIGH}                       # the 21st session back
    for i in range(10):
        by[f"2026-06-{2 + i:02d}"] = LOW            # 06-02 .. 06-11
    for i in range(10):
        by[f"2026-06-{12 + i:02d}"] = HIGH          # 06-12 .. 06-21
    judged = "2026-06-22"
    by[judged] = AL + MZ                            # share 0.50

    twenty = check(by, window=20)
    twenty_one = check(by, window=21)
    row20 = next(r for r in twenty["rows"] if r["session"] == judged)
    row21 = next(r for r in twenty_one["rows"] if r["session"] == judged)

    assert row20["baseline"] != row21["baseline"], \
        "precondition: 20 and 21 must actually disagree, or this test is blind"
    assert row20["baseline"] == pytest.approx(0.5379, abs=1e-3)
    assert row21["baseline"] == pytest.approx(0.9091, abs=1e-3)

    # 0.50 is inside tolerance of the 20-session baseline and far outside the
    # 21-session one, so the two windows disagree about whether to fire.
    assert not any(v.startswith(f"U1 {judged}") for v in twenty["violations"])
    assert any(v.startswith(f"U1 {judged}") for v in twenty_one["violations"])

    # and the shipped default must behave like 20
    default = check(by)
    assert not any(v.startswith(f"U1 {judged}") for v in default["violations"])


def test_the_pp_figure_in_the_message_is_percentage_points():
    """The U1 line quotes how far the share moved. That number is what a human
    acts on, and nothing was reading it.

    ⚠️ The input is chosen, not arbitrary. The first draft used a drift of
    0.2692, where *100 prints 26.92 -> "27" and *101 prints 27.19 -> "27" as
    well: the test was green against both the real line and the mutant. Most
    drifts do that, because `:.0f` throws away exactly the 1% the mutant adds.
    0.4804 is one of the few that survives the rounding: 48.04 -> "48",
    48.52 -> "49"."""
    from pipeline.tools.audit_universe_shape import check

    by = healthy(8)
    by["2026-06-09"] = AL + MZ[:1]             # 1/51 = 0.0196 vs 0.50
    out = check(by, tolerance=0.15)
    msg = next(v for v in out["violations"] if v.startswith("U1 2026-06-09"))
    # |0.0196 - 0.50| = 0.4804 -> *100 = 48.04 -> "48pp"; *101 = 48.52 -> "49pp"
    assert "moved 48pp" in msg, msg
    assert "tolerance 15pp" in msg, msg


def test_load_reads_the_date_column_it_found(tmp_path):
    """`d = (r.get(dc) or "")[:10]`. Swap that `or` for `and` and every date
    becomes the empty string, so load() returns {} and this guard passes every
    archive in the repo by seeing none of it."""
    from pipeline.tools.audit_universe_shape import load

    p = tmp_path / "arch.csv"
    p.write_text("date,ticker\n2026-06-01,AAPL\n2026-06-01,WMT\n2026-06-02,MSFT\n")
    by = load(p)
    assert by == {"2026-06-01": ["AAPL", "WMT"], "2026-06-02": ["MSFT"]}


def test_load_truncates_a_timestamp_to_its_date(tmp_path):
    """`[:10]` turns 2026-06-01T09:30 into 2026-06-01. One char more and each
    timestamp becomes its own session, so a day splits into many one-row
    sessions -- every one of them below MIN_ROWS, and therefore never judged."""
    from pipeline.tools.audit_universe_shape import load

    p = tmp_path / "stamped.csv"
    p.write_text("date,ticker\n"
                 "2026-06-01T09:30:00,AAPL\n"
                 "2026-06-01T15:59:00,WMT\n")
    by = load(p)
    assert list(by) == ["2026-06-01"], by
    assert by["2026-06-01"] == ["AAPL", "WMT"]
