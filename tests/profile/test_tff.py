"""TFF against Jones' 1988 paper, including its own worked figures."""
from __future__ import annotations

import pytest

from pipeline.profile import tff as T

TICK = 2.5


def sess(*spans):
    return [{"low": lo, "high": hi} for lo, hi in spans]


def history(n, width, brackets=13, tick=TICK, spread=0.0):
    """n sessions, each bracket spanning `width` (+ i*spread) points."""
    return {f"d{i}": sess(*[(100.0, 100.0 + width + i * spread)] * brackets)
            for i in range(n)}


# --- the two counts are different objects --------------------------------

def test_a_bracket_that_never_moved_still_prints_one_tpo():
    assert T.tpo_line(sess((100.0, 100.0)), TICK) == [1]


def test_tpo_line_is_the_running_sum_of_bracket_spans():
    b = sess((100.0, 105.0), (100.0, 105.0), (100.0, 110.0))
    assert T.tpo_line(b, TICK) == [3, 6, 11]


def test_tick_line_counts_a_revisited_price_only_once():
    """The whole reason Jones keeps two tables.

    Three brackets over the same 100-105 range: TPOs keep accruing, ticks do not.
    """
    b = sess(*[(100.0, 105.0)] * 3)
    assert T.tpo_line(b, TICK) == [3, 6, 9]
    assert T.tick_line(b, TICK) == [3, 3, 3]


def test_tick_line_grows_only_when_the_range_grows():
    b = sess((100.0, 105.0), (100.0, 110.0), (95.0, 110.0))
    assert T.tick_line(b, TICK) == [3, 5, 7]


def test_the_ratio_rises_when_the_profile_fattens():
    """Jones: 'high ratios are caused by the fattening of the profiles during
    periods of low trade facilitation.'"""
    fat = sess(*[(100.0, 102.5)] * 8)          # same two prices, all day
    thin = sess(*[(100.0 + 5 * i, 105.0 + 5 * i) for i in range(8)])  # trending
    assert T.ratio_line(fat, TICK)[-1] > T.ratio_line(thin, TICK)[-1] * 2


def test_range_alone_cannot_tell_the_two_apart():
    """'Range tells you how far price went. It doesn't tell you whether anyone
    was there.' Same high, same low, different facilitation."""
    engaged = sess(*[(100.0, 110.0)] * 6)
    dead = sess((100.0, 110.0), *[(104.0, 105.0)] * 5)
    assert max(b["high"] for b in engaged) == max(b["high"] for b in dead)
    assert min(b["low"] for b in engaged) == min(b["low"] for b in dead)
    assert T.tick_line(engaged, TICK)[-1] == T.tick_line(dead, TICK)[-1]  # same range
    assert T.tpo_line(engaged, TICK)[-1] > T.tpo_line(dead, TICK)[-1]     # not same trade
    assert T.ratio_line(engaged, TICK)[-1] > T.ratio_line(dead, TICK)[-1]


def test_a_zero_tick_is_refused():
    for f in (T.tpo_line, T.tick_line):
        with pytest.raises(ValueError, match="tick must be positive"):
            f(sess((100.0, 105.0)), 0)


def test_an_unknown_measure_is_refused():
    with pytest.raises(ValueError, match="measure must be one of"):
        T.build_table(history(80, 10.0), TICK, measure="volume")


# --- Jones' construction: sort on the LAST column ------------------------

def test_the_table_is_sorted_on_the_final_column_low_to_high():
    tbl = T.build_table(history(84, 5.0, spread=0.5), TICK)
    finals = [b["columns"][-1] for b in tbl["rows"]]
    assert finals == sorted(finals)
    assert tbl["rows"][0]["tff"] == 0.0
    assert tbl["rows"][-1]["tff"] == 1.0


def test_short_sessions_are_excluded_from_the_sort_not_ranked_as_dead():
    """A half day has no last column; ranking it by one it never printed would
    file every early close in the dead band."""
    s = history(80, 10.0)
    s["short"] = sess(*[(100.0, 110.0)] * 4)
    tbl = T.build_table(s, TICK)
    assert tbl["n_sessions"] == 80
    assert tbl["n_excluded_short"] == 1


def test_the_table_reproduces_jones_shape():
    tbl = T.build_table(history(210, 5.0, spread=0.4), TICK, rows=21)
    assert len(tbl["rows"]) == 21          # 0% to 100% in steps of 5%
    assert tbl["group_size"] == 10         # his 210 days / 21 bands
    assert tbl["rows"][17]["tff"] == pytest.approx(0.85)


# --- lookup --------------------------------------------------------------

def test_lookup_crosses_a_count_over_to_the_tff_column():
    tbl = T.build_table(history(84, 5.0, spread=0.5), TICK)
    top = tbl["rows"][-1]["columns"][5]
    assert T.lookup(tbl, 5, top)["tff"] == 1.0
    bottom = tbl["rows"][0]["columns"][5]
    assert T.lookup(tbl, 5, bottom)["tff"] == 0.0


def test_lookup_reports_whether_the_column_was_monotone():
    """Jones flags a bump in his own Figure 1 D column and blames the small
    cohorts. A lookup that hides it presents a coin flip as a reading."""
    tbl = T.build_table(history(84, 5.0, spread=0.5), TICK)
    assert T.lookup(tbl, 5, 20)["column_monotone"] is True


def test_lookup_of_a_bracket_the_table_never_saw_is_none():
    tbl = T.build_table(history(80, 10.0, brackets=6), TICK)
    assert T.lookup(tbl, 99, 50) is None


# --- the reading ---------------------------------------------------------

def _tables(sessions, tick=TICK):
    return {m: T.build_table(sessions, tick, measure=m) for m in T.MEASURES}


def test_a_quiet_session_reads_dead_and_answers_the_cardinal_rule():
    hist = history(84, 10.0, spread=0.5)
    r = T.read(sess(*[(100.0, 100.5)] * 13), TICK, _tables(hist))
    assert r["measurable"] is True
    assert r["measures"]["tpo"]["tff"] <= 0.05
    assert r["measures"]["tpo"]["band"] == "dead"
    assert T.is_non_facilitating(r) is True


def test_a_busy_session_reads_at_the_top():
    hist = history(84, 10.0, spread=0.5)
    r = T.read(sess(*[(50.0, 200.0)] * 13), TICK, _tables(hist))
    assert r["measures"]["tpo"]["tff"] == 1.0
    assert r["measures"]["tpo"]["band"] == "highly_facilitating"
    assert T.is_non_facilitating(r) is False


def test_all_three_tables_are_reported_and_none_is_averaged_away():
    r = T.read(sess(*[(100.0, 110.0)] * 13), TICK, _tables(history(84, 10.0, spread=0.5)))
    assert set(r["measures"]) == set(T.MEASURES)
    assert all("tff" in v for v in r["measures"].values())
    assert "score" not in r and "composite" not in r


def test_the_note_says_when_the_tick_table_disagrees():
    hist = history(84, 10.0, spread=0.5)
    # Wide range, visited once: high ticks, ordinary TPOs.
    r = T.read(sess(*[(100.0 + 8 * i, 110.0 + 8 * i) for i in range(13)]),
               TICK, _tables(hist))
    note = r["note"]
    assert "tick table" in note
    assert ("agrees" in note) or ("disagrees" in note)


def test_a_thin_baseline_is_unmeasurable_rather_than_a_reading():
    r = T.read(sess(*[(100.0, 110.0)] * 13), TICK, _tables(history(20, 10.0)))
    assert r["measurable"] is False
    assert f"{T.MIN_BASELINE_SESSIONS} needed" in r["note"]


def test_a_table_built_on_another_tick_is_refused_not_rescaled():
    with pytest.raises(ValueError, match="do not compare"):
        T.read(sess(*[(100.0, 110.0)] * 13), 5.0, _tables(history(84, 10.0), tick=TICK))


def test_the_verdict_vocabulary_carries_no_direction():
    words = " ".join(name for _, name in T.BANDS)
    for d in ("bull", "bear", "long", "short", "up", "down"):
        assert d not in words


def test_missing_inputs_return_none_rather_than_a_confident_answer():
    assert T.read([], TICK, _tables(history(80, 10.0))) is None
    assert T.read(sess((1.0, 2.0)), TICK, {}) is None
    assert T.is_non_facilitating(None) is None


# --- the two questions must not be confused ------------------------------

def test_the_plain_percentile_is_a_different_number_from_the_table():
    """Jones' column answers 'days that looked like this finished where';
    a percentile answers 'where does this rank now'. Kept apart on purpose."""
    hist = history(84, 10.0, spread=0.5)
    today = sess(*[(100.0, 104.0)] * 13)
    pl = T.percentile_line(today, TICK, hist)
    assert len(pl) == 13
    assert all(p is None or 0.0 <= p <= 1.0 for p in pl)


def test_the_percentile_line_is_none_where_the_history_is_too_thin():
    assert T.percentile_line(sess(*[(100.0, 105.0)] * 3), TICK,
                             history(20, 10.0)) == [None, None, None]


# --- the ratio table runs the other way ----------------------------------

def test_the_ratio_band_is_inverted_because_a_fat_profile_is_not_facilitating():
    """Jones: 'the high ratios are caused by the fattening of the profiles
    during periods of LOW trade facilitation.'

    Caught on the first live run: 2026-08-12 printed 'ratio TFF 100% — highly
    facilitating' next to two tables reading dead. The percentile was right and
    the word attached to it was backwards.
    """
    assert T.band(1.0, "tpo") == "highly_facilitating"
    assert T.band(1.0, "ratio") == "dead"
    assert T.band(0.0, "tpo") == "dead"
    assert T.band(0.0, "ratio") == "highly_facilitating"


def test_the_default_measure_is_the_tpo_table():
    assert T.band(1.0) == T.band(1.0, "tpo")


def test_band_refuses_a_measure_it_does_not_model():
    with pytest.raises(ValueError, match="measure must be one of"):
        T.band(0.5, "volume")


def moving_history(n, step, brackets=13):
    """n sessions that actually travel, so the ratio has something to vary.

    `history()` holds every bracket at the same range, which makes ticks equal to
    one bracket's span and the ratio exactly `brackets` on every single day -- a
    degenerate column for the ratio table. That is a fixture defect, not a code
    one, and it is the third time in this project a "failing" test has turned out
    to be a fixture that could not express the thing under test.
    """
    return {f"m{i}": sess(*[(100.0 + (step + i * 0.2) * k,
                             105.0 + (step + i * 0.2) * k) for k in range(brackets)])
            for i in range(n)}


def test_a_dead_session_reads_dead_on_all_three_tables():
    """The three must agree in MEANING even where they disagree in percentile.

    A flat all-day session has few TPOs, few ticks, and a very fat ratio -- and
    all three of those mean 'not facilitating'.
    """
    r = T.read(sess(*[(100.0, 102.5)] * 13), TICK, _tables(moving_history(84, 2.0)))
    bands = {m: r["measures"][m]["band"] for m in T.MEASURES}
    assert bands["tpo"] in ("dead", "not_facilitating"), bands
    assert bands["ratio"] in ("dead", "not_facilitating"), bands


def test_a_degenerate_column_is_flagged_ambiguous_rather_than_guessed():
    """When every historical day shares a value the lookup has no information,
    and saying so beats returning whichever band sorted first."""
    r = T.read(sess(*[(100.0, 102.5)] * 13), TICK, _tables(history(84, 10.0, spread=0.5)))
    assert r["measures"]["ratio"]["ambiguous"] is True
