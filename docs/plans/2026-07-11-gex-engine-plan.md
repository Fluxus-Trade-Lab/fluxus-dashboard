# Fluxus GEX Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A daily unattended pipeline that pulls SPX + QQQ option chains from IBKR, computes dealer-gamma structure (3 tenors), and emits versioned `data/gex/gex_YYYYMMDD.json` + a rendered HTML brief, committed to the repo.

**Architecture:** Pure-math core (`compute.py`, `derive.py`) with all IBKR I/O isolated in `ibkr.py`, assembled by `engine.py`, rendered by `render.py` (Jinja2). Outputs are dated JSON + HTML in `data/gex/`. Scheduled by launchd; IB Gateway + IBC provide headless auto-login.

**Tech Stack:** Python 3.14 (`.venv/` at repo root), `ib_async`, `pandas`, `jinja2`, `pytest`. Spec: `docs/plans/2026-07-11-gex-engine-design.md`.

**Conventions that matter (learned the hard way):**
- IBKR clientIds must be LOW (1–30); high IDs hang TWS.
- QQQ chains: filter to strikes that exist for the expiry (the chain lists 0.5 strikes that error).
- Sparse greeks (after-hours) must become `null` + a quality flag, never zeros.
- SPX index quote may be missing without a CBOE sub → fall back to SPY×10.

---

### Task 1: Scaffolding + dependencies

**Files:**
- Create: `pipeline/gex/__init__.py` (empty)
- Create: `tests/gex/__init__.py` (empty)
- Create: `data/gex/.gitkeep` (empty)

- [ ] **Step 1: Install deps into the repo venv**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System && .venv/bin/python -m pip install --quiet jinja2 pytest && .venv/bin/python -c "import jinja2, pytest; print('deps ok')"`
Expected: `deps ok`

- [ ] **Step 2: Create package dirs and empty files**

Run:
```bash
cd /Users/taolezhu/Documents/AI-Trading-System
mkdir -p pipeline/gex/templates tests/gex/fixtures data/gex scripts
touch pipeline/gex/__init__.py tests/gex/__init__.py data/gex/.gitkeep
```

- [ ] **Step 3: Copy the known-answer fixture**

The repo root has `esplan_20260710.csv` (a real ES chain pull with columns `strike,right,iv,delta,gamma,mid,oi`).

Run: `cp esplan_20260710.csv tests/gex/fixtures/chain_es_20260710.csv`

- [ ] **Step 4: Commit**

```bash
git add pipeline/gex tests/gex data/gex/.gitkeep
git commit -m "chore(gex): scaffold gex engine package"
```

---

### Task 2: `compute.py` — per-tenor gamma math (TDD)

**Files:**
- Create: `pipeline/gex/compute.py`
- Test: `tests/gex/test_compute.py`

**Contract:** `compute_tenor(df, spot, multiplier) -> dict`. `df` columns: `strike, right ('C'/'P'), gamma, oi, iv, mid` (NaN allowed). Returns the per-tenor metrics dict used by the schema. Dealer-side assumption (v1): dealers long calls / short puts → `net_gex_strike = (cgamma*coi − pgamma*poi) * mult * spot² * 0.01` (dollars per 1% move).

- [ ] **Step 1: Write the failing tests (hand-computed synthetic chain)**

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/gex/test_compute.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.gex.compute'`

- [ ] **Step 3: Implement `compute.py`**

```python
# pipeline/gex/compute.py
"""Pure gamma math for one instrument+tenor. No I/O.

Dealer-side assumption (v1, documented in schema): dealers are long calls and
short puts, so net GEX per strike = (call_gamma*call_oi - put_gamma*put_oi)
* multiplier * spot^2 * 0.01  (dollars per 1% underlying move).
"""
import math
import pandas as pd

GREEKS_MIN_COVERAGE = 0.5  # below this fraction of populated gammas → degraded


def _num(x):
    try:
        x = float(x)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def compute_tenor(df: pd.DataFrame, spot: float, multiplier: int) -> dict:
    C = df[df.right == "C"].set_index("strike").sort_index()
    P = df[df.right == "P"].set_index("strike").sort_index()
    ks = sorted(set(C.index) & set(P.index))

    gammas = [_num(g) for g in pd.concat([C["gamma"], P["gamma"]])]
    coverage = (sum(1 for g in gammas if g is not None) / len(gammas)) if gammas else 0.0
    degraded = coverage < GREEKS_MIN_COVERAGE

    # --- OI walls (always available; OI is a static daily figure) ---
    def top(side, n=5):
        s = side["oi"].map(_num).dropna()
        s = s[s > 0].sort_values(ascending=False).head(n)
        return [{"strike": float(k), "oi": int(v)} for k, v in s.items()]

    walls_top_calls, walls_top_puts = top(C), top(P)

    # --- ATM straddle / IV (works whenever mids/ivs are present) ---
    straddle = atm_iv = None
    if ks:
        atm = min(ks, key=lambda k: abs(k - spot))
        cm, pm = _num(C.loc[atm, "mid"]), _num(P.loc[atm, "mid"])
        if cm is not None and pm is not None and (cm + pm) > 0:
            straddle = cm + pm
        atm_iv = _num(C.loc[atm, "iv"])

    if degraded or not ks:
        cw = walls_top_calls[0]["strike"] if walls_top_calls else None
        pw = walls_top_puts[0]["strike"] if walls_top_puts else None
        return dict(net_gex_mm=None, flip=None, pin=None, vol_trigger=None,
                    call_wall=cw, put_wall=pw, wall_basis="oi_fallback",
                    straddle=straddle, atm_iv=atm_iv,
                    walls_top_calls=walls_top_calls, walls_top_puts=walls_top_puts,
                    greeks_coverage=round(coverage, 2), quality="degraded")

    # --- gamma-notional per strike ---
    net, absg, cnot, pnot = {}, {}, {}, {}
    scale = multiplier * spot * spot * 0.01
    for k in ks:
        cg = (_num(C.loc[k, "gamma"]) or 0.0) * (_num(C.loc[k, "oi"]) or 0.0)
        pg = (_num(P.loc[k, "gamma"]) or 0.0) * (_num(P.loc[k, "oi"]) or 0.0)
        cnot[k], pnot[k] = cg, pg
        net[k] = (cg - pg) * scale
        absg[k] = cg + pg

    total = sum(net.values())
    pin = max(absg, key=absg.get)
    call_wall = max(cnot, key=cnot.get)
    put_wall = max(pnot, key=pnot.get)

    # flip = cumulative-net-GEX zero crossing nearest to spot
    cum, crossings, prev = 0.0, [], None
    for k in ks:
        cum += net[k]
        if prev is not None and (prev < 0) != (cum < 0):
            crossings.append(k)
        prev = cum
    flip = min(crossings, key=lambda k: abs(k - spot)) if crossings else None

    # vol trigger (v1 heuristic): strongest positive-net-GEX strike in (put_wall, spot]
    cand = {k: v for k, v in net.items() if put_wall < k <= spot and v > 0}
    vol_trigger = max(cand, key=cand.get) if cand else flip

    return dict(net_gex_mm=round(total / 1e6, 3), flip=flip, pin=pin,
                vol_trigger=vol_trigger, call_wall=call_wall, put_wall=put_wall,
                wall_basis="gamma", straddle=straddle, atm_iv=atm_iv,
                walls_top_calls=walls_top_calls, walls_top_puts=walls_top_puts,
                greeks_coverage=round(coverage, 2), quality="ok")
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/gex/test_compute.py -q`
Expected: `3 passed`

- [ ] **Step 5: Add the real-chain smoke test (append to the same test file)**

```python
# append to tests/gex/test_compute.py
def test_real_es_chain_smoke():
    # Real pull from 2026-07-10 (ES, spot ~7570): regime was firmly POSITIVE.
    df = pd.read_csv("tests/gex/fixtures/chain_es_20260710.csv")
    m = compute_tenor(df, spot=7570.0, multiplier=50)
    assert m["quality"] == "ok"
    assert m["net_gex_mm"] > 1000            # strongly positive that day (+~2,900)
    assert 7500 <= m["pin"] <= 7650
    assert m["put_wall"] < 7570 < m["call_wall"] + 100
```

- [ ] **Step 6: Run tests**

Run: `.venv/bin/python -m pytest tests/gex/test_compute.py -q`
Expected: `4 passed`

- [ ] **Step 7: Commit**

```bash
git add pipeline/gex/compute.py tests/gex/test_compute.py tests/gex/fixtures/chain_es_20260710.csv
git commit -m "feat(gex): per-tenor gamma computation with quality flags"
```

---

### Task 3: `derive.py` — calendar, tenors, regime, migration, strategy fit (TDD)

**Files:**
- Create: `pipeline/gex/derive.py`
- Test: `tests/gex/test_derive.py`

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/gex/test_derive.py -q`
Expected: FAIL — module not found

- [ ] **Step 3: Implement `derive.py`**

```python
# pipeline/gex/derive.py
"""Deterministic derivations: tenor/OPEX calendar, regime, migration, strategy fit."""
from datetime import date, timedelta

SWING_WINDOW, SWING_TARGET = (5, 14), 9
MONTHLY_MIN_DTE = 15
IV_CONDOR_FLOOR = 0.12


def third_friday(year: int, month: int) -> date:
    d = date(year, month, 1)
    fridays = [d + timedelta(days=i) for i in range(31)
               if (d + timedelta(days=i)).month == month
               and (d + timedelta(days=i)).weekday() == 4]
    return fridays[2]


def _dte(expiry: str, today: date) -> int:
    return (date(int(expiry[:4]), int(expiry[4:6]), int(expiry[6:])) - today).days


def select_tenors(expiries: list[str], today: date) -> dict:
    exps = sorted(set(expiries))
    front = next((e for e in exps if 0 <= _dte(e, today) <= 2), None)
    lo, hi = SWING_WINDOW
    swing_c = [e for e in exps if lo <= _dte(e, today) <= hi]
    swing = min(swing_c, key=lambda e: abs(_dte(e, today) - SWING_TARGET)) if swing_c else None
    monthly = None
    y, m = today.year, today.month
    for _ in range(4):
        tf = third_friday(y, m)
        e = tf.strftime("%Y%m%d")
        if (tf - today).days >= MONTHLY_MIN_DTE and e in exps:
            monthly = e
            break
        m = 1 if m == 12 else m + 1
        y = y + 1 if m == 1 else y
    return {"front": front, "swing": swing, "monthly": monthly}


def opex_flag(today: date) -> dict:
    tf = third_friday(today.year, today.month)
    if tf < today:
        m = 1 if today.month == 12 else today.month + 1
        y = today.year + 1 if m == 1 else today.year
        tf = third_friday(y, m)
    dte = (tf - today).days
    return {"date": tf.isoformat(), "dte": dte, "within_week": dte <= 5}


def regime_of(net_gex_mm) -> str:
    if net_gex_mm is None:
        return "unknown"
    return "positive" if net_gex_mm > 0 else "negative"


def wall_migration(cur: dict, prior: dict | None) -> dict:
    if not prior:
        return {"call_wall": None, "put_wall": None, "flip": None,
                "note": "no prior day"}
    out, notes = {}, []
    for k in ("call_wall", "put_wall", "flip"):
        a, b = cur.get(k), prior.get(k)
        out[k] = round(a - b, 1) if (a is not None and b is not None) else None
    if out.get("call_wall") and out["call_wall"] > 0:
        notes.append(f"call wall rolled up +{out['call_wall']:.0f} (bullish tell)")
    if out.get("call_wall") and out["call_wall"] < 0:
        notes.append(f"call wall rolled down {out['call_wall']:.0f}")
    if out.get("put_wall") and out["put_wall"] > 0:
        notes.append(f"put wall raised +{out['put_wall']:.0f} (floor strengthening)")
    out["note"] = "; ".join(notes) if notes else "walls unchanged"
    return out


def strategy_fit(regime: str, atm_iv: float | None) -> list[dict]:
    """v1 rule table encoding the July-2026 validated rules."""
    pos = regime == "positive"
    iv = atm_iv or 0.0
    condor = ("avoid", "short-gamma risk in negative gamma") if not pos else \
             (("avoid", f"credit too thin (ATM IV {iv:.0%} < 12%)") if iv < IV_CONDOR_FLOOR
              else ("situational", "range supported, but lean with the drift"))
    return [
        dict(name="bull_put_spread",
             rating="favored" if pos else "caution",
             why="sell far-OTM below the put wall; floor + regime on-side" if pos
                 else "wait for a held floor before selling puts"),
        dict(name="dip_fade_call",
             rating="favored" if pos else "conditional",
             why="dips get bought in positive gamma; buy at put wall/pin" if pos
                 else "only at a major put wall with the leader confirming"),
        dict(name="iron_condor", rating=condor[0], why=condor[1]),
        dict(name="calendar_call_wall",
             rating="viable" if pos else "avoid",
             why="short near-term gamma wants a dampened grind" if pos
                 else "violent zig-zag chops the short leg"),
        dict(name="lotto_otm_call", rating="lotto",
             why="~6% hit rate for 4x; tiny size only, on violent reversals"),
        dict(name="naked_short_put", rating="avoid",
             why="undefined tail; use the defined-risk spread instead"),
    ]


def build_plan(regime, flip, put_wall, call_wall, pin, opex, migration) -> list[str]:
    p = []
    if flip:
        p.append(f"Line in the sand: {flip:.0f} — above = dampened grind; below = amplify, stand down.")
    if put_wall and (call_wall or pin):
        tgt = pin or call_wall
        p.append(f"Buy dips at the {put_wall:.0f} put wall → target {tgt:.0f}; fade strength into {call_wall:.0f}.")
    if regime == "negative" and put_wall:
        p.append(f"Negative gamma: no premium selling; breaks of {put_wall:.0f} accelerate.")
    if opex and opex.get("within_week"):
        p.append(f"OPEX {opex['date']} in {opex['dte']}d — monthly gamma rolls off; expect regime shift after.")
    if migration and migration.get("note") and "rolled up" in migration["note"]:
        p.append(f"Wall migration: {migration['note']}.")
    return p
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/gex/test_derive.py -q`
Expected: `7 passed`

- [ ] **Step 5: Commit**

```bash
git add pipeline/gex/derive.py tests/gex/test_derive.py
git commit -m "feat(gex): tenor/OPEX calendar, regime, wall migration, strategy-fit rules"
```

---

### Task 4: `schema.py` — assemble + validate `gex.json` v1 (TDD)

**Files:**
- Create: `pipeline/gex/schema.py`
- Test: `tests/gex/test_schema.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/gex/test_schema.py -q`
Expected: FAIL — module not found

- [ ] **Step 3: Implement `schema.py`**

```python
# pipeline/gex/schema.py
"""gex.json v1 — the data contract every consumer reads."""

VERSION = 1
TENOR_REQUIRED = {"expiry", "net_gex_mm", "flip", "pin", "vol_trigger",
                  "call_wall", "put_wall", "wall_basis", "straddle", "atm_iv",
                  "walls_top_calls", "walls_top_puts", "greeks_coverage",
                  "quality", "delta_vs_prior", "converted"}
TOP_REQUIRED = {"version", "asof", "stale", "opex", "instruments", "read",
                "strategy_fit", "assumptions"}


def build_document(asof, stale, stale_reason, opex, instruments, read,
                   strategy_fit) -> dict:
    return {
        "version": VERSION, "asof": asof, "stale": stale,
        "stale_reason": stale_reason, "opex": opex,
        "instruments": instruments, "read": read,
        "strategy_fit": strategy_fit,
        "assumptions": {
            "dealer_side": "long calls / short puts (v1 baseline heuristic)",
            "gex_formula": "(cgamma*coi - pgamma*poi) * mult * spot^2 * 0.01",
        },
    }


def validate(doc: dict) -> None:
    missing = TOP_REQUIRED - set(doc)
    if missing:
        raise ValueError(f"gex.json missing top-level keys: {sorted(missing)}")
    if doc["version"] != VERSION:
        raise ValueError(f"unsupported version {doc['version']}")
    for sym, inst in doc["instruments"].items():
        for req in ("spot", "basis", "tenors"):
            if req not in inst:
                raise ValueError(f"{sym}: missing '{req}'")
        for tname, tenor in inst["tenors"].items():
            if tenor is None:
                continue  # tenor may be unavailable (e.g., no 0-2DTE expiry)
            miss = TENOR_REQUIRED - set(tenor)
            if miss:
                raise ValueError(f"{sym}.{tname}: missing {sorted(miss)}")
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/gex/test_schema.py -q`
Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add pipeline/gex/schema.py tests/gex/test_schema.py
git commit -m "feat(gex): gex.json v1 schema build + validation"
```

---

### Task 5: `ibkr.py` — all IBKR I/O (chain pulls, quotes, bases)

**Files:**
- Create: `pipeline/gex/ibkr.py`

No unit tests (network module); Task 8 exercises it live. Keep ALL `ib_async` imports here so the math modules stay pure.

- [ ] **Step 1: Implement `ibkr.py`**

```python
# pipeline/gex/ibkr.py
"""All IBKR I/O for the GEX engine. Rules encoded here:
- LOW clientIds only (high IDs hang TWS after repeated sessions).
- Ports tried in order: IB Gateway live (4001), paper (4002), TWS (7496).
- SPX spot falls back to SPY*10 when the CBOE index quote is missing.
- QQQ: only request strikes that qualify (chain lists phantom .5 strikes).
"""
import math
import pandas as pd
from ib_async import IB, Stock, Index, Option, ContFuture

PORTS = (4001, 4002, 7496)
CLIENT_ID = 9
CHAIN_WIDTH = 0.035          # +/-3.5% of spot
SETTLE_SECONDS = 5

INSTRUMENTS = {
    "SPX": dict(kind="index", exch="CBOE", tclass="SPXW", strike_step=5,
                multiplier=100),
    "QQQ": dict(kind="stock", exch="SMART", tclass="QQQ", strike_step=1,
                multiplier=100),
}


def _num(x):
    try:
        x = float(x)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def _first(*vals):
    for v in vals:
        if _num(v) is not None:
            return float(v)
    return None


def connect(client_id: int = CLIENT_ID) -> IB:
    last = None
    for port in PORTS:
        try:
            ib = IB()
            ib.connect("127.0.0.1", port, clientId=client_id, timeout=15)
            return ib
        except Exception as e:      # noqa: BLE001 — try next port
            last = e
    raise ConnectionError(f"no IBKR endpoint on ports {PORTS}: {last}")


def underlier(symbol: str):
    cfg = INSTRUMENTS[symbol]
    return (Index(symbol, cfg["exch"], "USD") if cfg["kind"] == "index"
            else Stock(symbol, "SMART", "USD"))


def get_spot(ib: IB, symbol: str) -> float | None:
    u = underlier(symbol)
    ib.qualifyContracts(u)
    t = ib.reqTickers(u)[0]
    spot = _first(t.last, t.marketPrice(), t.close)
    if spot is None and symbol == "SPX":          # no CBOE index sub
        spy = Stock("SPY", "SMART", "USD")
        ib.qualifyContracts(spy)
        ts = ib.reqTickers(spy)[0]
        s = _first(ts.last, ts.marketPrice(), ts.close)
        spot = s * 10 if s else None
    return spot


def get_bases(ib: IB) -> dict:
    """Live conversion anchors: ES-SPX basis and NQ/QQQ ratio."""
    out = {}
    try:
        es = ContFuture("ES", "CME"); ib.qualifyContracts(es)
        spx = get_spot(ib, "SPX")
        t = ib.reqTickers(es)[0]
        esp = _first(t.last, t.marketPrice(), t.close)
        if esp and spx:
            out["ES_minus_SPX"] = round(esp - spx, 1)
    except Exception:                               # noqa: BLE001
        pass
    try:
        nq = ContFuture("NQ", "CME"); ib.qualifyContracts(nq)
        t = ib.reqTickers(nq)[0]
        nqp = _first(t.last, t.marketPrice(), t.close)
        qq = get_spot(ib, "QQQ")
        if nqp and qq:
            out["NQ_over_QQQ"] = round(nqp / qq, 3)
    except Exception:                               # noqa: BLE001
        pass
    return out


def get_expirations(ib: IB, symbol: str) -> list[str]:
    cfg = INSTRUMENTS[symbol]
    u = underlier(symbol)
    ib.qualifyContracts(u)
    sec = "IND" if cfg["kind"] == "index" else "STK"
    chains = ib.reqSecDefOptParams(u.symbol, "", sec, u.conId)
    ch = next((c for c in chains
               if c.tradingClass == cfg["tclass"]
               and c.exchange in ("SMART", cfg["exch"])), chains[0])
    return sorted(ch.expirations), ch


def pull_chain(ib: IB, symbol: str, expiry: str, spot: float) -> pd.DataFrame:
    cfg = INSTRUMENTS[symbol]
    _, ch = get_expirations(ib, symbol)
    lo, hi = spot * (1 - CHAIN_WIDTH), spot * (1 + CHAIN_WIDTH)
    step = cfg["strike_step"]
    strikes = sorted(k for k in ch.strikes
                     if lo <= k <= hi and float(k) == float(int(k // step) * step))
    opts = [Option(symbol, expiry, k, r, "SMART", tradingClass=cfg["tclass"])
            for k in strikes for r in ("C", "P")]
    opts = [o for o in ib.qualifyContracts(*opts) if getattr(o, "conId", None)]
    tickers = ib.reqTickers(*opts)
    handles = {o.conId: ib.reqMktData(o, "100,101", False, False) for o in opts}
    ib.sleep(SETTLE_SECONDS)
    rows = []
    for o, t in zip(opts, tickers):
        mg = t.modelGreeks
        h = handles[o.conId]
        rows.append(dict(
            strike=float(o.strike), right=o.right,
            gamma=_num(mg.gamma) if mg else None,
            iv=_num(mg.impliedVol) if mg else None,
            mid=_num(t.marketPrice()),
            oi=_num(h.callOpenInterest if o.right == "C" else h.putOpenInterest),
        ))
    for o in opts:
        ib.cancelMktData(o)
    return pd.DataFrame(rows)


if __name__ == "__main__":                          # manual smoke: needs IBKR up
    ib = connect()
    for sym in INSTRUMENTS:
        spot = get_spot(ib, sym)
        exps, _ = get_expirations(ib, sym)
        print(f"{sym}: spot={spot} expiries[:3]={exps[:3]}")
    print("bases:", get_bases(ib))
    ib.disconnect()
```

- [ ] **Step 2: Syntax check (no network)**

Run: `.venv/bin/python -c "import ast; ast.parse(open('pipeline/gex/ibkr.py').read()); print('parse ok')"`
Expected: `parse ok`

- [ ] **Step 3: Commit**

```bash
git add pipeline/gex/ibkr.py
git commit -m "feat(gex): IBKR I/O module (ports fallback, SPX/QQQ chain pulls, live bases)"
```

---

### Task 6: `render.py` + brief template (TDD golden-substring)

**Files:**
- Create: `pipeline/gex/render.py`
- Create: `pipeline/gex/templates/brief.html.j2`
- Test: `tests/gex/test_render.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/gex/test_render.py
from pipeline.gex.render import render_brief
from tests.gex.test_schema import tenor_stub

def make_doc(stale=False):
    from pipeline.gex.schema import build_document
    return build_document(
        asof="2026-07-11T08:00:00-04:00", stale=stale,
        stale_reason="pull failed" if stale else None,
        opex={"date": "2026-07-17", "dte": 6, "within_week": False},
        instruments={"SPX": {"spot": 7543.6, "basis": {"ES": 53.0},
                             "tenors": {"front": tenor_stub(),
                                        "swing": tenor_stub(),
                                        "monthly": tenor_stub()}}},
        read={"regime": "positive",
              "bull": ["floor held"], "bear": ["extended"],
              "plan": ["Line in the sand: 7590"]},
        strategy_fit=[{"name": "bull_put_spread", "rating": "favored",
                       "why": "floor + regime on-side"}])

def test_render_contains_key_values():
    html = render_brief(make_doc())
    # NOTE: the n0 filter renders thousands separators — assert "7,650" not "7650"
    for token in ("7543.6", "7,650", "7,550", "bull_put_spread", "favored",
                  "positive", "Line in the sand: 7590", "2026-07-17"):
        assert token in html, f"missing {token}"

def test_render_stale_banner():
    assert "STALE" in render_brief(make_doc(stale=True))
    assert "STALE" not in render_brief(make_doc(stale=False))
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/gex/test_render.py -q`
Expected: FAIL — module not found

- [ ] **Step 3: Implement `render.py`**

```python
# pipeline/gex/render.py
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

_env = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=False,           # we control all inputs; template emits raw numbers
)
_env.filters["n0"] = lambda v: f"{v:,.0f}" if v is not None else "—"
_env.filters["n2"] = lambda v: f"{v:,.2f}" if v is not None else "—"
_env.filters["pc"] = lambda v: f"{v:.0%}" if v is not None else "—"


def render_brief(doc: dict) -> str:
    return _env.get_template("brief.html.j2").render(d=doc)
```

- [ ] **Step 4: Create the template**

```html
{# pipeline/gex/templates/brief.html.j2 — populated ONLY from gex.json #}
<style>
:root{--bg:#0A0D13;--panel:#111621;--line:#1E2633;--txt:#C7CDD8;--mut:#79828F;
--dim:#525b69;--accent:#5AA9FF;--good:#42B96A;--bad:#EF5E6B;--warn:#D6A34C;
--mono:ui-monospace,Menlo,Consolas,monospace;
--sans:-apple-system,"Segoe UI",system-ui,sans-serif}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--txt);font-family:var(--sans);margin:0;
padding:38px 20px 60px}
.doc{max-width:760px;margin:0 auto}
h1{font-size:26px;font-weight:600;margin:2px 0 6px}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.16em;
text-transform:uppercase;color:var(--accent);margin:0 0 10px}
.meta{font-family:var(--mono);font-size:12px;color:var(--dim);
border-top:1px solid var(--line);border-bottom:1px solid var(--line);
padding:10px 0;margin-top:12px;display:flex;justify-content:space-between;
flex-wrap:wrap;gap:8px}
.stale{background:rgba(239,94,107,.15);border:1px solid var(--bad);
color:#F4838C;font-family:var(--mono);padding:10px 14px;border-radius:8px;
margin-top:16px;font-weight:600}
section{margin-top:28px}
.lbl{font-family:var(--mono);font-size:11px;letter-spacing:.14em;
text-transform:uppercase;color:var(--mut);margin:0 0 12px;display:flex;
align-items:center;gap:10px}
.lbl::after{content:"";flex:1;height:1px;background:var(--line)}
table{width:100%;border-collapse:collapse;font-size:13px;
border:1px solid var(--line);border-radius:8px;overflow:hidden}
th{font-family:var(--mono);font-size:10px;letter-spacing:.1em;
text-transform:uppercase;color:var(--dim);text-align:left;padding:9px 12px;
background:#0E131C;border-bottom:1px solid var(--line)}
td{padding:9px 12px;border-bottom:1px solid var(--line);
font-variant-numeric:tabular-nums}
tr:last-child td{border-bottom:none}
.mono{font-family:var(--mono)}
.pos{color:var(--good)}.neg{color:#F4838C}.warn{color:#E0B463}
ul{margin:0;padding-left:18px}li{margin:0 0 8px;font-size:13px;line-height:1.55}
.foot{margin-top:32px;padding-top:12px;border-top:1px solid var(--line);
font-family:var(--mono);font-size:11px;color:var(--dim)}
</style>
<div class="doc">
<p class="eyebrow">Fluxus Desk · Dealer Positioning Research (auto-generated)</p>
<h1>GEX Daily Brief</h1>
<div class="meta"><span>{{ d.asof }}</span>
<span>OPEX {{ d.opex.date }} · {{ d.opex.dte }}d
{%- if d.opex.within_week %} · <b class="warn">GAMMA ROLL-OFF WEEK</b>{% endif %}</span>
<span>regime: <b class="{{ 'pos' if d.read.regime=='positive' else 'neg' }}">
{{ d.read.regime }}</b></span></div>
{% if d.stale %}<div class="stale">STALE DATA — {{ d.stale_reason }} —
levels below are from the last good run.</div>{% endif %}

{% for sym, inst in d.instruments.items() %}
<section><p class="lbl">{{ sym }} · spot {{ inst.spot }}
{%- for b, v in inst.basis.items() %} · {{ b }} basis {{ v }}{% endfor %}</p>
<table><thead><tr><th>tenor</th><th>expiry</th><th>net GEX $mm</th><th>flip</th>
<th>vol trig</th><th>put wall</th><th>pin</th><th>call wall</th>
<th>straddle</th><th>IV</th><th>Δ call wall</th></tr></thead><tbody>
{% for tname in ["front","swing","monthly"] %}{% set t = inst.tenors.get(tname) %}
{% if t %}<tr class="mono"><td>{{ tname }}</td><td>{{ t.expiry }}</td>
<td class="{{ 'pos' if t.net_gex_mm and t.net_gex_mm>0 else 'neg' }}">
{{ t.net_gex_mm|n0 }}{% if t.quality!='ok' %} <span class="warn">({{ t.quality }})</span>{% endif %}</td>
<td>{{ t.flip|n0 }}</td><td>{{ t.vol_trigger|n0 }}</td>
<td class="pos">{{ t.put_wall|n0 }}</td><td>{{ t.pin|n0 }}</td>
<td class="neg">{{ t.call_wall|n0 }}</td><td>±{{ t.straddle|n2 }}</td>
<td>{{ t.atm_iv|pc }}</td>
<td>{{ t.delta_vs_prior.call_wall|n0 if t.delta_vs_prior else '—' }}</td>
</tr>
{% if t.converted %}<tr><td></td><td colspan="10" style="color:var(--mut)">
{% for csym, lv in t.converted.items() %}{{ csym }}: flip {{ lv.flip|n0 }},
put wall {{ lv.put_wall|n0 }}, call wall {{ lv.call_wall|n0 }} &nbsp; {% endfor %}
</td></tr>{% endif %}
{% endif %}{% endfor %}
</tbody></table></section>
{% endfor %}

<section><p class="lbl">Strategy fit</p>
<table><thead><tr><th>structure</th><th>rating</th><th>why</th></tr></thead><tbody>
{% for s in d.strategy_fit %}<tr><td class="mono">{{ s.name }}</td>
<td class="{{ 'pos' if s.rating in ('favored','go','viable') else ('neg' if s.rating=='avoid' else 'warn') }}">
{{ s.rating }}</td><td style="color:var(--mut)">{{ s.why }}</td></tr>{% endfor %}
</tbody></table></section>

<section><p class="lbl">The read</p>
<b class="pos">Bull</b><ul>{% for x in d.read.bull %}<li>{{ x }}</li>{% endfor %}</ul>
<b class="neg">Bear</b><ul>{% for x in d.read.bear %}<li>{{ x }}</li>{% endfor %}</ul>
</section>

<section><p class="lbl">The plan</p>
<ul>{% for x in d.read.plan %}<li>{{ x }}</li>{% endfor %}</ul></section>

<p class="foot">Fluxus internal · not investment advice ·
assumptions: {{ d.assumptions.dealer_side }} · v{{ d.version }}</p>
</div>
```

- [ ] **Step 5: Run tests**

Run: `.venv/bin/python -m pytest tests/gex/test_render.py -q`
Expected: `2 passed`

- [ ] **Step 6: Commit**

```bash
git add pipeline/gex/render.py pipeline/gex/templates/brief.html.j2 tests/gex/test_render.py
git commit -m "feat(gex): brief renderer + template"
```

---

### Task 7: `engine.py` — orchestrator with stale handling + git publish

**Files:**
- Create: `pipeline/gex/engine.py`
- Test: `tests/gex/test_engine_offline.py`

- [ ] **Step 1: Write the failing offline e2e test**

The engine must support `--offline-fixture <csv>` (uses the fixture chain for every tenor, spot from CLI) so the full assemble→write→render path is testable without IBKR.

```python
# tests/gex/test_engine_offline.py
import json
from pathlib import Path
from pipeline.gex.engine import run

def test_offline_end_to_end(tmp_path):
    out = run(out_dir=tmp_path, offline_fixture="tests/gex/fixtures/chain_es_20260710.csv",
              offline_spot=7570.0, do_git=False)
    latest = json.loads((tmp_path / "latest.json").read_text())
    assert latest["version"] == 1
    assert latest["stale"] is False
    spx = latest["instruments"]["SPX"]
    assert spx["tenors"]["swing"]["net_gex_mm"] is not None
    assert (tmp_path / "latest.html").exists()
    dated = list(tmp_path.glob("gex_*.json"))
    assert len(dated) == 1
    assert out["ok"] is True

def test_offline_stale_on_missing_fixture(tmp_path):
    # First produce a good run, then force a failure → stale copy of last good
    run(out_dir=tmp_path, offline_fixture="tests/gex/fixtures/chain_es_20260710.csv",
        offline_spot=7570.0, do_git=False)
    out = run(out_dir=tmp_path, offline_fixture="tests/gex/fixtures/DOES_NOT_EXIST.csv",
              offline_spot=7570.0, do_git=False)
    latest = json.loads((tmp_path / "latest.json").read_text())
    assert latest["stale"] is True and latest["stale_reason"]
    assert out["ok"] is False
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/gex/test_engine_offline.py -q`
Expected: FAIL — module not found

- [ ] **Step 3: Implement `engine.py`**

```python
# pipeline/gex/engine.py
"""Orchestrator: pull → compute → derive → schema → write → render → publish."""
import argparse
import json
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from pipeline.gex import compute, derive, render, schema

OUT_DIR = Path("data/gex")
INSTR_MULT = {"SPX": 100, "QQQ": 100}


def _prior_doc(out_dir: Path, today_tag: str):
    older = sorted(p for p in out_dir.glob("gex_*.json") if today_tag not in p.name)
    if not older:
        return None
    try:
        return json.loads(older[-1].read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _convert(sym: str, tenor: dict, bases: dict) -> dict:
    lv = {k: tenor.get(k) for k in ("flip", "put_wall", "call_wall", "pin")}
    out = {}
    if sym == "SPX":
        b = bases.get("ES_minus_SPX")
        if b is not None:
            out["ES"] = {k: (v + b if v is not None else None) for k, v in lv.items()}
        out["SPY"] = {k: (round(v / 10, 1) if v is not None else None)
                      for k, v in lv.items()}
    if sym == "QQQ":
        r = bases.get("NQ_over_QQQ")
        if r is not None:
            out["NQ"] = {k: (round(v * r) if v is not None else None)
                         for k, v in lv.items()}
    return out


def _assemble(chains: dict, spots: dict, bases: dict,
              out_dir: Path, today: date) -> dict:
    today_tag = today.strftime("%Y%m%d")
    prior = _prior_doc(out_dir, today_tag)
    instruments, primary = {}, None
    for sym, tenors in chains.items():
        spot = spots[sym]
        tdocs = {}
        for tname, (expiry, df) in tenors.items():
            if df is None:
                tdocs[tname] = None
                continue
            m = compute.compute_tenor(df, spot=spot, multiplier=INSTR_MULT[sym])
            m["expiry"] = expiry
            prior_t = None
            if prior:
                prior_t = (prior.get("instruments", {}).get(sym, {})
                           .get("tenors", {}).get(tname))
            m["delta_vs_prior"] = derive.wall_migration(m, prior_t)
            m["converted"] = _convert(sym, m, bases)
            tdocs[tname] = m
        instruments[sym] = {"spot": round(spot, 2), "basis": bases,
                            "tenors": tdocs}
        if sym == "SPX" and tdocs.get("swing"):
            primary = tdocs["swing"]

    regime = derive.regime_of(primary["net_gex_mm"] if primary else None)
    opex = derive.opex_flag(today)
    plan = derive.build_plan(
        regime=regime,
        flip=primary.get("flip") if primary else None,
        put_wall=primary.get("put_wall") if primary else None,
        call_wall=primary.get("call_wall") if primary else None,
        pin=primary.get("pin") if primary else None,
        opex=opex,
        migration=primary.get("delta_vs_prior") if primary else None)
    read = {"regime": regime,
            "bull": [f"net GEX {primary['net_gex_mm']:+,.0f} $mm — dips get bought"]
                    if regime == "positive" and primary else [],
            "bear": [f"net GEX {primary['net_gex_mm']:+,.0f} $mm — moves amplify"]
                    if regime == "negative" and primary else [],
            "plan": plan}
    fit = derive.strategy_fit(regime,
                              primary.get("atm_iv") if primary else None)
    return schema.build_document(
        asof=datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        stale=False, stale_reason=None, opex=opex, instruments=instruments,
        read=read, strategy_fit=fit)


def _write(doc: dict, out_dir: Path, today: date) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = today.strftime("%Y%m%d")
    (out_dir / f"gex_{tag}.json").write_text(json.dumps(doc, indent=1))
    (out_dir / "latest.json").write_text(json.dumps(doc, indent=1))
    html = render.render_brief(doc)
    (out_dir / f"brief_{tag}.html").write_text(html)
    (out_dir / "latest.html").write_text(html)


def _mark_stale(out_dir: Path, reason: str, today: date) -> None:
    latest = out_dir / "latest.json"
    if not latest.exists():
        return
    doc = json.loads(latest.read_text())
    doc["stale"], doc["stale_reason"] = True, reason
    _write(doc, out_dir, today)


def _git_publish(out_dir: Path, today: date, push: bool) -> None:
    try:
        subprocess.run(["git", "add", str(out_dir)], check=True)
        subprocess.run(["git", "commit", "-m",
                        f"chore(gex): daily gex data {today.isoformat()}"],
                       check=True)
        if push:
            subprocess.run(["git", "push"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[gex] git publish skipped/failed: {e}")  # never kill the run


def run(out_dir=OUT_DIR, offline_fixture=None, offline_spot=None,
        do_git=True, push=True) -> dict:
    out_dir = Path(out_dir)
    today = date.today()
    try:
        if offline_fixture:
            df = pd.read_csv(offline_fixture)
            expiry = "20260717"
            chains = {"SPX": {t: (expiry, df) for t in ("front", "swing", "monthly")}}
            spots = {"SPX": offline_spot}
            bases = {"ES_minus_SPX": 53.0}
        else:
            from pipeline.gex import ibkr
            ib = ibkr.connect()
            try:
                chains, spots = {}, {}
                bases = ibkr.get_bases(ib)
                for sym in ibkr.INSTRUMENTS:
                    spot = ibkr.get_spot(ib, sym)
                    if spot is None:
                        raise RuntimeError(f"no spot for {sym}")
                    exps, _ = ibkr.get_expirations(ib, sym)
                    tmap = derive.select_tenors(exps, today)
                    chains[sym] = {
                        t: ((e, ibkr.pull_chain(ib, sym, e, spot)) if e else (None, None))
                        for t, e in tmap.items()}
                    spots[sym] = spot
            finally:
                ib.disconnect()
        doc = _assemble(chains, spots, bases, out_dir, today)
        schema.validate(doc)
        _write(doc, out_dir, today)
        if do_git:
            _git_publish(out_dir, today, push)
        return {"ok": True}
    except Exception as e:                          # noqa: BLE001
        print(f"[gex] RUN FAILED: {e}")
        _mark_stale(out_dir, f"{type(e).__name__}: {e}", today)
        if do_git:
            _git_publish(out_dir, today, push)
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_DIR))
    ap.add_argument("--offline-fixture")
    ap.add_argument("--offline-spot", type=float)
    ap.add_argument("--no-git", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    a = ap.parse_args()
    result = run(out_dir=a.out, offline_fixture=a.offline_fixture,
                 offline_spot=a.offline_spot, do_git=not a.no_git,
                 push=not a.no_push)
    raise SystemExit(0 if result["ok"] else 1)
```

- [ ] **Step 4: Run the offline tests**

Run: `.venv/bin/python -m pytest tests/gex/test_engine_offline.py -q`
Expected: `2 passed`

- [ ] **Step 5: Run the full suite**

Run: `.venv/bin/python -m pytest tests/gex -q`
Expected: all pass (compute 4, derive 7, schema 2, render 2, engine 2 = 17)

- [ ] **Step 6: Commit**

```bash
git add pipeline/gex/engine.py tests/gex/test_engine_offline.py
git commit -m "feat(gex): engine orchestrator with offline mode, stale handling, git publish"
```

---

### Task 8: Live integration run (requires TWS or Gateway running)

**Files:** none (produces `data/gex/*`)

- [ ] **Step 1: Confirm an IBKR endpoint is up** (user: TWS on 7496 works today; Gateway later)

Run: `.venv/bin/python pipeline/gex/ibkr.py`
Expected: prints SPX + QQQ spots, first expiries, and bases. If `ConnectionError`, ask the user to start TWS/Gateway and retry.

- [ ] **Step 2: Full live run without pushing**

Run: `.venv/bin/python -m pipeline.gex.engine --no-push`
Expected: exit 0; `data/gex/latest.json`, `gex_YYYYMMDD.json`, `latest.html`, `brief_YYYYMMDD.html` created; one commit `chore(gex): daily gex data ...` on the branch.

- [ ] **Step 3: Sanity-review the output with the user**

Run: `.venv/bin/python -c "import json; d=json.load(open('data/gex/latest.json')); s=d['instruments']['SPX']['tenors']['swing']; print(d['read']['regime'], s['net_gex_mm'], s['flip'], s['put_wall'], s['call_wall'])"`
Expected: values consistent with the current market picture (cross-check against the most recent manual pull in the session). **Open `data/gex/latest.html` and have the user eyeball the brief.**

- [ ] **Step 4: Push**

```bash
git push
```

---

### Task 9: Scheduling + unattended infra docs

**Files:**
- Create: `scripts/run_gex_engine.sh`
- Create: `docs/gex-engine-setup.md`
- Create: `~/Library/LaunchAgents/com.fluxus.gex-engine.plist` (outside repo)

- [ ] **Step 1: Create the runner script**

```bash
#!/bin/zsh
# scripts/run_gex_engine.sh — launchd entrypoint for the daily GEX run.
set -u
REPO="/Users/taolezhu/Documents/AI-Trading-System"
LOG="$REPO/data/gex/engine.log"
cd "$REPO" || exit 1
echo "=== gex run $(date -u +%FT%TZ) ===" >> "$LOG"
"$REPO/.venv/bin/python" -m pipeline.gex.engine >> "$LOG" 2>&1
echo "=== exit $? ===" >> "$LOG"
```

Run: `chmod +x scripts/run_gex_engine.sh`

- [ ] **Step 2: Create the launchd plist**

Note: launchd uses **local time**. This Mac runs on JST; 8:00am ET (EDT) = **21:00 JST**. Adjust `Hour` if the Mac's timezone differs or when US DST shifts (EST = 22:00 JST).

Write to `~/Library/LaunchAgents/com.fluxus.gex-engine.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.fluxus.gex-engine</string>
  <key>ProgramArguments</key><array>
    <string>/Users/taolezhu/Documents/AI-Trading-System/scripts/run_gex_engine.sh</string>
  </array>
  <key>StartCalendarInterval</key><array>
    <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>21</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Weekday</key><integer>2</integer><key>Hour</key><integer>21</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Weekday</key><integer>3</integer><key>Hour</key><integer>21</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Weekday</key><integer>4</integer><key>Hour</key><integer>21</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Weekday</key><integer>5</integer><key>Hour</key><integer>21</integer><key>Minute</key><integer>0</integer></dict>
  </array>
  <key>StandardErrorPath</key><string>/tmp/com.fluxus.gex-engine.err</string>
</dict></plist>
```

Run: `launchctl load ~/Library/LaunchAgents/com.fluxus.gex-engine.plist && launchctl list | grep fluxus.gex`
Expected: the job appears in the list.

- [ ] **Step 3: Write the setup doc (Gateway + IBC)**

Create `docs/gex-engine-setup.md` with this content:

```markdown
# GEX Engine — Unattended Setup (IB Gateway + IBC)

The engine tries ports 4001 (Gateway live) → 4002 (Gateway paper) → 7496 (TWS).
It works with TWS today; Gateway+IBC makes it unattended.

## 1. Install IB Gateway (stable channel)
Download "IB Gateway — Stable" from interactivebrokers.com → Trading → API.
Install to /Applications. Log in once manually; under Configure → Settings → API:
enable ActiveX/Socket clients, Read-Only API, trusted IP 127.0.0.1, port 4001.

## 2. Install IBC (auto-login / dialog handling)
https://github.com/IbcAlpha/IBC → download the latest macOS release zip,
unzip to /opt/ibc. Edit /opt/ibc/config.ini:
    IbLoginId=<your username>
    IbPassword=<password>            # or leave blank to type once per boot
    TradingMode=live
    AcceptIncomingConnectionAction=accept
    ExistingSessionDetectedAction=primary
    AutoRestartTime=08:35 PM         # before the 21:00 JST run
Then make /opt/ibc/gatewaystartmacos.sh executable and test it: Gateway should
start and log in with no dialogs.

## 3. Keep Gateway alive
Create a second LaunchAgent (com.fluxus.ibgateway.plist) with
KeepAlive=true and RunAtLoad=true pointing at gatewaystartmacos.sh, OR add
Gateway to Login Items. IBC handles the daily re-auth/restart dialogs.

## 4. The daily engine job
com.fluxus.gex-engine.plist runs scripts/run_gex_engine.sh weekdays 21:00 JST
(= 8:00am EDT; change Hour to 22 during EST). Logs: data/gex/engine.log.

## 5. Failure behavior
If the pull fails, the engine republishes the last good JSON/brief with
stale=true and a red STALE banner, and still commits (the archive records the
gap). Fix = make sure Gateway is up, rerun manually:
    .venv/bin/python -m pipeline.gex.engine
```

- [ ] **Step 4: Commit**

```bash
git add scripts/run_gex_engine.sh docs/gex-engine-setup.md
git commit -m "feat(gex): launchd runner + unattended Gateway/IBC setup docs"
```

---

### Task 10: Wire-up finish — memory + playbook pointers

**Files:**
- Modify: `/Users/taolezhu/.claude/projects/-Users-taolezhu-Documents-AI-Trading-System/memory/project_gex_levels.md` (add pointer) — or MEMORY.md entry
- Modify: `docs/spx-0dte-july-dip-buy-playbook.md` (tooling section)

- [ ] **Step 1: Add engine pointer to the playbook tooling section**

In `docs/spx-0dte-july-dip-buy-playbook.md` §8, append:

```markdown
- `pipeline/gex/` — **GEX engine** (daily 8am ET auto-run): SPX+QQQ dealer-gamma
  structure → `data/gex/latest.json` + HTML brief. See
  `docs/plans/2026-07-11-gex-engine-design.md` and `docs/gex-engine-setup.md`.
```

- [ ] **Step 2: Update memory** — add one line to the auto-memory `MEMORY.md` Trading Strategies section:

```markdown
- GEX Engine — `pipeline/gex/` daily auto brief (SPX+QQQ, 3 tenors) → `data/gex/latest.json`; design: docs/plans/2026-07-11-gex-engine-design.md
```

- [ ] **Step 3: Final full test run + commit**

Run: `.venv/bin/python -m pytest tests/gex -q`
Expected: all pass.

```bash
git add docs/spx-0dte-july-dip-buy-playbook.md
git commit -m "docs: point playbook at the GEX engine"
```
