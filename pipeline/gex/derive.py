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


def iv_tenors(expiries: list[str], today: date) -> dict:
    """Expiries whose ATM IV is fit to feed the strategy rules.

    Deliberately excludes 0DTE. Its IV spikes into expiry as sqrt(T) collapses,
    so it tracks the clock rather than the vol regime -- on 2026-07-21 the SPX
    0DTE printed 21.6% while every other tenor sat at 13-16%. Rules about
    multi-day structures must not read it.

    Returns the nearest forward expiry ("one_dte") and the swing tenor the rest
    of this module already targets ("swing"), either of which may be None when
    the chain does not reach that far.
    """
    exps = sorted(set(expiries))
    one_dte = next((e for e in exps if _dte(e, today) >= 1), None)
    lo, hi = SWING_WINDOW
    cands = [e for e in exps if lo <= _dte(e, today) <= hi]
    swing = min(cands, key=lambda e: abs(_dte(e, today) - SWING_TARGET)) if cands else None
    return {"one_dte": one_dte, "swing": swing}


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
    if out.get("put_wall") and out["put_wall"] < 0:
        notes.append(f"put wall dropped {out['put_wall']:.0f} (floor weakening)")
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


WALL_COLLAPSE_TOL = 0.01           # walls within 1% of each other → magnet


def _collapsed(t: dict | None) -> bool:
    """True when a tenor's put/pin/call walls are all within WALL_COLLAPSE_TOL."""
    if not t:
        return False
    lvls = [t.get(k) for k in ("put_wall", "pin", "call_wall")]
    if not all(lvls):
        return False
    return (max(lvls) - min(lvls)) / max(lvls) < WALL_COLLAPSE_TOL


def _g(t: dict | None, key: str):
    return None if t is None else t.get(key)


def build_plan(regime, tenors, opex, migration=None) -> list[str]:
    """Cross-tenor plan bullets. `tenors` is a dict with keys 'front'/'swing'/'monthly',
    each a compute_tenor() result or None. The old single-tenor form was ambiguous when
    walls collapsed onto one strike (put=pin=call → 'buy X target X fade X')."""
    p = []
    front, swing = tenors.get("front"), tenors.get("swing")

    # Line in the sand: prefer the swing flip (multi-day regime line), fall back to front.
    los = _g(swing, "flip") or _g(front, "flip")
    if los:
        p.append(f"Line in the sand: {los:.0f} — above = dampened grind; below = amplify, stand down.")

    # 0DTE divergence: front short-gamma while swing constructive → the trade IS the break.
    fg, sg = _g(front, "net_gex_mm"), _g(swing, "net_gex_mm")
    if fg is not None and sg is not None and fg < 0 and sg > 0:
        line = _g(front, "put_wall") or _g(front, "pin")
        if line:
            p.append(f"0DTE net GEX {fg:+,.0f} $mm vs swing {sg:+,.0f} — divergence: "
                     f"a break of {line:.0f} amplifies today.")

    # Support/target/resistance. If swing walls collapsed, emit magnet msg instead of the 3-level trade.
    if _collapsed(swing):
        magnet = _g(swing, "pin") or _g(swing, "put_wall")
        p.append(f"Weekly walls stacked at {magnet:.0f} — magnet trade; expect pin action, "
                 "low directional edge unless it breaks.")
    else:
        support = _g(front, "put_wall") or _g(swing, "put_wall")
        target = _g(swing, "pin") or _g(swing, "put_wall")
        resist = _g(front, "call_wall") or _g(swing, "call_wall")
        if support and target:
            tail = f"; fade rips into {resist:.0f}" if resist and resist != support else ""
            p.append(f"Buy dips at {support:.0f} put wall → target {target:.0f}{tail}.")

    if regime == "negative":
        wall = _g(swing, "put_wall") or _g(front, "put_wall")
        if wall:
            p.append(f"Negative gamma: no premium selling; breaks of {wall:.0f} accelerate.")

    if opex and opex.get("within_week"):
        p.append(f"OPEX {opex['date']} in {opex['dte']}d — monthly gamma rolls off; "
                 "expect regime shift after.")

    if migration and migration.get("note") and "rolled up" in migration["note"]:
        p.append(f"Wall migration: {migration['note']}.")

    return p
