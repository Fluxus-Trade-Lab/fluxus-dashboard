# GEX Brief → Packaged Product — Research & Plan

**Date:** 2026-08-03
**Status:** Proposal, nothing built
**Question:** How do SpotGamma / MenthorQ present this, what are we missing, and what
should we package for the Fluxus community?

---

## 1. The competitive landscape has three tiers, not one

**Institutional-adjacent — SpotGamma** ($67–299/mo, Institutional $1,999+)
- Named proprietary levels: **Zero Gamma, Volatility Trigger™, Risk Pivot, Call Wall,
  Put Wall**. The two we lack are Volatility Trigger and Risk Pivot.
- **TRACE** — three models over the same chain: **Gamma, Delta Pressure, Charm Pressure**.
  They already ship charm. It is not a differentiator, it is table stakes at this tier.
- **HIRO** — real-time options flow (our OptionsFlow engine is the analogue).
- **Founder's Note** — twice daily, premarket + post-close. Commentary + levels + events.
- Breadth: Equity Hub 3,500+ tickers, scanners, vol dashboard, options calculator.
- Community: Discord + twice-weekly Q&A.

**Quant-platform — MenthorQ**
- 64+ models; **natively-computed futures options gamma** (ES, NQ, RTY, CL, GC) is the
  stated moat — no basis conversion.
- **GEX Levels 1–10**: secondary structure, *ranked*. Not just the primary walls — a
  ladder of lesser levels for scalp targets and stop placement.
- **Blind Spot levels**: inflection points that look technically unremarkable.
- Vol suite: VRP, smile, skew, term structure. **Q-Score** momentum.
- Distribution is the real story: dashboard + TradingView + **10 platform integrations**
  (NinjaTrader, Sierra, Bookmap, Quantower…) + Discord + daily newsletter + an AI
  natural-language screener.

**Indie newsletter — "Gamma Edge" (Substack)** ← *the realistic template for us*
- ~1,200–1,500 words before the paywall, daily.
- Structure: opening → **macro block (SPX + VIX curve)** → **per-ticker cards**.
- Each card: price · gamma status · net GEX ($mm) · support · resistance · gamma flip ·
  **one paragraph of plain English**.
- Free/paid split: **3 tickers free, 7 behind the wall** (10 total).
- Explicit positioning: institutional feeds cost thousands; free tools use one flat vol
  across strikes and therefore misplace levels.

**Read:** SpotGamma and MenthorQ compete on breadth and integrations — we cannot and
should not. The indie letter competes on **selection, interpretation and voice**, which
is exactly where Fluxus already has an asset.

---

## 2. Gap analysis

### Missing, high value / low effort
| Gap | Note |
|---|---|
| **Wall migration is computed but not shown** | `derive.wall_migration()` exists and is tested. Day-over-day movement of call/put/flip is the single most narrative-ready number we already own and do not publish. |
| **No plain-English interpretation** | Our brief is a numbers table. Every competitor pairs each number with a sentence. This is the largest gap and it is writing, not engineering. |
| **No historical context** | "net GEX −1.9B" means nothing alone. Percentile vs the trailing 30–60 sessions turns it into a signal. We have the dated JSON archive to compute this today. |
| **`build_plan()` / `strategy_fit()` unused in the brief** | Both exist in `derive.py`. |

### Missing, high value / real effort
| Gap | Note |
|---|---|
| **Ranked secondary levels (MenthorQ GEX 1–10)** | We publish 3 walls. A ranked ladder of the next 7 strikes is a genuine product feature and is mostly sorting data we already have. |
| **Delta pressure per strike** | SpotGamma TRACE = gamma + delta + charm. We have gamma + charm. Delta is the missing third. |
| **Multi-ticker** | We are SPX-only. QQQ was scoped and never finished. The indie template needs ~5–10 names. |
| **Vol surface beyond VIX/VIX3M** | Skew and VRP are what let you say *why* IV is where it is. |

### Not worth chasing
Breadth (3,500 tickers), 10 platform integrations, an AI screener, a 500-hour academy.
Losing propositions against funded competitors.

---

## 3. What we already have that they do not

1. **Charm as bounded drift-to-expiry.** SpotGamma ships "Charm Pressure" as a rate. We
   found on live data that the per-day rate is **92.6% determined by the 0DTE time floor**
   and switched to `terminal delta − current delta`, which is floor-free. That is a
   defensible methodological claim, and it is publishable.
2. **Gamma × charm confluence, auto-detected.** Nobody surfaces "both metrics loaded and
   same-signed on one strike" as a named output. On 2026-07-31 it flagged 7400; the
   session low printed 7399.83. One instance is not evidence, but it is the seed of a
   trackable, falsifiable claim.
3. **Total methodological transparency.** Every competitor's levels are proprietary black
   boxes. We can show the formula. Against an audience that has been burned by black
   boxes, *this is the wedge* — and it matches the Fluxus anti-dopamine / radical-
   transparency brand rather than fighting it.
4. **The EM cross-check** (IV-implied vs actual straddle) — a free credibility signal
   nobody publishes.

---

## 4. Product proposal

**Position:** not "another levels service". **"The brief that shows its work."**
Publish the levels *and* the method, and keep a public accuracy record. That is the one
axis where being small is an advantage.

### Shape — daily brief, three blocks
1. **The Board** — spot, regime + *percentile vs 60 days*, call wall / flip / put wall,
   **day-over-day migration**, ES equivalents (with the basis stated, measured at the
   simultaneous cash close — see the +70 error in this repo's history for why).
2. **The Chart** — existing gamma + charm SVG with the confluence table.
3. **The Read** — 150–250 words, plain English, in the Fluxus voice. What changed, what
   would falsify it, what level is the day's hinge. *Levels as falsification lines, not
   predictions* (see `reference_options_analysis_method`).

### Tiering (mirrors the indie template, fits existing Substack)
- **Free:** SPX board + chart, published premarket. Builds the list.
- **Paid:** + The Read, + ES/NQ equivalents, + confluence table, + the running accuracy
  log, + weekend "what the walls did" review.

### Cadence
Premarket only to start. SpotGamma's twice-daily is a commitment trap — the memory note
on content routine already flags 断更 risk. One reliable daily beats two unreliable.

### The differentiator to build deliberately
**A public hit-rate log.** Every day, record the confluence strike and the walls; every
week, score what price actually did. Nobody publishes this because it can embarrass them.
That is precisely why it is credible — and it is the same discipline already applied to
the trade-log reviews.

---

## 5. Roadmap

**Phase 1 — make the brief publishable (~1 day)**
- Wire `wall_migration()` into the brief.
- Net-GEX percentile vs trailing 60 sessions from the dated JSON archive.
- Ranked secondary levels (next 7 strikes by |GEX|).
- Markdown export alongside the HTML, for paste-into-Substack.

**Phase 2 — the record (~1 day)**
- Append each day's board to a JSONL log.
- Weekly scorer: did price touch/hold/break each published level. Emit a public table.

**Phase 3 — coverage (~2 days)**
- Finish QQQ. Add 2–3 single names off the existing `single_name_gamma.py`.
- Delta pressure per strike (completes the TRACE triad).

**Phase 4 — distribution**
- Substack template + the free/paid split.
- Only then consider a TradingView Pine overlay for paid subscribers
  (`gex_to_pine.py` already exists).

---

## 6. Things to settle before building

- **Disclaimer.** Every competitor carries one. Publishing levels commercially needs the
  same, plus a clear "not advice" line. Worth a look from someone qualified before money
  changes hands.
- **Data licensing.** IBKR/OPRA market data has redistribution terms. Publishing *derived*
  levels is normally fine; republishing raw chain data is normally not. **Check the
  subscriber agreement before publishing anything containing per-strike OI.**
- **Cadence commitment.** Premarket ET = 21:00 JST. Sustainable, but it is a daily
  commitment and the archive shows the 断更 risk is real.

## Sources
- [SpotGamma pricing](https://spotgamma.com/subscribe-to-spotgamma/)
- [SpotGamma GEX levels](https://spotgamma.com/gamma-exposure-gex/)
- [SpotGamma Founder's Note](https://support.spotgamma.com/hc/en-us/articles/15341610402579-What-is-the-SpotGamma-Founder-s-Note)
- [MenthorQ](https://menthorq.com/)
- [MenthorQ GEX Levels 1–10](https://menthorq.com/guide/gex-levels/)
- [Gamma Edge newsletter example](https://goatacademy.substack.com/p/gamma-edge-june-5-2026)
