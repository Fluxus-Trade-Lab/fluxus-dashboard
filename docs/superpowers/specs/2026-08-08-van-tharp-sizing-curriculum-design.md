# Van Tharp Position-Sizing Curriculum — SizingTab Design

**Date:** 2026-08-08
**Where:** `frontend/src/components/journal/SizingTab.jsx` (AI Coach → Sizing tab, strategy key `sizing`)
**Status:** Approved design, pre-implementation

## Goal

Extend the AI Coach → **Sizing** tab into a *living* Dr. Van K. Tharp position-sizing
curriculum: teach his framework AND tie each lesson to this $1M account's own audited
numbers, so the trader learns and practices in one place. Ongoing module — new Tharp
teachings get appended over time, so structure must make appending a one-object edit.

Sources: Van Tharp, *Definitive Guide to Position Sizing*; LordFed, *Size Matters*
(https://www.lordfed.co.uk/p/size-matters). Account numbers from memories
`project_behavioral_diagnosis.md` and `project_performance_review.md`.

## Decisions (confirmed with user)

1. **R-distribution source: live client-side.** Compute in-browser from the live
   portfolio book (`usePortfolio()` → `enrichTrades`), which already emits per-trade
   `rr` anchored to the locked-at-entry stop (`initialStop ?? stopPrice`). Self-updating
   as the book syncs; zero pipeline coupling; works on this branch today. No new JSON,
   no Python.
2. **v1 scope: full launch set + both interactive tools.** Ship all 7 lessons + SQN/
   expectancy readout + Monte-Carlo objective tool now.

## Architecture

### New pure module: `frontend/src/components/journal/lib/sizingStats.js`

No React. Pure, unit-testable functions consumed by `SizingTab`.

- `closedR(trades)` → `number[]` — R-multiples of closed trades with a valid risk unit
  (`riskUnit > 0`, i.e. a real stop). Filters out stopless trades so R isn't degenerate.
  Reuses `t.rr` from `enrichTrades` (do not recompute).
- `expectancyStats(rs)` → `{ n, meanR, stdevR, winRate, payoff }` — sample stdev (n−1).
- `sqn(rs)` → `number` — Tharp's System Quality Number = `√n × meanR / stdevR`.
  Return `null` when `n < 2` or `stdevR === 0`.
- `sqnBand(sqn)` → `{ label, tone }` — Tharp's quality bands:
  `< 1.6` Poor · `1.6–1.9` Below average · `2.0–2.4` Average · `2.5–2.9` Good ·
  `3.0–5.0` Excellent · `5.1–6.9` Superb · `≥ 7.0` "Holy Grail".
- `bootstrapObjective(rs, opts)` → objective Monte-Carlo. `opts = { riskPct, horizon,
  paths, targetReturnPct, maxDDPct, seed }`. For each path: `equity = 1`; for each of
  `horizon` trades, draw `R` uniformly with replacement from `rs`, apply
  `equity *= 1 + (riskPct/100) * R`, track running peak and max drawdown. Returns
  `{ endReturns: number[] (sorted), pReachTarget, pBreachDD, medianReturn, p5, p95,
     medianMaxDD, histogram }`. Deterministic given `seed` (mulberry32 PRNG) so the UI
  doesn't reshuffle every render.

Guardrails: if `rs.length < ~20`, the tools render but show a low-sample caveat.

### `SizingTab.jsx` changes

1. **Wrap in `<PortfolioProvider>`.** Split into `SizingTab` (thin wrapper) + inner
   `SizingContent`, mirroring `AnalyticsTab`/`RiskTab`. Currently the tab calls
   `usePortfolio()` with no provider on this branch and would throw. This satisfies the
   task's "keep it wrapped" requirement.
2. Keep the existing `METHODS` accordions, `SizingCalculator`, `PortfolioAudit`
   unchanged.
3. Add three new sections (order below).

### Data flow

`SizingContent` computes `enriched = enrichTrades(state.trades, capital, state.dailyPrices)`
once (already done), derives `rs = closedR(enriched)`, and passes `rs` + derived stats
to the new sections. No network, no new state store.

## Page layout (top → bottom)

1. Existing: `METHODS` accordions
2. **NEW — "Van Tharp: the study of position sizing"** — `<TharpLessons>`
3. **NEW — SQN + Expectancy readout** — `<SqnReadout>`
4. **NEW — Position-Sizing-to-Objective Monte-Carlo** — `<ObjectiveSimulator>`
5. Existing: `SizingCalculator`
6. Existing: `PortfolioAudit`

(Teaching → diagnose → simulate → calculate → audit: concept flows into this account's
reality, then into hands-on tools.)

## Component: `<TharpLessons>`

A `LESSONS` data array rendered as accordion cards in the existing accordion style.
Each entry: `{ key, title, subtitle, principle (Tharp's teaching, 2–4 sentences),
ourNumber: { stat, value, read }, source }`. Appending a future lesson = push one object.

Launch set (7):

| key | Principle | This account's number |
|---|---|---|
| `r-multiples` | Every result in units of initial risk; expectancy = mean R | **+0.88R** expectancy, 39.9% WR, 3.40× payoff |
| `how-much-separate` | Sizing answers "HOW MUCH", independent of entry/exit; it's the part that meets your objectives | corr(size, R) ≈ **0** — sizing added no edge |
| `percent-risk` | Risk the same % of equity every trade | real 1R ≈ **0.52%** vs **0.25%** target (2× intended) |
| `percent-volatility` | Size by ATR so every position risks equal volatility | high-ATR names (ALAB/DOCN ATR **8–21%**) |
| `anti-martingale` | Press winners, cut losers; never average down unless pre-planned | re-attacks averaged **+1.21R** — leak was *oversizing* the failures (BABA −$54k), not re-adding |
| `kelly-trap` | Full/half-Kelly maximises growth only if edge is stationary & correctly measured | f* = **15.9%/1R** here — degenerate on a +90%/6-mo bull sample; don't trust it |
| `discipline-over-prediction` | You can't forecast R at entry; consistent risk beats conviction sizing | plain **equal risk → +66.7%** vs actual; conviction **anti**-predicts (−0.16) |

Each card footer cites the source (Tharp DGPS / LordFed *Size Matters*).

## Component: `<SqnReadout>`

Compact stat panel from `expectancyStats(rs)` + `sqn(rs)`:

- Tiles: N trades · Mean R · Stdev R · **SQN** · quality band label.
- Below: a one-line plain-English read — what the SQN says about system quality and
  what raising it requires (tighten the loss tail / raise payoff, not bet size).
- Formula shown inline: `SQN = √N × (mean R ÷ stdev R)`.
- Caveat line when `n < 20`.

## Component: `<ObjectiveSimulator>` — the centerpiece

Tharp's *position-sizing-to-objectives via Monte-Carlo*: bootstrap this account's own R
distribution to answer "what % risk hits my goal with an acceptable chance of an X%
drawdown?"

**Inputs (controls):**

- Risk % per trade — slider, default **0.25%** (his target); quick-set chips at 0.25 /
  0.52 (his actual) / 1.0 / 2.0%.
- Horizon (# trades) — default 300 (~one of his half-years).
- Paths — default 2000.
- Target return % — default +50%.
- Max acceptable drawdown % — default 20%.

**Outputs:**

- Headline verdict line: "At {risk}% risk over {horizon} trades: median **+{x}%**,
  hits +{target}% **{pReachTarget}%** of the time, with **{pBreachDD}%** chance of a
  >{maxDD}% drawdown."
- Stat tiles: median return · 5th/95th pctile · median max DD · P(target) · P(DD breach).
- A small histogram (or percentile fan) of ending returns; the target line marked.
- Recompute is memoized on inputs; deterministic via seed.

**Model note (shown as a caption):** i.i.d. bootstrap of realized R — ignores serial
correlation, regime shifts, and that R itself is non-stationary; it sizes to *this*
sample's edge, which a bull-market sample overstates. Explicitly Tharp's point: size to
objectives, and recognise the sample's limits.

## Testing

- Unit tests for `sizingStats.js` (Vitest, matching repo test setup): `expectancyStats`
  on a known R array; `sqn` against a hand-computed value; `sqn` returns null for n<2 /
  zero-variance; `bootstrapObjective` determinism given a seed, and monotonicity
  (higher risk % → wider ending-return spread on a +EV distribution).
- Manual: verify in preview (`preview_start` name `fluxus-dashboard`, AI Coach =
  `#/journal` → Sizing tab) that all sections render, provider wrap works, and the
  simulator responds to inputs.

## Deploy

Work on `feat/gex-engine`, then cherry-pick the frontend commit(s) to `main` via
`git worktree add <tmp> origin/main` → cherry-pick → `git push origin HEAD:main`. Never
touch the dirty main working tree (see memory git-safety rules).

## Out of scope (v1)

- No Python / pipeline changes; no new committed JSON.
- No percent-volatility *calculator* (ATR model is taught, not yet a live sizing tool) —
  candidate for a later append.
- Conviction-tier (Test/Core/Press) sizing tool — taught via the anti-martingale/
  discipline lessons; interactive version deferred.
