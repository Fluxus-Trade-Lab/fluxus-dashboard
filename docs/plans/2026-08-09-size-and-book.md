# Items 4 and 5: the institutional size filter, and the order book

Both were parked as "data problems, not code problems". Having checked what the
feed actually gives us, that framing was half wrong. One is buildable today with
data we already pay for. The other is partly free and partly genuinely expensive,
and the expensive part should be priced, not promised.

---

## Item 4 — the size filter (`lot size > 10`)

### The thing I had wrong

I filed this as "needs trade-level data we don't have." We have it. But there is
a harder problem underneath that I had not seen:

**Open interest carries no size information, in principle.** OI is a count of
contracts currently open. It does not record who opened them, in what
increments, or when. A 500-lot block and fifty 10-lots are the same integer.

So a size filter on our GEX is **not unavailable, it is impossible** — the
information was never in the input. Any "institutional GEX" built from OI would
be fabricated. That is worth stating plainly because it kills a whole family of
tempting features.

### Where size does exist

The **trade tape** carries it, and we already pull it:

* `reqHistoricalTicks(whatToShow="TRADES")` returns tick-by-tick prints with size
* `pipeline/flow/ibkr_historical.py` already paginates it
* `pipeline/flow/aggregate.py` already computes `premium = price × size × 100`

So the buildable version is not "institutional positioning" but
**institutional participation in today's flow**, per strike:

```
for each strike:
    all_premium   = Σ price × size × 100                    over every print
    large_premium = Σ price × size × 100   where size ≥ N
    institutional_share = large_premium / all_premium
```

That is a real measure, it is honest about what it measures, and it composes
with the flow ratio built today: a strike that is *hot* on flow-vs-positioning
**and** dominated by large prints is a different object from one that is hot on
retail one-lots.

### One improvement on his rule

His screen is `lot size > 10`. Contract count is a proxy for "big"; **dollars is
the thing itself**. A 5-lot of a $50 option is $25,000 of intent; a 20-lot of a
$0.10 option is $200. On SPX, where strikes span three orders of magnitude in
premium, a fixed lot threshold systematically over-counts cheap wings and
under-counts the money.

So: threshold on **premium per print**, with lot size retained as a reported
field for comparability with how everyone else screens. Both numbers, one
decision.

### What a size filter cannot catch

Institutions slice. A 500-lot worked as fifty 10-lots by an algo looks exactly
like fifty retail 10-lots to any per-print filter. This is not a tuning problem;
it is a limit of the measurement. The honest framing is that a size filter finds
**blocks**, not **institutions**, and the two are not the same set. Any output
should say `block share`, never `institutional share`.

### Cost

`reqHistoricalTicks` returns 1,000 ticks per request and must be paginated. A
full SPX session across 50 strikes × 2 rights is many thousands of requests and
will hit pacing limits. The tractable scope is the same one OptionsFlow already
uses: the ATM core, roughly ±2% of spot, ~30 contracts. That is a session's worth
of pulling, not a background job.

**Verdict: buildable, scoped to the ATM core, no new subscription.**

---

## Item 5 — the limit order book

### What IBKR will and will not give

* `reqMktDepth` — full depth. Available for futures, some equities, forex.
  **Not available for OPRA options through IBKR.** Options come as top-of-book.
* `reqMktData` on an option — returns `bidSize` and `askSize` alongside the
  prices. Verified present on the `Ticker` object.

And the finding that matters:

> **We subscribe to option quotes on every GEX pull and read only bid and ask.
> `bidSize` and `askSize` arrive on the same subscription and are discarded.**

That is the same shape as the volume bug two days ago — the data was already
paid for and the field was never read.

### What level-1 resting size gets us

Not a ladder, but not nothing:

| Measure | What it says |
|---|---|
| `bidSize` vs `askSize` per strike | which side is resting size at the top of book |
| the same, across the strike grid | where resting interest concentrates, independent of OI and of prints |
| change across the session's pulls | whether size is being **added** or **pulled** — the second is often the more informative |

Crucially this is **resting intent**, which is a genuinely different object from
both OI (settled positioning) and the tape (completed trades). It would be a
fourth framework, and by the independence rule that already governs
`reference_map`, a fourth *independent* one.

### The caveat that must ride with it

Top-of-book size on options is thin, quoted largely by market makers, and
refreshes constantly. It is closer to "what the MM is willing to show" than to
"what the market wants to do". Displayed size is also not committed size —
hidden and reserve orders exist. So the honest claim is narrow: **displayed
top-of-book size**, sampled at the pull, nothing more.

### What full depth would take, priced

* OPRA depth is a paid exchange feed with per-user fees, not a code change.
* Vendors that carry OPRA MBO/MBP exist (Databento among them). Real monthly cost.
* **This should be priced against a specific question before being bought.**
  Right now there is no question we have that depth answers and level-1 does not,
  because we have never used level-1.

**Verdict: level-1 resting size is free and unused — build it. Full depth stays
unpriced until level-1 shows what it cannot answer.**

---

## Order

1. **Read `bidSize`/`askSize` in the GEX pull** — hours, no new data, and it
   opens a fourth independent framework.
2. **Block-share per strike from the tape** — scoped to the ATM core, threshold
   on premium per print, reported as `block share` and never as `institutional`.
3. **Full depth** — do not buy until (1) has run long enough to name the question
   it cannot answer.

The temptation with both of these is to promise the institutional read and
deliver a proxy. Neither the tape nor the top of book sees institutions; they see
blocks and they see displayed size. Saying so is the whole difference between
these being useful and being decoration.
