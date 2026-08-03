# Build Notes — publishable drafts

Five pieces, each a real error found and fixed while building the GEX engine.
Drafts only: the facts and numbers are verified, **the voice is not yours yet** —
rewrite before publishing. No claim of edge in any of them; the point is method.

Standard closing line to consider: *"Published because it was wrong, not because
it worked."*

---

## 1. A unit that was off by 100×

**Hook:** Vega has two conventions and nobody tells you which one you're holding.

Textbook vega is the price change per **1.00** of sigma — a 100-point move in
implied vol. IBKR reports vega per **one vol point**. They differ by a factor of
100, and both are "vega".

I hit this building a structure evaluator. A butterfly showed net vega −0.175.
The question that mattered was: if IV collapses 8 points after the announcement,
what does that do to the position? With the right convention: `−0.175 × −8 =
+1.40`. With the textbook one: `+140` on a position whose entire max profit was
63.55. The second number is absurd, which is the only reason I caught it.

The fix is one division. The lesson is that **an absurd number is a gift** — it
is the errors that land in a plausible range that survive.

There is now a test that fails if the `/100` ever disappears:

> A 1-point IV move on a 2DTE ATM SPX option is worth single-digit dollars, not
> hundreds.

**Takeaway:** when a greek arrives from a feed, check its units against a case
where you already know the rough answer.

---

## 2. Implied vol solved against the wrong number

**Hook:** I was backing IV out of option prices using spot. Everyone does. It's
wrong for index options, by about a vol point.

To fill gaps when the greek feed goes dark, I solve implied vol from the mid
price. Against **spot**, the 1DTE SPX chain returned 24.91%. IBKR's own model
said 26.05%. Consistently low, every strike, ~1.1 vol points.

Index options are priced off the **forward**, not spot. Rebuilding the same
solve against the parity forward (`ATM strike + call − put`) closed the gap to
about 0.1.

What makes this worth writing down is not the fix — it's that **the wrong answer
looked completely reasonable**. 24.91% is a perfectly plausible 1DTE IV. Without
a second source to disagree with it, it ships.

**Takeaway:** a computed value with no independent cross-check is an assumption
with decimal places.

---

## 3. A metric that was 92% an artifact of its own floor

**Hook:** I built a charm exposure model, got a clean number, and then found the
number was mostly a constant I had chosen myself.

Charm is delta decay — how far delta drifts as time passes, with nothing else
moving. The natural way to publish it is a rate: dollars of delta per day. So
that's what I built. Total: −9.69B/day, peaking at 7250.

Then I checked which expiry supplied it:

```
expiry     T(days)   share of |charm|
20260731     0.5          92.6%
20260803     3.0           1.7%
20260804     4.0           2.1%
```

Charm carries a `1/T^1.5` term. As expiry approaches, it diverges. Every model
puts a floor on T so this doesn't blow up — mine was half a day. **So 92.6% of
the headline number was determined by a parameter I picked, not by the market.**
Change the floor, change the answer.

"Per day" is also meaningless for a contract with hours left. It extrapolates a
rate past the option's own life.

The replacement is bounded and floor-free: **total drift to expiry**, `terminal
delta − current delta`. Delta at expiry is exactly 0 or ±1, so the quantity
cannot diverge, and it answers the question that actually matters — how much
re-hedging must still happen.

**Takeaway:** when a metric depends on a stabilising constant, check how much of
the output *is* the constant.

---

## 4. The day the market didn't move and travelled 1.32× its expected range

**Hook:** "The index is flat and the straddle barely decayed, so options were
overpriced." Both facts true. Conclusion wrong.

Mid-session, SPX:

```
prior close  7,437.63
open         7,462.13
high         7,489.52
low          7,399.83
now          7,436.65   (−0.98 on the day)
```

Net: unchanged. **Path: 89.7 points.** The morning straddle priced ±34 — about
68 points of range for the *whole day*. Two hours in, the market had travelled
**1.32× the full-day implied range**.

So: were options overpriced?

- For someone **holding** a straddle — yes, it hurt. Straddle P&L depends on
  **displacement**: where price ends.
- For **realised volatility** — no, the opposite. Vol depends on the **path**,
  and the path exceeded what was priced.

Two different quantities that both get called "how much did it move". A static
snapshot only ever sees displacement.

**Takeaway:** name which one you mean before concluding anything about whether
vol was cheap.

---

## 5. A basis that was 40 points of nothing

**Hook:** I computed the ES–SPX basis at +70. The real number was +29.5. The
difference was a clock.

At 02:30 ET I pulled both:

```
SPX  7,489.72   ← cash is closed; this is Friday's last print
ES   7,559.75   ← trading right now
```

Subtract, and you "measure" a +70 basis. But one leg was hours stale. The extra
40 points were **the overnight move in ES**, which is not basis at all.

Measured properly — both quoted at the same instant, Friday's cash close:

```
SPX 7,489.72   ES 7,519.25   →  basis +29.5
```

Which then says something useful: ES at 7,559.75 minus a 29.5 basis implies SPX
around 7,530 — the overnight had already moved it ~40 points.

I had flagged exactly this hazard earlier the same week, about a different
number, and still walked into it.

**Takeaway:** a difference between two quotes is only meaningful if they were
quoted at the same moment. When one market is closed, you are not measuring a
spread, you are measuring time.

---

## Notes on using these

- Every number above is from the repo's own commits and can be re-derived.
- Sequence suggestion: **4 first** (most broadly useful, needs no options
  background), then 5, 1, 2, 3.
- Optional series title: *Build Notes*. The consistent shape is
  `what I believed → what the data said → what changed → what it generalises to`.
