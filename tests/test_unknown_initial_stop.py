"""A trade with no entry stop on record carries no R, everywhere.

Andy trails stops in the tracker (2026-08-17), so the live stop is not the one
the position was sized against; substituting it divides that trade's R by the
wrong number and the result still looks like an R. `initial_stop` therefore
became Optional, and six call sites were doing arithmetic on it.

The suite passed at every step of that change, because every fixture in it has
a stop. These tests are the ones that would not have.
"""
from __future__ import annotations

from datetime import date

import pytest

from pipeline.portfolio.pyramid_analyzer import _make_campaign
from pipeline.portfolio.trade_parser import Trade, TrimEvent


def trade(initial_stop, *, closed=True):
    return Trade(
        ticker='ABCD', direction='long', sector='Technology',
        entry_date=date(2026, 1, 5), entry_price=100.0,
        original_qty=300, current_qty=0,
        stop_price=112.0,          # trailed well above entry — the wrong denominator
        initial_stop=initial_stop,
        closed=closed,
        trims=(TrimEvent(date=date(2026, 2, 1), price=130.0, qty=300, type='sell_rest'),),
    )


def test_no_entry_stop_means_no_R():
    t = trade(None)
    assert t.R_dollars is None
    assert t.realized_R is None
    assert t.has_R is False


def test_a_known_entry_stop_still_measures():
    t = trade(90.0)
    assert t.R_dollars == pytest.approx(3000.0)     # |100 - 90| * 300
    assert t.realized_R == pytest.approx(3.0)       # (130-100)*300 / 3000
    assert t.has_R is True


def test_the_trailed_stop_is_not_used_as_a_substitute():
    """The whole point: this trade's stop has been trailed to 112, above entry.
    Backfilling would have produced a 1R of $3,600 and an R of +2.5 — numbers
    that look ordinary and describe a position nobody ever sized."""
    assert trade(None).realized_R is None


def test_has_R_is_false_rather_than_raising():
    """`R_dollars > 0` raises TypeError once None is possible, and it was
    spelled that way at six call sites."""
    assert trade(None).has_R is False
    # A stop AT the entry gives |100-100| = 0, which is not a denominator
    # either — the pre-existing `R_dollars <= 0` case, still covered.
    assert trade(100.0).has_R is False


def test_realized_pl_survives_without_an_R():
    """Dollars are still knowable — it is only the R denominator that is not."""
    assert trade(None).realized_pl == pytest.approx((130.0 - 100.0) * 300)


def test_a_campaign_on_an_unmeasured_first_layer_reports_no_R():
    """The campaign is denominated in the first layer's R. `first_R > 0` used
    to raise here, and the fallback would have called it a flat campaign."""
    c = _make_campaign('ABCD', 'long', [trade(None), trade(90.0)])
    assert c.actual_realized_R == 0


def test_a_campaign_with_a_measured_first_layer_still_divides():
    c = _make_campaign('ABCD', 'long', [trade(90.0)])
    assert c.actual_realized_R == pytest.approx(3.0)
