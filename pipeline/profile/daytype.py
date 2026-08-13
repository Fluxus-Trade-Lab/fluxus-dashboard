"""The auction's development stage — the state variable everything else lacks.

    "We're now watching a chatbot ... call out the auction's current development
     stage."                              — @TailThatWagsDog, 2026-08-12

This is the one named thing his app does that we could not do at all, and it is
the fix for a gap logged the day before: **every statistic this repo holds is
unconditional.** A hit rate over all sessions averages a trend day and a
balanced day into a number that describes neither.

Two classifications, because they answer different questions at different times:

  * **open type** — decidable within the first bracket or two, from where price
    opens against the PRIOR session's value and what it does next
  * **day type** — decidable only at the close, from the initial balance, the
    extensions, and the shape of the finished profile

## The honest risk, stated before the code

Five outputs with adjustable cuts is a free-parameter farm, and this project has
already caught itself twice picking a number that made a finding appear. So:

  * every threshold is a module constant with the sweep beside it
  * `classify` returns the rule that fired and the measurements it fired on,
    never a bare label
  * a session the rules cannot separate comes back ``unclassified``, which is a
    real answer and not a bucket for leftovers

Day types in the Market Profile literature are described, not defined — Dalton
gives shapes and tendencies rather than cutoffs. The numbers here are ours. They
are stated as ours, and the base rates they produce are the check on whether
they carve anything real.

## What this is not

No day type is bullish or bearish and none of these functions returns a
direction. A trend day is a trend day in whichever direction it ran.
"""
from __future__ import annotations

from . import facilitation as FAC
from . import tpo as MP

# --- day type -----------------------------------------------------------
# All expressed as the initial balance's share of the whole session range,
# which is the standard way the literature describes the distinction ("a normal
# day's range is largely set in the first hour"). Swept in `sweep_day_types`
# over 2 years; the base rates each setting produces are in
# data/profile/daytype_base_rate.json.
NORMAL_IB_SHARE = 0.85      # at or above: the IB set essentially the whole day
VARIATION_IB_SHARE = 0.45   # between: one side extended meaningfully
# Below VARIATION_IB_SHARE the day ran, and the close decides whether it ran
# ONE way (trend) or simply went wide.
TREND_CLOSE_IN_EXTREME = 0.20   # close within this share of the range of an end

# --- open type ----------------------------------------------------------
# How many brackets count as "the open". This was the classifier's first real
# bug and the base rates caught it within minutes of being measured: the
# original read the WHOLE session, so over thirteen brackets almost every day
# eventually traded back through its opening range. open_drive fired once in 496
# sessions (0.2%) and open_rejection_reverse took 42.5% -- not a classification,
# a description of what any full day does.
#
# The open is the open. Three brackets is 09:30-11:00 ET, which is the window
# the type is supposed to be decidable in and the reason it is worth having:
# a day type needs the close, an open type does not.
OPEN_WINDOW = 3

# "Drove away and never came back" needs a definition of came back. A bracket
# whose range re-enters the opening bracket is a return.
DRIVE_MAX_RETURN_PERIODS = 0    # open-drive: no bracket re-enters the open range
TEST_DRIVE_MAX_TEST = 1         # open-test-drive: at most this many probes back

DAY_TYPES = ("normal", "normal_variation", "trend", "neutral",
             "double_distribution", "unclassified")
OPEN_TYPES = ("open_drive", "open_test_drive", "open_rejection_reverse",
              "open_auction", "unclassified")


def _range(bars) -> tuple[float, float]:
    return min(b["low"] for b in bars), max(b["high"] for b in bars)


def ib_share(bars: list[dict]) -> float | None:
    """The initial balance's range as a share of the whole session's.

    None when the session never moved — a zero-range day has no share to take,
    and returning 1.0 would file it as a textbook normal day.
    """
    ib = MP.initial_balance(bars)
    if not ib:
        return None
    lo, hi = _range(bars)
    span = hi - lo
    if span <= 0:
        return None
    return (ib["high"] - ib["low"]) / span


def day_type(bars: list[dict], tick: float = 2.5) -> dict:
    """Classify the finished session. Returns the rule and its measurements.

    Order matters and is stated: a session that extended on BOTH sides is
    neutral whatever its IB share, because two-sided extension is a statement
    about an unresolved auction that the range cannot make. Double distribution
    is checked next because it is a shape claim that overrides a width claim.
    """
    if not bars:
        return {"type": "unclassified", "rule": "no bars", "measurements": {}}
    ib = MP.initial_balance(bars)
    fac = FAC.facilitation(bars, ib)
    share = ib_share(bars)
    lo, hi = _range(bars)
    span = hi - lo
    close = bars[-1]["close"]
    # 0 at the low, 1 at the high.
    close_pos = (close - lo) / span if span > 0 else 0.5
    counts = MP.tpo_counts(MP.build_profile(bars, tick))
    dd = _double_distribution(counts, tick)

    m = {"ib_share": round(share, 4) if share is not None else None,
         "close_position": round(close_pos, 4),
         "range": round(span, 4),
         "facilitation_state": (fac or {}).get("state"),
         "double_distribution": dd}

    if share is None:
        return {"type": "unclassified",
                "rule": "the session had no range — nothing to divide by",
                "measurements": m}
    if (fac or {}).get("state") == "two_sided":
        return {"type": "neutral",
                "rule": "extended on both sides of the initial balance — the "
                        "auction resolved nothing",
                "measurements": m}
    if dd["is_double"]:
        return {"type": "double_distribution",
                "rule": f"two separate areas of acceptance split by a thin zone "
                        f"at {dd['split_price']:,.1f}",
                "measurements": m}
    if share >= NORMAL_IB_SHARE:
        return {"type": "normal",
                "rule": f"the initial balance set {share:.0%} of the day's "
                        f"range, at or above the {NORMAL_IB_SHARE:.0%} cut",
                "measurements": m}
    if share >= VARIATION_IB_SHARE:
        return {"type": "normal_variation",
                "rule": f"the initial balance set {share:.0%} of the range — "
                        f"one side extended without the day running",
                "measurements": m}
    in_extreme = min(close_pos, 1 - close_pos) <= TREND_CLOSE_IN_EXTREME
    if in_extreme:
        return {"type": "trend",
                "rule": f"the initial balance set only {share:.0%} of the range "
                        f"and the close finished {close_pos:.0%} up it — one-way",
                "measurements": m}
    return {"type": "unclassified",
            "rule": f"the range ran well past the initial balance ({share:.0%}) "
                    f"but the close came back to {close_pos:.0%} of it — wide "
                    f"and undecided, which is not one of the named shapes",
            "measurements": m}


# A price splits the profile when its TPO count is at most this share of the
# smaller of the two peaks either side. Held deliberately tight: a shallow dip
# in a single distribution is not two distributions.
DD_TROUGH_SHARE = 0.40
DD_MIN_PEAK_TPOS = 3


def _double_distribution(counts: dict[float, int], tick: float) -> dict:
    """Two areas of acceptance with a thin zone between them.

    Reported with the split price and the depth so the near-misses are visible.
    A boolean alone would make "no double distribution today" and "the cut is
    too tight" look identical, which is the failure `profile_gaps` was added to
    stop in the volume profile.
    """
    if len(counts) < 5:
        return {"is_double": False, "split_price": None, "depth": None,
                "note": "too few prices to hold two distributions"}
    prices = sorted(counts)
    best = None
    for i in range(1, len(prices) - 1):
        lo_peak = max(counts[p] for p in prices[:i])
        hi_peak = max(counts[p] for p in prices[i + 1:])
        trough = counts[prices[i]]
        smaller = min(lo_peak, hi_peak)
        if smaller < DD_MIN_PEAK_TPOS:
            continue
        depth = trough / smaller
        if best is None or depth < best[0]:
            best = (depth, prices[i])
    if best is None:
        return {"is_double": False, "split_price": None, "depth": None,
                "note": "no interior price had a real peak on both sides"}
    depth, price = best
    return {"is_double": depth <= DD_TROUGH_SHARE, "split_price": price,
            "depth": round(depth, 4),
            "note": (f"deepest interior trough is {depth:.0%} of the smaller "
                     f"peak, against a {DD_TROUGH_SHARE:.0%} cut")}


def open_type(bars: list[dict], prior_value: dict | None = None) -> dict:
    """Classify the open. Decidable early, which is the point of it.

    `prior_value` is the previous session's value area — {"low", "high"} — and
    is what makes "opened outside value" answerable. Without it the location
    half cannot be assessed and the result says so rather than guessing.
    """
    if len(bars) < 3:
        return {"type": "unclassified",
                "rule": f"only {len(bars)} bracket(s) — the open has not "
                        f"finished developing",
                "measurements": {}}
    first = bars[0]
    o_lo, o_hi = first["low"], first["high"]
    # Only the opening window. See OPEN_WINDOW for why this is not the whole day.
    later = bars[1:OPEN_WINDOW]
    # Brackets that traded back inside the opening bracket's range.
    returns = sum(1 for b in later if b["low"] <= o_hi and b["high"] >= o_lo)
    open_px = first.get("open", (o_lo + o_hi) / 2)
    inside_value = None
    if prior_value and prior_value.get("low") is not None:
        inside_value = prior_value["low"] <= open_px <= prior_value["high"]

    # Did price leave the opening bracket in both directions before settling?
    went_up = any(b["high"] > o_hi for b in later)
    went_down = any(b["low"] < o_lo for b in later)

    m = {"opening_range": [o_lo, o_hi], "open": open_px,
         "open_window_brackets": OPEN_WINDOW,
         "brackets_returning_to_open": returns,
         "opened_inside_prior_value": inside_value,
         "left_up": went_up, "left_down": went_down}

    if returns <= DRIVE_MAX_RETURN_PERIODS and (went_up or went_down):
        return {"type": "open_drive",
                "rule": "left the opening bracket and no later bracket traded "
                        "back into it — conviction from the bell",
                "measurements": m}
    if went_up and went_down:
        return {"type": "open_rejection_reverse",
                "rule": "left the opening bracket in BOTH directions — one side "
                        "was rejected and the auction turned",
                "measurements": m}
    if returns <= TEST_DRIVE_MAX_TEST and (went_up or went_down):
        return {"type": "open_test_drive",
                "rule": f"tested back into the opening bracket {returns} time(s) "
                        f"and then went — conviction after a probe",
                "measurements": m}
    if inside_value is True:
        return {"type": "open_auction",
                "rule": "opened inside the prior session's value and rotated — "
                        "no conviction either way",
                "measurements": m}
    return {"type": "unclassified",
            "rule": (f"traded back into the opening bracket {returns} times "
                     f"without a directional resolution"
                     + ("" if inside_value is not None else
                        ", and no prior value area was supplied to say whether "
                        "the open was inside it")),
            "measurements": m}


def classify(bars: list[dict], prior_value: dict | None = None,
             tick: float = 2.5) -> dict:
    """Both stages together — the auction's development, named."""
    return {"open": open_type(bars, prior_value),
            "day": day_type(bars, tick),
            "note": "no day type is bullish or bearish; a trend day is a trend "
                    "day in whichever direction it ran"}


def sweep_open_window(sessions: dict[str, list[dict]],
                     prior_values: dict[str, dict] | None = None,
                     windows=(2, 3, 4, 6, 13)) -> list[dict]:
    """What counts as "the open", swept.

    13 is the whole session and is included to show the failure that prompted
    the constant: read over a full day, open_drive vanishes and
    open_rejection_reverse swallows everything.

    `prior_values` maps a date to that day's PRIOR value area and is required
    for the sweep to reproduce the shipped classification. Its first version
    omitted the argument entirely, so `opened_inside_prior_value` was always
    None, `open_auction` could never fire, and the sweep reported 0 where the
    live run reported 114. **A sweep that cannot reproduce the thing it sweeps
    is worse than no sweep** -- it is a second, wrong classifier presented as
    evidence about the first.
    """
    import collections
    global OPEN_WINDOW
    keep = OPEN_WINDOW
    pv = prior_values or {}
    out = []
    try:
        for w in windows:
            OPEN_WINDOW = w
            c = collections.Counter(open_type(bs, pv.get(d))["type"]
                                    for d, bs in sessions.items())
            out.append({"window": w, "n": len(sessions),
                        "had_prior_value": sum(1 for d in sessions if pv.get(d)),
                        **{t: c.get(t, 0) for t in OPEN_TYPES}})
    finally:
        OPEN_WINDOW = keep
    return out


def sweep_day_types(sessions: dict[str, list[dict]],
                    normals=(0.75, 0.80, 0.85, 0.90),
                    variations=(0.35, 0.45, 0.55)) -> list[dict]:
    """What the two width cuts do to the base rates.

    The cuts are ours, not Dalton's — he describes shapes and tendencies, not
    cutoffs. This is the table that says whether they carve anything, and it
    exists so the constants can never sit in the module as bare numbers.
    """
    import collections
    global NORMAL_IB_SHARE, VARIATION_IB_SHARE
    keep = (NORMAL_IB_SHARE, VARIATION_IB_SHARE)
    out = []
    try:
        for n in normals:
            for v in variations:
                if v >= n:
                    continue
                NORMAL_IB_SHARE, VARIATION_IB_SHARE = n, v
                c = collections.Counter(day_type(bs)["type"]
                                        for bs in sessions.values())
                out.append({"normal_cut": n, "variation_cut": v,
                            "n": len(sessions),
                            **{t: c.get(t, 0) for t in DAY_TYPES}})
    finally:
        NORMAL_IB_SHARE, VARIATION_IB_SHARE = keep
    return out
