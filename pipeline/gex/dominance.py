"""Which force governs each strike — gamma, charm, or neither.

GEX and charm are the same dealer book differentiated against two different
variables: gamma is delta sensitivity to **price**, charm is delta sensitivity to
**time**. Gamma says where hedging flow fires if the market moves; charm says
where it fires if the market does nothing. They need not sit at the same strike,
and when they don't, that is the useful part.

The practical consequence, which is the reason to compute this at all: a balance
that *holds* is charm-governed — time drags dealer delta toward the strike and
the range tightens on its own, with no opinion about direction. A balance that
*breaks* is gamma-governed — the move has to happen first, and then hedging flow
either damps it or amplifies it.

**The measurement problem.** The two series are not in the same units — one is
dollars of delta per 1% move, the other dollars of delta drift to expiry. Any
statement that one "dominates" a strike is really a statement about a chosen
normalisation. That choice lives in `normalise` and is echoed in every result,
because a label whose meaning depends on a hidden constant is decoration.
"""
from __future__ import annotations

import statistics as st

# Below this, in normalised units, a strike is not being driven by either force
# and gets `neither` rather than a coin-flip winner.
QUIET = 0.5
# Inside this ratio the two are called a draw. Without it, 1.01 vs 1.00 would
# read as "gamma-governed".
DRAW_RATIO = 1.25

METHODS = ("zscore", "maxabs")


def normalise(values: dict[float, float], method: str = "zscore") -> dict[float, float]:
    """Put one per-strike series on a comparable scale.

    ``zscore``  centre and divide by the standard deviation across the grid.
                Robust to the two series having wildly different magnitudes,
                which they do.
    ``maxabs``  divide by the largest absolute value. Keeps the sign and the
                shape but is dominated by a single outlier strike.

    Both are defensible; neither is canonical. The caller picks and the result
    says which.
    """
    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}")
    if not values:
        return {}
    if method == "maxabs":
        peak = max(abs(v) for v in values.values())
        return {k: (v / peak if peak else 0.0) for k, v in values.items()}
    vals = list(values.values())
    mu = st.mean(vals)
    sd = st.pstdev(vals)
    if sd == 0:
        return {k: 0.0 for k in values}
    return {k: (v - mu) / sd for k, v in values.items()}


def dominant_exposure(gex: dict[float, float], charm: dict[float, float],
                      method: str = "zscore", quiet: float = QUIET,
                      draw_ratio: float = DRAW_RATIO) -> list[dict]:
    """Per strike: which force is larger, and what would activate it.

    Only strikes present in BOTH series are returned. A strike with gamma and no
    charm is not a strike where gamma dominates — it is a strike we failed to
    measure charm at, and merging the two cases would invent a finding.
    """
    shared = sorted(set(gex) & set(charm))
    if not shared:
        return []
    g = normalise({k: gex[k] for k in shared}, method)
    c = normalise({k: charm[k] for k in shared}, method)

    out = []
    for k in shared:
        ag, ac = abs(g[k]), abs(c[k])
        if ag < quiet and ac < quiet:
            dom, activated = "neither", "nothing — this strike is quiet in both"
        elif max(ag, ac) < min(ag, ac) * draw_ratio:
            dom, activated = "both", "the crossover — either force can hand off here"
        elif ag > ac:
            dom, activated = "gamma", "displacement — requires a move to engage"
        else:
            dom, activated = "charm", "the passage of time — decay drags dealer delta here"
        out.append({
            "strike": k, "gex": gex[k], "charm": charm[k],
            "gex_norm": g[k], "charm_norm": c[k],
            "dominant": dom, "activated_by": activated,
            "same_sign": gex[k] * charm[k] > 0,
            "method": method,
        })
    return out


def crossover(rows: list[dict], quiet: float = QUIET) -> dict | None:
    """The strike where the handoff happens — the closest thing to a draw.

    This is the price at which the book stops being time-driven and starts being
    price-driven, which is a more useful thing to name than either peak alone.

    **BOTH** forces must clear `quiet` to qualify. Taking the smallest gap over
    the whole grid instead picks a far-OTM strike where the two are 0.5 and 0.2
    sigma — a handoff between two nothings, and an argmax over noise of exactly
    the kind that keeps costing us. Returns None when no strike qualifies.
    """
    live = [r for r in rows
            if min(abs(r["gex_norm"]), abs(r["charm_norm"])) >= quiet]
    if not live:
        return None
    best = min(live, key=lambda r: abs(abs(r["gex_norm"]) - abs(r["charm_norm"])))
    # The nearest candidate is not automatically a handoff. On 2026-08-05 the
    # closest pair was 1.00 vs 0.61 sigma -- clearly gamma-governed, and calling
    # it "the crossover" because nothing beat it would be the function lying
    # about what it found. The caller gets the row AND whether it qualifies.
    return {**best, "is_handoff": best["dominant"] == "both"}


def summary(rows: list[dict]) -> dict:
    """Counts by governing force, for a one-line read of the whole grid."""
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["dominant"]] = counts.get(r["dominant"], 0) + 1
    return {"counts": counts, "n": len(rows),
            "method": rows[0]["method"] if rows else None}
