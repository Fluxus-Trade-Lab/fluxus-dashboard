"""The flow read: what traded, where, and which side lifted — and nothing more."""
from __future__ import annotations

import pytest

from pipeline.flow import session as S

SPOT = 7750.0


def p(strike, price, size, side="BOT", right="C"):
    return {"strike": strike, "price": price, "size": size, "side": side,
            "right": right}


# --- per strike ----------------------------------------------------------

def test_bought_and_sold_premium_are_kept_apart():
    rows = S.per_strike([p(7750, 10.0, 5, "BOT"), p(7750, 8.0, 10, "SOLD")])
    s = rows[7750.0]
    assert s["bot_premium"] == pytest.approx(5000.0)
    assert s["sold_premium"] == pytest.approx(8000.0)
    assert s["premium"] == pytest.approx(13000.0)


def test_unclassifiable_prints_get_their_own_bucket():
    """Not split, not dropped, not assigned to the majority. An unclassifiable
    print is a fact about liquidity at that moment."""
    rows = S.per_strike([p(7750, 10.0, 5, "BOT"), p(7750, 10.0, 5, "UNKNOWN")])
    s = rows[7750.0]
    assert s["unknown_premium"] == pytest.approx(5000.0)
    assert s["bot_premium"] + s["sold_premium"] == pytest.approx(5000.0)
    assert s["classified_share"] == pytest.approx(0.5)


def test_net_lift_is_over_classified_premium_not_over_everything():
    """A session with many unknown prints must report a WEAKER reading, not a
    diluted one — the denominator is what we could actually call."""
    rows = S.per_strike([p(7750, 10.0, 10, "BOT"),
                         p(7750, 10.0, 90, "UNKNOWN")])
    assert rows[7750.0]["net_lift"] == pytest.approx(1.0)
    assert rows[7750.0]["classified_share"] == pytest.approx(0.1)


def test_calls_and_puts_are_split():
    rows = S.per_strike([p(7750, 10.0, 5, right="C"),
                         p(7750, 4.0, 5, right="P")])
    assert rows[7750.0]["call_premium"] == pytest.approx(5000.0)
    assert rows[7750.0]["put_premium"] == pytest.approx(2000.0)


def test_a_strike_nobody_touched_does_not_appear():
    assert 7800.0 not in S.per_strike([p(7750, 10.0, 5)])


def test_zero_priced_prints_are_dropped_by_the_block_tagger():
    rows = S.per_strike([p(7750, 0.0, 5), p(7750, 10.0, 5)])
    assert rows[7750.0]["n"] == 1


# --- belt and wings ------------------------------------------------------

def test_the_zones_are_moneyness_not_points():
    """1% of 7,750 is ~78 points; the same rule at 4,000 is ~40. A fixed point
    width would mean two different things."""
    strikes = S.per_strike([p(7750, 10, 5), p(7800, 5, 5), p(7700, 5, 5),
                            p(8200, 1, 5), p(7300, 1, 5)])
    z = S.zones(strikes, SPOT, belt_pct=0.01)["zones"]
    assert z["belt"]["strikes"] == 3          # 7700, 7750, 7800 within 1%
    assert z["upper_wing"]["strikes"] == 1
    assert z["lower_wing"]["strikes"] == 1


def test_zone_shares_sum_to_the_session():
    strikes = S.per_strike([p(7750, 10, 5), p(8200, 1, 5), p(7300, 1, 5)])
    z = S.zones(strikes, SPOT)
    assert sum(b["share_of_session"] for b in z["zones"].values()) == pytest.approx(1.0)


def test_a_zero_spot_cannot_place_a_strike():
    strikes = S.per_strike([p(7750, 10, 5)])
    z = S.zones(strikes, 0.0)
    assert all(b["strikes"] == 0 for b in z["zones"].values())


# --- his question --------------------------------------------------------

def test_a_one_sided_belt_reads_as_bid():
    strikes = S.per_strike([p(7750, 20, 50, "BOT"), p(7750, 5, 10, "SOLD")])
    bb = S.belt_bid(S.zones(strikes, SPOT))
    assert bb["state"] == "bid"
    assert bb["net_lift"] > S.BELT_BID_LIFT


def test_the_other_side_reads_as_offered_not_as_not_bid():
    strikes = S.per_strike([p(7750, 5, 10, "BOT"), p(7750, 20, 50, "SOLD")])
    assert S.belt_bid(S.zones(strikes, SPOT))["state"] == "offered"


def test_an_even_belt_is_balanced():
    strikes = S.per_strike([p(7750, 10, 10, "BOT"), p(7750, 10, 10, "SOLD")])
    assert S.belt_bid(S.zones(strikes, SPOT))["state"] == "balanced"


def test_too_few_classified_prints_is_unknown_never_balanced():
    """A net lift computed from a third of the prints is a statement about the
    third. Unknown and balanced are different answers."""
    strikes = S.per_strike([p(7750, 20, 50, "BOT"),
                            p(7750, 20, 300, "UNKNOWN")])
    bb = S.belt_bid(S.zones(strikes, SPOT))
    assert bb["state"] == "unknown"
    assert f"{S.MIN_CLASSIFIED:.0%} needed" in bb["note"]


def test_an_empty_belt_is_unknown():
    strikes = S.per_strike([p(8200, 1, 5)])
    bb = S.belt_bid(S.zones(strikes, SPOT))
    assert bb["state"] == "unknown"
    assert "nothing traded in the belt" in bb["note"]


# --- the campaign question ----------------------------------------------

def _hist(*states):
    return [{"session": f"d{i}", "belt_bid": {"state": s}}
            for i, s in enumerate(states)]


def test_one_session_is_a_desk_two_is_a_campaign():
    """His threshold, made countable."""
    assert S.repeats(_hist("bid"))["consecutive"] == 1
    assert "single desk" in S.repeats(_hist("bid"))["reading"]
    r = S.repeats(_hist("bid", "bid"))
    assert r["consecutive"] == 2
    assert "campaign threshold is 2" in r["reading"]


def test_the_run_counts_backwards_from_today_and_stops_at_the_break():
    r = S.repeats(_hist("bid", "bid", "offered", "bid"))
    assert r["consecutive"] == 1 and r["through"] == "d3"


def test_a_broken_run_is_no_run():
    assert S.repeats(_hist("bid", "offered"))["consecutive"] == 0


def test_an_empty_history_is_no_run_rather_than_an_error():
    assert S.repeats([])["consecutive"] == 0


def test_unknown_does_not_extend_a_run():
    """An unmeasurable session cannot be counted as agreement."""
    assert S.repeats(_hist("bid", "unknown"))["consecutive"] == 0


# --- the free parameter --------------------------------------------------

def test_the_belt_width_is_swept():
    strikes = S.per_strike([p(7750, 10, 5), p(7790, 5, 5), p(7900, 2, 5),
                            p(7600, 2, 5)])
    rows = S.sweep_belt(strikes, SPOT)
    assert [r["belt_pct"] for r in rows] == [0.005, 0.0075, 0.01, 0.015, 0.02]
    # A wider belt can never hold a smaller share of the session.
    shares = [r["belt_share"] for r in rows]
    assert shares == sorted(shares)


# --- the whole read ------------------------------------------------------

def test_the_read_carries_its_own_limits():
    r = S.session_read([p(7750, 10, 5)], SPOT, "2026-08-13")
    assert r["session"] == "2026-08-13"
    assert "cannot tell you which" in r["note"]
    assert {"belt_bid", "zones", "belt_sweep", "block_summary"} <= set(r)


def test_no_field_or_state_is_named_for_intent():
    """He reads hedging and speculating. The tape supports neither word."""
    r = S.session_read([p(7750, 10, 5)], SPOT, "2026-08-13")
    blob = repr(r).lower()
    for w in ("hedging", "speculating", "institutional"):
        assert w not in blob or w in r["note"]


# --- the side is often unaffordable, and its absence is a stated fact ----

def test_a_tape_without_quotes_reports_no_sides_rather_than_balanced():
    """The measured reason: quote ticks cost 142s per contract against 1.9s for
    trades, and the 1-minute bar proxy agreed with tick NBBO 56.7% of the time
    against a 50% coin. Refusing the proxy is the point."""
    prints = [p(7750, 10, 5, "UNKNOWN"), p(7750, 8, 5, "UNKNOWN")]
    r = S.session_read(prints, SPOT, "2026-08-13")
    assert r["sides_available"] is False
    assert r["belt_bid"]["state"] == "unknown"
    assert "without quote ticks" in r["belt_bid"]["note"]
    assert "56.7%" in r["belt_bid"]["note"]


def test_a_tape_with_quotes_still_answers_the_question():
    prints = [p(7750, 20, 50, "BOT"), p(7750, 5, 10, "SOLD")]
    r = S.session_read(prints, SPOT, "2026-08-13")
    assert r["sides_available"] is True
    assert r["belt_bid"]["state"] == "bid"


def test_no_sides_still_leaves_premium_and_blocks_readable():
    """Most of the read survives; only the side-dependent half does not."""
    prints = [p(7750, 40, 10, "UNKNOWN"), p(8200, 1, 5, "UNKNOWN")]
    r = S.session_read(prints, SPOT, "2026-08-13")
    assert r["total_premium"] == pytest.approx(40500.0)
    assert r["zones"]["belt"]["share_of_session"] > 0.9
    assert r["block_summary"]["block_share"] is not None


def test_the_availability_question_is_asked_of_the_prints_not_of_a_zero():
    """'We did not pull quotes' and 'the quotes were crossed all day' are
    different facts, and only the first is a budget decision."""
    assert S.sides_available([]) is False
    assert S.sides_available([p(7750, 1, 1, "BOT")] * 6 + [p(7750, 1, 1, "UNKNOWN")] * 4)
    assert not S.sides_available([p(7750, 1, 1, "BOT")] * 4 + [p(7750, 1, 1, "UNKNOWN")] * 6)


def test_a_pull_that_never_reached_the_wings_says_so():
    """The first live run covered only +/-0.6% of spot, so every strike landed
    in the belt and 'belt = 100% of premium' described the sample, not the
    market. That looks like a finding and is a sampling failure."""
    strikes = S.per_strike([p(7740, 10, 5), p(7750, 10, 5), p(7760, 10, 5)])
    r = S.session_read([p(7740, 10, 5), p(7750, 10, 5)], SPOT, "2026-08-13")
    assert r["zones_covered"] is False
    assert "did not reach the wings" in r["coverage_note"]
    assert "about the sample, not the market" in r["coverage_note"]


def test_a_pull_that_reached_both_wings_is_covered():
    r = S.session_read([p(7750, 10, 5), p(8200, 1, 5), p(7300, 1, 5)],
                       SPOT, "2026-08-13")
    assert r["zones_covered"] is True
    assert r["coverage_note"] is None


def test_a_re_run_cannot_become_a_second_session():
    """The append-only log gets a new row every run. The first live day left two
    rows for 2026-08-12, and without collapsing them a single re-pull would
    clear his two-session campaign threshold from one day of data."""
    hist = [{"session": "2026-08-12", "belt_bid": {"state": "bid"}},
            {"session": "2026-08-12", "belt_bid": {"state": "bid"}}]
    r = S.repeats(hist)
    assert r["consecutive"] == 1
    assert "single desk" in r["reading"]


def test_the_last_row_for_a_session_wins():
    hist = [{"session": "2026-08-12", "belt_bid": {"state": "offered"}},
            {"session": "2026-08-12", "belt_bid": {"state": "bid"}}]
    assert S.repeats(hist)["consecutive"] == 1
    assert S.repeats(hist, "offered")["consecutive"] == 0


def test_sessions_are_ordered_by_date_not_by_file_order():
    hist = [{"session": "2026-08-12", "belt_bid": {"state": "bid"}},
            {"session": "2026-08-10", "belt_bid": {"state": "offered"}},
            {"session": "2026-08-11", "belt_bid": {"state": "bid"}}]
    assert S.repeats(hist)["consecutive"] == 2      # 08-11 and 08-12
    assert S.repeats(hist)["through"] == "2026-08-11"


# --- the tenor is part of the read's identity ---------------------------

def test_reads_of_the_same_tenor_are_comparable():
    reads = [{"session": "2026-08-12", "dte": 1},
             {"session": "2026-08-13", "dte": 1}]
    c = S.comparable(reads)
    assert c["comparable"] is True
    assert "1DTE" in c["note"]


def test_a_mixed_tenor_set_is_refused_not_averaged():
    """Measured on the first three sessions stored: 1DTE, 1DTE, 0DTE gave
    69k / 112k / 792k prints and $2,783 / $3,305 / $1,140 per print. Seven times
    the prints and a third the premium each is a different instrument, not a
    market that changed."""
    reads = [{"session": "2026-08-12", "dte": 1},
             {"session": "2026-08-13", "dte": 1},
             {"session": "2026-08-14", "dte": 0}]
    c = S.comparable(reads)
    assert c["comparable"] is False
    assert "different books" in c["note"]
    assert c["tenors"][1] == ["2026-08-12", "2026-08-13"]
    assert c["tenors"][0] == ["2026-08-14"]


def test_the_odd_session_out_is_named_not_dropped():
    """Which one is excluded is the caller's decision and usually the
    interesting one."""
    c = S.comparable([{"session": "a", "dte": 1}, {"session": "b", "dte": 0}])
    assert set(c["tenors"]) == {0, 1}


def test_a_read_carries_its_tenor():
    r = S.session_read([p(7750, 10, 5)], SPOT, "2026-08-14", dte=0)
    assert r["dte"] == 0


def test_a_read_with_no_tenor_says_none_rather_than_guessing_zero():
    assert S.session_read([p(7750, 10, 5)], SPOT, "2026-08-14")["dte"] is None
