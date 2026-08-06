"""Join the auction read to the dealer read — the integrated reference map.

This is the module the rest of the project was missing. Our old "confluence" was
gamma against charm: two derivatives of the *same* dealer book, so agreement
between them was close to arithmetic. Market Profile levels come from price and
time alone and know nothing about the options chain, so when a TPOC and a charm
peak land on the same strike that is two independent instruments pointing at one
price.

Three rules this file exists to enforce:

1. **Independence is the whole claim.** Levels are tagged with which framework
   produced them, and a match is only reported as confluence when the two sides
   come from different frameworks. Two gamma levels agreeing is not evidence.
2. **Tolerance is a free parameter.** Whether 7,795 and 7,800 "agree" depends
   entirely on a number someone chose. It is an argument, defaulted once, and
   echoed in the output.
3. **Disagreement gets printed too.** `conflicts()` names where the two reads
   point opposite ways. A brief that only shows agreement has no way to be wrong.
"""
from __future__ import annotations

AUCTION = "auction"
OPTIONS = "options"

# Half a 5-point SPX strike interval: two levels inside this are indistinguishable
# at the resolution the strike grid offers.
DEFAULT_TOLERANCE = 5.0

# A wall carrying less than this share of the largest strike is the biggest
# on its side only because something has to be. The number is a judgement,
# not a finding: measured put walls have come in at 3% (clear noise) and 6%
# (arguable) on consecutive sessions, so it is an argument, not a constant
# buried in a branch.
THIN_WALL_FRAC = 0.10


def auction_levels(profile: dict) -> list[dict]:
    """Named price levels the session's profile produced, with what each means."""
    t = profile.get("tpo") or {}
    out: list[dict] = []

    def add(price, name, note):
        if isinstance(price, (int, float)):
            out.append({"price": float(price), "name": name, "framework": AUCTION,
                        "note": note})

    add(t.get("tpoc"), "TPOC", "most time — the session's fairest price")
    va = t.get("value_area") or {}
    add(va.get("high"), "value area high",
        f"top of the {va.get('covered', 0)*100:.0f}% band ({va.get('method')} method)")
    add(va.get("low"), "value area low",
        f"bottom of the {va.get('covered', 0)*100:.0f}% band ({va.get('method')} method)")
    ib = t.get("initial_balance") or {}
    add(ib.get("high"), "initial balance high", "top of the first two brackets")
    add(ib.get("low"), "initial balance low", "bottom of the first two brackets")

    pe = t.get("poor_extremes") or {}
    if pe.get("poor_high"):
        add(pe.get("high"), "poor high",
            f"{pe.get('high_tpos')} TPOs at the extreme — stopped without excess")
    if pe.get("poor_low"):
        add(pe.get("low"), "poor low",
            f"{pe.get('low_tpos')} TPOs at the extreme — stopped without excess")
    for side, label in (("buying", "buying tail"), ("selling", "selling tail")):
        tl = (t.get("tails") or {}).get(side)
        if tl and tl.get("significant"):
            add(tl["high"] if side == "selling" else tl["low"], label,
                f"{tl['length']} single prints — one-timeframe rejection")
    return out


def options_levels(gex: dict) -> list[dict]:
    """Named price levels the dealer book produced."""
    out: list[dict] = []

    def add(price, name, note):
        if isinstance(price, (int, float)):
            out.append({"price": float(price), "name": name, "framework": OPTIONS,
                        "note": note})

    add(gex.get("call_wall"), "call wall", "largest positive gamma above")
    add(gex.get("put_wall"), "put wall", "largest negative gamma below")
    add(gex.get("zero_gamma_flip"), "zero-gamma flip", "dampening above, amplifying below")
    add(gex.get("charm_peak_strike"), "charm peak", "largest delta drift to expiry")
    return out


def reference_map(auction: list[dict], options: list[dict],
                  tolerance: float = DEFAULT_TOLERANCE) -> list[dict]:
    """Every level, sorted high to low, with cross-framework matches attached.

    A row's `confluence` is True only when levels from BOTH frameworks sit inside
    `tolerance`. Levels that stand alone are kept — the map is the session's whole
    furniture, not a highlight reel.
    """
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    rows: list[dict] = []
    used: set[int] = set()
    for i, a in enumerate(auction + options):
        if i in used:
            continue
        group = [a]
        for j, b in enumerate(auction + options):
            if j <= i or j in used:
                continue
            if abs(b["price"] - a["price"]) <= tolerance:
                group.append(b)
                used.add(j)
        frameworks = {g["framework"] for g in group}
        rows.append({
            "price": sum(g["price"] for g in group) / len(group),
            "members": group,
            "frameworks": sorted(frameworks),
            "confluence": len(frameworks) > 1,
            "spread": max(g["price"] for g in group) - min(g["price"] for g in group),
            "tolerance": tolerance,
        })
    return sorted(rows, key=lambda r: -r["price"])


def conflicts(profile: dict, gex: dict, spot: float | None = None,
              thin_wall_frac: float = THIN_WALL_FRAC) -> list[dict]:
    """Where the two frameworks point opposite ways.

    Printed alongside the agreements on purpose. A read that only reports
    confluence cannot be contradicted by its own inputs, which makes it
    unfalsifiable by construction.
    """
    out: list[dict] = []
    t = profile.get("tpo") or {}
    va = t.get("value_area") or {}
    flip = gex.get("zero_gamma_flip")
    regime = gex.get("regime")

    # The dealer book says one regime; the auction says balance or imbalance.
    if isinstance(flip, (int, float)) and va.get("low") is not None:
        if flip < va["low"]:
            out.append({
                "issue": "flip sits below the value area",
                "detail": f"zero-gamma flip {flip:,.0f} is {va['low']-flip:,.0f} pts "
                          f"below the value-area low {va['low']:,.0f}. The options book "
                          f"calls the whole balance dampened; the auction's own floor is "
                          f"much higher and would break first.",
            })
        elif flip > va["high"]:
            out.append({
                "issue": "flip sits above the value area",
                "detail": f"zero-gamma flip {flip:,.0f} is above the value-area high "
                          f"{va['high']:,.0f} — the accepted range is entirely inside "
                          f"negative gamma.",
            })

    # An initial balance that never overlapped value means the day auctioned away
    # from where it opened; the options rails were set before that happened.
    ib = t.get("initial_balance") or {}
    if ib and va.get("low") is not None and va.get("high") is not None:
        if ib.get("low", 0) > va["high"] or ib.get("high", 0) < va["low"]:
            out.append({
                "issue": "initial balance does not overlap the value area",
                "detail": f"IB {ib['low']:,.0f}-{ib['high']:,.0f} vs value "
                          f"{va['low']:,.0f}-{va['high']:,.0f}. The session left where it "
                          f"opened and built value elsewhere — a directional day, not a "
                          f"balance, whatever the gamma regime says.",
            })

    # A wall so small it is an argmax over noise should not be read as support.
    # Strike keys arrive as "7400", "7400.0" or 7400.0 depending on who wrote the
    # file, so normalise to float rather than trusting any one spelling — a
    # missed lookup here would silently switch the check off on live data.
    ps = {float(k): v for k, v in (gex.get("per_strike_gex") or {}).items()}
    peak = max((abs(v) for v in ps.values()), default=None)
    for side, key in (("put", "put_wall"), ("call", "call_wall")):
        lvl = gex.get(key)
        mag = ps.get(float(lvl)) if isinstance(lvl, (int, float)) else None
        if lvl and mag is not None and peak:
            if abs(mag) < thin_wall_frac * peak:
                out.append({
                    "issue": f"{side} wall is an argmax over noise",
                    "detail": f"{lvl:,.0f} carries {abs(mag)/1e9:.2f}B, "
                              f"{abs(mag)/peak*100:.0f}% of the largest strike. It is the "
                              f"biggest on its side only because something has to be.",
                })
    return out


def strongest(rows: list[dict]) -> dict | None:
    """The single tightest cross-framework agreement.

    One sentence ranking the evidence is worth more than a table nobody reads to
    the bottom. Ties break toward the smaller spread, then the higher price.
    """
    conf = [r for r in rows if r["confluence"]]
    if not conf:
        return None
    return min(conf, key=lambda r: (r["spread"], -r["price"]))


def todays_business(profile: dict, gex: dict, spot: float | None = None) -> dict | None:
    """One question for the session, stated before it opens, with both branches.

    This is a fork, not a forecast: the read commits to what each outcome would
    MEAN, and the session settles which branch ran. The question is generated
    from where spot sits relative to yesterday's value area, because that is the
    auction's own frame: above value = acceptance being tested from above,
    below = from below, inside = balance until proven otherwise.
    """
    t = profile.get("tpo") or {}
    va = t.get("value_area") or {}
    if va.get("low") is None or va.get("high") is None:
        return None
    s = spot if isinstance(spot, (int, float)) else gex.get("spot")
    if not isinstance(s, (int, float)):
        return None
    tpoc = t.get("tpoc")
    call_wall, put_wall = gex.get("call_wall"), gex.get("put_wall")
    flip = gex.get("zero_gamma_flip")

    def lvl(x, name):
        return f"{name} {x:,.0f}" if isinstance(x, (int, float)) else None

    if s > va["high"]:
        return {
            "question": (f"Does price hold ABOVE yesterday's value area high "
                         f"{va['high']:,.0f} — i.e. is the up-auction being accepted?"),
            "holds": " → ".join(x for x in (
                f"acceptance above {va['high']:,.0f} keeps the up-auction alive",
                lvl(call_wall, "next objection is the call wall")) if x),
            "fails": " → ".join(x for x in (
                f"back inside value marks {s:,.0f} as rejected excess",
                lvl(tpoc, "first magnet is the TPOC"),
                lvl(va["low"], "then value area low")) if x),
            "frame": "above_value",
        }
    if s < va["low"]:
        return {
            "question": (f"Does price hold BELOW yesterday's value area low "
                         f"{va['low']:,.0f} — i.e. is the down-auction being accepted?"),
            "holds": " → ".join(x for x in (
                f"acceptance below {va['low']:,.0f} confirms the down-auction",
                lvl(flip, "gamma flips at"),
                lvl(put_wall, "put wall")) if x),
            "fails": " → ".join(x for x in (
                f"back inside value marks the break as a failed auction",
                lvl(tpoc, "first magnet is the TPOC")) if x),
            "frame": "below_value",
        }
    return {
        "question": (f"Spot opens INSIDE yesterday's value "
                     f"({va['low']:,.0f}–{va['high']:,.0f}) — does the balance hold?"),
        "holds": " → ".join(x for x in (
            f"rotation around {tpoc:,.0f}" if isinstance(tpoc, (int, float))
            else "two-sided rotation",
            "responsive trade at the edges") if x),
        "fails": " → ".join(x for x in (
            f"acceptance outside either edge starts a new auction",
            lvl(call_wall, "above, toward"),
            lvl(flip, "below, gamma flips at")) if x),
        "frame": "inside_value",
    }
