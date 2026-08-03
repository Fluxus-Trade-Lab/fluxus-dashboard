# Repeatable Process — what to add, what to cut

**Date:** 2026-08-03
**Question:** How do we turn the研究 into processes that run without heroics?

---

## The finding that should reshape the engine

His stated core principle:

> **"The tell isn't where the money sits. It's in the sequence (aka context)."**

Where OI sits is a static snapshot. What he trades is the **order in which things
happen** — *"SPX 0DTE flow tracked and identified five inflections today. Puts ran
$1.06B vs $461M calls … into an 83-point fade."* He counts **inflections**, not levels.

**Our entire GEX stack is static snapshots.** One pull, one picture, no memory of the
path. That is a real methodological gap, and it is the same gap that produced the
"SPX options are overpriced" error earlier in this repo: net displacement ≈ 0 while the
path travelled 1.32× the implied range. **Displacement is what a snapshot sees; the
sequence is what actually happened.**

Good news: `OptionsFlow` already models sequence (regime timeline, flips, runs,
anomalies). It is simply **not connected to the GEX brief**. That connection is the
single highest-value structural change available.

---

## His content system, sorted by whether it is repeatable

| Line | Repeatable? | Cost per unit |
|---|---|---|
| **ACE** — portfolio model, "Rotation Runway", **auto-updates each evening** | **fully automated** | ~0 |
| Daily 0DTE narration (premarket → intraday → recap) | manual, high discipline | high |
| Volume Profile teaching, 3-step sequences | episodic, evergreen | medium, reusable |
| AI-as-analyst experiments | event-driven | low, high engagement |
| Rebalancing critique / opinion | episodic | low |

**The pattern worth stealing:** the flagship is *machine-generated and self-updating*;
the human output is *narration and teaching on top of it*. He does not hand-produce the
data layer. Neither should we — and unlike him, our data layer is already built.

---

## 加法 — what to add

**A1. Wire OptionsFlow's sequence into the GEX brief.** *(highest value)*
The brief currently answers "where are the walls". It should also answer "what order did
today happen in": inflection count, regime flips, the run structure. Both engines exist;
nothing connects them.

**A2. The scorecard (Phase 2 as planned).** He publishes a per-day score. Nobody
publishes a **cumulative** one. Log every published level, score weekly.

**A3. Publish the build as content.** *(free, and we keep skipping it)*
This session alone produced publishable teaching moments as a **byproduct of building**:
- vega per vol-point vs per 1.00 sigma — a 100× error hiding in a unit
- solving IV off spot vs the forward — 1.1 vol points of silent bias
- charm's per-day rate being 92.6% an artifact of a time floor
- path vs displacement (the "overpriced" correction)
- a stale cash quote against a live future producing a fake +70 basis

Each is a short post, each is *already written* in the commit messages, and each
demonstrates method rather than claiming edge. **This is the "shows its work" wedge
executing itself.** Zero marginal cost.

**A4. Label AI-Human explicitly.** He tags it. It costs nothing and buys credibility.

## 减法 — what to cut

**S1. Do not do live intraday narration.** It is his highest-cost line and it needs a
US-hours human. RTH is 21:00–04:00 JST. **This is the one thing we structurally cannot
sustain** — and the archive already flags 断更 as the known failure mode.
→ Replace with **one premarket brief + one post-close recap**, both generated.

**S2. Do not chase multi-ticker breadth yet.** SPX + QQQ done properly beats 10 names
done thinly, and the marginal name adds cost with no new method.

**S3. Do not build a second dashboard.** The HTML brief is the dashboard. Adding a web
app before there is a reader is backwards.

**S4. Drop "one more metric" as the default improvement.** We have gamma, charm,
confluence, EM, VIX term, percentile, migration, ladder. The gap is **sequence and
interpretation**, not another greek.

---

## The three processes

### P1 — Daily brief (automated, ~0 human minutes)
```
07:00 ET  launchd → gex_levels.py            OI settled, premarket window
          → build_snapshot.py                json + html + md
          → append to levels log             for the scorecard
          → notify                           md ready to paste
```
Status: **~90% built.** Missing: the log append, and the launchd job pointing at the
new snapshot builder. Guardrails already exist (ET-window check, TWS probe, no silent
failure).

### P2 — Weekly scorecard (automated compute, ~15 human minutes)
```
Fri post-close → score the week's published levels against actual OHLC
               → cumulative hit-rate table
               → publish, unedited
```
The rule that makes it credible: **publish it whether or not it flatters us.** Same
discipline as the trade-log reviews.

### P3 — Build-as-content (~20 min per item, only when something is learned)
```
bug found / method corrected
  → the commit message is already the draft
  → 200-400 words: what was wrong, how it was caught, what changed
  → no claim of edge, only method
```
Trigger is **discovery, not calendar** — which is why it cannot go stale.

---

## Sequencing

1. **P1 to fully automated** — finish the log append + launchd wiring. *≈half a day.*
2. **A1, sequence into the brief** — the real methodological upgrade. *≈1 day.*
3. **P2 scorecard** — needs ~2 weeks of P1 logs before it says anything. Build the
   scorer now, publish when n is respectable.
4. **A3 build-as-content** — start immediately; the backlog is already written.

## The honest constraint

He posts through the US session because he lives there. **We cannot copy the cadence.**
What we can copy is the **discipline** — scoring in public, showing the machinery,
labelling the AI honestly — and deliver it on a schedule that survives JST. One
generated brief that never misses beats three manual posts that stop in week three.
