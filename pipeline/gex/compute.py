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
    # OI matters as much as gamma: net GEX = gamma*OI, so missing OI silently zeroes
    # the notional. Gate on OI coverage too, else a greeks-present/OI-absent pull
    # collapses to a fake net_gex_mm=0.0 labeled "ok" (C1).
    ois = [_num(o) for o in pd.concat([C["oi"], P["oi"]])]
    oi_coverage = (sum(1 for o in ois if o is not None and o > 0) / len(ois)) if ois else 0.0
    degraded = coverage < GREEKS_MIN_COVERAGE or oi_coverage < GREEKS_MIN_COVERAGE

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
                    greeks_coverage=round(coverage, 2),
                    oi_coverage=round(oi_coverage, 2), quality="degraded")

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
                greeks_coverage=round(coverage, 2),
                oi_coverage=round(oi_coverage, 2), quality="ok")
