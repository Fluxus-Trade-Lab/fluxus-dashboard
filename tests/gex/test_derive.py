# tests/gex/test_derive.py
from datetime import date
from pipeline.gex.derive import (third_friday, select_tenors, opex_flag,
                                 regime_of, wall_migration, strategy_fit,
                                 build_plan)

EXPIRIES = ["20260713", "20260714", "20260715", "20260716", "20260717",
            "20260720", "20260724", "20260731", "20260821", "20260918"]

def test_third_friday():
    assert third_friday(2026, 7) == date(2026, 7, 17)
    assert third_friday(2026, 8) == date(2026, 8, 21)

def test_select_tenors():
    t = select_tenors(EXPIRIES, today=date(2026, 7, 11))
    assert t["front"] == "20260713"      # nearest 0-2 DTE
    assert t["swing"] == "20260720"      # DTE 9, closest to target 9 in [5,14]
    assert t["monthly"] == "20260821"    # next monthly OPEX with DTE >= 15

def test_opex_flag():
    f = opex_flag(today=date(2026, 7, 13))
    assert f["date"] == "2026-07-17" and f["dte"] == 4 and f["within_week"] is True

def test_regime():
    assert regime_of(2940.0) == "positive"
    assert regime_of(-2815.0) == "negative"
    assert regime_of(None) == "unknown"

def test_wall_migration():
    prior = {"call_wall": 7600.0, "put_wall": 7500.0, "flip": 7550.0}
    cur = {"call_wall": 7650.0, "put_wall": 7550.0, "flip": 7590.0}
    d = wall_migration(cur, prior)
    assert d["call_wall"] == 50.0 and d["put_wall"] == 50.0 and d["flip"] == 40.0
    assert "rolled up" in d["note"]          # SpotGamma's bullish tell

def test_strategy_fit_rules():
    pos = {s["name"]: s["rating"] for s in strategy_fit("positive", atm_iv=0.15)}
    assert pos["bull_put_spread"] == "favored"
    assert pos["dip_fade_call"] == "favored"
    assert pos["iron_condor"] == "situational"
    assert pos["naked_short_put"] == "avoid"
    thin = {s["name"]: s["rating"] for s in strategy_fit("positive", atm_iv=0.10)}
    assert thin["iron_condor"] == "avoid"    # credit too thin below 12% IV
    neg = {s["name"]: s["rating"] for s in strategy_fit("negative", atm_iv=0.20)}
    assert neg["iron_condor"] == "avoid" and neg["calendar_call_wall"] == "avoid"
    assert neg["dip_fade_call"] == "conditional"

def test_build_plan_mentions_levels():
    txt = " ".join(build_plan(regime="positive", flip=7590.0, put_wall=7550.0,
                              call_wall=7650.0, pin=7650.0,
                              opex={"date": "2026-07-17", "dte": 4, "within_week": True},
                              migration={"note": "call wall rolled up +50"}))
    for token in ("7590", "7550", "7650", "OPEX", "rolled up"):
        assert token in txt
