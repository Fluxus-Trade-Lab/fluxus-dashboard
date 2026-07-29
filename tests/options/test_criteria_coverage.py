"""The three fields that operationalise the harder trade criteria.

Each of these exists to turn a phrase a trader says into something checkable:
  "convexity"                -> net_gamma sign
  "liquidity in the wings"   -> the WORST leg, not the average
  "same side as the dealers" -> sign of dealer gamma at the payoff peak
"""
import pytest

from pipeline.options.structures import Leg, evaluate


def _fly(**kw) -> list[Leg]:
    """Body at 7350 carries the most gamma — gamma peaks near the money, so
    equal per-leg gamma would be an unrealistic fixture that hides the sign."""
    d = dict(oi=1000, volume=500)
    d.update(kw)
    gammas = d.pop("gammas", (0.0008, 0.0012, 0.0006))
    return [
        Leg("BUY", 1, 7425, "P", mid=38.25, bid=38.10, ask=38.40, gamma=gammas[0], **d),
        Leg("SELL", 2, 7350, "P", mid=16.55, bid=16.40, ask=16.70, gamma=gammas[1], **d),
        Leg("BUY", 1, 7275, "P", mid=6.30, bid=6.20, ask=6.40, gamma=gammas[2], **d),
    ]


def test_long_fly_is_net_short_gamma_at_the_body():
    # 0.0008 - 2(0.0012) + 0.0006 < 0. A long fly has a convex *payoff* but is
    # SHORT gamma at the body — the word "convexity" glosses over that, and it
    # is why a fly survives a vol crush where a long straddle does not.
    r = evaluate(_fly())
    assert r["net_gamma"] == pytest.approx(-0.001, abs=1e-9)
    assert r["long_convexity"] is False


def test_long_strangle_is_long_convexity():
    legs = [Leg("BUY", 1, 7500, "C", mid=20.0, gamma=0.0008),
            Leg("BUY", 1, 7300, "P", mid=18.0, gamma=0.0007)]
    r = evaluate(legs)
    assert r["net_gamma"] == pytest.approx(0.0015, abs=1e-9)
    assert r["long_convexity"] is True


def test_liquidity_reports_the_binding_leg_not_the_average():
    legs = _fly()
    legs[2].oi = 12          # one illiquid wing
    legs[2].volume = 3
    r = evaluate(legs)
    assert r["min_leg_oi"] == 12          # not the 1000/1000/12 mean
    assert r["min_leg_volume"] == 3
    assert r["thinnest_legs"] == ["7275P"]


def test_worst_leg_spread_is_the_max_not_the_mean():
    legs = _fly()
    legs[1].bid, legs[1].ask = 15.0, 18.0     # 3.00 wide on a 16.55 mid
    r = evaluate(legs)
    assert r["worst_leg_spread_pct"] == pytest.approx(18.13, abs=0.05)


def test_dealer_gamma_sign_at_payoff_peak():
    gex = {7425: -1.2e9, 7350: +3.3e8, 7275: -0.4e9}
    r = evaluate(_fly(), dealer_gex=gex)
    assert r["max_profit_at"] == 7350
    assert r["peak_dealer_gex"] == pytest.approx(3.3e8)
    assert r["peak_dealer_long_gamma"] is True      # dealers pin toward the body

    r_neg = evaluate(_fly(), dealer_gex={7350: -2.4e9})
    assert r_neg["peak_dealer_long_gamma"] is False  # dealers amplify away from it


def test_absent_optional_data_is_omitted_not_faked():
    r = evaluate(_fly(gammas=(None, None, None), oi=None, volume=None))
    assert r["net_gamma"] is None and r["long_convexity"] is None
    assert r["min_leg_oi"] is None and r["thinnest_legs"] is None
    assert "peak_dealer_gex" not in r      # no dealer data supplied
