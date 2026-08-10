"""Read the GEX series as STATES and TRANSITIONS, not as a number.

From @TailThatWagsDog, 2026-08-09, on ~3,800 SPX sessions of market-maker
positioning: *"The trade signal isn't in where GEX sits … The signal is in how
GEX moves … Slow transitions are noise. Fast ones are information."*

His findings, stated so they can be argued with rather than absorbed:

* hedging support **rebuilding** as a selloff stabilises, or early in a fresh
  rally — strong forward returns. The same move inside a tight consolidation —
  worthless. **Context decides.**
* gradual **erosion** of support means little.
* support **vanishing abruptly, skipping states it normally walks through** —
  sharply negative forward returns. Fired **four times in fifteen years**.

**Two reasons we do not port his thresholds, and one reason we cannot test him.**

First, his headline collapse is +5bn to -0.05bn in a session, about -5B. Our own
routine daily deltas run -14B to +21B — three to four times his epic. Either his
series is normalised differently or ours is far noisier; either way "-5B is a
collapse" is a statement about HIS distribution. So every boundary here is a
**percentile of our own history**, self-calibrating, and moves as the history
grows.

Second, he has 3,800 sessions and we have twenty. His strongest finding fires
about once in 950 sessions, so our expected count is 0.02. **This module cannot
and does not test his claim.** It builds the measurement so that a test becomes
possible later, and it says `unproven` until it has one.

And the thing worth saying out loud: **four occurrences in fifteen years is
n=4.** Four for four is striking and it is also the sample size at which we
refuse our own findings — `scorecard.MIN_TESTED` is 30. Holding his claim to a
lower standard than ours would be a courtesy, not an analysis.
"""
from __future__ import annotations

import statistics as st

# Five states, from the percentiles of our own net-GEX history. Named rather
# than numbered so a transition reads as a sentence.
STATES = ("deeply negative", "negative", "neutral", "positive", "deeply positive")
# Percentile cuts between them. A free parameter, sweepable, echoed in output.
CUTS = (0.10, 0.35, 0.65, 0.90)

# Below this many sessions the percentile boundaries are being fitted to noise.
MIN_HISTORY = 30


def state_boundaries(history: list[float], cuts: tuple = CUTS) -> list[float]:
    """Percentile cuts of OUR series — never absolute dollar levels."""
    if not history:
        return []
    xs = sorted(history)
    return [xs[min(int(c * len(xs)), len(xs) - 1)] for c in cuts]


def classify(value: float, bounds: list[float]) -> str:
    if not bounds:
        return "unknown"
    for i, b in enumerate(bounds):
        if value < b:
            return STATES[i]
    return STATES[-1]


def transitions(series: list[tuple[str, float]], cuts: tuple = CUTS) -> list[dict]:
    """Session-over-session state moves, with how many states were skipped.

    `speed` is the number of state boundaries crossed in one session. His whole
    claim lives in this number: one is a walk, three or four is the market
    skipping states it normally passes through.
    """
    if len(series) < 2:
        return []
    hist = [v for _, v in series]
    bounds = state_boundaries(hist, cuts)
    out = []
    for (d0, v0), (d1, v1) in zip(series, series[1:]):
        s0, s1 = classify(v0, bounds), classify(v1, bounds)
        i0, i1 = STATES.index(s0), STATES.index(s1)
        out.append({
            "from_session": d0, "session": d1,
            "from_state": s0, "to_state": s1,
            "from_value": v0, "to_value": v1, "delta": v1 - v0,
            "speed": abs(i1 - i0),
            "direction": ("rebuild" if i1 > i0 else
                          "erosion" if i1 < i0 else "held"),
            "n_history": len(hist),
            "calibrated": len(hist) >= MIN_HISTORY,
        })
    return out


def notable(rows: list[dict], min_speed: int = 2) -> list[dict]:
    """Transitions that skipped states. Slow ones are noise, per the source."""
    return [r for r in rows if r["speed"] >= min_speed]


def summary(rows: list[dict]) -> dict:
    """What the series is doing, and how far it is from being testable."""
    if not rows:
        return {"n": 0, "testable": False,
                "note": "no transitions yet — a state series needs two sessions"}
    speeds = [r["speed"] for r in rows]
    last = rows[-1]
    n_hist = last["n_history"]
    return {
        "n": len(rows),
        "n_history": n_hist,
        "calibrated": last["calibrated"],
        "mean_speed": round(st.mean(speeds), 2),
        "max_speed": max(speeds),
        "n_notable": len(notable(rows)),
        "latest": {"from": last["from_state"], "to": last["to_state"],
                   "speed": last["speed"], "direction": last["direction"],
                   "delta": last["delta"]},
        # The honest headline. His finding fires ~1 in 950 sessions.
        "testable": n_hist >= 950,
        "note": (f"{n_hist} sessions held. The source's strongest finding fires "
                 f"about once in 950, so nothing here tests it — "
                 f"{950 - n_hist} sessions short. Boundaries are percentiles of "
                 f"our own series and will move as it grows."
                 if n_hist < 950 else "history is deep enough to begin testing"),
    }
