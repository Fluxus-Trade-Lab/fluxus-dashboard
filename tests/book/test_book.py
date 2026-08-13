"""The scoreboard: damage with error bars, and a test a rule can actually fail."""
from __future__ import annotations

import pytest

from pipeline.book import killlog as L
from pipeline.book import killtest as K
from pipeline.book import metrics as M


def flat(n, r=0.0):
    return [r] * n


# --- drawdown ------------------------------------------------------------

def test_a_rising_series_has_no_drawdown():
    assert M.max_drawdown([0.01] * 10)["max_drawdown"] == 0.0


def test_drawdown_is_peak_to_trough_not_first_to_last():
    # Up 10%, down 20%, back up. The damage is the 20%, not the net.
    r = [0.10, -0.20, 0.15]
    d = M.max_drawdown(r)
    assert d["max_drawdown"] == pytest.approx(-0.20, abs=1e-9)
    assert d["peak_index"] == 1 and d["trough_index"] == 2


def test_the_trough_and_peak_are_reported_not_just_the_depth():
    """Two books with the same depth in different places fail differently."""
    d = M.max_drawdown([0.0] * 5 + [-0.1] + [0.0] * 5)
    assert d["trough_index"] == 6      # curve index: 0 is inception
    assert set(d) >= {"max_drawdown", "trough_index", "peak_index", "n"}


def test_time_underwater_separates_books_with_the_same_max_drawdown():
    quick = [-0.10, 0.12] + [0.0] * 20          # one bad day, recovers
    long_ = [-0.10] + [0.0] * 20 + [0.12]       # same depth, underwater all month
    assert (M.summary(quick)["max_drawdown"]
            == pytest.approx(M.summary(long_)["max_drawdown"], abs=1e-9))
    assert M.summary(quick)["time_underwater"] < M.summary(long_)["time_underwater"]


def test_summary_of_nothing_is_zeros_not_an_error():
    assert M.summary([])["n"] == 0


# --- the paired bootstrap -----------------------------------------------

def test_the_comparison_refuses_windows_of_different_length():
    """The pairing is the whole source of power; a padded side compares two
    different markets."""
    with pytest.raises(ValueError, match="paired"):
        M.drawdown_advantage(flat(100), flat(90))


def _noisy(n, seed=11):
    """A market-like series: always some down days, so a resample never draws
    two perfectly flat curves. The all-positive fixture that shipped first is
    not a market and made every interval touch zero."""
    import random
    rng = random.Random(seed)
    return [rng.gauss(0.0005, 0.008) for _ in range(n)]


def test_a_genuinely_shallower_book_shows_a_positive_advantage():
    """A hedge that is on through every bad stretch, not just one.

    The first fixture damped a single 15-day episode inside 115 days, and the
    interval correctly refused to exclude zero: about one resample in eight
    never draws that stretch at all, and then the two books are identical. That
    was the method being properly conservative, not a bug -- and a 15-day
    divergence in a 115-day sample is genuinely not establishable at 90%.
    """
    control = _noisy(300, 5)
    book = [c * 0.5 if c < 0 else c for c in control]   # damps every down day
    a = M.drawdown_advantage(book, control, draws=400)
    assert a["advantage"] > 0
    assert a["ci_low"] > 0 and a["excludes_zero"] is True
    assert "took less damage" in a["note"]


def test_a_short_lived_edge_is_reported_as_undecidable_not_as_absent():
    """The conservative case, asserted on purpose so nobody 'fixes' it."""
    control = _noisy(50) + [-0.02] * 15 + _noisy(50, 12)
    book = control[:50] + [-0.005] * 15 + control[65:]
    a = M.drawdown_advantage(book, control, draws=400)
    assert a["advantage"] > 0            # the point estimate favours the book
    assert a["excludes_zero"] is False   # and the sample cannot support it
    assert a["p_tied"] > 0.02            # resamples that never draw the episode


def test_two_identical_books_cannot_be_told_apart():
    r = _noisy(60) + [-0.02] * 12 + _noisy(60, 12)
    a = M.drawdown_advantage(list(r), list(r), draws=400)
    assert a["advantage"] == 0.0
    assert a["excludes_zero"] is False
    assert "cannot tell the two apart" in a["note"]


def test_a_worse_book_is_named_as_worse_not_merely_not_better():
    control = _noisy(300, 5)
    book = [c * 1.8 if c < 0 else c for c in control]   # amplifies every down day
    a = M.drawdown_advantage(book, control, draws=400)
    assert a["advantage"] < 0
    assert a["ci_high"] < 0
    assert "took MORE damage" in a["note"]


def test_the_result_is_never_a_bare_number():
    a = M.drawdown_advantage(flat(80, 0.001), flat(80, 0.001), draws=200)
    assert {"ci_low", "ci_high", "p_book_worse", "block", "draws"} <= set(a)


def test_the_block_length_changes_the_answer_and_the_sweep_shows_it():
    """Why block=1 is in the sweep and not silently absent.

    The textbook argument for blocks is that destroying volatility clustering
    destroys the runs that MAKE drawdowns. I first asserted that block=1 must
    therefore give a visibly tighter interval; on a synthetic fixture the two
    came within a thousandth of each other, so the assertion was mine and not
    the data's. What the sweep must guarantee is that the choice is VISIBLE.
    """
    control = _noisy(400, 3)
    book = [c * 0.7 for c in control]
    rows = {r["block"]: r for r in
            M.bootstrap_sensitivity(book, control, blocks=(1, 21), draws=300)}
    assert set(rows) == {1, 21}
    assert all("ci_low" in r and "ci_high" in r for r in rows.values())


def test_the_block_length_is_swept_not_chosen_quietly():
    rows = M.bootstrap_sensitivity(flat(200, 0.001), flat(200, 0.001), draws=100)
    assert [r["block"] for r in rows] == [1, 5, 10, 21, 42]


def test_a_zero_block_is_refused():
    with pytest.raises(ValueError, match="block must be at least 1"):
        M.drawdown_advantage(flat(50), flat(50), block=0)


# --- the kill test -------------------------------------------------------

def _series(n=400, hedge=0.6, fire_from=200, fire_to=260, bad=-0.02):
    base = [0.001] * n
    for i in range(fire_from, fire_to):
        base[i] = bad
    overlay = [-hedge * b for b in base]
    active = [fire_from <= i < fire_to for i in range(n)]
    return base, overlay, active


def test_the_split_is_time_ordered_never_shuffled():
    assert K.split(100, 0.7) == 70


def test_an_impossible_train_fraction_is_refused():
    with pytest.raises(ValueError, match="strictly between 0 and 1"):
        K.split(100, 1.0)


def test_misaligned_series_are_refused():
    with pytest.raises(ValueError, match="align"):
        K.apply_rule(flat(10), flat(10), [True] * 9)


def test_the_control_is_the_book_without_the_rule_not_the_market():
    base, overlay, active = _series()
    r = K.kill_test("hedge", base, overlay, active, draws=300)
    # The control's out-of-sample summary is base alone, by construction.
    assert r["out_of_sample"]["control"] == M.summary(base[r["split_index"]:])


def test_a_hedge_that_fires_in_the_bad_stretch_survives():
    # Bad stretch placed inside the out-of-sample tail.
    base, overlay, active = _series(fire_from=300, fire_to=360)
    r = K.kill_test("hedge", base, overlay, active, draws=400)
    assert r["verdict"] == "survived"
    assert "excludes zero" in r["note"]


def test_a_hedge_that_fires_only_in_rallies_is_killed():
    n = 400
    base = [0.001] * n
    for i in range(300, 340):
        base[i] = -0.02
    # Fires during calm, never during the damage: pure cost.
    active = [360 <= i < 395 for i in range(n)]
    overlay = [-0.6 * b for b in base]
    # Give the control a drawdown to lose; the book should not beat it.
    r = K.kill_test("mistimed", base, overlay, active, draws=400)
    assert r["verdict"] in ("killed", "undecided")
    assert r["verdict"] != "survived"


def test_a_rule_that_never_fires_out_of_sample_is_undecided_not_killed():
    base, overlay, active = _series(fire_from=50, fire_to=110)
    r = K.kill_test("early-only", base, overlay, active, draws=200)
    assert r["verdict"] == "undecided"
    assert "nothing to test, which is not the same as failing" in r["note"]


def test_too_short_an_out_of_sample_window_is_undecided():
    base, overlay, active = _series(n=100, fire_from=80, fire_to=95)
    r = K.kill_test("short", base, overlay, active, draws=100)
    assert r["verdict"] == "undecided"
    assert f"{K.MIN_OOS_DAYS} needed" in r["note"]


def test_in_sample_figures_are_reported_so_overfitting_is_visible():
    base, overlay, active = _series(fire_from=300, fire_to=360)
    r = K.kill_test("hedge", base, overlay, active, draws=200)
    assert "in_sample" in r and "out_of_sample" in r
    assert r["in_sample"]["book"]["n"] == r["split_index"]


def test_the_verdict_vocabulary_has_no_pass():
    assert set(K.VERDICTS) == {"survived", "killed", "undecided"}
    assert "passed" not in K.VERDICTS


def test_the_timing_shuffled_control_holds_the_firing_count_fixed():
    base, overlay, active = _series(fire_from=300, fire_to=360)
    r = K.shuffled_control("hedge", base, overlay, active, draws=200)
    assert r["n_fired_total"] == sum(active)
    assert "timing-shuffled" in r["rule"]


# --- the kill log --------------------------------------------------------

def _row(verdict="killed", rule="r"):
    return L.entry({"rule": rule, "verdict": verdict, "n_days": 400,
                    "n_oos_days": 120, "n_fired_oos": 30,
                    "advantage": {"advantage": -0.01, "ci_low": -0.03,
                                  "ci_high": -0.002, "block": 21, "draws": 500},
                    "note": "n"},
                   hypothesis="h", computed_from="prior session close",
                   date="2026-08-13")


def test_a_rule_without_a_hypothesis_cannot_be_logged():
    with pytest.raises(ValueError, match="stated hypothesis"):
        L.entry({"rule": "r", "verdict": "killed"}, hypothesis="",
                computed_from="x", date="2026-08-13")


def test_a_rule_without_a_lookahead_statement_cannot_be_logged():
    """The kill test cannot detect lookahead; the claim has to be written down."""
    with pytest.raises(ValueError, match="lookahead is unfalsifiable"):
        L.entry({"rule": "r", "verdict": "killed"}, hypothesis="h",
                computed_from="", date="2026-08-13")


def test_an_unknown_verdict_is_refused():
    with pytest.raises(ValueError, match="verdict must be one of"):
        L.entry({"rule": "r", "verdict": "passed"}, hypothesis="h",
                computed_from="x", date="2026-08-13")


def test_deaths_are_recorded_as_carefully_as_survivals(tmp_path):
    p = tmp_path / "kill.jsonl"
    for v in ("killed", "killed", "survived", "undecided"):
        L.append(_row(v), p)
    c = L.counts(L.read(p))
    assert c == {"survived": 1, "killed": 2, "undecided": 1, "tested": 4}


def test_survivors_cannot_be_reported_without_the_denominator(tmp_path):
    p = tmp_path / "kill.jsonl"
    for v in ("killed", "killed", "survived"):
        L.append(_row(v), p)
    s = L.survivors(L.read(p))
    assert len(s["survivors"]) == 1
    assert s["tested"] == 3 and s["killed"] == 2
    assert s["survival_rate"] == pytest.approx(1 / 3)
    # The family-wise risk rides along; a caller cannot take the list alone.
    assert "p_at_least_one_false_survivor" in s


def test_the_search_is_priced_as_it_grows(tmp_path):
    p = tmp_path / "kill.jsonl"
    for i in range(20):
        row = _row(rule=f"r{i}")
        row["hypothesis"] = f"h{i}"     # twenty genuinely distinct ideas
        L.append(row, p)
    fe = L.family_error_now(L.read(p))
    assert fe["tested"] == 20 and fe["hypotheses"] == 20
    assert fe["p_at_least_one_false_survivor"] == pytest.approx(0.642, abs=0.002)


def test_an_empty_log_says_so_rather_than_implying_a_clean_record():
    assert "nothing has been tested yet" in L.report([])


def test_the_search_is_priced_on_hypotheses_not_on_runs(tmp_path):
    """A timing-shuffled control tests one idea twice, not two ideas.

    Counting runs would price a search of six hypotheses as a search of twelve
    and make the whole exercise look more dangerous than it is.
    """
    p = tmp_path / "kill.jsonl"
    for i in range(6):
        for tag in ("", " [timing-shuffled]"):
            row = _row(rule=f"r{i}{tag}")
            row["hypothesis"] = f"h{i}"          # the control shares its idea
            L.append(row, p)
    fe = L.family_error_now(L.read(p))
    assert fe["tested"] == 12
    assert fe["hypotheses"] == 6
    assert fe["p_at_least_one_false_survivor"] == pytest.approx(0.2649, abs=0.002)
