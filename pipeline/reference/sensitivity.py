"""Which conclusions survive the constants we chose, and which are artifacts.

Every threshold in this project was defended in a comment when it was written —
`THIN_WALL_FRAC = 0.10`, `DEFAULT_TOLERANCE = 5.0`, `QUIET = 0.5`, a 70% value
area, a "pair" value-area method. Each argument was reasonable in isolation.
None of them has ever been varied, and the brief's published conclusions depend
on all of them jointly.

That is the actual exposure. A confluence that appears at tolerance 5 and
vanishes at tolerance 4 is not a finding about the market; it is a finding about
a number someone typed. This module tells the two apart by re-running the same
conclusion across a parameter's plausible range and reporting whether the answer
moved.

The discipline it enforces: **a conclusion is reportable only with its stability.**
"Two frameworks agree at 7,748" and "two frameworks agree at 7,748 across every
tolerance from 2.5 to 10" are different claims, and only the second one is
worth acting on.

Deliberately NOT a search for the best parameter. Tuning a threshold until the
answer looks good is how a free parameter becomes a conclusion. The sweep only
ever reports variance.
"""
from __future__ import annotations

from collections import Counter


def sweep(fn, values: list) -> list[dict]:
    """Run `fn(value)` across `values`; keep failures rather than dropping them.

    A parameter that makes the computation raise is information — it marks the
    edge of the range where the method is defined at all — and silently skipping
    it would make the surviving range look wider than it is.
    """
    out = []
    for v in values:
        try:
            out.append({"value": v, "result": fn(v), "error": None})
        except Exception as e:                  # noqa: BLE001 - the error IS data
            out.append({"value": v, "result": None,
                        "error": f"{type(e).__name__}: {e}"})
    return out


def stability(runs: list[dict]) -> dict:
    """How much the answer moved across the sweep.

    `stable` means every successful run agreed. `modal_share` is the fraction
    that agreed with the most common answer — a conclusion holding at 0.6 is
    barely a conclusion, and the number says so rather than a bare True/False.
    """
    ok = [r for r in runs if r["error"] is None]
    if not ok:
        return {"stable": None, "n": 0, "n_failed": len(runs), "answers": {},
                "modal": None, "modal_share": None}
    keys = [_hashable(r["result"]) for r in ok]
    counts = Counter(keys)
    modal, hits = counts.most_common(1)[0]
    return {
        "stable": len(counts) == 1,
        "n": len(ok),
        "n_failed": len(runs) - len(ok),
        "answers": {str(k): c for k, c in counts.most_common()},
        "modal": modal,
        "modal_share": hits / len(ok),
        "flips_at": [r["value"] for r, k in zip(ok, keys) if k != modal],
    }


def _hashable(x):
    """Collapse a result to something comparable, preserving order-independence
    for sets of levels but NOT for ordered conclusions."""
    if isinstance(x, (list, set, tuple)):
        return tuple(sorted(_hashable(i) for i in x))
    if isinstance(x, dict):
        return tuple(sorted((k, _hashable(v)) for k, v in x.items()))
    return x


def frange(lo: float, hi: float, step: float) -> list[float]:
    """Inclusive float range, rounded to kill accumulation drift."""
    if step <= 0:
        raise ValueError("step must be positive")
    n = int(round((hi - lo) / step))
    return [round(lo + i * step, 10) for i in range(n + 1)]


# --------------------------------------------------------------- conclusions

def strongest_price(profile: dict, gex: dict, tolerance: float) -> float | None:
    """The headline: which price the two frameworks agree on most tightly."""
    from pipeline.profile import synthesis as SY
    rows = SY.reference_map(SY.auction_levels(profile), SY.options_levels(gex),
                            tolerance=tolerance)
    s = SY.strongest(rows)
    return round(s["price"], 1) if s else None


def confluence_prices(profile: dict, gex: dict, tolerance: float) -> list[float]:
    """Every price where both frameworks land — the set, not just the winner."""
    from pipeline.profile import synthesis as SY
    rows = SY.reference_map(SY.auction_levels(profile), SY.options_levels(gex),
                            tolerance=tolerance)
    return [round(r["price"], 1) for r in rows if r["confluence"]]


def conflict_issues(profile: dict, gex: dict, thin_wall_frac: float) -> list[str]:
    from pipeline.profile import synthesis as SY
    return [c["issue"] for c in SY.conflicts(profile, gex,
                                             thin_wall_frac=thin_wall_frac)]


def business_frame(profile: dict, gex: dict, coverage: float,
                   method: str = "pair") -> str | None:
    """Which fork the day's question takes — the conclusion most exposed to the
    value-area parameters, since the whole question is 'where is spot relative
    to value'."""
    from pipeline.profile import synthesis as SY
    from pipeline.profile import tpo as MP
    counts = {float(k): v for k, v in (profile.get("tpo", {})
                                       .get("counts") or {}).items()}
    if not counts:
        return None
    va = MP.value_area(counts, coverage=coverage, method=method)
    patched = {"tpo": {**profile["tpo"], "value_area": va}}
    q = SY.todays_business(patched, gex)
    return q["frame"] if q else None


def report(profile: dict, gex: dict) -> list[dict]:
    """Sweep every decision parameter that touches a published conclusion.

    Ranges are the plausible span a reasonable practitioner might pick, not a
    span chosen to make anything look stable.
    """
    specs = [
        ("tolerance", "strongest confluence price", frange(2.5, 12.5, 2.5),
         lambda v: strongest_price(profile, gex, v)),
        ("tolerance", "set of confluence prices", frange(2.5, 12.5, 2.5),
         lambda v: confluence_prices(profile, gex, v)),
        ("thin_wall_frac", "which conflicts are reported", frange(0.02, 0.20, 0.02),
         lambda v: conflict_issues(profile, gex, v)),
        ("value_area_coverage", "today's question frame", frange(0.60, 0.80, 0.05),
         lambda v: business_frame(profile, gex, v)),
        ("value_area_method", "today's question frame", ["pair", "single"],
         lambda v: business_frame(profile, gex, 0.70, v)),
    ]
    out = []
    for param, conclusion, values, fn in specs:
        runs = sweep(fn, values)
        st = stability(runs)
        out.append({"parameter": param, "conclusion": conclusion,
                    "range": [values[0], values[-1]] if values else None,
                    "n_values": len(values), **st,
                    "runs": [{"value": r["value"],
                              "answer": str(_hashable(r["result"])),
                              "error": r["error"]} for r in runs]})
    return out
