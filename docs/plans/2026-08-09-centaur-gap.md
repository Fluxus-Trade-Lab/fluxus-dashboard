# What we were missing: we were not building a centaur

Source: @TailThatWagsDog is **Stephen Harlin, MD** — a reconstructive plastic
surgeon who built an AI Clinical Decision Support System before he built
nextSignals. His bio is the thesis: *"Realizing the AI-human hybrid and Centaur
in financial modeling."* Every chart he publishes cites the same two papers:

* Silberzahn & Jones, "Chess, Centaurs and Your Future as an Investor," *Forbes*, 2015
* **Saghafian & Idan, "Effective Generative AI: The Human-Algorithm Centaur,"
  *Harvard Data Science Review* 6(4), 2024** (arXiv 2406.10942)

His methodology is not from trading. It is from **clinical decision support**.
We spent weeks on the tastylive / Steidlmayer lineage and were reading the wrong
shelf.

## The finding that reframes the project

The paper names our arrangement as an anti-pattern. In its taxonomy, human input
that is *"used orthogonally to the AI model … by working on a different set of
records than the machine"* is **workload partitioning**, explicitly distinguished
from centaurs.

**"I compute, you decide" is workload partitioning.** The machine emits numbers,
the human decides, and the decision evaporates. Nothing learns. We have a
scorecard for the machine's levels and *zero records of Andy's judgement* — in
eight months.

## The empirical result that makes it worth fixing

In the paper's Mayo Clinic experiment the ranking was:

> **centaur > algorithm > human experts**

The best human expert was *significantly below the algorithm alone*, and feeding
that human's intuition to the algorithm still produced a gain. Both naive
positions are wrong: "trust the human" loses to the algorithm, and "trust the
algorithm" loses to the centaur.

## Symbiotic learning — the three properties, and what each demands of us

| Paper's property | What we had | What was built |
|---|---|---|
| 1. Learning uses multiple inputs, at least one a record of **subjective** human judgement | nothing — Andy's calls were never recorded | `pipeline/centaur/log.py` |
| 2. Human input enters the combined estimate **directly**, not beside it | n/a | `pipeline/centaur/blend.py` |
| 3. Its influence is **constrained** by measured expertise and feedback quality | assumed, never measured | `pipeline/centaur/skill.py` |

Property 3 is the one everyone skips, and skipping it turns a centaur into an
average — which is worse than the better judge alone.

## Design choices that carry the paper's result

* **Neither party can be silenced or take over** (`MIN_WEIGHT` 0.20,
  `MAX_WEIGHT` 0.80). The Mayo gain exists *because* the weaker judge kept
  influence. A merge that let measured skill run to zero would reproduce the
  algorithm and lose the gain.
* **Unproven ≠ average.** A party with too few scored views gets 0.35, not 0.5.
  Over-trusting an unmeasured judge costs more than under-weighting one.
* **`stand_aside` is a first-class direction**, never a hit and never a miss.
  "I have no view" is data about calibration.
* **Conviction multiplies weight**, so presence alone is not a vote.
* **`asof` is required.** A view recorded after the fact is a memory.
* **One view per party per session per horizon** — no revising once the tape moved.

## What this is not

The machine states a **prediction**, which gets scored. It never states a
**recommendation**, which would get followed. Nothing in this package sizes a
position. The merge informs Andy's decision; it does not replace it.

## Day one, run for real

```
machine  weight 0.58   measured: hit rate 52.2% vs 33.3% chance
human    weight 0.35   unproven: 0 scored views
```

The machine already has a record — 52.2% of tested levels held, above the 33.3%
three-way chance line. Andy has none, so he is capped at 0.35 until he has 20
scored views. **That number is the whole point: it goes up only by him logging
calls and being right.**

## Next

1. A one-line way for Andy to log a view — anything heavier will not get used.
2. Machine views generated from the brief each session, so the pairing accrues
   without effort.
3. Score both against session outcomes; the weights then move on their own.
4. Revisit at n=20: the first honest comparison of the two judges.
