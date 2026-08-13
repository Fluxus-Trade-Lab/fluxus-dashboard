"""The auction's development stage: named states, with the rule that fired."""
from __future__ import annotations

import pytest

from pipeline.profile import daytype as D


def bars(*spans, close=None):
    out = [{"low": lo, "high": hi, "open": lo, "close": hi} for lo, hi in spans]
    if close is not None:
        out[-1]["close"] = close
    return out


# --- the width measure ---------------------------------------------------

def test_ib_share_is_the_initial_balance_over_the_whole_range():
    b = bars((100.0, 110.0), (100.0, 110.0), (100.0, 120.0))
    assert D.ib_share(b) == pytest.approx(10 / 20)


def test_a_session_that_never_moved_has_no_share_rather_than_a_full_one():
    """Returning 1.0 would file a zero-range day as a textbook normal day."""
    assert D.ib_share(bars((100.0, 100.0), (100.0, 100.0))) is None


# --- day types -----------------------------------------------------------

def test_an_initial_balance_that_set_the_day_is_normal():
    b = bars(*[(100.0, 110.0)] * 2, *[(101.0, 109.0)] * 10, close=105.0)
    d = D.day_type(b)
    assert d["type"] == "normal"
    assert "initial balance set" in d["rule"]


def test_one_side_extending_without_a_run_is_a_normal_variation():
    b = bars((100.0, 110.0), (100.0, 110.0), *[(105.0, 118.0)] * 10, close=110.0)
    d = D.day_type(b)
    assert d["type"] == "normal_variation"


def test_a_small_balance_and_a_close_on_the_extreme_is_a_trend():
    b = bars((100.0, 103.0), (100.0, 103.0),
             *[(100.0 + 4 * i, 104.0 + 4 * i) for i in range(1, 11)],
             close=143.0)
    d = D.day_type(b)
    assert d["type"] == "trend"
    assert "one-way" in d["rule"]


def test_extending_both_sides_is_neutral_whatever_the_width():
    b = bars((100.0, 110.0), (100.0, 110.0), (95.0, 105.0), (94.0, 104.0),
             (105.0, 118.0), (106.0, 119.0), close=107.0)
    d = D.day_type(b)
    assert d["type"] == "neutral"
    assert "resolved nothing" in d["rule"]


def test_a_wide_day_that_closes_in_the_middle_is_unclassified_not_forced():
    """Leftovers get their own answer rather than being swept into a named
    shape. A five-way classifier that never says 'none of these' is a
    five-way relabelling of everything."""
    b = bars((100.0, 103.0), (100.0, 103.0),
             (100.0, 140.0), (100.0, 140.0), (100.0, 140.0), close=120.0)
    d = D.day_type(b)
    assert d["type"] == "unclassified"
    assert "not one of the named shapes" in d["rule"]


def test_every_classification_carries_the_rule_and_the_measurements():
    d = D.day_type(bars(*[(100.0, 110.0)] * 12, close=105.0))
    assert d["rule"] and isinstance(d["rule"], str)
    assert {"ib_share", "close_position", "facilitation_state"} <= set(d["measurements"])


def test_no_bars_is_unclassified_rather_than_an_error():
    assert D.day_type([])["type"] == "unclassified"


# --- double distribution -------------------------------------------------

def test_two_areas_split_by_a_thin_zone_are_a_double_distribution():
    # Heavy at 100-104, one thin bracket crossing, heavy at 120-124.
    lower = [(100.0, 104.0)] * 5
    cross = [(104.0, 120.0)]
    upper = [(120.0, 124.0)] * 5
    d = D.day_type(bars(*lower, *cross, *upper, close=122.0), tick=2.0)
    assert d["type"] == "double_distribution"
    assert d["measurements"]["double_distribution"]["split_price"] is not None


def test_a_shallow_dip_in_one_distribution_is_not_two():
    b = bars(*[(100.0, 120.0)] * 4, *[(104.0, 116.0)] * 6, close=110.0)
    dd = D.day_type(b, tick=2.0)["measurements"]["double_distribution"]
    assert dd["is_double"] is False
    # The near-miss is visible: depth and cut are both reported.
    assert dd["depth"] is not None and "against a" in dd["note"]


def test_the_double_distribution_check_says_when_it_could_not_look():
    b = bars((100.0, 102.0), (100.0, 102.0))
    dd = D.day_type(b, tick=2.0)["measurements"]["double_distribution"]
    assert dd["is_double"] is False
    assert "too few prices" in dd["note"] or "no interior price" in dd["note"]


# --- open types ----------------------------------------------------------

def test_leaving_the_opening_bracket_and_never_returning_is_an_open_drive():
    b = bars((100.0, 102.0), (103.0, 106.0), (107.0, 110.0), (111.0, 114.0))
    o = D.open_type(b)
    assert o["type"] == "open_drive"
    assert "no later bracket traded back into it" in o["rule"]


def test_leaving_in_both_directions_is_a_rejection_reverse():
    b = bars((100.0, 102.0), (103.0, 106.0), (99.0, 101.0), (96.0, 98.0))
    assert D.open_type(b)["type"] == "open_rejection_reverse"


def test_the_open_is_read_over_the_opening_window_not_the_whole_day():
    """The bug the base rates caught.

    An afternoon that trades back through the morning's range is not a comment
    on the open. Read over all 13 brackets, open_drive fired once in 496
    sessions and open_rejection_reverse took 42.5% -- a description of what any
    full day does, not a classification.
    """
    drive = [(100.0, 102.0), (103.0, 106.0), (107.0, 110.0)]
    afternoon_return = [(99.0, 112.0)] * 10
    b = bars(*drive, *afternoon_return)
    assert D.open_type(b)["type"] == "open_drive"
    assert D.open_type(b)["measurements"]["open_window_brackets"] == D.OPEN_WINDOW


def test_the_opening_window_is_swept_and_restored():
    sessions = {f"d{i}": bars((100.0, 102.0), (103.0, 106.0), (107.0, 110.0),
                              *[(99.0, 112.0)] * 10) for i in range(5)}
    before = D.OPEN_WINDOW
    rows = D.sweep_open_window(sessions)
    assert D.OPEN_WINDOW == before
    assert [r["window"] for r in rows] == [2, 3, 4, 6, 13]
    # The whole-session reading is the failure case, kept visible in the sweep.
    assert rows[-1]["open_drive"] < rows[1]["open_drive"]


def test_the_sweep_must_reproduce_the_live_classification():
    """It did not, and the disagreement was the tell.

    The first sweep took no prior value areas, so opened_inside_prior_value was
    always None, open_auction could never fire, and the sweep reported 0 where
    the live run reported 114. A sweep that cannot reproduce the classifier it
    is sweeping is a second, wrong classifier presented as evidence about the
    first.
    """
    sessions = {f"d{i}": bars(*[(100.0, 102.0)] * 5) for i in range(4)}
    pv = {d: {"low": 95.0, "high": 110.0} for d in sessions}
    live = sum(1 for d, bs in sessions.items()
               if D.open_type(bs, pv[d])["type"] == "open_auction")
    row = next(r for r in D.sweep_open_window(sessions, pv)
               if r["window"] == D.OPEN_WINDOW)
    assert row["open_auction"] == live == 4
    assert row["had_prior_value"] == 4
    # ...and without them the sweep says so rather than silently disagreeing.
    blind = next(r for r in D.sweep_open_window(sessions)
                 if r["window"] == D.OPEN_WINDOW)
    assert blind["had_prior_value"] == 0


def test_a_probe_back_into_the_open_then_a_drive_is_a_test_drive():
    b = bars((100.0, 102.0), (101.0, 103.0), (104.0, 107.0), (108.0, 111.0))
    o = D.open_type(b)
    assert o["type"] == "open_test_drive"
    assert "then went" in o["rule"]


def test_rotating_inside_prior_value_is_an_open_auction():
    b = bars(*[(100.0, 102.0)] * 5)
    o = D.open_type(b, prior_value={"low": 95.0, "high": 110.0})
    assert o["type"] == "open_auction"
    assert o["measurements"]["opened_inside_prior_value"] is True


def test_without_a_prior_value_area_the_location_half_says_it_is_missing():
    """Silence and 'outside value' must not look alike."""
    o = D.open_type(bars(*[(100.0, 102.0)] * 5))
    assert o["measurements"]["opened_inside_prior_value"] is None
    assert "no prior value area was supplied" in o["rule"]


def test_too_few_brackets_to_call_the_open():
    o = D.open_type(bars((100.0, 102.0), (101.0, 103.0)))
    assert o["type"] == "unclassified"
    assert "has not finished developing" in o["rule"]


# --- the whole thing -----------------------------------------------------

def test_classify_returns_both_stages():
    c = D.classify(bars(*[(100.0, 110.0)] * 12, close=105.0))
    assert set(c) == {"open", "day", "note"}
    assert c["day"]["type"] in D.DAY_TYPES
    assert c["open"]["type"] in D.OPEN_TYPES


def test_no_state_name_carries_a_direction():
    words = " ".join(D.DAY_TYPES + D.OPEN_TYPES)
    for d in ("bull", "bear", "long", "short"):
        assert d not in words
    assert "whichever direction" in D.classify(bars(*[(1.0, 2.0)] * 5))["note"]


# --- the cuts are ours and are swept -------------------------------------

def test_the_width_cuts_are_swept_and_the_sweep_restores_the_shipped_ones():
    sessions = {f"d{i}": bars(*[(100.0, 100.0 + 5 + i)] * 2,
                              *[(100.0, 100.0 + 20 + i)] * 10, close=110.0)
                for i in range(20)}
    before = (D.NORMAL_IB_SHARE, D.VARIATION_IB_SHARE)
    rows = D.sweep_day_types(sessions)
    assert (D.NORMAL_IB_SHARE, D.VARIATION_IB_SHARE) == before
    assert rows and all(r["variation_cut"] < r["normal_cut"] for r in rows)
    assert all(sum(r[t] for t in D.DAY_TYPES) == r["n"] for r in rows)


def test_the_sweep_restores_the_constants_even_when_it_raises(monkeypatch):
    """A sweep that leaks its last setting would silently change the shipped
    classifier for every later caller in the process."""
    before = (D.NORMAL_IB_SHARE, D.VARIATION_IB_SHARE)

    def boom(*a, **k):
        raise RuntimeError("x")

    monkeypatch.setattr(D, "day_type", boom)
    with pytest.raises(RuntimeError):
        D.sweep_day_types({"a": bars((1.0, 2.0))})
    assert (D.NORMAL_IB_SHARE, D.VARIATION_IB_SHARE) == before
