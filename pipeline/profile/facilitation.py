"""Did the market facilitate trade out there, or just print through it?

Built 2026-08-12 from the rule he stated that morning, ahead of CPI:

    "No trade until the market is facilitating trade ... that is, until price
    extends beyond the initial balance and BUILDS there, rather than merely
    printing through it on the headline."

CORRECTION, same day. This paragraph used to say TFF was "a ratio across TPO
expansion, tick activity and volume movement" and that we could not implement it
for want of tick data. Both halves were wrong, and reading Jones' 1988 paper
settled it: volume is explicitly NOT part of TFF, and his "ticks" are price ticks
traversed, not a trade tape. TFF is implemented in full in `tff.py`. This module
is the narrower rule -- initial-balance extension and acceptance -- which Jones
does not cover and which is a different question from how much trade the session
facilitated overall. The distinction it turns on:

    **extension** — price traded beyond the initial balance at all
    **acceptance** — price STAYED out there and built structure

A headline spike makes an extension and no acceptance. That case and a genuine
range extension look identical on a high/low, which is why a levels ladder
cannot tell them apart and why "levels alone are not enough to risk your money
on" is a statement about missing information, not about discipline.

Why this layer matters more than another indicator. Everything else in this
package DESCRIBES a session. This is the first thing that GATES on one — it
answers "is there anything to do yet", which is the question a description never
reaches. It also happens to be the kind of claim our own power arithmetic says
is settleable: range extension occurs most sessions, so occurrences accrue at
roughly the rate of the calendar rather than a few times a year.

Nothing here sizes or recommends. It reports whether the precondition a stated
rule requires was met, and how far from the line it landed when it was not.
"""
from __future__ import annotations

# Two free parameters, and after MIN_SCORED they do not get to sit here as bare
# numbers. Both were swept over 123 SPX sessions, 2026-02 to 2026-08:
#
#   share \ periods      1        2        3
#          0.25       92.7%    89.4%    84.6%     <- share of sessions the
#          0.50       85.4%    78.0%    74.8%        gate opens on
#          0.75       76.4%    74.8%    68.3%
#
# Smooth and monotone in both directions with no cliff, so the shipped 0.50/2 is
# not a picked point. It also says something the feature itself will not:
# **no setting turns this into a selective filter.** The gate opens on roughly
# three sessions in four whatever we choose.
#
# That is the honest reading. This is not a session-selection filter; it is a
# WITHIN-session timing gate, which is how he states it — "no trade UNTIL". The
# value is in the ~18% of sessions where price extended and never built, because
# those are indistinguishable from a real extension on a high/low and are
# exactly what the rule refuses.
MIN_BUILD_SHARE = 0.50
MIN_BUILT_PERIODS = 2

# Measured, not assumed. 123 SPX sessions: 61.8% facilitated, 18.7% two-sided,
# 17.9% extended-and-rejected, 1.6% never left the balance. SPY on the same 123
# sessions agrees 91.1% of the time — the 9% gap is the cost of our instrument
# choice, and it is a measurement rather than an argument.
BASE_RATE_SESSIONS = 123
BASE_RATE_GATE_OPENS = 0.780


def _side_extension(bars: list[dict], ib: dict, side: str) -> dict:
    """Everything about one side's extension: how far, when, and how much held.

    `bars` are the session's period bars in order, the same 30-minute brackets
    the profile is built from. Brackets inside the initial balance itself are
    excluded from the count -- the IB cannot extend beyond itself.
    """
    n_ib = ib["periods"]
    rest = bars[n_ib:]
    beyond = ib["high"] if side == "up" else ib["low"]

    extended, built, first_i, extreme = [], 0, None, None
    for i, b in enumerate(rest):
        out = (b["high"] > beyond) if side == "up" else (b["low"] < beyond)
        if not out:
            continue
        if first_i is None:
            first_i = i + n_ib + 1          # 1-indexed bracket number
        extended.append(i)
        # How much of this bracket's range lived beyond the line. A bracket that
        # merely tagged the level contributes almost nothing; one that traded
        # entirely outside contributes all of itself.
        span = b["high"] - b["low"]
        out_span = (b["high"] - beyond) if side == "up" else (beyond - b["low"])
        share = 1.0 if span <= 0 else max(0.0, min(1.0, out_span / span))
        if share >= MIN_BUILD_SHARE:
            built += 1
        e = b["high"] if side == "up" else b["low"]
        if extreme is None or (e > extreme if side == "up" else e < extreme):
            extreme = e

    return {
        "side": side, "reference": beyond,
        "extended": bool(extended),
        "n_periods_beyond": len(extended),
        "n_periods_built": built,
        "first_period": first_i,
        "extreme": extreme,
        "distance": (None if extreme is None else
                     round(abs(extreme - beyond), 4)),
        "accepted": built >= MIN_BUILT_PERIODS,
    }


def facilitation(bars: list[dict], ib: dict | None) -> dict | None:
    """Was the initial balance extended, and was the extension accepted?

    Returns a verdict per side plus a session-level `state`:

      ``no_extension``  price never left the initial balance
      ``rejected``      it left and did not build -- printed through
      ``facilitated``   it left and built there
      ``two_sided``     both sides extended; whether either was accepted is
                        reported per side and never averaged away

    `rejected` is deliberately not called "failed". A rejection is a completed
    auction result -- the market went to look and declined -- and naming it a
    failure would smuggle in a direction.
    """
    if not bars or not ib:
        return None
    up = _side_extension(bars, ib, "up")
    dn = _side_extension(bars, ib, "down")

    if up["extended"] and dn["extended"]:
        state = "two_sided"
    elif not up["extended"] and not dn["extended"]:
        state = "no_extension"
    else:
        side = up if up["extended"] else dn
        state = "facilitated" if side["accepted"] else "rejected"

    return {
        "state": state,
        "up": up, "down": dn,
        "initial_balance": {"low": ib["low"], "high": ib["high"],
                            "periods": ib["periods"]},
        "tradeable": (up["accepted"] or dn["accepted"]),
        "thresholds": {"min_build_share": MIN_BUILD_SHARE,
                       "min_built_periods": MIN_BUILT_PERIODS},
        "note": _explain(state, up, dn),
    }


def _explain(state: str, up: dict, dn: dict) -> str:
    """Plain sentence per branch.

    Built per-branch rather than assembled from a shared prefix. That shape has
    now let a correct check down three times in this project, most recently as
    "only an edge of no size is visible".
    """
    if state == "no_extension":
        return ("price never left the initial balance — no extension to accept "
                "or reject")
    if state == "two_sided":
        u = "accepted" if up["accepted"] else "rejected"
        d = "accepted" if dn["accepted"] else "rejected"
        return (f"both sides extended: up {u} ({up['n_periods_built']} brackets "
                f"built), down {d} ({dn['n_periods_built']} built)")
    side = up if up["extended"] else dn
    if state == "facilitated":
        return (f"{side['side']} extension accepted — {side['n_periods_built']} "
                f"brackets built beyond {side['reference']:,.2f}, "
                f"{side['distance']:,.2f} at the extreme")
    return (f"{side['side']} extension rejected — reached "
            f"{side['distance']:,.2f} beyond {side['reference']:,.2f} but only "
            f"{side['n_periods_built']} bracket(s) built there; the market went "
            f"to look and declined")


def gate(fac: dict | None, direction: str) -> dict:
    """His rule as a precondition on a directional idea. Never a recommendation.

    Answers only whether the stated precondition holds, and says what is missing
    when it does not. A `False` with no reason is the thing this project keeps
    refusing to ship.
    """
    if fac is None:
        return {"open": None, "reason": "no session structure — cannot say",
                "measurable": False}
    if direction not in ("up", "down"):
        raise ValueError("direction must be 'up' or 'down'")
    side = fac[direction]
    if not side["extended"]:
        return {"open": False, "measurable": True,
                "reason": f"no {direction} extension out of the initial balance yet"}
    if not side["accepted"]:
        return {"open": False, "measurable": True,
                "reason": (f"{direction} extended {side['distance']:,.2f} beyond "
                           f"{side['reference']:,.2f} but built only "
                           f"{side['n_periods_built']} of the "
                           f"{MIN_BUILT_PERIODS} brackets required")}
    return {"open": True, "measurable": True,
            "reason": (f"{direction} extension accepted — "
                       f"{side['n_periods_built']} brackets built beyond "
                       f"{side['reference']:,.2f}")}
