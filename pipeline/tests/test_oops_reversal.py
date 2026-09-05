"""Larry Williams' Oops! pattern -- the author's definition, both sides.

TraderLion borrows the name; the Trade-Lab Breakouts model book on this
machine labels 23 bars "Oops Reversal" and defines none of them. Until the
definition was traced to Williams (2026-09-05) the term stayed out of the
code under the rule that a name without a definition is not a field.

    OOPS BUY   open below yesterday's low, then trades back up through it
    OOPS SELL  open above yesterday's high, then trades back down through it
"""
import math
import pytest

from pipeline.adapters.yfinance_adapter import oops_reversal


# yesterday: high 105, low 100
PH, PL = 105.0, 100.0


class TestBuy:
    def test_gap_below_the_low_then_reclaim_is_a_buy(self):
        assert oops_reversal(98.0, 101.0, 97.5, PH, PL) == (True, False)

    def test_touching_the_low_counts_as_reclaiming_it(self):
        """The buy stop sits AT yesterday's low; reaching it fills it."""
        assert oops_reversal(98.0, 100.0, 97.5, PH, PL) == (True, False)

    def test_gap_down_that_never_recovers_is_not(self):
        assert oops_reversal(98.0, 99.5, 96.0, PH, PL) == (False, False)

    def test_an_open_exactly_at_the_low_is_not_a_gap(self):
        """Strict: the panic has to have opened BELOW the range."""
        assert oops_reversal(100.0, 103.0, 99.0, PH, PL) == (False, False)

    def test_an_ordinary_inside_day_is_nothing(self):
        assert oops_reversal(102.0, 104.0, 101.0, PH, PL) == (False, False)


class TestSell:
    def test_gap_above_the_high_then_failure_is_a_sell(self):
        assert oops_reversal(107.0, 108.0, 104.0, PH, PL) == (False, True)

    def test_gap_up_that_holds_is_not(self):
        assert oops_reversal(107.0, 109.0, 106.0, PH, PL) == (False, False)

    def test_an_open_exactly_at_the_high_is_not_a_gap(self):
        assert oops_reversal(105.0, 106.0, 102.0, PH, PL) == (False, False)


class TestShape:
    def test_both_sides_cannot_fire_on_one_bar(self):
        """An open is either below the low or above the high, never both."""
        for o in (95.0, 100.0, 102.5, 105.0, 110.0):
            b, s = oops_reversal(o, 120.0, 80.0, PH, PL)
            assert not (b and s)

    def test_missing_inputs_are_false_not_a_guess(self):
        assert oops_reversal(None, 101.0, 97.5, PH, PL) == (False, False)
        assert oops_reversal(98.0, math.nan, 97.5, PH, PL) == (False, False)
        assert oops_reversal("x", 101.0, 97.5, PH, PL) == (False, False)

    def test_the_reclaim_holding_into_the_close_is_not_part_of_it(self):
        """Williams' pattern is the trigger, not the outcome.

        A day that gaps below, reclaims the low intraday and then closes back
        under it is STILL an Oops buy by the definition -- the stop filled.
        Folding "and it held" in here would silently tighten the pattern into
        something the author did not describe; that belongs in its own column.
        """
        # open 98, high 101 (reclaimed), low 96 -- close is not an input at all
        assert oops_reversal(98.0, 101.0, 96.0, PH, PL) == (True, False)
