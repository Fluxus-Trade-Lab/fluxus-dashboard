"""Self-consistency warnings — replicate the number, alarm when it drifts.

Taken from @TailThatWagsDog, 2026-07-28, quoting his own pipeline's output:

    "The eligibility screen thins the book as expected, and the self-consistency
     warning fires correctly when the replicated baseline drifts from the
     model's own number."

That is a check we have run by hand every time it mattered — Black-Scholes
greeks against IBKR's own, our SPX/VIX regression against the slope printed on
his chart — and caught a real error each time. It has never been automated.

Why this and not more unit tests. Our error log says five of six logged errors
were *correct arithmetic on a wrong input or definition*: vega per vol-point vs
per sigma, IV solved off spot instead of the forward, a basis measured against a
stale cash print, day volume read from `callVolume` instead of `volume`. A unit
test asserts that a function does what its author meant. A replicated baseline
asserts that two independent routes to the same quantity agree, which is the only
thing that catches a wrong input — the code was never broken.

A check here is a triple: the published number, an independently computed
baseline, and a tolerance that says how far apart they may legitimately be.
Tolerances are arguments, never constants buried in a branch, because "these
agree" is a claim about a number someone chose.
"""
from __future__ import annotations

# A check whose two routes are not actually independent proves nothing. Kept as
# a field so a reviewer can see what was claimed, not inferred from a name.
ROUTES = ("independent", "same_source")


def check(name: str, published: float | None, baseline: float | None, *,
          tol_abs: float | None = None, tol_rel: float | None = None,
          route: str = "independent", unit: str = "",
          note: str | None = None) -> dict:
    """Compare a published number against a replicated one.

    Exactly one of `tol_abs`/`tol_rel` must be given: an absolute tolerance on a
    quantity that spans orders of magnitude is meaningless, and a relative one
    on a quantity that crosses zero is worse.

    A missing value on either side is `unavailable`, never `ok`. Silence where a
    check should have run is the failure mode this module exists to prevent.
    """
    if route not in ROUTES:
        raise ValueError(f"route must be one of {ROUTES}")
    if (tol_abs is None) == (tol_rel is None):
        raise ValueError("give exactly one of tol_abs or tol_rel")

    out = {"name": name, "published": published, "baseline": baseline,
           "route": route, "unit": unit, "note": note,
           "tol_abs": tol_abs, "tol_rel": tol_rel}
    if published is None or baseline is None:
        return {**out, "status": "unavailable", "drift": None,
                "detail": "one side was not computed — this check did not run"}

    drift = published - baseline
    if tol_abs is not None:
        ok = abs(drift) <= tol_abs
        detail = f"|{drift:+.4g}| vs tolerance {tol_abs:g}{unit}"
    else:
        denom = abs(baseline)
        if denom == 0:
            return {**out, "status": "unavailable", "drift": drift,
                    "detail": "relative tolerance against a zero baseline is undefined"}
        rel = abs(drift) / denom
        ok = rel <= tol_rel
        detail = f"{rel:.2%} apart vs tolerance {tol_rel:.2%}"
    return {**out, "status": "ok" if ok else "DRIFT", "drift": drift,
            "detail": detail}


def run(checks: list[dict]) -> dict:
    """Summarise a set of checks.

    `unavailable` counts against the run rather than being ignored. A pipeline
    where half the checks quietly did not execute is not a pipeline that passed.
    """
    drifted = [c for c in checks if c["status"] == "DRIFT"]
    missing = [c for c in checks if c["status"] == "unavailable"]
    return {
        "n": len(checks),
        "ok": len(checks) - len(drifted) - len(missing),
        "drift": len(drifted),
        "unavailable": len(missing),
        "clean": not drifted and not missing,
        "failures": drifted,
        "not_run": missing,
    }


# --------------------------------------------------------------- the checks

def gex_checks(gex: dict) -> list[dict]:
    """Replicate what the GEX brief publishes, by a second route each time."""
    out = []

    ps = {float(k): v for k, v in (gex.get("per_strike_gex") or {}).items()}

    # total_gex is published as its own field; the per-strike map should sum to
    # it. Two routes through the same aggregation catch a strike dropped between
    # the sum and the map — the plumbing class of error.
    out.append(check("total GEX vs sum of per-strike",
                     gex.get("total_gex"), sum(ps.values()) if ps else None,
                     tol_rel=0.001, route="same_source", unit=" $/1%",
                     note="same source, so this catches plumbing only"))

    # The call wall is defined as the argmax of the per-strike map. If the
    # published strike is not that argmax, one of the two was computed from a
    # different grid.
    if ps:
        out.append(check("call wall vs argmax of per-strike",
                         gex.get("call_wall"), max(ps, key=lambda k: ps[k]),
                         tol_abs=0.0, unit=" pts"))
        out.append(check("put wall vs argmin of per-strike",
                         gex.get("put_wall"), min(ps, key=lambda k: ps[k]),
                         tol_abs=0.0, unit=" pts"))

    # The flip is where the dealer-gamma PROFILE crosses zero. The profile is
    # gamma recomputed at each hypothetical spot; the per-strike map is net GEX
    # summed by strike. They share the word "gamma" and are different objects —
    # the first version of this check compared them and fired a 97-point drift
    # against a correct pipeline. That is the conflated-quantity error this
    # module exists to catch, committed by the module.
    flip = gex.get("zero_gamma_flip")
    prof = gex.get("profile") or []
    if flip is not None and len(prof) > 1:
        crossed = None
        for i in range(1, len(prof)):
            a, b = prof[i - 1][1], prof[i][1]
            if (a < 0 <= b) or (a > 0 >= b):
                crossed = (prof[i - 1][0] + prof[i][0]) / 2.0
                break
        out.append(check("zero-gamma flip vs profile zero-crossing",
                         flip, crossed, tol_abs=10.0, unit=" pts",
                         note="baseline is the midpoint of the bracketing pair on "
                              "the fine grid; the published value interpolates"))

    # An ATM IV outside a plausible band is not a drift, it is a unit error --
    # the class that put vega off by 100x. Baseline is the midpoint of the band.
    iv = gex.get("atm_iv_1dte")
    if iv is not None:
        out.append(check("ATM IV in a plausible band", iv, 0.20,
                         tol_abs=0.60, unit=" (decimal fraction)",
                         note="catches a percentage entered where a fraction belongs"))
    return out


def profile_checks(profile: dict) -> list[dict]:
    """Replicate the auction numbers."""
    t = profile.get("tpo") or {}
    counts = {float(k): v for k, v in (t.get("counts") or {}).items()}
    out = []
    if counts:
        # Independent route: the TPOC must be a price that actually carries the
        # maximum TPO count. Comparing against a bare argmax was wrong — three
        # strikes tied at 10 on 2026-08-06 and the published value correctly
        # took the one nearest mid-range, so the naive check fired on a correct
        # pipeline. Membership in the tied set is the claim that holds either way.
        peak = max(counts.values())
        tied = sorted(k for k, v in counts.items() if v == peak)
        tpoc = t.get("tpoc")
        nearest = min(tied, key=lambda k: abs(k - tpoc)) if (tied and tpoc) else None
        out.append(check("TPOC is one of the max-count strikes",
                         tpoc, nearest, tol_abs=0.0, unit=" pts",
                         note=f"{len(tied)} strike(s) tied at {peak} TPOs; the "
                              f"published value must be one of them"))
        out.append(check("session high vs max of the profile grid",
                         t.get("high"), max(counts), tol_abs=0.0, unit=" pts"))
        out.append(check("session low vs min of the profile grid",
                         t.get("low"), min(counts), tol_abs=0.0, unit=" pts"))
    va = t.get("value_area") or {}
    if va and counts:
        total = sum(counts.values())
        inside = sum(v for k, v in counts.items()
                     if va["low"] <= k <= va["high"])
        out.append(check("value-area coverage vs recount inside the band",
                         va.get("covered"), inside / total if total else None,
                         tol_abs=0.005, unit=" of TPOs"))
    return out
