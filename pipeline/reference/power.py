"""How many sessions before a claim about skill becomes decidable.

Written 2026-08-11, in answer to a question worth more than most of the code
here: if there were a repeatable edge in front of us, could we tell?

The honest answer was no, and the arithmetic says why. `centaur.skill` gates on
`MIN_SCORED = 20`, a number invented with no reference to any effect size. At
n=20 the 95% interval on a hit rate is ±22 points, and the power to detect a
60%-vs-50% edge is 22% — meaning four times out of five a real 60% edge would
be sitting in the data and the gate would still read "not enough". Worse, it
does not read "not enough *for what*", so the threshold looks like a standard
when it is a guess. That is the `free_parameter` class from this project's own
error taxonomy, committed inside the module whose job is to police exactly it.

This module replaces the guess with a statement. Nothing here is novel — it is
the normal-approximation power calculation for one proportion — and that is the
point: the number was always computable, and was never computed.

Two things it makes impossible to avoid:

  * **A threshold has to name its effect size.** `sessions_needed(0.60)` is 152
    sessions. `sessions_needed(0.55)` is 616, about two and a half trading
    years. A gate that does not say which of these it is claiming is not a gate.
  * **Probes are not free.** Twenty independent checks at α=0.05 produce at
    least one false positive 64% of the time. This repo emits nine consistency
    checks, a pattern checklist, a transition state, a flow ratio and a
    conflict list every single session. `family_error()` prices that, and it is
    the arithmetic behind the two NULL results already on record — 0 of 42
    mined sequences beating a matched baseline, and a 52-week-high momentum
    filter with negative alpha. Both looked like findings first.
"""
from __future__ import annotations

from math import ceil, sqrt
from statistics import NormalDist

_N = NormalDist()

# Trading days in a year, for turning a sample size into a wait.
SESSIONS_PER_YEAR = 252


def power(n: int, p1: float, p0: float = 0.5, alpha: float = 0.05) -> float:
    """Chance of detecting a true rate `p1` against null `p0` with `n` trials.

    One-sided: we only care about beating the null, never about proving we are
    worse than a coin. Normal approximation, which is adequate above roughly
    n=20 and is stated rather than hidden because below that the answer is
    "nowhere near enough" by any method.
    """
    if n <= 0 or not 0 < p1 < 1 or not 0 < p0 < 1:
        raise ValueError("n must be positive and rates strictly between 0 and 1")
    crit = p0 + _N.inv_cdf(1 - alpha) * sqrt(p0 * (1 - p0) / n)
    return 1 - _N.cdf((crit - p1) / sqrt(p1 * (1 - p1) / n))


def sessions_needed(p1: float, p0: float = 0.5, alpha: float = 0.05,
                    beta: float = 0.20) -> int:
    """Sample size to detect `p1` against `p0` at (1-beta) power."""
    if p1 == p0:
        raise ValueError("an effect size of zero needs infinite sessions — "
                         "name the edge you are claiming")
    za, zb = _N.inv_cdf(1 - alpha), _N.inv_cdf(1 - beta)
    n = ((za * sqrt(p0 * (1 - p0)) + zb * sqrt(p1 * (1 - p1))) / (p1 - p0)) ** 2
    return ceil(n)


def interval(n: int, p: float = 0.5, conf: float = 0.95) -> float:
    """Half-width of the confidence interval on a rate — how blurry `n` is.

    Defaulting to p=0.5 gives the WIDEST interval for that n. A gate should be
    designed against its worst case, not its most flattering one.
    """
    if n <= 0:
        raise ValueError("n must be positive")
    return _N.inv_cdf(1 - (1 - conf) / 2) * sqrt(p * (1 - p) / n)


def family_error(k: int, alpha: float = 0.05) -> float:
    """Chance that at least one of `k` independent probes fires by luck alone."""
    if k < 0:
        raise ValueError("k must be non-negative")
    return 1 - (1 - alpha) ** k


def detectable(n: int, p0: float = 0.5, alpha: float = 0.05,
               beta: float = 0.20) -> float | None:
    """The SMALLEST edge `n` sessions can actually find.

    The inverse of the question everyone asks. Anything closer to the null than
    this is invisible at that sample size, so a scorecard sitting on `n` and
    reporting "no edge" is only entitled to say "no edge of at least this size".
    Returns None when n cannot reach any rate below certainty.
    """
    lo, hi = p0 + 1e-9, 1 - 1e-9
    if power(n, hi, p0, alpha) < 1 - beta:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        if power(n, mid, p0, alpha) < 1 - beta:
            lo = mid
        else:
            hi = mid
    return hi


def verdict(n: int, claimed: float, p0: float = 0.5, alpha: float = 0.05,
            beta: float = 0.20) -> dict:
    """What `n` sessions entitle a claim of `claimed` to say. Never a boolean.

    `status` is one of:

      ``decidable``    n meets the power requirement for that effect
      ``underpowered`` the claim may well be true and this sample cannot show it
    """
    need = sessions_needed(claimed, p0, alpha, beta)
    pw = power(n, claimed, p0, alpha) if n > 0 else 0.0
    floor = detectable(n, p0, alpha, beta) if n > 0 else None
    short = max(0, need - n)
    return {
        "n": n, "claimed": claimed, "null": p0,
        "power": pw, "sessions_needed": need, "short_by": short,
        "interval_half_width": interval(n) if n > 0 else None,
        "smallest_detectable": floor,
        "status": "decidable" if n >= need else "underpowered",
        "note": (f"n={n} gives {pw:.0%} power against a claimed {claimed:.0%}; "
                 f"{need} sessions needed ({need / SESSIONS_PER_YEAR:.1f} trading "
                 f"years), short by {short}"
                 + (f". At this n only an edge of {floor:.0%} or better is "
                    f"visible at all" if floor else
                    ". At this n no edge is reliably visible")),
    }


def years_to_decide(p1: float, fires_per_year: float, p0: float = 0.5,
                    alpha: float = 0.05, beta: float = 0.20) -> dict:
    """Calendar time before a CONDITIONAL claim becomes decidable.

    The question that actually matters, and the one `sessions_needed` alone
    cannot answer. A pattern is not observed every session — it is observed when
    its conditions are met — so the wait is set by two numbers together: how big
    the edge is, and how often the setup appears.

    They pull against each other. A filter selective enough to produce a large
    edge fires rarely, and a filter that fires daily is too loose to produce
    one. Between them sits a narrow band of claims a daily practice can settle
    inside a working horizon, and everything outside it is a claim we may hold
    but must not pretend to be testing.

    This is why a published setup arrives as a ten-condition checklist rather
    than a tendency. The conditions are not decoration; they are what buys an
    effect large enough to be found before the decade is out.
    """
    if fires_per_year <= 0:
        raise ValueError("a setup that never fires can never be decided")
    n = sessions_needed(p1, p0, alpha, beta)
    return {"edge": p1, "occurrences_needed": n,
            "fires_per_year": fires_per_year,
            "years": n / fires_per_year,
            "decidable_within_3y": n / fires_per_year <= 3.0}


def frontier(edges=(0.60, 0.65, 0.70, 0.75, 0.80),
             rates=(4, 12, 26, 52, 126, 252)) -> str:
    """Years-to-decide across effect size and how often the setup appears.

    Read it as the shape of what is knowable here, not as a target. Cells inside
    three years are claims a daily practice can actually settle.
    """
    out = ["Years to decide, by edge (rows) and setups per year (columns).",
           "  '.' = settled inside 3 years.", ""]
    out.append("  edge  n   " + "".join(f"{r:>8}/yr" for r in rates))
    for e in edges:
        n = sessions_needed(e)
        cells = ""
        for r in rates:
            y = n / r
            cells += f"{y:>7.1f}{'.' if y <= 3 else ' '}"
        out.append(f"  {e:.0%}  {n:>3}   {cells}")
    return "\n".join(out)


def report(ns=(6, 20, 60, 120, 252, 504), edges=(0.55, 0.60, 0.65, 0.70)) -> str:
    """The table this module exists to keep in front of us."""
    out = ["Sessions needed for 80% power against a 50% null:"]
    for e in edges:
        n = sessions_needed(e)
        out.append(f"  {e:.0%} hit rate ...... {n:>5} sessions "
                   f"({n / SESSIONS_PER_YEAR:.1f} trading years)")
    out.append("")
    out.append("What a given sample can see:")
    for n in ns:
        f = detectable(n)
        out.append(f"  n={n:<4} ±{interval(n) * 100:4.1f} pts   "
                   + (f"smallest visible edge {f:.0%}" if f
                      else "no edge reliably visible"))
    out.append("")
    out.append("Probes are not free — P(at least one false positive), α=0.05:")
    for k in (1, 5, 10, 20, 42):
        out.append(f"  {k:>3} probes ...... {family_error(k):5.1%}")
    return "\n".join(out)
