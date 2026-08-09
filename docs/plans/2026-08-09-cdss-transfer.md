# What clinical decision support knows that we didn't

Harlin built an AI Clinical Decision Support System before nextSignals, and the
vocabulary he never drops — "AI-driven **decision support**", "**personalization**
of the interpretation" — is CDSS vocabulary. CDSS has spent twenty years on the
one question we only started asking last week: **how should a human and a model
share a decision without the pair being worse than either alone.**

The literature has numbers. Ours has none yet, so theirs is the prior.

---

## 1. The price of a centaur is measurable, and it is not zero

Kern et al., automation bias under time pressure in computational pathology
(arXiv 2411.00998). 28 trained pathology experts, 560 AI-aided estimates:

| | |
|---|---|
| AI integration on performance | **significant improvement**, F(1,108)=8.32, p<.01 (mean error 13.55 → 11.74) |
| **Positive consultations** — AI corrected a wrong human call | **29** |
| **Negative consultations** — AI overturned a call the human had RIGHT | **38** |
| **Automation-bias rate** | **~7%** (38/560) |

Read those together, because either alone is propaganda. **On the flip cases the
AI was net harmful — 29 saves against 38 breaks — and overall accuracy still
improved significantly.** Both true. A centaur that reports only the aggregate is
hiding the 7%; one that reports only the 7% is arguing against a system that
demonstrably worked.

**Built:** `skill.consultations()` keeps exactly this ledger, and
`score_views.py` prints it every post-close. Until it has rows, "the merge helps"
is an assertion, and it currently has zero rows and says so.

## 2. Time pressure does not change the error rate — it doubles the cost

Same study. Automation bias occurred at ~7% **with or without** a 10-second
countdown. But when it occurred under pressure the damage roughly doubled
(mean deviation 19.42 → 27.79), and reliance on the machine **rose** (0.49 →
0.55 overall; 0.58 → 0.65 on precisely the cases where following was wrong).

The dangerous combination is not "rushed people make more mistakes". It is
**people defer more at exactly the moment deferring is most expensive.**

**Built:** `skill.under_pressure()` splits views by whether they were filed
inside RTH. We cannot measure reliance directly, but recording the condition is
the prerequisite for ever testing it. Current state: 7 filed calm, 2 while
trading.

## 3. Explanation stability is a mechanism, not an aesthetic

From the calibrated-trust literature: **higher explanation stability across
near-identical inputs improves calibrated trust and reduces automation bias.**

We already built the instrument for this and filed it under the wrong heading.
The sensitivity sweep found our headline confluence flipped between a 5.0pt and
a 7.5pt tolerance. I treated that as a correctness problem. It is also a **trust
calibration** problem: a brief whose conclusions move on a parameter the reader
cannot see teaches them either to over-trust it or to stop reading. Stability is
the thing being communicated, not a footnote about it.

## 4. Experts and novices need opposite explanations

Novices benefit from **prescriptive counterfactuals**; experts from **concise,
faithful cues aligned with their existing schema**.

Andy is the expert case. This is independent support for the standing rule —
"calculate and test, I decide" — arrived at from the other direction: a
prescriptive brief would be the wrong shape for this reader regardless of whether
prescription is appropriate. What an expert wants is the measurement in his own
vocabulary, which is what "auction says WHAT, dealer book says WHERE" is.

## 5. Two failure modes we have no defence against

**Alert fatigue.** CDSS's oldest and most expensive lesson: alerts that fire too
often get dismissed reflexively, and then the one that mattered gets dismissed
too. We now emit nine self-consistency checks, a conflicts list, a resolution, a
hot-strikes list and a track record — every session, whether or not anything
changed. **Nothing in our system suppresses an alert that fires every day.**

**Deskilling.** If the human routinely lets the model filter and frame, they stop
doing the reasoning that made them worth merging with. This is a real risk for a
centaur specifically: the better the machine's brief, the less the human
practises forming a view without it. The mitigation the literature suggests is
ordering — **the human commits first, then sees the machine.**

Our current order is the wrong way round. The brief is pushed at 07:30 and Andy
logs a view afterwards, if at all, having already read it. That is not an
independent second opinion; it is an anchored one.

---

## What this changes

| Change | Why |
|---|---|
| **Consultation ledger** — built | "the merge helps" needs a denominator |
| **Pressure flag on views** — built | same error rate, double cost, more deferral |
| Sensitivity sweep reframed as **trust calibration**, not just correctness | stability is what is being communicated |
| **Human commits before seeing the brief** — NOT built | the current order anchors the human and courts deskilling |
| **Alert suppression** — NOT built | nine checks that always pass will be skimmed within a fortnight |

The last two are the real work. The first is an ordering change to the daily
chain: log the view, then read the brief. The second needs a rule for what
counts as *news* — an alert should fire when a check changes state, not when it
runs.

## Sources

- Kern et al., *Automation Bias in AI-Assisted Medical Decision-Making under
  Time Pressure in Computational Pathology*, arXiv 2411.00998 — the 7% number
  and the pressure result
- Saghafian & Idan, *Effective Generative AI: The Human-Algorithm Centaur*,
  HDSR 6(4) 2024 — the symbiotic-learning framework already built
- Calibrated-trust and appropriate-reliance literature on explanation stability,
  expert/novice explanation preference, alert fatigue and deskilling
