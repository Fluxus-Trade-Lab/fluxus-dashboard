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

# The size of edge this gate is entitled to claim it can find. Everything below
# follows from it: `MIN_SCORED` is now computed, not chosen.
#
# It was chosen once. `MIN_SCORED = 20` sat here as a bare number with no
# reference to any effect, and the arithmetic it implied was never run. At
# n=20 the 95% interval on a hit rate is +/-22 points and the power to see a
# 60%-vs-50% edge is 22% -- so four times in five a real edge would be in the
# data and this gate would still say "not enough", without ever saying not
# enough FOR WHAT. That is the `free_parameter` class from our own taxonomy,
# committed inside the module whose job is to police it.
#
# 0.60 is a deliberate choice and an expensive one: 153 sessions, most of a
# trading year. Claiming to detect 0.55 instead would cost 617 sessions, about
# two and a half years, which is the honest price of a small edge and the
# reason small-edge claims are not decidable on a daily cadence.
from pipeline.reference import power as PW

CLAIMED_EDGE = 0.60
NULL_RATE = 0.50
MIN_SCORED = PW.sessions_needed(CLAIMED_EDGE, NULL_RATE)  # 153

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
    # Carried alongside the rate so the rate can never be read without it. A
    # hit rate at n=6 is not a weak measurement of skill; it is not a
    # measurement of skill, and `power` is what says so in numbers.
    pw = PW.verdict(n, CLAIMED_EDGE, NULL_RATE) if n else None
    return {
        "source": source, "n_scored": n, "n_abstained": abstained,
        "hits": hits, "misses": n - hits,
        "hit_rate": (hits / n) if n else None,
        "conviction_weighted_rate": (weighted_hits / weight) if weight else None,
        "enough": enough,
        "power": pw,
        "note": None if enough else _thin_note(n, pw),
    }


def _thin_note(n: int, pw: dict | None) -> str:
    """Say not-enough FOR WHAT, and what this sample could see if it were there.

    The floor clause is built as a whole sentence per branch rather than by
    concatenating a shared prefix onto two endings — that shape produced "only
    an edge of no size is visible" at n=2, which is the third time in this
    project a correct guard has been let down by the string that reports it.
    """
    head = (f"only {n} scored views; {MIN_SCORED} needed to detect a "
            f"{CLAIMED_EDGE:.0%} edge against {NULL_RATE:.0%} at 80% power")
    if not pw:
        return head
    tail = f" — at n={n} the rate is +/-{pw['interval_half_width'] * 100:.0f} points"
    floor = pw["smallest_detectable"]
    if floor is None:
        return f"{head}{tail}, and no edge of any size is visible"
    return f"{head}{tail}, and only an edge of {floor:.0%} or better is visible"


def edge_over_chance(s: dict, baseline: float = 1 / 3) -> float | None:
    """Hit rate minus the rate a coin would get across three live directions.

    Reported instead of the bare hit rate because 40% sounds bad and is, in
    fact, above chance here. The baseline is an argument since a party that
    never says `range` faces a different chance level.
    """
    return None if s["hit_rate"] is None else s["hit_rate"] - baseline


# ---------------------------------------------------------- consultations

def consultations(paired: list[dict], outcomes: dict[str, str],
                  merged: dict[str, str] | None = None) -> dict:
    """The accounting a centaur owes: when the merge overrode a party, did it help?

    Taken from the automation-bias literature that Harlin's CDSS background sits
    in. Kern et al. measured 28 pathology experts over 560 AI-aided estimates and
    split every case where the human changed their mind into:

        positive consultation — AI corrected a decision the human had wrong
        negative consultation — AI overturned one the human had RIGHT

    They found 29 positive against 38 negative, an **automation-bias rate of
    ~7%**. Note what that means: on the flip cases alone the AI was net harmful,
    and overall performance still improved significantly. Both facts are true and
    a centaur that reports only one of them is selling something.

    So this is the ledger we owe. Without it "the merge helps" is an assertion.

    `merged` maps session -> the direction the merge actually produced. When it
    is omitted the machine's direction stands in, which is what an unweighted
    merge would do — stated rather than silently assumed.
    """
    pos, neg, both_right, both_wrong = [], [], [], []
    for p in paired:
        s = p["session"]
        actual = outcomes.get(s)
        if actual is None:
            continue
        h = p["human"]["direction"]
        m = p["machine"]["direction"]
        if h == "stand_aside" or m == "stand_aside":
            continue                       # no override happened, so no verdict
        outcome_of = (merged or {}).get(s, m)
        h_ok, o_ok = (h == actual), (outcome_of == actual)
        if h == outcome_of:
            (both_right if h_ok else both_wrong).append(s)
        elif o_ok and not h_ok:
            pos.append(s)                  # the merge saved a wrong human call
        elif h_ok and not o_ok:
            neg.append(s)                  # the merge broke a right one
        else:
            both_wrong.append(s)
    n = len(pos) + len(neg) + len(both_right) + len(both_wrong)
    return {
        "n_scored_pairs": n,
        "positive": pos, "negative": neg,
        "n_positive": len(pos), "n_negative": len(neg),
        "n_agreed_right": len(both_right), "n_agreed_wrong": len(both_wrong),
        # The headline: how often the merge broke a call the human had right.
        "automation_bias_rate": (len(neg) / n) if n else None,
        "net_consultations": len(pos) - len(neg),
        "reference": "Kern et al. measured ~7% (38/560) in computational pathology, "
                     "against 29 positive consultations — net negative on flips while "
                     "overall accuracy still improved",
    }


def under_pressure(rows: list[dict]) -> dict:
    """Split views by whether they were filed while the market was trading.

    The same study found time pressure did NOT change the automation-bias RATE
    (7% either way) but roughly doubled its cost when it happened — mean error
    19.4 to 27.8 — and that reliance on the machine ROSE under pressure
    (0.49 to 0.55). The dangerous combination is deferring more at exactly the
    moment deferring is most expensive.

    We cannot measure reliance directly, but we can record the condition, which
    is the prerequisite for ever testing it here.
    """
    import datetime as dt
    calm, live = [], []
    for r in rows:
        stamp = (r.get("asof") or "")[11:16]
        try:
            t = dt.time(int(stamp[:2]), int(stamp[3:5]))
        except (ValueError, IndexError):
            continue
        (live if dt.time(9, 30) <= t <= dt.time(16, 0) else calm).append(r)
    return {"calm": len(calm), "live": len(live),
            "note": "views filed during RTH are the ones the literature says carry "
                    "the same error rate at roughly double the cost"}
