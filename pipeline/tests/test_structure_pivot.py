"""Tests for the Structure Pivot port (oratnek's Advanced Structure Pivot).

Source of truth: indicators/third_party/oratnek_advanced_structure_pivot.pine
(verbatim). Every assertion below is traceable to a line of that script; where
the script's DESCRIPTION and its CODE disagree, the code wins and the test says
which line.

The port is a bar-by-bar state machine because the original is: pivots confirm
`len` bars late, structures die on any bar whose low undercuts the HL, the
winner is re-chosen every bar, and the phase can only advance. None of that
can be read off the last bar alone.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from pipeline.screeners import structure_pivot as SP


# ---------------------------------------------------------------- fixtures --

def bars(lows, highs=None, closes=None, opens=None) -> pd.DataFrame:
    """Build an OHLC frame from a low path. Highs default to low + 2, closes
    to the midpoint, opens to the previous close -- flat enough that the
    structure is decided by what the test spells out, not by accident."""
    lows = np.asarray(lows, dtype=float)
    n = len(lows)
    highs = np.asarray(highs, dtype=float) if highs is not None else lows + 2.0
    closes = np.asarray(closes, dtype=float) if closes is not None else (lows + highs) / 2.0
    opens = np.asarray(opens, dtype=float) if opens is not None else np.r_[closes[0], closes[:-1]]
    idx = pd.bdate_range("2026-01-02", periods=n)
    return pd.DataFrame({"open": opens, "high": highs, "low": lows, "close": closes}, index=idx)


def ll_hl_path(n_pre=30, ll=90.0, hl=95.0, peak=105.0, base=100.0):
    """A clean LL -> peak -> HL sequence on a flat base, wide enough that
    lengths 2..5 all see both pivots. Returns (lows, highs, i_ll, i_peak, i_hl)."""
    lows = [base] * n_pre
    highs = [base + 2] * n_pre
    # LL: dip over 11 bars so len<=5 pivots on the centre
    dip = [base, 97, 94, 92, ll, 92, 94, 97, base, base, base]
    i_ll = len(lows) + 4
    lows += dip; highs += [x + 2 for x in dip]
    # rally to peak over 6 bars, peak bar has the max high
    up = [base, 101, 103, peak - 2, 103, 101]
    i_peak = len(lows) + 3
    lows += up; highs += [x + 2 for x in up]
    highs[i_peak] = peak
    # HL: dip over 11 bars, centre = hl (> ll)
    dip2 = [base, 98, 96, hl + 1, hl, hl + 1, 96, 98, base, base, base]
    i_hl = len(lows) + 4
    lows += dip2; highs += [x + 2 for x in dip2]
    return lows, highs, i_ll, i_peak, i_hl


# ------------------------------------------------------------ pivot maths --

class TestPivotDetection:
    def test_pivot_low_confirms_len_bars_late(self):
        """ta.pivotlow(low, L, L) at bar b reports low[b-L]; the pivot exists
        from bar b on, not from bar b-L. A port that back-dates the setup
        would look clairvoyant in a backtest."""
        lows = [100] * 40 + [90] + [100] * 20
        df = bars(lows)
        st = SP.run(df, min_len=3, max_len=3)
        # confirmed at bar 40+3 = 43; before that no pivot known
        assert st.states[0].curr_idx == 40
        assert st.states[0].confirmed_at == 43

    def test_ties_break_like_pine(self):
        """Pine's pivotlow needs the centre STRICTLY below both flanks (equal
        lows on either side disqualify). Pinned here so a golden check that
        disagrees points at this test, not at ten call sites."""
        lows = [100] * 40 + [90, 90] + [100] * 20   # two equal lows: no pivot at either
        st = SP.run(bars(lows), min_len=2, max_len=2)
        assert st.states[0].curr_p is None


class TestStructure:
    def test_ll_then_hl_forms_a_setup_with_pine_levels(self):
        lows, highs, i_ll, i_peak, i_hl = ll_hl_path()
        df = bars(lows, highs)
        st = SP.run(df)
        assert st.setup is True
        assert st.ll == pytest.approx(90.0)
        assert st.hl == pytest.approx(95.0)
        assert st.pivot_2nd == pytest.approx(105.0)          # max high strictly between LL and HL
        rng = 105.0 - 95.0
        assert st.pivot_1st == pytest.approx(95.0 + rng * 0.618)
        assert st.tp1 == pytest.approx(95.0 + rng * 1.764)
        assert st.tp2 == pytest.approx(95.0 + rng * 2.618)
        assert st.phase == 1

    def test_second_pivot_excludes_the_pivot_bars_themselves(self):
        """break_val scans prev_idx+1 .. curr_idx-1 (source: `start_s =
        st.prev_idx + 1`, `end_s = st.curr_idx - 1`). A high ON the LL or HL
        bar must not become the 2nd Pivot."""
        lows, highs, i_ll, i_peak, i_hl = ll_hl_path()
        highs[i_hl] = 200.0                       # absurd high on the HL bar itself
        st = SP.run(bars(lows, highs))
        assert st.pivot_2nd == pytest.approx(105.0)

    def test_a_low_under_the_hl_kills_the_setup(self):
        """Main loop: `if st.is_setup and low < st.curr_p: st.is_setup := false`.
        Any bar, any amount, no close required."""
        lows, highs, *_ = ll_hl_path()
        lows += [94.9]; highs += [97.0]              # one tick under HL 95
        st = SP.run(bars(lows, highs))
        assert st.setup is False

    def test_a_low_under_the_ma_fails_the_structure(self):
        """draw_long fail check: `fail = low < ma_stop` -- LOW, not close, though
        the published description says close. Code wins."""
        lows, highs, *_ = ll_hl_path()
        df = bars(lows, highs)
        st_before = SP.run(df)
        assert st_before.setup
        ma = st_before.ma
        lows += [ma - 0.01]; highs += [ma + 5]      # low pierces MA, close well above
        closes = list(SP.run(bars(lows, highs)).df["close"]) if False else None
        st = SP.run(bars(lows, highs, closes=None))
        assert st.setup is False
        assert st.failed_today is True

    def test_fail_check_skips_the_creation_bar(self):
        """`if not just_created:` -- on the bar the setup is first drawn the MA
        check is not applied (the setup can be born below its MA and live).
        The creation bar's low must stay ABOVE the HL though, or the main-loop
        `low < curr_p` kills it before it is ever drawn -- a different rule."""
        lows, highs, i_ll, i_peak, i_hl = ll_hl_path(base=100.0)
        # truncate right after the HL so the last bar is the confirmation bar
        # for the shortest length (2): HL at i_hl, confirmed at i_hl + 2
        lows, highs = lows[:i_hl + 3], highs[:i_hl + 3]
        lows[-1] = 95.5                              # under any MA of lows (~98), above HL 95
        st = SP.run(bars(lows, highs))
        assert st.setup is True
        assert st.created_today is True
        assert st.failed_today is False
        assert st.ma > 95.5, "premise: creation-bar low really is under the MA"


class TestWinner:
    def test_tightest_picks_the_lowest_second_pivot(self):
        """find_winner 'Tightest Structure': among setup states, the smallest
        break_val wins (lowest resistance = best R/R)."""
        lows, highs, i_ll, i_peak, i_hl = ll_hl_path()
        st = SP.run(bars(lows, highs), priority="tightest")
        setups = [s for s in st.states if s.is_setup and s.break_val is not None]
        assert st.winner.break_val == min(s.break_val for s in setups)

    def test_longest_picks_the_last_setup_state(self):
        """'Longest Length' sets upd := true for every candidate, so the LAST
        setup state in min->max order wins -- i.e. the longest len."""
        lows, highs, *_ = ll_hl_path()
        st = SP.run(bars(lows, highs), priority="longest")
        setups = [s for s in st.states if s.is_setup and s.break_val is not None]
        assert st.winner.len == max(s.len for s in setups)

    def test_shortest_picks_the_first(self):
        lows, highs, *_ = ll_hl_path()
        st = SP.run(bars(lows, highs), priority="shortest")
        setups = [s for s in st.states if s.is_setup and s.break_val is not None]
        assert st.winner.len == min(s.len for s in setups)

    def test_no_setup_falls_back_to_the_shortest_state_and_tracks_the_running_low(self):
        """No winner -> states[0]; and if that state is not a setup and today's
        low undercuts its curr_p, curr_p/curr_idx are OVERWRITTEN with today's
        low (source: `win_long.curr_p := low`). This mutates states_long[0]
        for good and changes what its next confirmed pivot compares against."""
        # a confirmed pivot at 30 (95), then a fresh lower low at 41 (80) that
        # is not yet a confirmed pivot -- the fallback tracks it anyway
        lows = [100] * 30 + [95] + [100] * 10 + [80]
        st = SP.run(bars(lows))
        assert st.setup is False
        assert st.states[0].curr_p == pytest.approx(80.0)
        assert st.states[0].curr_idx == 41
        # and a fresh low with NO prior pivot is left alone (`not na(curr_p)`)
        st2 = SP.run(bars([100] * 40 + [80]))
        assert st2.states[0].curr_p is None


class TestPhases:
    def _setup_then(self, extra_highs, extra_lows=None):
        lows, highs, *_ = ll_hl_path()
        base = SP.run(bars(lows, highs))
        assert base.setup
        for k, h in enumerate(extra_highs):
            lo = extra_lows[k] if extra_lows else 99.0
            lows.append(lo); highs.append(h)
        return base, SP.run(bars(lows, highs))

    def test_high_at_second_pivot_advances_to_phase_2_and_fixes_stop_at_first(self):
        """`if d.phase == 1 and high >= w.break_val: d.phase := 2` -- HIGH, not
        close (description says close). Stop = 1st Pivot, fixed."""
        base, st = self._setup_then([105.0])
        assert st.phase == 2
        assert st.stop == pytest.approx(st.pivot_1st)

    def test_high_at_tp1_advances_to_phase_3_stop_is_max_of_first_and_ma(self):
        lows, highs, *_ = ll_hl_path()
        base = SP.run(bars(lows, highs))
        _, st = self._setup_then([105.0, base.tp1 + 0.5])
        assert st.phase == 3
        assert st.stop == pytest.approx(max(st.pivot_1st, st.ma))

    def test_phase_never_reverts_while_the_structure_lives(self):
        base, st = self._setup_then([105.0, 99.5, 99.5, 99.5])
        assert st.phase == 2

    def test_phase_1_stop_trails_the_ma(self):
        base, st = self._setup_then([101.0, 101.0])
        assert st.phase == 1
        assert st.stop == pytest.approx(st.ma)


class TestScreenerSignals:
    """rt_* signals: previous close on/under the level AND today's close over
    it, with the exclusivity chain 1st < 2nd < TP1 < TP2 (a close already over
    the next level suppresses the lower signal)."""

    def _with_closes(self, closes_tail, highs_tail=None):
        lows, highs, *_ = ll_hl_path()
        base = SP.run(bars(lows, highs))
        n0 = len(lows)
        for k, c in enumerate(closes_tail):
            lows.append(min(99.0, c - 0.5)); highs.append(highs_tail[k] if highs_tail else max(c + 0.5, 101.0))
        df = bars(lows, highs)
        closes = list(df["close"])
        for k, c in enumerate(closes_tail):
            closes[n0 + k] = c
        df["close"] = closes
        return base, SP.run(df)

    def test_first_break_fires_on_the_crossing_close_only(self):
        lows, highs, *_ = ll_hl_path()
        b = SP.run(bars(lows, highs))
        p1 = b.pivot_1st
        _, s1 = self._with_closes([p1 - 0.2, p1 + 0.2])
        assert s1.signal == "1st_break"
        _, s2 = self._with_closes([p1 - 0.2, p1 + 0.2, p1 + 0.3])
        assert s2.signal is None                    # already above yesterday: no re-fire

    def test_exclusivity_second_over_first(self):
        lows, highs, *_ = ll_hl_path()
        b = SP.run(bars(lows, highs))
        _, s = self._with_closes([b.pivot_1st - 0.2, b.pivot_2nd + 0.2], highs_tail=[100.0, b.pivot_2nd + 0.5])
        assert s.signal == "2nd_break"              # not 1st_break, though it crossed both

    def test_stop_hit_uses_the_current_phase_stop(self):
        lows, highs, *_ = ll_hl_path()
        b = SP.run(bars(lows, highs))
        # push into phase 2 (high >= 2nd), then close back under the 1st pivot
        p1, p2 = b.pivot_1st, b.pivot_2nd
        _, s = self._with_closes([p2 + 0.1, p1 - 0.1], highs_tail=[p2 + 0.5, p1 + 0.5])
        # the bar that closes under the 1st: low is min(99, close-0.5) -- must stay above HL 95 and MA
        assert s.phase == 2
        assert s.signal == "stop_hit"


class TestOutputContract:
    def test_flat_history_yields_no_structure_and_no_nan(self):
        st = SP.run(bars([100.0] * 60))
        d = st.to_row()
        assert d["sp_setup"] is False
        for k, v in d.items():
            assert not (isinstance(v, float) and math.isnan(v)), k

    def test_short_history_is_unmeasured(self):
        st = SP.run(bars([100.0] * 5))
        assert st.to_row()["sp_setup"] is None

    def test_row_carries_the_levels_and_distances(self):
        lows, highs, *_ = ll_hl_path()
        d = SP.run(bars(lows, highs)).to_row()
        for k in ("sp_setup", "sp_len", "sp_ll", "sp_hl", "sp_1st", "sp_2nd", "sp_tp1", "sp_tp2",
                  "sp_phase", "sp_stop", "sp_signal", "sp_days", "sp_dist_1st_pct", "sp_dist_2nd_pct"):
            assert k in d, k
        assert d["sp_dist_1st_pct"] == pytest.approx((d["sp_1st"] / d["sp_close"] - 1) * 100, abs=0.01)
