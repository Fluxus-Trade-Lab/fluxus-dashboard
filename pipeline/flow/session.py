"""One session's order-book read — the second opinion, from different data.

    "Hedging in the belt, speculating in both wings, and the two indices are
     running different books."          — @TailThatWagsDog, 2026-08-12 premarket

    "Watch whether the SPX belt bid repeats tomorrow. Today's session can be a
     single desk rebalancing; two, at today's size, suggests a campaign."
                                                        — same day, 16:15 ET

His app juxtaposes an auction read against a flow read. Ours could not do that
honestly, because both of our reads came out of the same chain snapshot — a
conflict between them could only ever have been a statement about our own
arithmetic, never about the market. This module is the half that comes from the
**tape**: settled prints, classified by which side lifted, aggregated in dollars.

## What this can and cannot say

It measures **what traded, where, and which side was the aggressor**. It does
not measure intent. "Hedging in the belt" is his reading, not a field: a put
bought at the belt is a hedge or a directional bet and the tape cannot tell you
which. So nothing here is named `hedging` or `speculating`, and the vocabulary
stops at what a print can support.

Blocks are `block.py`'s business and are thresholded on premium rather than lot
count, for reasons measured on 26,837 real prints there. Nothing here calls a
block institutional — institutions slice, and a 500-lot worked as fifty 10-lots
is invisible to any per-print rule.

## The aggressor side is often not available, and that is measured

Classifying which side lifted needs the contemporaneous NBBO on the same
contract. Measured on SPX 7750C for 2026-08-12:

    TRADES ticks     3,514   4 pages    1.9s   per contract
    BID_ASK ticks   60,648  60 pages    142s   per contract, still not finished

Eighty contracts of quote ticks is roughly three hours, so the exact method is
not affordable on a daily chain. The obvious cheap substitute -- 1-minute BID
and ASK bars, 1.6s per contract -- was tested against the tick NBBO on the same
769 overlapping prints:

    agreement 56.7%, against a 50% coin on a two-way call
    disagreements symmetric: 155 SOLD->BOT, 152 BOT->SOLD

**That is noise, not a cheaper measurement.** So the proxy is refused, and a
session pulled without quote ticks reports `sides_available: False` and every
side-dependent reading comes back `unknown`. His belt-bid question is one of
those. Saying "balanced" from unclassified prints would be inventing the
half we could not afford.

What IS affordable without quotes: premium per strike, block share, the
call/put split, and belt-versus-wings by premium. That is most of the read and
it is stated for what it is.

## Two pinned series, and why the slot is not the calendar

A read is of ONE expiry, and letting the puller take whatever expiry came first
is how the first three landed on 1DTE, 1DTE and 0DTE:

    2026-08-12   expiry 20260813   slot 1     69,100 prints   $2,783/print
    2026-08-13   expiry 20260814   slot 1    111,629 prints   $3,305/print
    2026-08-14   expiry 20260814   slot 0    792,338 prints   $1,140/print

Seven times the prints and a third the premium each. **That is not the market
changing, it is a different instrument** — a 0DTE on its own expiry day and a
1DTE are different books with different participants.

So two series are pinned and kept apart:

  ``tenor 0``   the expiry equal to the session date
  ``tenor 1``   the FIRST expiry strictly after it

**`tenor` is the slot and `dte` is the calendar**, and they are different on
purpose. A Friday's tenor-1 expires Monday — one expiry step, three calendar
days. Normalising that away would hide a real property of the instrument: a
weekend sits inside it, and a weekend is not nothing. `comparable()` therefore
keys on the SLOT, and `dte` rides along as the fact it is.

## Belt and wings

Defined on **moneyness**, not on a fixed number of points, so the split means
the same thing at 4,000 and at 7,800. The width is a free parameter and is
swept.
"""
from __future__ import annotations

from . import block as B

# Half-width of the belt as a fraction of spot. 1% of 7,750 is ~78 points,
# roughly the 0DTE expected move on a normal session — the region where dealers
# actually have to hedge. Swept in `sweep_belt`.
BELT_PCT = 0.01

SIDES = ("BOT", "SOLD", "UNKNOWN")


def _zone(strike: float, spot: float, belt_pct: float) -> str:
    if spot <= 0:
        return "unknown"
    m = strike / spot - 1.0
    if abs(m) <= belt_pct:
        return "belt"
    return "upper_wing" if m > 0 else "lower_wing"


def per_strike(prints: list[dict]) -> dict[float, dict]:
    """Premium bought and sold at each strike, with the block share.

    A print must carry `strike`, `price`, `size`, `side` and `right`. Prints the
    classifier could not call arrive as ``UNKNOWN`` and are kept in their own
    bucket rather than split, dropped, or assigned to the majority — an
    unclassifiable print is a fact about liquidity at that moment.
    """
    tagged = B.tag_prints(prints)
    acc: dict[float, dict] = {}
    for t in tagged:
        k = t.get("strike")
        if not isinstance(k, (int, float)):
            continue
        s = acc.setdefault(float(k), {
            "premium": 0.0, "bot_premium": 0.0, "sold_premium": 0.0,
            "unknown_premium": 0.0, "block_premium": 0.0,
            "call_premium": 0.0, "put_premium": 0.0,
            "n": 0, "n_block": 0})
        p = t["premium"]
        s["premium"] += p
        s["n"] += 1
        side = t.get("side")
        if side == "BOT":
            s["bot_premium"] += p
        elif side == "SOLD":
            s["sold_premium"] += p
        else:
            s["unknown_premium"] += p
        if t.get("right") == "C":
            s["call_premium"] += p
        elif t.get("right") == "P":
            s["put_premium"] += p
        if t["is_block"]:
            s["block_premium"] += p
            s["n_block"] += 1
    for s in acc.values():
        s["block_share"] = s["block_premium"] / s["premium"] if s["premium"] else None
        classified = s["bot_premium"] + s["sold_premium"]
        # Net lift as a share of the premium we could actually classify. Divided
        # by the classified total rather than by everything, so a session with
        # many unknown prints reports a weaker reading instead of a diluted one.
        s["net_lift"] = ((s["bot_premium"] - s["sold_premium"]) / classified
                         if classified else None)
        s["classified_share"] = classified / s["premium"] if s["premium"] else None
    return acc


def zones(strikes: dict[float, dict], spot: float,
          belt_pct: float = BELT_PCT) -> dict:
    """Belt versus wings, in his vocabulary and only as far as the tape supports.

    Returns a bucket per zone plus the shares, and says how much premium could
    not be classified — a belt reading built on 40% classified prints is a
    different claim from one built on 95%.
    """
    out = {z: {"premium": 0.0, "bot_premium": 0.0, "sold_premium": 0.0,
               "unknown_premium": 0.0, "block_premium": 0.0,
               "call_premium": 0.0, "put_premium": 0.0, "n": 0, "strikes": 0}
           for z in ("belt", "upper_wing", "lower_wing")}
    for k, s in strikes.items():
        z = _zone(k, spot, belt_pct)
        if z not in out:
            continue
        b = out[z]
        b["strikes"] += 1
        for f in ("premium", "bot_premium", "sold_premium", "unknown_premium",
                  "block_premium", "call_premium", "put_premium", "n"):
            b[f] += s[f]
    total = sum(b["premium"] for b in out.values())
    for b in out.values():
        b["share_of_session"] = b["premium"] / total if total else None
        classified = b["bot_premium"] + b["sold_premium"]
        b["net_lift"] = ((b["bot_premium"] - b["sold_premium"]) / classified
                         if classified else None)
        b["classified_share"] = classified / b["premium"] if b["premium"] else None
        b["block_share"] = b["block_premium"] / b["premium"] if b["premium"] else None
    # A pull whose strikes never reached past the belt reports 100% belt, which
    # looks like a finding and is a sampling failure. The first live run did
    # exactly this: select_core is budget-first and covered +/-0.6% of spot, so
    # the wings were never sampled and "belt = 100% of premium" said nothing
    # about the market at all.
    touched = [z for z, b in out.items() if b["strikes"]]
    covered = len(touched) > 1
    return {"spot": spot, "belt_pct": belt_pct, "total_premium": total,
            "zones": out, "zones_covered": covered,
            "coverage_note": (None if covered else
                              f"only the {touched[0] if touched else 'no'} zone "
                              f"had any strikes — the pull did not reach the "
                              f"wings, so this split is about the sample, not "
                              f"the market")}


# A belt reading is only reported as a bid when this much of the belt's premium
# could be classified at all. Below it the answer is unknown, because a net lift
# computed from a third of the prints is a statement about the third.
MIN_CLASSIFIED = 0.50
# How one-sided the belt must be before the word "bid" is used.
BELT_BID_LIFT = 0.10


def belt_bid(z: dict) -> dict:
    """Was the belt bid? His question, answered in three states.

    ``bid`` / ``offered`` / ``balanced``, or ``unknown`` when too little of the
    belt's premium could be classified. Unknown is not balanced.
    """
    b = z["zones"]["belt"]
    cs = b["classified_share"]
    if not b["premium"] or cs is None:
        return {"state": "unknown", "net_lift": None, "classified_share": cs,
                "note": "nothing traded in the belt"}
    if cs < MIN_CLASSIFIED:
        return {"state": "unknown", "net_lift": b["net_lift"],
                "classified_share": cs,
                "note": (f"only {cs:.0%} of belt premium could be classified; "
                         f"{MIN_CLASSIFIED:.0%} needed before a lift is a reading")}
    lift = b["net_lift"]
    if lift >= BELT_BID_LIFT:
        state = "bid"
    elif lift <= -BELT_BID_LIFT:
        state = "offered"
    else:
        state = "balanced"
    return {"state": state, "net_lift": round(lift, 4),
            "classified_share": round(cs, 4),
            "premium": b["premium"], "block_share": b["block_share"],
            "note": (f"belt net lift {lift:+.0%} on {cs:.0%} classified premium, "
                     f"{b['block_share']:.0%} of it in blocks"
                     if b["block_share"] is not None else
                     f"belt net lift {lift:+.0%} on {cs:.0%} classified premium")}


def comparable(reads: list[dict]) -> dict:
    """Can these session reads be put side by side at all?

    Only if they share a tenor. Returns the verdict and the tenors seen, and
    never silently drops the odd one out -- which session is excluded is a
    decision for the caller, and it is usually the interesting one.
    """
    tenors = {}
    for r in reads:
        tenors.setdefault(r.get("tenor"), []).append(r.get("session"))
    ok = len(tenors) == 1
    return {
        "comparable": ok, "tenors": {k: sorted(v) for k, v in tenors.items()},
        "note": (f"all {len(reads)} reads are tenor {next(iter(tenors))}" if ok else
                 "mixed tenors — a 0DTE on its expiry day and a 1DTE are "
                 "different books with different participants, so a difference "
                 "across them is about which the chain offered, not the market"),
    }


def repeats(history: list[dict], state: str = "bid") -> dict:
    """How many consecutive sessions the belt has read the same way.

    His falsifiable claim, made countable: "today's session can be a single desk
    rebalancing; two, at today's size, suggests a campaign." One is an event,
    two is a pattern, and the only way to know which is to have kept yesterday.

    `history` is oldest-first; each row needs `session` and `belt_bid.state`.

    Rows are collapsed to ONE PER SESSION, last written wins. The log is
    append-only and a re-run appends again -- the first live day produced two
    rows for 2026-08-12 -- and without this a single re-pull would read as two
    consecutive sessions and clear his campaign threshold from one day of data.
    A count of sessions has to count sessions.
    """
    seen = {}
    for row in history:
        seen[row.get("session")] = row
    history = [seen[k] for k in sorted(seen)]

    run, last = 0, None
    for row in reversed(history):
        s = ((row.get("belt_bid") or {}).get("state"))
        if s != state:
            break
        run += 1
        last = row.get("session")
    return {"state": state, "consecutive": run, "through": last,
            "reading": ("no run" if run == 0 else
                        "a single desk rebalancing" if run == 1 else
                        f"{run} sessions running — his campaign threshold is 2")}


def sweep_belt(strikes: dict[float, dict], spot: float,
               widths=(0.005, 0.0075, 0.01, 0.015, 0.02)) -> list[dict]:
    """What the belt width does to the split. It is a free parameter."""
    out = []
    for w in widths:
        z = zones(strikes, spot, w)
        bb = belt_bid(z)
        out.append({"belt_pct": w,
                    "belt_share": z["zones"]["belt"]["share_of_session"],
                    "belt_strikes": z["zones"]["belt"]["strikes"],
                    "belt_state": bb["state"], "net_lift": bb["net_lift"]})
    return out


def sides_available(prints: list[dict], min_share: float = MIN_CLASSIFIED) -> bool:
    """Did enough prints arrive with a real aggressor call to read a side?

    False when the tape was pulled without quote ticks, which is the normal
    affordable case. It is asked of the raw prints rather than inferred from a
    zero, because "we did not pull quotes" and "the quotes were crossed all day"
    are different facts and only the first is a budget decision.
    """
    if not prints:
        return False
    known = sum(1 for p in prints if p.get("side") in ("BOT", "SOLD"))
    return known / len(prints) >= min_share


def session_read(prints: list[dict], spot: float, session: str,
                 belt_pct: float = BELT_PCT, dte: int | None = None,
                 tenor: int | None = None) -> dict:
    """The whole flow read for one session, ready to store and to juxtapose."""
    strikes = per_strike(prints)
    z = zones(strikes, spot, belt_pct)
    tagged = B.tag_prints(prints)
    have_sides = sides_available(prints)
    return {
        "session": session, "spot": spot, "tenor": tenor, "dte": dte,
        "n_prints": len(prints),
        "sides_available": have_sides,
        "block_summary": B.block_share(tagged),
        "zones": z["zones"], "total_premium": z["total_premium"],
        "zones_covered": z["zones_covered"],
        "coverage_note": z["coverage_note"],
        "belt_bid": (belt_bid(z) if have_sides else
                     {"state": "unknown", "net_lift": None,
                      "classified_share": None,
                      "note": "the tape was pulled without quote ticks, so no "
                              "print has an aggressor side. The 1-minute bar "
                              "proxy was tested and agrees with tick NBBO 56.7% "
                              "of the time against a 50% coin, so it is refused "
                              "rather than used"}),
        "belt_sweep": sweep_belt(strikes, spot),
        "per_strike": {str(k): v for k, v in sorted(strikes.items())},
        "note": "what traded and which side lifted — not why. A put bought at "
                "the belt is a hedge or a directional bet and the tape cannot "
                "tell you which.",
    }
