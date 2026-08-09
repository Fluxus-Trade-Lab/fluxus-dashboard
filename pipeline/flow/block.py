"""Which prints are blocks — thresholded on dollars, not on contract count.

@TailThatWagsDog screens the book at `lot size > 10`. Contract count is a proxy
for size; premium is size itself. On SPX, where per-contract prices span
$0.10 to $211 in a single session, a fixed lot threshold cannot mean one thing.

**This was asserted before it was tested, which was the wrong order.** Measured
on 26,837 real SPX prints from 2026-08-07 (expiry 2026-08-10, ±8 strikes around
a 7,757.64 close, $108.9M of premium):

    corr(size, premium) = +0.29

Weak enough that the two rules are genuinely different instruments rather than
the same one described twice. At matched selectivity — the same NUMBER of prints
selected, so neither rule wins by being greedier:

    lot >= 10   -> 1,865 prints, 42.6% of session premium
    top 1,865 by premium ->      59.5% of session premium     +17.0 points

and the two picked the same print only 32.3% of the time. The prints each rule
took *alone* say exactly what the mechanism is:

    his only  — median $1.65/contract, 1.19% out of the money
    mine only — median $34.77/contract, 0.42% out of the money

So the specific claim holds: a fixed lot threshold buys cheap wings and skips
the money. It holds at every threshold from 2 to 100 (gap +10 to +17 points),
and to capture half the session's premium the lot rule needs **3x more prints**.

**What lot count still knows that premium does not.** A thousand far-OTM wings
bought as one-lots is tail hedging, and it is institutional; premium ranks each
print low even though the campaign is large. Premium finds where the money is in
a single print; lot count carries a signature of *behaviour*. Both are stored,
the threshold is on premium, and neither is called "institutional" — see below.

**Why this is `block`, never `institutional`.** Institutions slice. A 500-lot
worked as fifty 10-lots by an algo is indistinguishable from fifty retail
10-lots to any per-print rule. That is a limit of the measurement, not a
threshold to tune. These functions find blocks.

One session, one expiry, one underlying. The direction of the effect is large
and consistent across thresholds; the magnitude should not be quoted as a
constant.
"""
from __future__ import annotations

CONTRACT_MULTIPLIER = 100

# $10,000 of premium in a single print. Near the measured top-1,865 boundary on
# the sample session ($10,337), so it is calibrated rather than round-numbered.
BLOCK_PREMIUM = 10_000.0
# Kept because it is how everyone else screens, and because it carries the
# behavioural signature premium misses. Reported, never the gate.
CONVENTIONAL_LOT = 10


def premium(price: float, size: float) -> float:
    return price * size * CONTRACT_MULTIPLIER


def tag_prints(prints: list[dict], block_premium: float = BLOCK_PREMIUM,
               lot: int = CONVENTIONAL_LOT) -> list[dict]:
    """Annotate each print with its premium and both rules' verdicts.

    Prints with a non-positive price or size are dropped: a zero-premium print
    is a feed artefact, and letting it through would deflate every share below.
    """
    out = []
    for p in prints:
        px, sz = p.get("price"), p.get("size")
        if not px or not sz or px <= 0 or sz <= 0:
            continue
        prem = premium(px, sz)
        out.append({**p, "premium": prem,
                    "is_block": prem >= block_premium,
                    "is_large_lot": sz >= lot})
    return out


def block_share(tagged: list[dict]) -> dict:
    """What fraction of premium arrived in blocks, and how the rules differ.

    `agreement` is carried because it is the number that says whether the choice
    of rule mattered on this data — at 100% the argument above is moot.
    """
    if not tagged:
        return {"n": 0, "total_premium": 0.0, "block_share": None,
                "large_lot_share": None, "agreement": None}
    total = sum(t["premium"] for t in tagged)
    blk = sum(t["premium"] for t in tagged if t["is_block"])
    lot = sum(t["premium"] for t in tagged if t["is_large_lot"])
    agree = sum(1 for t in tagged if t["is_block"] == t["is_large_lot"])
    return {
        "n": len(tagged),
        "n_block": sum(1 for t in tagged if t["is_block"]),
        "n_large_lot": sum(1 for t in tagged if t["is_large_lot"]),
        "total_premium": total,
        "block_premium": blk,
        "block_share": blk / total if total else None,
        "large_lot_share": lot / total if total else None,
        "agreement": agree / len(tagged),
    }


def by_strike(tagged: list[dict]) -> dict[float, dict]:
    """Block share per strike — the per-strike series the brief can use.

    A strike is reported only if something traded there. Zero premium and no
    prints are different facts, and a strike nobody touched should not appear
    with a 0% block share as though it had been measured.
    """
    acc: dict[float, dict] = {}
    for t in tagged:
        k = t.get("strike")
        if not isinstance(k, (int, float)):
            continue
        s = acc.setdefault(float(k), {"premium": 0.0, "block_premium": 0.0,
                                      "n": 0, "n_block": 0})
        s["premium"] += t["premium"]
        s["n"] += 1
        if t["is_block"]:
            s["block_premium"] += t["premium"]
            s["n_block"] += 1
    for s in acc.values():
        s["block_share"] = s["block_premium"] / s["premium"] if s["premium"] else None
    return acc


def compare_rules(prints: list[dict], lot: int = CONVENTIONAL_LOT) -> dict:
    """Run both rules at MATCHED selectivity and report the gap.

    Matched selectivity is the whole point. Comparing `lot >= 10` against
    `premium >= $10k` compares two different sample sizes, and the greedier rule
    wins for free. Selecting the same NUMBER of prints by each criterion is the
    only comparison that isolates the criterion.
    """
    tagged = tag_prints(prints, lot=lot)
    if not tagged:
        return {"n": 0, "gap_pct_points": None}
    total = sum(t["premium"] for t in tagged)
    by_lot = [t for t in tagged if t["is_large_lot"]]
    k = len(by_lot)
    if not k or not total:
        return {"n": len(tagged), "gap_pct_points": None,
                "note": f"no print reached {lot} lots on this sample"}
    by_prem = sorted(tagged, key=lambda t: -t["premium"])[:k]

    def key(t):
        return (t.get("strike"), t.get("right"), t.get("time"), t["size"], t["price"])

    share_lot = sum(t["premium"] for t in by_lot) / total
    share_prem = sum(t["premium"] for t in by_prem) / total
    return {
        "n": len(tagged), "n_selected": k,
        "lot_threshold": lot,
        "premium_threshold": by_prem[-1]["premium"],
        "share_by_lot": share_lot,
        "share_by_premium": share_prem,
        "gap_pct_points": (share_prem - share_lot) * 100,
        "overlap": len({key(t) for t in by_lot} & {key(t) for t in by_prem}) / k,
    }
