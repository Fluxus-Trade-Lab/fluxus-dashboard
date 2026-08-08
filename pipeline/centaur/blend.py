"""Property 2: the merge, with the human's influence bounded by measurement.

The paper's equation 5.3 combines a model fitted to data with a model fitted to
human judgement, subject to constraints on how far the combination may lean
either way. This module is the small, honest version of that: a weight for each
party, derived from measured skill, hard-capped so that neither can be silenced
and neither can take over.

Why cap BOTH ends. The paper's Mayo result — centaur > algorithm > human experts
— only exists because the human retained influence while being the weaker judge.
A merge that let measured skill drive the weight all the way to zero would have
reproduced the algorithm and lost the gain; one that let it run to one would have
reproduced the human and lost more. The floor and the ceiling are the finding,
not a hedge.

What this module refuses to do: pick a trade. It returns a view and the reason
it holds that view. Sizing, entry and exit stay outside this package.
"""
from __future__ import annotations

# Neither party is ever fully silenced or fully trusted. See the module note.
MIN_WEIGHT = 0.20
MAX_WEIGHT = 0.80
# Until a party has enough scored views, it gets this and no more.
UNPROVEN_WEIGHT = 0.35


def weight_from_skill(s: dict, baseline: float = 1 / 3) -> dict:
    """Turn a measured hit rate into a bounded weight.

    An unproven party is not treated as average — it is treated as *unproven*,
    which is a smaller number, because the cost of over-trusting a judge we have
    not measured is larger than the cost of under-weighting one we have.
    """
    if not s.get("enough") or s.get("hit_rate") is None:
        return {"weight": UNPROVEN_WEIGHT, "basis": "unproven",
                "detail": s.get("note")}
    # Map [baseline, 1.0] onto [0.5, MAX] and [0, baseline] onto [MIN, 0.5].
    hr = s["hit_rate"]
    if hr >= baseline:
        span = (1.0 - baseline) or 1.0
        w = 0.5 + (hr - baseline) / span * (MAX_WEIGHT - 0.5)
    else:
        span = baseline or 1.0
        w = MIN_WEIGHT + hr / span * (0.5 - MIN_WEIGHT)
    return {"weight": round(min(MAX_WEIGHT, max(MIN_WEIGHT, w)), 4),
            "basis": "measured", "detail": f"hit rate {hr:.1%} vs {baseline:.1%} chance"}


def merge(machine: dict, human: dict, w_machine: float, w_human: float) -> dict:
    """Combine two views into one, and say how it was reached.

    Conviction multiplies weight, so a party that is merely present counts for
    less than one that is committed. `stand_aside` contributes no score to any
    direction but is reported, because a party stepping back from a call the
    other is making is itself the finding on that day.
    """
    total = w_machine + w_human
    if total <= 0:
        raise ValueError("weights must sum to something positive")
    scores: dict[str, float] = {}
    contributions = []
    for v, w in ((machine, w_machine), (human, w_human)):
        share = w / total
        if v["direction"] == "stand_aside":
            contributions.append({"source": v["source"], "direction": "stand_aside",
                                  "share": round(share, 4), "counted": False})
            continue
        pts = share * v["conviction"]
        scores[v["direction"]] = scores.get(v["direction"], 0.0) + pts
        contributions.append({"source": v["source"], "direction": v["direction"],
                              "conviction": v["conviction"],
                              "share": round(share, 4), "points": round(pts, 4),
                              "counted": True})
    if not scores:
        return {"direction": "stand_aside", "agreed": True, "margin": 0.0,
                "scores": {}, "contributions": contributions,
                "note": "both parties stood aside"}

    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    top, top_pts = ranked[0]
    runner_pts = ranked[1][1] if len(ranked) > 1 else 0.0
    agreed = machine["direction"] == human["direction"]
    return {
        "direction": top,
        "agreed": agreed,
        "margin": round(top_pts - runner_pts, 4),
        "scores": {k: round(v, 4) for k, v in scores.items()},
        "contributions": contributions,
        "note": ("both parties agree" if agreed else
                 f"parties disagree; {top} carried by margin {top_pts - runner_pts:.2f}"),
    }


def centaur_view(machine: dict, human: dict, machine_skill: dict,
                 human_skill: dict) -> dict:
    """The whole merge, from two views and two measured records.

    Returns the combined view plus every input to it, so the result can be
    argued with rather than accepted.
    """
    wm = weight_from_skill(machine_skill)
    wh = weight_from_skill(human_skill)
    out = merge(machine, human, wm["weight"], wh["weight"])
    out["weights"] = {"machine": wm, "human": wh}
    return out
