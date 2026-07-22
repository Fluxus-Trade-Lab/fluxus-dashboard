# tests/gex/test_derive.py
from datetime import date
from pipeline.gex.derive import (third_friday, select_tenors, opex_flag,
                                 regime_of, wall_migration, strategy_fit, iv_tenors,
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

def test_wall_migration_reports_put_wall_drop():
    # A falling put wall is the floor weakening -- must not go unreported, or a
    # two-sided widening (call up / put down) reads as a one-sided bullish tell.
    prior = {"call_wall": 7525.0, "put_wall": 7500.0, "flip": 7523.5}
    cur = {"call_wall": 7550.0, "put_wall": 7450.0, "flip": 7525.2}
    d = wall_migration(cur, prior)
    assert d["put_wall"] == -50.0
    assert "put wall dropped -50" in d["note"]
    assert "rolled up" in d["note"]           # both sides reported

def test_iv_tenors_skips_0dte():
    # 0DTE ATM IV spikes into expiry as sqrt(T) collapses -- it tracks the
    # clock, not the vol regime, so neither IV reading may come from it.
    t = iv_tenors(["20260721", "20260722", "20260723", "20260724", "20260727"],
                  today=date(2026, 7, 21))
    assert t["one_dte"] == "20260722"     # not 20260721, which expires today
    assert t["swing"] == "20260727"       # DTE 6, inside [5,14]

def test_iv_tenors_swing_targets_9dte():
    t = iv_tenors(EXPIRIES, today=date(2026, 7, 11))
    assert t["one_dte"] == "20260713"     # DTE 2, nearest forward expiry
    assert t["swing"] == "20260720"       # DTE 9, the SWING_TARGET

def test_iv_tenors_missing_candidates():
    # A chain that reaches only 3 days out has no swing tenor at all; the
    # caller must get None rather than a silently-wrong near-dated stand-in.
    t = iv_tenors(["20260721", "20260722", "20260724"], today=date(2026, 7, 21))
    assert t["one_dte"] == "20260722"
    assert t["swing"] is None
    assert iv_tenors([], today=date(2026, 7, 21)) == {"one_dte": None, "swing": None}

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

def test_strategy_fit_condor_missing_iv_is_not_thin():
    # atm_iv=None means "no swing tenor in the chain", NOT "IV is 0%". It must
    # not masquerade as a genuine credit-too-thin avoid: same rating string
    # would make a data gap look like a real read.
    c = next(s for s in strategy_fit("positive", atm_iv=None) if s["name"] == "iron_condor")
    assert c["rating"] == "unknown"
    assert "0%" not in c["why"]              # never fabricate a 0% reading
    assert "unavailable" in c["why"].lower()
    # A real thin reading still avoids, and stays distinct from the None case.
    thin = next(s for s in strategy_fit("positive", atm_iv=0.10) if s["name"] == "iron_condor")
    assert thin["rating"] == "avoid" and "12%" in thin["why"]

def _t(**kw):
    """Minimal tenor dict with sensible defaults."""
    base = dict(net_gex_mm=None, flip=None, put_wall=None, pin=None, call_wall=None)
    base.update(kw)
    return base

def test_build_plan_normal_positive_uses_front_walls_and_swing_target():
    # Front sets today's put wall (support); swing pin is the target; front call is the fade level.
    tenors = {"front": _t(net_gex_mm=3000, put_wall=7550, pin=7600, call_wall=7650),
              "swing": _t(net_gex_mm=1500, flip=7580, put_wall=7500, pin=7620, call_wall=7700)}
    txt = " ".join(build_plan(regime="positive", tenors=tenors,
                              opex={"date": "2026-07-17", "dte": 4, "within_week": True},
                              migration={"note": "call wall rolled up +50"}))
    for token in ("Line in the sand: 7580", "Buy dips at 7550", "target 7620",
                  "fade rips into 7650", "OPEX", "rolled up"):
        assert token in txt, f"missing {token} in: {txt}"

def test_build_plan_collapsed_walls_becomes_magnet_not_three_of_same():
    # Regression for today's bug: put=pin=call=7500 must NOT render "buy 7500 target 7500 fade 7500".
    tenors = {"front": _t(net_gex_mm=-500, put_wall=7550, pin=7550, call_wall=7545),
              "swing": _t(net_gex_mm=600, flip=7575, put_wall=7500, pin=7500, call_wall=7500)}
    plan = build_plan(regime="positive", tenors=tenors, opex={"within_week": False}, migration=None)
    txt = " ".join(plan)
    assert "magnet" in txt.lower() and "7500" in txt
    # And the broken line must NOT be present
    assert "target 7500; fade" not in txt

def test_build_plan_flags_front_negative_divergence():
    # 0DTE short-gamma while swing is still positive = the trade IS the divergence.
    tenors = {"front": _t(net_gex_mm=-2000, put_wall=7550, pin=7550, call_wall=7545),
              "swing": _t(net_gex_mm=600, flip=7575, put_wall=7500, pin=7500, call_wall=7500)}
    txt = " ".join(build_plan(regime="positive", tenors=tenors,
                              opex={"within_week": False}, migration=None))
    assert "0DTE" in txt and "divergence" in txt and "7550" in txt

def test_build_plan_missing_front_still_produces_swing_plan():
    tenors = {"front": None,
              "swing": _t(net_gex_mm=1500, flip=7580, put_wall=7500, pin=7620, call_wall=7700)}
    txt = " ".join(build_plan(regime="positive", tenors=tenors,
                              opex={"within_week": False}, migration=None))
    assert "7580" in txt and ("7500" in txt or "7620" in txt)
