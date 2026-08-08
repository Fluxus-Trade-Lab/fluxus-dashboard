"""Property 3: measure how much each party's judgement is worth.

The paper's constraint — "the influence of human input data on the final model's
parameters is constrained to ensure appropriate reliance on human intuition
given the specific traits of the environment, the degree of human expertise, and
feedback quality" — is the part everyone skips. Skipping it turns a centaur into
an average, and an average of a good judge and a bad one is worse than the good
judge alone.

So expertise is measured here, forward-only, from the log. Three refusals carry
the discipline:

* A view is scored against what happened AFTER it was recorded. Anything else is
  hindsight wearing a timestamp.
* `stand_aside` is never counted as a hit or a miss. It is a real decision, and
  folding it in either direction would flatter or punish it for free.
* Below `MIN_SCORED` the answer is "not enough" rather than a hit rate. Two
  correct calls out of three is not a skill estimate.
"""
from __future__ import annotations

# Enough that a hit rate is not dominated by one lucky week. Ten sessions of
# noise reads as 70% often enough to fool anyone, including us.
MIN_SCORED = 20

# What actually happened in a session, in the same vocabulary as a view.
OUTCOMES = ("up", "down", "range")


def outcome(open_: float, high: float, low: float, close: float,
            range_frac: float = 0.25) -> str:
    """Classify a session in the vocabulary the views use.

    `range` is not "small move" — it is a close that finished in the middle of
    its own range, i.e. an auction that went nowhere it could hold. The
    threshold is an argument because it is a choice, and one this project has
    learned to keep visible.
    """
    span = high - low
    if span <= 0:
        return "range"
    pos = (close - low) / span
    if range_frac <= pos <= 1 - range_frac:
        return "range"
    return "up" if close > open_ else "down"


def score_view(v: dict, actual: str) -> str | None:
    """`hit`, `miss`, or None when the view declined to call it."""
    if v["direction"] == "stand_aside":
        return None
    return "hit" if v["direction"] == actual else "miss"


def skill(rows: list[dict], source: str, outcomes: dict[str, str],
          horizon: str = "intraday") -> dict:
    """Hit rate for one party over the sessions that have a settled outcome.

    Also reports the rate weighted by conviction, because a party that is right
    when it says 3 and wrong when it says 1 is more useful than its flat hit
    rate suggests — and one with the opposite pattern is worse.
    """
    scored, weighted_hits, weight = [], 0.0, 0.0
    abstained = 0
    for r in rows:
        if r.get("source") != source or r.get("horizon") != horizon:
            continue
        actual = outcomes.get(r["session"])
        if actual is None:
            continue
        s = score_view(r, actual)
        if s is None:
            abstained += 1
            continue
        scored.append(s)
        weight += r["conviction"]
        if s == "hit":
            weighted_hits += r["conviction"]
    n = len(scored)
    hits = scored.count("hit")
    enough = n >= MIN_SCORED
    return {
        "source": source, "n_scored": n, "n_abstained": abstained,
        "hits": hits, "misses": n - hits,
        "hit_rate": (hits / n) if n else None,
        "conviction_weighted_rate": (weighted_hits / weight) if weight else None,
        "enough": enough,
        "note": None if enough else
                f"only {n} scored views; {MIN_SCORED} needed before this is a skill estimate",
    }


def edge_over_chance(s: dict, baseline: float = 1 / 3) -> float | None:
    """Hit rate minus the rate a coin would get across three live directions.

    Reported instead of the bare hit rate because 40% sounds bad and is, in
    fact, above chance here. The baseline is an argument since a party that
    never says `range` faces a different chance level.
    """
    return None if s["hit_rate"] is None else s["hit_rate"] - baseline
