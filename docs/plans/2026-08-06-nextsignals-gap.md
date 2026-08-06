# What we would need to produce nextSignals' daily report

Source: @TailThatWagsDog, 2026-08-04, "Auction Market Value Process and Advanced
Options Sentiment Analysis: An Integration" — page four of four, *Data Synthesis*.
Instrument: **SPY front month**, not SPX. Footer credits "AI-Human Hybrid
Modeling · Claude Opus 5".

The report's four pages are `AUCTION MARKET » ORDER BOOK » OPTIONS CHAIN »
DATA SYNTHESIS`. We saw only the last, which is the join of the other three.
That page alone is enough to enumerate the inputs.

---

## The honest scoreboard

| Input the report uses | Do we have it? |
|---|---|
| Per-strike gamma exposure | **yes** — `pipeline/gex/`, from open interest |
| Per-strike charm exposure | **yes** — `bs_charm`, per-strike charm, charm flip |
| Call/put walls, zero-gamma flip | **yes** |
| Volume and OI per strike | **yes** — fetched, but only OI is used downstream |
| ATM IV by tenor, expected move | **yes** |
| 25-delta skew | **as of today** — `pipeline/reference/skew_log.py`, n=0 so far |
| Market Profile: TPOC, VPOC, singles, value area, time diversity | **no — nothing** |
| Side-classified flow per strike (bought-put band / sold-put zone) | **partial** — OptionsFlow classifies, but ATM-core strikes only, separate repo |
| Gamma computed from **volume** rather than OI | **no** |
| A normalized skew sentiment reading ("55% bearish") | **no** — needs the store above plus history |
| Forward-scored track record of published levels | **yes — and he does not publish one** |

---

## Gap 1 — Market Profile. This is the whole missing half.

Seven of the eight levels in his reference map are named by auction structure,
not by options:

```
770      no structure — unexplored
760.0-760.3   8/4 single-print high, balance top
758.0    8/3 TPOC
755.6    8/3 VPOC without time diversity
750      8/3 period 1-3 area
748.3    8/3 low singles
745.3    7/31 TPOC
```

Every one of those terms is a Market Profile primitive we do not compute:

- **TPO profile** — 30-minute letter brackets; price × time occupancy
- **TPOC** — the price with the most TPOs (time point of control)
- **VPOC** — the price with the most *volume* (a different price, and the
  difference between the two is exactly what he means by "VPOC without time
  diversity": volume piled up there but time did not)
- **Singles / single prints** — prices touched in only one bracket; they mark
  where the auction moved too fast to build acceptance
- **Value area** — the ~70% volume band
- **Balance / balance boundary** — a two-sided range vs a one-way auction
- **Poor high** — a high without excess, i.e. unfinished business

**What it takes:** intraday bars, which we can already pull from IBKR. 30-minute
bars give the TPO letters; 1-minute or tick data gives volume-at-price for VPOC.
No new vendor, no new subscription. The computation is fully deterministic and
testable against a golden fixture the way the flow classifier was.

**Why it matters more than any options feature:** his entire method is *two
independent frameworks landing on the same price*. Right now we only have one.
Every "confluence" we compute is gamma vs charm — two views of the same dealer
book. His confluence is the auction versus the dealer book, which are genuinely
independent inputs. That is the difference between confirming yourself and
being confirmed by something else.

---

## Gap 2 — his gamma is computed from volume, not open interest

The table is headed **`GEX-VOLUME`**:

```
STRIKE   GEX-VOLUME    CHARM      DOMINANT EXPOSURE   ACTIVATED BY
760        -35.3      +1,935.5    charm               the passage of time
755         -9.4        -579.0    both, modest        the crossover
750        -54.9        -450.0    gamma               displacement
```

Ours is GEX-from-OI. These are different quantities: OI is accumulated
positioning, volume is today's flow. Neither is wrong, and a strike can be large
in one and small in the other — that gap is itself information.

**What it takes:** almost nothing. We already fetch volume per strike (tick
101). It is a second series alongside the existing one.

## Gap 3 — the dominant-exposure classification

We compute per-strike GEX and per-strike charm, and we compute the charm flip.
We do **not** label which force governs each strike, because GEX and charm are in
different units and comparing them needs an explicit normalization. He does it
and states the rule plainly: *a balance that holds is charm-governed, a balance
that breaks is gamma-governed.*

**What it takes:** a normalization choice (z-score each series across the strike
grid is the obvious one) plus the label. Small, and it sits on data we already
have. The honest version reports the normalization used, since the label is only
as meaningful as that choice.

## Gap 4 — side-classified flow across the whole chain

"Calls being sold −3.08M net in 750–760", "sold-put zone", "top of bought-put
band", "max premium, 44k volume" — these need every print classified
buyer-initiated or seller-initiated and then aggregated *per strike*, in premium.

We have the classifier (`OptionsFlow`, Lee-Ready, validated on a golden replay).
What we lack is coverage: it runs on ATM-core strikes, not the full chain, and it
lives in a separate repo with no path into the GEX brief.

**What it takes:** the most work of anything here — widening the tape and paying
the market-data cost for it. Worth staging after Market Profile.

## Gap 5 — "skew is 55% bearish"

A normalized reading, not a raw level. Unblocked as of today: the daily store
exists. It needs history before it can say anything, and the store will keep
saying `thin` until n ≥ 30. That is roughly six trading weeks away.

---

## What he does that costs nothing but discipline

- **One question per day, stated before the session.** "Does the nascent
  758.0–760.3 balance hold as acceptance above 8/3's TPOC?" — with two named
  branches and the consequence of each. Not a forecast; a fork.
- **A `WHAT CONFLICTS` section.** He writes down where his own two frameworks
  disagree and which one he lets win, and names the rule
  ("framework-over-opinion"). Publishing the disagreement is what makes the
  agreement mean something.
- **Naming the strongest thing in the read.** "Two independent methods landing on
  755.6 is the strongest thing in this read." One sentence that ranks the
  evidence.

All three are format, not data. We can adopt them this week.

## What we have that he does not publish

A forward-scored record. His report makes a genuinely falsifiable call every
morning and, as far as the public feed shows, never grades it. Ours grades
itself in the same document — currently **12 held / 10 broke / 25 untested,
54.5% of tested**, which is unflattering and is the point.

---

## Order of work

| # | Item | Effort | Unlocks |
|---|---|---|---|
| 1 | TPO profile + VPOC + singles + value area | days | the second independent framework — everything else is decoration without it |
| 2 | GEX-from-volume alongside GEX-from-OI | hours | flow-vs-positioning divergence per strike |
| 3 | Dominant-exposure label (gamma vs charm) | hours | the "activated by" column |
| 4 | One-question-per-day + conflicts section in the brief | hours | format only |
| 5 | Full-chain side-classified flow | weeks | the bought/sold bands |
| 6 | Normalized skew sentiment | 6 weeks of waiting | "N% bearish" |

Items 2, 3 and 4 are a single afternoon and would close most of the *visible*
gap. Item 1 is the one that actually changes what we know.
