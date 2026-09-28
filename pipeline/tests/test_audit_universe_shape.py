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


# ----------------------------------------------------------- 2026-09-28
# The 18 survivors the sweep has been reporting since 2026-09-02, read one by
# one for the first time. 17 of them are real holes and are pinned below; the
# one left standing is `indent=1 -> 2` on the JSON the tool writes, which is
# whitespace -- a test for it would freeze a harmless formatting choice.
#
# Every test in this block was run against its own mutant and seen RED first;
# the index in the sweep's site list is named so the next reader can redo that.

def as_csv(tmp_path, by_session, name="arch.csv"):
    p = tmp_path / name
    lines = ["date,ticker"]
    for d in sorted(by_session):
        lines += [f"{d},{t}" for t in by_session[d]]
    p.write_text("\n".join(lines) + "\n")
    return p


def test_the_split_letter_itself_sorts_before_the_split_not_after():
    """Kills [32] L64 `Gt -> GtE` -- the comparison that DEFINES the statistic.

    Every existing test is blind to it: `AL` is all A-names and `MZ` all
    W-names, and neither "A" nor "W" changes side when `>` becomes `>=`. The
    split letter is the only input that does, and there was no L-name in the
    suite.

    Why it matters beyond pedantry: L is one of the busiest initials on the
    tape (LLY, LIN, LMT, LOW, LRCX...). Counting them as "after L" inflates
    every session's share AND the trailing median it is compared against, so
    the drift stays small -- an M-to-Z truncation would be partly absorbed by
    the L-names still being counted on the far side. This guard exists because
    a content-dimension cut hides from count-dimension checks; measuring the
    content dimension one letter off is the same failure one level in.
    """
    assert share_after(["LLY", "LIN", "LMT"]) == 0.0
    assert share_after(["LLY", "MMM"]) == 0.5
    assert share_after(["LLY", "MMM"], split="M") == 0.0


def test_u2_fires_at_exactly_min_rows():
    """Kills [2] L57 `MIN_ROWS = 50 -> 51` and [20] L83 `GtE -> Gt` together.

    Both mutants do the same thing: move the smallest sample on which a hard
    zero counts as evidence up by one row. 50 rows is the declared floor, so
    50 rows must fire. The number is written out here on purpose -- change
    MIN_ROWS and this test has to change with it, and that cost is the point.
    """
    by = healthy(8)
    by["2026-06-09"] = AL                  # exactly 50 rows, none after 'L'
    assert len(by["2026-06-09"]) == 50     # the fixture, not the guard
    out = check(by)
    assert any(v.startswith("U2 2026-06-09") for v in out["violations"]), out


def test_one_row_below_min_rows_is_still_small_sample_noise():
    """The other side of the same floor: 49 rows must stay quiet.

    `test_u2_ignores_a_zero_that_is_just_a_small_sample` uses 3 rows, which is
    nowhere near the boundary -- it would stay green if MIN_ROWS were lowered
    to 4. This one holds the floor from below.
    """
    by = healthy(8)
    by["2026-06-09"] = AL[:49]
    assert not any(v.startswith("U2") for v in check(by)["violations"])


def test_three_trailing_sessions_are_enough_to_judge():
    """Kills [29] L89 `Lt -> LtE` and [37] L89 `3 -> 4`.

    `len(prior) < 3` is where this guard stops saying "not judged" and starts
    accusing. The fourth session has exactly three priors, so it is the first
    one that must be judged. Both mutants push that to the fifth -- and U3 is
    a warning, never fatal, so the effect is that a truncation landing on the
    fourth session of any archive is reported as "not enough history" and
    passes. An archive that is truncated from early on is exactly the case the
    docstring calls the worst one, because it poisons every later baseline.
    """
    by = healthy(3)                                  # 0.50 on three sessions
    by["2026-06-04"] = AL + MZ[:1]                   # 1/51 = 0.0196, not a hard 0
    out = check(by)
    assert not out["ok"], out
    assert any(v.startswith("U1 2026-06-04") for v in out["violations"]), out
    assert not any("2026-06-04" in w for w in out["warnings"]), out["warnings"]


def test_a_drift_of_exactly_the_tolerance_is_inside_the_tolerance():
    """Kills [39] L92 `Gt -> GtE` -- is `--tolerance` allowed or forbidden?

    ⚠️ The numbers are chosen so the boundary is REACHABLE. `abs(sh - base)`
    has to equal `tolerance` to the bit, which rules out the default: 0.15 is
    not 0.15 in binary and no achievable share lands on it. 0.25 is exact, and
    a baseline of 0.50 against a share of 0.25 is exactly 0.25 away.

    (Same trap as audit_calendar_gaps L258, where the default threshold
    `1.0 - 0.8` == 0.19999999999999996 is unreachable and left `>=` vs `>`
    untestable for four sweeps.)
    """
    by = healthy(8)
    by["2026-06-09"] = AL * 3 + MZ                   # 50/200 = 0.25 exactly
    assert check(by, tolerance=0.25)["ok"], check(by, tolerance=0.25)["violations"]
    # one hair further out and it does fire, so the test above is not vacuous
    by["2026-06-09"] = AL * 3 + MZ[:49]              # 49/199 = 0.2462
    assert not check(by, tolerance=0.25)["ok"]


def test_the_share_and_baseline_in_the_row_are_the_numbers_measured():
    """Kills [26] L80 `Is -> IsNot` on `None if sh is None else round(sh, 4)`.

    Inverted, the field reports None for every session that HAS a share, and
    calls `round(None, 4)` on the ones that do not. Nothing was reading these
    two numbers, and they are the machine-readable half of the report -- the
    printed violation lines are for humans, `rows` is for whatever consumes
    the JSON.
    """
    out = check(healthy(8))
    last = out["rows"][-1]
    assert last["share"] == 0.5, last
    assert last["baseline"] == 0.5, last


def test_the_share_fields_carry_the_four_decimals_they_declare():
    """Kills [33] L80 and [34] L81 `round(x, 4) -> round(x, 5)`.

    One name of three is 0.333333..., the smallest sample where the declared
    precision is visible at all: with the 50/50 fixtures every share is exact
    and four digits equal five on every possible input.
    """
    by = {f"2026-06-{d:02d}": AL[:2] + MZ[:1] for d in range(1, 6)}
    last = check(by)["rows"][-1]
    assert last["share"] == 0.3333, last
    assert last["baseline"] == 0.3333, last


def test_the_tolerance_a_u1_quotes_is_the_tolerance_it_was_given():
    """Kills [48] L97 `100 -> 101` -- the tolerance in the U1 message.

    ⚠️ 0.15 cannot separate the two: 15.00 and 15.15 both print "15". Same
    rounding trap the 09-02 note above records for the drift figure, one
    format string over. 0.6 prints 60 against 61, so the tolerance has to be
    dialled up for the assertion to mean anything -- and the drift then has to
    clear it, which is why the baseline here is 0.98 rather than 0.50 (0.50
    cannot move more than 0.50).
    """
    by = {f"2026-06-{d:02d}": MZ + AL[:1] for d in range(1, 9)}   # 50/51 = 0.9804
    by["2026-06-09"] = AL + MZ[:1]                               # 1/51 = 0.0196
    out = check(by, tolerance=0.6)
    msg = next(v for v in out["violations"] if v.startswith("U1 2026-06-09"))
    assert "tolerance 60pp" in msg, msg


def test_load_needs_both_a_date_and_a_ticker_to_keep_a_row(tmp_path):
    """Kills [14] L119 `And -> Or` on `if d and t:`.

    Turned into `or`, a row with a ticker and no date opens a session called
    "" and a row with a date and no ticker files an empty symbol under a real
    one. Both are silent: the "" session is below MIN_ROWS so it is never
    judged, and `share_after` drops blank symbols -- so the damage shows up
    only as a share computed over a denominator that quietly disagrees with
    the row count printed beside it.
    """
    from pipeline.tools.audit_universe_shape import load

    p = tmp_path / "ragged.csv"
    p.write_text("date,ticker\n2026-06-01,AAPL\n,ORPHAN\n2026-06-01,\n")
    assert load(p) == {"2026-06-01": ["AAPL"]}, load(p)


def test_load_finds_the_date_column_in_a_single_row_archive(tmp_path):
    """Kills [45] L112 `0 -> 1`: `if c in rows[0]` reading `rows[1]` instead.

    A one-row archive then raises IndexError before anything is checked. Same
    shape as `read_archive_dates` in audit_calendar_gaps, pinned there on
    09-27 -- column detection that indexes past the only row it has.
    """
    from pipeline.tools.audit_universe_shape import load

    p = tmp_path / "one.csv"
    p.write_text("date,ticker\n2026-06-01,AAPL\n")
    assert load(p) == {"2026-06-01": ["AAPL"]}


class TestMainExitCodeAndPrinting:
    """`main()` had exactly one test (the empty-archive branch). Everything
    below the archive read -- the exit code, the header, the `-q` flag -- was
    unpinned."""

    def test_a_clean_archive_exits_zero_and_a_truncated_one_exits_one(self, tmp_path):
        """Kills [16] L155 `0 -> 1` and [17] L155 `1 -> 2`.

        ⭐ Fifth module with this survivor: audit_archives, audit_ledger,
        audit_ci_test_coverage and audit_calendar_gaps L423 each carried it
        too (pinned 09-25, 09-26, 09-27). `0 -> 1` is the quiet one -- CI goes
        red on every clean night, and a guard that is always red stops being
        read. `1 -> 2` is louder than it looks: argparse already uses exit 2
        for "you called me wrong", so it merges "the archive is broken" into
        "the command line is broken".
        """
        from pipeline.tools.audit_universe_shape import main

        clean = as_csv(tmp_path, healthy(8), "clean.csv")
        assert main([str(clean)]) == 0

        by = healthy(8)
        by["2026-06-09"] = AL
        assert main([str(as_csv(tmp_path, by, "broken.csv"))]) == 1

    def test_the_header_quotes_the_tolerance_it_was_given(self, tmp_path, capsys):
        """Kills [43] L145 `100 -> 101` on the header line.

        Same unreachable-boundary problem as the U1 message: 0.15 prints "15"
        either way, so the run has to ask for 0.6.
        """
        from pipeline.tools.audit_universe_shape import main

        main([str(as_csv(tmp_path, healthy(8))), "--tolerance", "0.6"])
        assert "tolerance 60pp" in capsys.readouterr().out

    def test_the_default_run_prints_the_header_and_the_warnings(self, tmp_path, capsys):
        """Kills [9] L143 and [10] L148 `drop not` on `if not a.quiet:`.

        Dropped, the two flags invert: the header and the U3 warnings appear
        ONLY under `-q`. Nothing was reading either stream.
        """
        from pipeline.tools.audit_universe_shape import main

        main([str(as_csv(tmp_path, healthy(4)))])
        out = capsys.readouterr().out
        assert "sessions, split 'L'" in out, out
        assert "WARN U3" in out, out

    def test_quiet_drops_the_header_and_the_warnings_and_keeps_the_verdict(
            self, tmp_path, capsys):
        """The other side of the same two flags -- `-q` is documented as "only
        print the sessions that failed", so a U3 warning leaking into it
        defeats the whole flag."""
        from pipeline.tools.audit_universe_shape import main

        main([str(as_csv(tmp_path, healthy(4))), "-q"])
        out = capsys.readouterr().out
        assert "sessions, split 'L'" not in out, out
        assert "WARN" not in out, out
        assert "OK: 0 violations" in out, out
