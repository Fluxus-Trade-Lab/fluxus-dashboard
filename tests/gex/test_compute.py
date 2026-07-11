# tests/gex/test_compute.py
import math
import pandas as pd
import pytest
from pipeline.gex.compute import compute_tenor

def synthetic_chain():
    # strikes 90/100/110, spot 100, mult 100 — hand-computed expectations:
    # net GEX per strike ($): 90: (0.01*100-0.02*300)*100*100^2*0.01 = -50_000
    #                        100: (0.03*200-0.03*100)*10_000       = +30_000
    #                        110: (0.02*400-0.01*50)*10_000        = +75_000
    # total +55_000 → +0.055 $mm ; cum(-50k,-20k,+55k) flips at 110 → flip=110
    # pin = max(cg*coi+pg*poi) → 100 (9.0) ; call_wall = max cg*coi → 110 (8.0)
    # put_wall = max pg*poi → 90 (6.0) ; vol_trigger = max net>0 strike in (90,100] → 100
    rows = [
        dict(strike=90.0,  right="C", gamma=0.01, oi=100, iv=0.20, mid=11.0),
        dict(strike=90.0,  right="P", gamma=0.02, oi=300, iv=0.22, mid=0.5),
        dict(strike=100.0, right="C", gamma=0.03, oi=200, iv=0.15, mid=5.0),
        dict(strike=100.0, right="P", gamma=0.03, oi=100, iv=0.16, mid=4.0),
        dict(strike=110.0, right="C", gamma=0.02, oi=400, iv=0.14, mid=1.0),
        dict(strike=110.0, right="P", gamma=0.01, oi=50,  iv=0.18, mid=10.5),
    ]
    return pd.DataFrame(rows)

def test_synthetic_known_answers():
    m = compute_tenor(synthetic_chain(), spot=100.0, multiplier=100)
    assert m["quality"] == "ok"
    assert math.isclose(m["net_gex_mm"], 0.055, rel_tol=1e-9)
    assert m["flip"] == 110.0
    assert m["pin"] == 100.0
    assert m["call_wall"] == 110.0
    assert m["put_wall"] == 90.0
    assert m["vol_trigger"] == 100.0
    assert math.isclose(m["straddle"], 9.0)
    assert math.isclose(m["atm_iv"], 0.15)
    assert m["greeks_coverage"] == 1.0

def test_sparse_greeks_degrade_not_zero():
    df = synthetic_chain()
    df["gamma"] = float("nan")          # after-hours: no greeks
    m = compute_tenor(df, spot=100.0, multiplier=100)
    assert m["quality"] == "degraded"
    assert m["net_gex_mm"] is None       # never a fake 0
    assert m["flip"] is None and m["vol_trigger"] is None
    # walls fall back to OI
    assert m["call_wall"] == 110.0 and m["put_wall"] == 90.0
    assert m["wall_basis"] == "oi_fallback"

def test_walls_top_lists():
    m = compute_tenor(synthetic_chain(), spot=100.0, multiplier=100)
    assert m["walls_top_calls"][0]["strike"] == 110.0
    assert m["walls_top_puts"][0]["strike"] == 90.0

# append to tests/gex/test_compute.py
def test_real_es_chain_smoke():
    # Real pull from 2026-07-10 (ES, spot ~7570, ±0.5%/+1% strike band 7535-7650):
    # regime was firmly POSITIVE. Values verified against the raw CSV before planning.
    df = pd.read_csv("tests/gex/fixtures/chain_es_20260710.csv")
    m = compute_tenor(df, spot=7570.0, multiplier=50)
    assert m["quality"] == "ok"
    assert m["net_gex_mm"] > 1000            # strongly positive (~3,972 for this band)
    assert m["pin"] == 7600.0                # abs-gamma magnet
    assert m["call_wall"] == 7600.0
    assert m["put_wall"] == 7580.0           # near-ATM high-gamma put in this narrow chain
    assert 7535.0 <= m["put_wall"] <= m["call_wall"] <= 7650.0
