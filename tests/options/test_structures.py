"""Structure math, validated against an independently-published worked example.

The golden fixture is the SPX 7425/7350/7275 put fly posted by
@TailThatWagsDog on 2026-07-29 with a full metrics table. Every number below
(debit, max profit, breakevens, R/R, net delta, net vega, sigma position) was
computed by a third party from the same quotes, so agreeing with it end-to-end
is a real check on this module rather than a restatement of its own output.
"""
import pytest

from pipeline.options.structures import Leg, evaluate, crush_pnl, payoff_at


def _spx_put_fly() -> list[Leg]:
    return [
        Leg("BUY", 1, 7425, "P", mid=38.25, bid=38.10, ask=38.40,
            iv=0.2285, delta=-0.48, vega=1.777, oi=896, volume=839),
        Leg("SELL", 2, 7350, "P", mid=16.55, bid=16.40, ask=16.70,
            iv=0.2590, delta=-0.24, vega=1.372, oi=1080, volume=983),
        Leg("BUY", 1, 7275, "P", mid=6.30, bid=6.20, ask=6.40,
            iv=0.2813, delta=-0.10, vega=0.792, oi=1115, volume=501),
    ]


def test_matches_published_fly_metrics():
    r = evaluate(_spx_put_fly(), forward=7432.45, implied_move_pts=82.95)
    assert r["net_debit"] == pytest.approx(11.45, abs=0.01)      # published 11.45
    assert r["max_profit"] == pytest.approx(63.55, abs=0.01)     # published 63.55
    assert r["max_profit_at"] == 7350
    assert r["max_loss"] == pytest.approx(-11.45, abs=0.01)
    assert r["rr"] == pytest.approx(5.55, abs=0.01)              # published 1:5.55
    assert r["breakevens"] == [pytest.approx(7286.45, abs=0.01),
                               pytest.approx(7413.55, abs=0.01)]
    assert r["profit_zone_width"] == pytest.approx(127.1, abs=0.1)
    assert r["net_delta"] == pytest.approx(-0.100, abs=0.001)    # published -0.100
    assert r["net_vega"] == pytest.approx(-0.175, abs=0.001)     # published -0.175
    assert r["peak_sigma"] == pytest.approx(-0.99, abs=0.01)     # published -0.99σ
    assert r["peak_vs_forward_pct"] == pytest.approx(-1.11, abs=0.01)


def test_fly_is_risk_defined_and_captures_put_skew():
    r = evaluate(_spx_put_fly())
    assert r["risk_defined"] is True
    assert r["unbounded_loss_up"] is False and r["unbounded_loss_down"] is False
    # Sells the 25.9% body against 22.85%/28.13% wings -> net short the richer vol.
    assert r["skew_capture"] > 0
    # Worst-case fill vs mid: published slippage 0.55 on an 11.45 debit (4.8%).
    assert r["slippage"] == pytest.approx(0.55, abs=0.01)
    assert r["slippage_pct_of_debit"] == pytest.approx(4.8, abs=0.1)


def test_crush_pnl_sign_and_size():
    # Published: net vega -0.175, an 8-point crush "is worth +1.40 to you".
    assert crush_pnl(-0.175, 8) == pytest.approx(1.40, abs=0.001)
    # Long vega loses on the same crush.
    assert crush_pnl(+0.175, 8) == pytest.approx(-1.40, abs=0.001)


def test_naked_strangle_is_flagged_unbounded_both_sides():
    legs = [Leg("SELL", 1, 7500, "C", mid=20.85),
            Leg("SELL", 1, 7350, "P", mid=24.30)]
    r = evaluate(legs)
    assert r["net_debit"] == pytest.approx(-45.15, abs=0.01)   # a credit
    assert r["is_debit"] is False
    # The tail runs against you on BOTH sides — this is the flag that separates
    # a naked strangle from a condor, and it must never read as "unbounded gain".
    assert r["unbounded_loss_up"] is True and r["unbounded_loss_down"] is True
    assert r["unbounded_profit_up"] is False and r["unbounded_profit_down"] is False
    assert r["risk_defined"] is False
    assert r["max_loss"] is None                               # no floor to report
    assert r["breakevens"] == [pytest.approx(7304.85, abs=0.01),
                               pytest.approx(7545.15, abs=0.01)]


def test_iron_condor_is_bounded_and_credit():
    legs = [Leg("BUY", 1, 7520, "C", mid=14.10), Leg("SELL", 1, 7500, "C", mid=20.85),
            Leg("SELL", 1, 7350, "P", mid=24.30), Leg("BUY", 1, 7330, "P", mid=20.10)]
    r = evaluate(legs)
    assert r["net_debit"] == pytest.approx(-10.95, abs=0.01)    # 10.95 credit
    assert r["risk_defined"] is True
    assert r["max_profit"] == pytest.approx(10.95, abs=0.01)
    assert r["max_loss"] == pytest.approx(-9.05, abs=0.01)      # 20 wide - 10.95


def test_payoff_at_is_piecewise_exact():
    legs = _spx_put_fly()
    assert payoff_at(7500, legs) == 0.0                # all puts worthless
    assert payoff_at(7350, legs) == pytest.approx(75)  # peak = wing width
    assert payoff_at(7000, legs) == pytest.approx(0)   # both wings offset the body
