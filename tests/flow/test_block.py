"""Block detection — thresholded on dollars, and honest about what it misses."""
import json
from pathlib import Path

import pytest

from pipeline.flow import block as B

SAMPLE = Path("data/reference/tape_SPX_20260807_sample.json")


def test_a_cheap_big_lot_is_not_a_block_and_an_expensive_small_one_is():
    # The whole argument in two prints: 20 lots of a $0.10 wing is $200;
    # 5 lots of a $50 option is $25,000.
    t = {x["price"]: x for x in B.tag_prints(
        [{"price": 0.10, "size": 20}, {"price": 50.0, "size": 5}])}
    assert t[0.10]["is_block"] is False and t[0.10]["is_large_lot"] is True
    assert t[50.0]["is_block"] is True and t[50.0]["is_large_lot"] is False


def test_zero_and_negative_prints_are_dropped_not_counted_as_zero_premium():
    out = B.tag_prints([{"price": 0.0, "size": 10}, {"price": 5.0, "size": 0},
                        {"price": -1.0, "size": 5}, {"price": 5.0, "size": 5}])
    assert len(out) == 1


def test_a_strike_nobody_traded_does_not_appear_with_a_zero_share():
    acc = B.by_strike(B.tag_prints([{"strike": 7700.0, "price": 5.0, "size": 5}]))
    assert set(acc) == {7700.0}


def test_agreement_is_reported_because_it_says_whether_the_rule_mattered():
    # If both rules label every print identically, the argument is moot and the
    # number must say so rather than being inferred from the shares.
    same = [{"price": 100.0, "size": 50}, {"price": 0.05, "size": 1}]
    assert B.block_share(B.tag_prints(same))["agreement"] == 1.0


def test_an_empty_tape_returns_none_shares_rather_than_zero():
    s = B.block_share([])
    assert s["block_share"] is None and s["large_lot_share"] is None


def test_comparison_is_at_matched_selectivity_not_matched_threshold():
    # 3 large lots exist, so the premium rule must also take exactly 3 — else
    # the greedier rule wins for free and the criterion is not isolated.
    prints = [{"price": 1.0, "size": 20}, {"price": 1.0, "size": 15},
              {"price": 1.0, "size": 12}, {"price": 80.0, "size": 5},
              {"price": 70.0, "size": 4}, {"price": 0.2, "size": 1}]
    c = B.compare_rules(prints)
    assert c["n_selected"] == 3
    assert c["share_by_premium"] > c["share_by_lot"]


def test_a_tape_with_no_large_lots_says_so_instead_of_dividing_by_zero():
    c = B.compare_rules([{"price": 5.0, "size": 1}])
    assert c["gap_pct_points"] is None and "no print reached" in c["note"]


# ------------------------------------------- the measured claim, pinned down

@pytest.mark.skipif(not SAMPLE.exists(), reason="sample tape not present")
def test_the_premium_rule_beats_the_lot_rule_on_the_real_session():
    """26,837 real SPX prints, 2026-08-07. This is the evidence for changing
    someone else's rule, and it lives in a test so it cannot quietly rot."""
    prints = json.loads(SAMPLE.read_text())["prints"]
    c = B.compare_rules(prints, lot=10)
    assert c["n"] > 20_000
    assert c["share_by_lot"] == pytest.approx(0.426, abs=0.01)
    assert c["share_by_premium"] == pytest.approx(0.595, abs=0.01)
    assert c["gap_pct_points"] > 15          # measured +17.0
    # And the rules genuinely disagree — otherwise the gap would be trivia.
    assert c["overlap"] < 0.40               # measured 32.3%


@pytest.mark.skipif(not SAMPLE.exists(), reason="sample tape not present")
def test_the_advantage_survives_every_threshold_not_just_the_convenient_one():
    prints = json.loads(SAMPLE.read_text())["prints"]
    for lot in (2, 5, 10, 20, 50, 100):
        c = B.compare_rules(prints, lot=lot)
        assert c["gap_pct_points"] > 8, f"gap collapsed at lot >= {lot}"
