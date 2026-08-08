"""The machine's own view for a session, derived from the brief. Not an opinion.

A centaur needs both parties to state something scoreable. The machine's half has
to be produced the same way every day from measurements alone, or its hit rate
means nothing — a view that drifts with whoever generated it cannot be a record.

The rule below is deterministic and reads off two things the brief already
computes: which gamma regime spot sits in, and where spot sits relative to the
prior session's value area.

  positive gamma  dealers hedge INTO moves, damping them
  negative gamma  dealers hedge WITH moves, amplifying them

so the same location means different things in each regime. Inside value with
dealers long gamma is the textbook balance and gets `range`; the same place with
dealers short gamma is not balance, it is a coiled spring, and the view defers
to the auction's own direction instead.

Conviction is 1-3 and comes from **agreement between the two frameworks**, which
is the only thing in this project that has ever earned the word evidence: the
auction and the dealer book are independent inputs, and gamma agreeing with
charm is not.

This is a PREDICTION. It gets scored. It is not a recommendation and it sizes
nothing.
"""
from __future__ import annotations


def _band(spot: float, va: dict) -> str:
    if va.get("low") is None or va.get("high") is None:
        return "unknown"
    if spot > va["high"]:
        return "above"
    if spot < va["low"]:
        return "below"
    return "inside"


def machine_direction(snapshot: dict) -> dict:
    """Return {direction, conviction, rationale} or None when unreadable.

    Returns None rather than a guess when the inputs are missing: a fabricated
    view would pollute the very record the weights are computed from.
    """
    g = snapshot.get("gex") or {}
    spot = g.get("spot")
    flip = g.get("zero_gamma_flip")
    if not isinstance(spot, (int, float)) or not isinstance(flip, (int, float)):
        return None

    # The brief carries the prior session's value area inside todays_business's
    # frame; fall back to reading it off the profile join when present.
    va = {}
    for row in (snapshot.get("reference_map") or []):
        for m in row["members"]:
            if m["name"] == "value area high":
                va["high"] = m["price"]
            elif m["name"] == "value area low":
                va["low"] = m["price"]
    band = _band(spot, va)
    positive = spot >= flip

    # Conviction: cross-framework agreement is the only real evidence we have.
    confluent = sum(1 for r in (snapshot.get("reference_map") or [])
                    if r.get("confluence"))
    conviction = 1 + min(2, confluent)

    if positive:
        if band == "inside":
            d = "range"
            why = (f"spot {spot:,.0f} above the flip {flip:,.0f} (dealers long gamma, "
                   f"hedging damps) and inside the prior value area — balance on both reads")
        elif band == "above":
            d = "up"
            why = (f"spot {spot:,.0f} accepted above value in positive gamma — "
                   f"up-auction continuing, but dampened")
        elif band == "below":
            d = "down"
            why = (f"spot {spot:,.0f} below value while dealers are long gamma — "
                   f"down-auction, dampened")
        else:
            d = "range"
            why = f"positive gamma above the flip {flip:,.0f}; no value area to place spot against"
            conviction = 1
    else:
        # Below the flip, hedging amplifies. Location stops meaning balance.
        if band == "above":
            d = "up"
        elif band == "below":
            d = "down"
        else:
            d, conviction = "stand_aside", 1
            why = (f"spot {spot:,.0f} below the flip {flip:,.0f} — dealers short gamma, "
                   f"moves amplify — but spot sits inside value with no directional read")
            return {"direction": d, "conviction": conviction, "rationale": why}
        why = (f"spot {spot:,.0f} below the flip {flip:,.0f} (dealers short gamma, "
               f"hedging amplifies) and {band} the prior value area")

    return {"direction": d, "conviction": conviction, "rationale": why}
