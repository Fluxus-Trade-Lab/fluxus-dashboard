# What he is actually building — the whole stack, and where we sit in it

Written 2026-08-12 from two posts that morning plus the eighteen months already
mined ([Jan–Jul 2026](2026-08-09-harlin-timeline-mining.md),
[2025](2026-08-09-harlin-2025.md), [the centaur gap](2026-08-09-centaur-gap.md),
[size and book](2026-08-09-size-and-book.md)).

The two posts changed the picture more than any single day before them, because
they showed the two layers we had never seen: **the portfolio** and **the
validation regime**. Everything we had mined until now was the middle of his
stack. We had been reading his instruments and mistaking them for his system.

---

## The stack

| | Layer | What he does | Us |
|---|---|---|---|
| **L0** | **Data selection** | MM-informed options feed, *not* the retail chain. Limit order book, not the settled chain. Regular monthlies. Lot > 10. | retail chain, OI only, all expiries pooled, no size filter |
| **L1** | **Instrument** | **SPY 30-min RTH profile** is the model surface — value, levels, scenarios all from there. ES is only the *overnight probe*: did those levels get reached and accepted before the open. | TPO on SPX, volume on ES, deliberately unconverted — which is why "do VPOC and TPOC coincide" was unanswerable for us until 3 days ago |
| **L2** | **Auction primitives** | Jones: mode/POC, value as **1σ**, **skewness**, **kurtosis**, TFF | strongest layer we have. We now hold both value definitions, both moments, LVNs, tails, poor extremes, single prints |
| **L3** | **Framework precedence** | auction is **root cause**; dealer book downstream; dark pools a third peer | precedence rule implemented. Dark pools: nothing, needs a vendor |
| **L4** | **The gate** | **"No trade until the market is facilitating trade"** — price must extend beyond the IB *and build there*, not print through on the headline | built today (`profile/facilitation.py`). This was our first gate of any kind |
| **L5** | **Portfolio** | named, versioned books with inception dates. Long-only index core + **defined-risk** overlays on dislocations. "Convexity comes from position structure, not from predicting anything." | **nothing.** We emit readings. There is no book |
| **L6** | **Validation** | kill-tests against **its own control**, out-of-sample splits. 17 vol signals died, a leverage overlay died, 8 base assets lost to plain SPY. Objective = **max drawdown**, −4.9% vs SPY −8.9% | power arithmetic built yesterday; no control, no OOS split, no book to draw down |
| **L7** | **Centaur loop** | human judgement recorded and fed back; "personalization of the interpretation" | log/blend/skill built; n=6 machine, n=2 human. Anchoring measured |

We are strong at L2, present at L3, new at L4, and **absent at L5 and L6** —
which is where his actual claims live.

---

## The three sentences that matter most

**"If a signal needed a forecast to work, we consistently found it didn't
perform."**

This is not modesty, it is an architecture. Convexity is bought with *position
structure* — defined risk, asymmetric exits — so the model never has to be right
about direction. Our entire centaur apparatus scores a **directional call**,
which is the thing he says does not pay.

**"The goal isn't more return — it's less damage."**

Drawdown, not hit rate, is the objective function. This is not a preference; it
changes what is knowable. A directional hit rate needs 153 sessions to separate
60% from a coin. A drawdown comparison runs on a continuous series against a
control, and gets there an order of magnitude sooner. **We chose the hardest
measurable thing and he chose an easier one that matters more.**

**"17 volatility signals died. A leverage overlay died. Eight alternative base
assets lost to plain SPY."**

He reports the denominator. Yesterday I said his "better than a coin flip" claim
was unfalsifiable as stated — that was about the sentence, and it was
incomplete about the method. Naming the kill count *is* family-wise error
control in practice, and it is the number almost nobody publishes.

---

## What was built today from this

**`pipeline/profile/facilitation.py`** — L4, the gate. Extension is not
acceptance. A headline spike and a genuine range extension are identical on a
session high/low, which is exactly why "levels alone are not enough to risk your
money on" is a statement about missing information rather than about discipline.

And the base rate, which is the thing we have never had for anything —
**123 SPX sessions, 2026-02 → 2026-08**:

| state | SPX | SPY |
|---|---|---|
| facilitated | 61.8% | 61.8% |
| two-sided | 18.7% | 22.8% |
| **extended and rejected** | **17.9%** | 12.2% |
| never left the balance | 1.6% | 3.3% |

Two findings, one of them against the feature:

1. **It is not a filter.** The gate opens on 78% of sessions, and a parameter
   sweep across 15 settings moves that only between 68% and 93% — smooth, no
   cliff. No threshold turns this into a selective screen. It is a *within-session
   timing* gate, which is how he states it ("no trade **until**"), and its value
   is the ~18% of sessions that extend and never build.
2. **SPX and SPY agree on 91.1% of sessions.** The 9% gap is the price of our
   instrument choice, now measured rather than argued. On 2026-04-08 SPX says
   rejected and SPY says facilitated — same market, different verdict, and his
   model surface is the one that says go.

Because range extension happens on nearly every session, any edge claim attached
to this gate is **settleable inside a year** — 0.8 years for a 60% edge, 0.3 for
65%. It is the first thing we hold that sits on the reachable side of the
frontier.

---

## Ranked, from here

| # | Item | Why here | Blocked? |
|---|---|---|---|
| 1 | **An objective function that isn't a hit rate** — track a paper book against a plain-SPY control and measure drawdown | his L6. Cheaper to measure than direction and closer to what matters | no |
| 2 | **Kill-test discipline** — every candidate rule runs against its own control on an out-of-sample split, and the death count is reported | turns our probe count from a liability into a denominator | no |
| 3 | **SPY as the profile instrument** alongside SPX | his L1. Dissolves the TPO/volume basis split; already known to change the verdict on 9% of sessions | no |
| 4 | **Defined-risk structure over directional call** | his L5. `pipeline/options/structures.py` exists and is unused by the daily chain | no |
| 5 | GEX-Volume / GEX-OI ratio as a first-class series | both series exist; the ratio is the signal | no |
| 6 | Institutional participation by premium per print | needs the flow tape wired into the daily chain | partly |
| 7 | Limit order book | resting intent vs settled positioning | needs a depth feed |
| 8 | Dark-pool regime states | a fourth framework | needs a vendor |

Items 1 and 2 are the ones that change what this project can ever prove. The
rest are instruments, and we already have more instruments than evidence.
