# tests/gex/test_schema.py
import pytest
from pipeline.gex.schema import build_document, validate

def tenor_stub():
    return dict(expiry="20260717", net_gex_mm=3202.0, flip=7590.0, pin=7650.0,
                vol_trigger=7600.0, call_wall=7650.0, put_wall=7550.0,
                wall_basis="gamma", straddle=83.25, atm_iv=0.14,
                walls_top_calls=[{"strike": 7650.0, "oi": 1391}],
                walls_top_puts=[{"strike": 7550.0, "oi": 463}],
                greeks_coverage=1.0, quality="ok",
                delta_vs_prior={"call_wall": 50.0, "put_wall": 50.0,
                                "flip": 40.0, "note": "call wall rolled up +50"},
                converted={"ES": {"flip": 7643.0, "put_wall": 7603.0,
                                  "call_wall": 7703.0, "pin": 7703.0},
                           "SPY": {"flip": 759.0, "put_wall": 755.0,
                                   "call_wall": 765.0, "pin": 765.0}})

def test_build_and_validate_roundtrip():
    doc = build_document(
        asof="2026-07-11T08:00:00-04:00", stale=False, stale_reason=None,
        opex={"date": "2026-07-17", "dte": 6, "within_week": False},
        instruments={"SPX": {"spot": 7543.6, "basis": {"ES": 53.0},
                             "tenors": {"front": tenor_stub(),
                                        "swing": tenor_stub(),
                                        "monthly": tenor_stub()}}},
        read={"regime": "positive", "bull": ["b"], "bear": ["r"], "plan": ["p"]},
        strategy_fit=[{"name": "bull_put_spread", "rating": "favored", "why": "w"}])
    validate(doc)  # must not raise
    assert doc["version"] == 1
    assert doc["assumptions"]["dealer_side"].startswith("long calls")

def test_validate_rejects_missing_tenor_key():
    bad = {"version": 1, "asof": "x", "stale": False, "instruments": {}}
    with pytest.raises(ValueError):
        validate(bad)
