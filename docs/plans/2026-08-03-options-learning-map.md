# Learning Map — Sosnoff/tastylive canon vs what TailThatWagsDog is actually inventing

**Date:** 2026-08-03
**Purpose:** Separate the borrowed layer from the original layer, so imitation is
deliberate rather than accidental.

---

## The single most useful finding

TailThatWagsDog is **fusing two schools that do not agree with each other**.

- **Sosnoff / tastylive:** markets are effectively random. Do not predict. Sell premium
  mechanically, at scale, and let occurrences do the work.
- **Dealer positioning (SpotGamma / MenthorQ lineage):** there *is* exploitable
  structure — dealer hedging creates locatable, repeatable flow at specific strikes.

Sosnoff says *"I don't believe that there's such a thing as a trend. It's just a random
case of multiple days in a row"* and *"it took me a really long time to realize that I
really don't know what's going to happen next."* A gamma-levels practitioner says the
opposite: here is the strike, here is why price reacts there.

**Neither is obviously right, and the tension is the interesting part.** Learn both
layers knowing they disagree — do not blend them into mush.

---

## Layer 1 — the tastylive canon (borrowed, well-documented, free)

This is the vocabulary layer. It is worth learning because it is where most of the
world's options language comes from, and because their research is genuinely large-sample.

**The mechanical core** (their headline backtest, SPY short strangle, 2005→2016+):
| Parameter | Their answer |
|---|---|
| Entry vol filter | IV Rank 50–100 |
| Strike | 16-delta each side |
| Tenor | 45 DTE |
| Profit target | close at 50% of credit |
| Time stop | manage at 21 DTE |
| Loss stop | credit doubles |

**Concepts to actually internalise:**
- **IV Rank / IV Percentile** — where current IV sits in its own history. Their entire
  entry logic is a percentile, not a level. *We have no percentile anywhere yet.*
- **Expected move** — and the habit of checking it against the real straddle.
- **POP / P50** — probability of profit vs probability of touching 50%.
- **Occurrences** — sample size as the source of edge, not per-trade accuracy.
- **Delta ≈ probability** — the 16-delta shorthand.
- **Theta decay + vega contraction** as two separate engines of a short-premium P&L.

**Philosophy worth taking:** position sizing over prediction; decision speed as an edge;
mechanical rules over discretion; humility about forecasting.

**Philosophy worth questioning:** the flat rejection of structure. If dealer positioning
is real, "markets are random" is too strong — and the GEX work in this repo assumes it
is too strong.

---

## Layer 2 — dealer positioning (borrowed from a different lineage)

Not taught by tastylive at all. Comes from the SpotGamma / MenthorQ world.
Already covered in `2026-08-03-gex-brief-productization.md`; in short: Zero Gamma,
Call/Put Wall, Volatility Trigger, Risk Pivot, charm pressure, ranked secondary levels.

**We are already competitive here.** That doc has the gap list.

---

## Layer 3 — what TailThatWagsDog is genuinely creating

Stripping out what he borrowed, four things look original:

**1. The fusion itself.** Applying tastylive's probabilistic discipline (expected move,
IV crush, mechanical checklists) *on top of* a dealer-positioning map. Neither parent
school does this.

**2. Live narration as the teaching method.** His cadence is
`premarket setup → intraday updates → post-session recap`, and the value is watching a
thesis survive or die in real time. His own line: *"Watching the flow ... as it flows ...
is where the edge is."* This is not a levels service; it is a **thinking-out-loud
service**. That is much harder to copy than a number, and much cheaper to produce.

**3. Path vs displacement, tracked publicly.** From 2026-07-31:
> *"Day range ~8.7 points against a ±5 pre-market straddle — realized vol blew past what
> was priced. IV 30.33% → 21.34%."*

He separates **how far price travelled** from **where it ended**, and scores the day
against what was priced. (This is the same distinction that corrected the "SPX options
are overpriced" read earlier in this repo's history.) **He publishes the scorecard.**

**4. AI-as-analyst as a content format.** The 2026-07-29 "AI option picking" test —
publish the prompt, publish the machine's answer, follow it as a natural history, and be
explicit that it is n=1 with no validated predictive value. Novel, honest, and highly
shareable.

---

## Layer 4 — what we could add that neither has

1. **Method transparency.** Every competitor's levels are proprietary. We can publish the
   formula. Already the proposed wedge.
2. **Bounded charm.** Our drift-to-expiry formulation vs their per-day rate — defensible
   and publishable (see `project_options_structure_engine`).
3. **Gamma × charm confluence as a named output.** Nobody surfaces it.
4. **A real hit-rate log.** He publishes a scorecard per day; nobody publishes a
   *cumulative* one. That is the gap.

---

## Study order (each step has something already built here)

| # | Study | Already in this repo |
|---|---|---|
| 1 | IV Rank / percentile | **missing — build it** (Phase 1) |
| 2 | Expected move vs realised range | `build_snapshot.py`, straddle pull |
| 3 | Delta ≈ probability, POP | `structure_eval.py` reports short-strike delta |
| 4 | Theta vs vega decomposition | `structures.py` net vega + `crush_pnl` |
| 5 | Dealer gamma map | `gex_levels.py` |
| 6 | Charm / time-driven hedging | `bs_charm` + confluence |
| 7 | Path vs displacement scorekeeping | **missing — Phase 2 hit-rate log** |

**Two gaps line up exactly with the productization plan**: IV percentile (Phase 1) and
the scorecard (Phase 2). Learning and building are the same work here.

## Caveat on imitation

Copy the **format and discipline** — cadence, checklist, published scorecard, honest
n-of-1 framing. Do not copy text; his posts are his. The transferable asset is the
*habit of scoring yourself in public*, which is also already the Fluxus brand position.

## Sources
- [Tom Sosnoff trading wisdom](https://inthemoneybyzerodha.substack.com/p/trading-wisdom-from-tom-sosnoff-lessons)
- [tastytrade backtesting methodology](https://tastytrade.com/learn/platforms-and-tools/research/backtest/)
- [tastytrade research review](https://www.sjoptions.com/does-tastytrade-work/)
- [@TailThatWagsDog on X](https://x.com/TailThatWagsDog)
