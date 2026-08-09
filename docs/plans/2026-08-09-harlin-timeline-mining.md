# Six months of @TailThatWagsDog — what we were missing, by period

Mined from his X timeline 2026-01 → 2026-08, plus nextSignals and the Centaur
Model site. Everything below is a direct quote or a close paraphrase of a dated
post, with what it implies for us.

Context established first: **he is Stephen Harlin, MD**, who built an AI
Clinical Decision Support System before nextSignals. The vocabulary he keeps
using — "AI-driven **decision support**", "**personalization** of the
interpretation" — is CDSS vocabulary, not trading vocabulary. See
[the centaur gap](2026-08-09-centaur-gap.md).

---

## Jan–Mar: the institutional filter, and GEX-Volume as a ratio

**Mar 24–25 — "Bedtime SPX Options Analysis. Limit Order Book, APR/MAY/JUN
regulars, lot size > 10."** Output: *"The net positioning is unambiguously
bullish — institutions are simultaneously buying upside calls and selling …"*

Three screens in one line, and **we run none of them**:

| His screen | Why | Us |
|---|---|---|
| **Limit order book**, not the chain | resting institutional intent, not prints | we read OI only |
| **Regular monthly expiries** (APR/MAY/JUN) | monthlies are where institutions sit; weeklies are noise | we aggregate 5 nearest expiries + swing + monthly, undifferentiated |
| **lot size > 10** | screens retail out of the sample | **no size filter anywhere** |

The third is the big one. Our GEX weights every contract equally regardless of
who put it on. A book that is 60% retail one-lots and 40% institutional blocks
gets read as one homogeneous positioning.

**Mar 24 — "top 100 SPX assets preloaded with a high GEX-Volume ratio."** He
uses GEX-Volume as a **ratio** and screens on it. We built the volume-weighted
series two days ago and left it as a second column. A ratio to the OI-weighted
series is the actual signal: *today's flow relative to standing positioning*.

**Mar 31 — "Personalization of the AI-enabled Interpretation of the Auction
Market Process — an Upgrade. Happy with the chatbot's interpretation …"**
Personalization, in CDSS, means the system adapts to *this* clinician. Our brief
is identical for every reader and has no notion of whose judgement it is
informing.

---

## Apr–May: the hierarchy, and what the human is actually for

**Apr 7 — "What's driving the price auction is NOT the options Greeks. Duhhhh.
Think root cause. Think auction market process development."**

An explicit ordering: **the auction is the cause, the dealer book is
downstream.** Our `reference_map` treats the two frameworks as symmetric peers
and, when they conflict, reports the conflict without resolving it. He resolves
it, and always the same way. His own report says so too: *"under
framework-over-opinion the auction structure is primary."*

**Apr 7 — "Why it's the AI-Human Hybrid … the Centaur. You … the human … you
count. Humans Matter. Today I gave Claude **Live Market Maker-Informed options
data … not the Thinkorswim options chain**."**

This is the clearest statement of what the human contributes, and it is not
judgement about direction — **it is knowing which data to put in front of the
model.** Retail chain vs MM-informed feed is a choice no model can make for
itself, and it dominates everything downstream.

**Apr 1 — Thinkscript studies comparing buying premium to selling premium,
`Premium = Cost × Volume`, running live during RTH in watchlists.**

A concrete formula for the order-book layer, and note what it is *not*: not
contract counts, not delta-weighted. Dollars committed per side.

---

## Jun–Jul: levels are not enough, and the self-consistency warning

**Jul 17 — "levels alone are not enough to risk your money on."**

Said in reply to "how do you use it?". This is a direct description of the
failure mode our brief is in: we publish a ladder of prices. He is explicit that
a ladder is not a read.

**Jul 22 — "Your platform informs and when combined with **AI-driven decision
support** … the two are your secret weapon."** And, on what he brings:
*"18 years of writing Thinkscript and actively trading futures and options."*
The human half of the centaur is **domain expertise encoded as instrumentation**,
not intuition about tomorrow.

**Jul 28 — quoting Claude's own output back:** *"The eligibility screen thins the
book as expected, and the **self-consistency warning fires correctly when the
replicated baseline drifts from the model's own number**."*

**This is the single most transferable thing in six months of posts.** His
pipeline computes a number, independently *replicates a baseline* for it, and
**warns automatically when the two diverge**. We have run exactly this check by
hand — BS greeks against IBKR's, our regression against his printed slope — and
caught real errors each time. It has never been automated. Our own error log says
five of six errors were *correct arithmetic on a wrong input or definition*,
which is precisely the class a replicated baseline catches and a unit test does
not.

**Aug 9 — decision rules embedded in the database engine.** Mostly does not apply
to us (batch, small, single-user); the one point that did — dynamic thresholding
— produced the sensitivity sweep and the finding that our headline confluence was
not stable.

---

## What to build, ranked

| # | Item | Why it ranks here | Blocked? |
|---|---|---|---|
| 1 | **Self-consistency warnings** — every published number gets an independently replicated baseline and an automatic divergence alarm | attacks our documented #1 error class directly; needs no new data | no |
| 2 | **Auction-over-options precedence** in `synthesis` — when the frameworks conflict, the auction is root cause and says so | he states the rule; we currently report conflicts without resolving them | no |
| 3 | **GEX-Volume / GEX-OI ratio** as a first-class series | both series already exist; the ratio is the signal, the columns are not | no |
| 4 | **Institutional size filter** — lot size > 10, regular monthlies only | our positioning read does not distinguish retail from institutional at all | needs trade-level data (the OptionsFlow tape), not OI |
| 5 | **Limit order book** rather than the chain | resting intent vs settled positioning | needs a depth feed we do not have |
| 6 | **Personalization** — the brief adapts to whose judgement it informs | CDSS's core idea; presupposes the centaur log has content | needs n≥20 human views |

Items 1–3 are buildable now. 4 and 5 are data problems, not code problems, and
should be priced before being promised.
