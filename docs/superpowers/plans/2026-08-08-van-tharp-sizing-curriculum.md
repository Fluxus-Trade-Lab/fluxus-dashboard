# Van Tharp Sizing Curriculum Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend AI Coach → Sizing tab into a living Van Tharp position-sizing curriculum: 7 lessons tied to this account's audited numbers, a live SQN/expectancy readout, and a bootstrap Monte-Carlo "size to objectives" simulator — all computed client-side from the live trade book.

**Architecture:** One pure stats module (`sizingStats.js`, no React, unit-tested) + three presentational components in a new `journal/sizing/` folder, wired into `SizingTab.jsx`, which gets split into a `<PortfolioProvider>` wrapper + inner content (mirroring `AnalyticsTab`/`RiskTab`). R-multiples come from `enrichTrades` (`t.rr`, anchored to locked-at-entry stop) — never recomputed.

**Tech Stack:** React 19, Vite 7, Tailwind CSS 4 (CSS-var tokens), recharts (already a dependency, see `SummarySection.jsx`), Vitest.

**Spec:** `docs/superpowers/specs/2026-08-08-van-tharp-sizing-curriculum-design.md`

## Global Constraints

- All colors via existing CSS-var tokens (`var(--color-surface)`, `var(--color-border)`, `var(--color-text)`, `var(--color-text-secondary)`, `var(--color-text-muted)`, `var(--color-bg)`, `var(--color-border-light)`, `var(--color-hover-bg)`) — no hardcoded hex except semantic green/red/amber Tailwind classes already used in this file (`text-green-600 dark:text-green-400` etc.).
- Anti-dopamine design language: tiny uppercase tracked section headers (`text-[10px] font-medium uppercase tracking-wide`), 9–12px type, no flashy colors.
- Do NOT recompute R — consume `t.rr` from `enrichTrades` (`frontend/src/components/portfolio/lib/calculations.js:97`), which anchors to `t.initialStop ?? t.stopPrice`.
- `SizingTab` must be wrapped in `<PortfolioProvider>` (it calls `usePortfolio()`).
- Monte-Carlo must be deterministic (seeded mulberry32 PRNG) so renders don't reshuffle.
- Lessons live in a `LESSONS` data array — appending a future Tharp lesson must be a one-object edit.
- Tests: Vitest, colocated `*.test.js` (repo pattern). Run from `frontend/`: `npx vitest run <path>`.
- All commits end with `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` (per session rules — keep whatever trailer the session mandates).

## File Structure

- Create: `frontend/src/components/journal/lib/sizingStats.js` — pure stats: PRNG, R extraction, expectancy, SQN, bands, bootstrap Monte-Carlo.
- Create: `frontend/src/components/journal/lib/sizingStats.test.js` — unit tests.
- Create: `frontend/src/components/journal/sizing/TharpLessons.jsx` — lessons accordion (data-driven).
- Create: `frontend/src/components/journal/sizing/SqnReadout.jsx` — SQN + expectancy stat panel.
- Create: `frontend/src/components/journal/sizing/ObjectiveSimulator.jsx` — Monte-Carlo objective tool.
- Modify: `frontend/src/components/journal/SizingTab.jsx` — provider wrap + wire new sections.

---

### Task 1: Core stats — `closedR`, `expectancyStats`, `sqn`, `sqnBand`, `mulberry32`

**Files:**
- Create: `frontend/src/components/journal/lib/sizingStats.js`
- Test: `frontend/src/components/journal/lib/sizingStats.test.js`

**Interfaces:**
- Consumes: enriched trade objects from `enrichTrades` — relevant fields: `isClosed: bool`, `entryPrice: number`, `initialStop?: number`, `stopPrice: number`, `rr: number`.
- Produces:
  - `mulberry32(seed: number): () => number` — deterministic PRNG in [0,1)
  - `closedR(enrichedTrades: object[]): number[]`
  - `expectancyStats(rs: number[]): { n, meanR, stdevR, winRate, payoff }`
  - `sqn(rs: number[]): number | null`
  - `sqnBand(value: number | null): { label: string, tone: 'bad'|'warn'|'neutral'|'good'|'muted' }`

- [ ] **Step 1: Write the failing tests**

```js
// frontend/src/components/journal/lib/sizingStats.test.js
import { describe, it, expect } from 'vitest'
import { mulberry32, closedR, expectancyStats, sqn, sqnBand } from './sizingStats'

describe('mulberry32', () => {
  it('is deterministic for a given seed', () => {
    const a = mulberry32(42)
    const b = mulberry32(42)
    expect([a(), a(), a()]).toEqual([b(), b(), b()])
  })
  it('yields values in [0, 1)', () => {
    const r = mulberry32(7)
    for (let i = 0; i < 1000; i++) {
      const v = r()
      expect(v).toBeGreaterThanOrEqual(0)
      expect(v).toBeLessThan(1)
    }
  })
})

describe('closedR', () => {
  const mk = (over) => ({
    isClosed: true, entryPrice: 100, initialStop: 95, stopPrice: 95, rr: 1.5, ...over,
  })
  it('returns rr of closed trades with a real stop', () => {
    expect(closedR([mk(), mk({ rr: -1 })])).toEqual([1.5, -1])
  })
  it('excludes open trades', () => {
    expect(closedR([mk({ isClosed: false })])).toEqual([])
  })
  it('excludes trades whose stop equals entry (no risk unit)', () => {
    expect(closedR([mk({ initialStop: 100, stopPrice: 100 })])).toEqual([])
  })
  it('falls back to stopPrice when initialStop is missing', () => {
    expect(closedR([mk({ initialStop: undefined, stopPrice: 95 })])).toEqual([1.5])
    expect(closedR([mk({ initialStop: undefined, stopPrice: 100 })])).toEqual([])
  })
  it('handles empty/undefined input', () => {
    expect(closedR([])).toEqual([])
    expect(closedR(undefined)).toEqual([])
  })
})

describe('expectancyStats', () => {
  it('computes mean, sample stdev, win rate, payoff on a known array', () => {
    // rs = [1, -1, 2]: mean = 2/3; sample stdev = sqrt(((1/3)^2 + (5/3)^2 + (4/3)^2)/2)
    const s = expectancyStats([1, -1, 2])
    expect(s.n).toBe(3)
    expect(s.meanR).toBeCloseTo(2 / 3, 10)
    expect(s.stdevR).toBeCloseTo(Math.sqrt(42 / 9 / 2), 10) // ≈ 1.5275
    expect(s.winRate).toBeCloseTo(2 / 3, 10)
    expect(s.payoff).toBeCloseTo(1.5, 10) // avg win 1.5 / avg |loss| 1
  })
  it('returns zeros for empty input', () => {
    expect(expectancyStats([])).toEqual({ n: 0, meanR: 0, stdevR: 0, winRate: 0, payoff: 0 })
  })
  it('payoff is 0 when there are no losses', () => {
    expect(expectancyStats([1, 2]).payoff).toBe(0)
  })
})

describe('sqn', () => {
  it('matches hand-computed value: sqrt(3) * (2/3) / 1.5275', () => {
    expect(sqn([1, -1, 2])).toBeCloseTo(Math.sqrt(3) * (2 / 3) / Math.sqrt(42 / 9 / 2), 10)
  })
  it('is null for n < 2', () => {
    expect(sqn([])).toBeNull()
    expect(sqn([1])).toBeNull()
  })
  it('is null for zero variance', () => {
    expect(sqn([1, 1, 1])).toBeNull()
  })
})

describe('sqnBand', () => {
  it('maps Tharp bands', () => {
    expect(sqnBand(null).label).toBe('—')
    expect(sqnBand(1.0).label).toBe('Poor')
    expect(sqnBand(1.7).label).toBe('Below average')
    expect(sqnBand(2.2).label).toBe('Average')
    expect(sqnBand(2.7).label).toBe('Good')
    expect(sqnBand(4.0).label).toBe('Excellent')
    expect(sqnBand(6.0).label).toBe('Superb')
    expect(sqnBand(7.5).label).toBe('Holy Grail')
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/components/journal/lib/sizingStats.test.js`
Expected: FAIL — cannot resolve `./sizingStats`

- [ ] **Step 3: Write the implementation**

```js
// frontend/src/components/journal/lib/sizingStats.js
/**
 * Pure sizing statistics for the Van Tharp curriculum (SQN, expectancy,
 * bootstrap Monte-Carlo). No React. Sources: Van Tharp, "Definitive Guide
 * to Position Sizing"; LordFed, "Size Matters".
 */

/** Deterministic PRNG (mulberry32) so simulations don't reshuffle every render. */
export function mulberry32(seed) {
  let a = seed >>> 0
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/**
 * R-multiples of closed trades that had a real initial stop.
 * Consumes the rr already computed by enrichTrades (anchored to the
 * locked-at-entry stop) — never recomputes R.
 */
export function closedR(enrichedTrades) {
  return (enrichedTrades || [])
    .filter(t => t.isClosed)
    .filter(t => {
      const stop = t.initialStop ?? t.stopPrice
      return Math.abs(t.entryPrice - stop) > 0
    })
    .map(t => t.rr || 0)
}

/** n, mean R, sample stdev (n−1), win rate, payoff (avg win R ÷ avg |loss R|). */
export function expectancyStats(rs) {
  const n = rs.length
  if (!n) return { n: 0, meanR: 0, stdevR: 0, winRate: 0, payoff: 0 }
  const meanR = rs.reduce((s, r) => s + r, 0) / n
  const stdevR = n > 1
    ? Math.sqrt(rs.reduce((s, r) => s + (r - meanR) ** 2, 0) / (n - 1))
    : 0
  const wins = rs.filter(r => r > 0)
  const losses = rs.filter(r => r < 0)
  const avgWin = wins.length ? wins.reduce((s, r) => s + r, 0) / wins.length : 0
  const avgLoss = losses.length
    ? Math.abs(losses.reduce((s, r) => s + r, 0) / losses.length)
    : 0
  return {
    n, meanR, stdevR,
    winRate: wins.length / n,
    payoff: avgLoss > 0 ? avgWin / avgLoss : 0,
  }
}

/** Tharp's System Quality Number = √N × meanR ÷ stdevR. Null when undefined. */
export function sqn(rs) {
  const { n, meanR, stdevR } = expectancyStats(rs)
  if (n < 2 || stdevR === 0) return null
  return Math.sqrt(n) * meanR / stdevR
}

/** Tharp's SQN quality bands (Definitive Guide to Position Sizing). */
export function sqnBand(value) {
  if (value == null) return { label: '—', tone: 'muted' }
  if (value < 1.6) return { label: 'Poor', tone: 'bad' }
  if (value < 2.0) return { label: 'Below average', tone: 'warn' }
  if (value < 2.5) return { label: 'Average', tone: 'neutral' }
  if (value < 3.0) return { label: 'Good', tone: 'good' }
  if (value <= 5.0) return { label: 'Excellent', tone: 'good' }
  if (value < 7.0) return { label: 'Superb', tone: 'good' }
  return { label: 'Holy Grail', tone: 'good' }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/components/journal/lib/sizingStats.test.js`
Expected: PASS (all)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/journal/lib/sizingStats.js frontend/src/components/journal/lib/sizingStats.test.js
git commit -m "feat(coach): pure sizing stats — R extraction, expectancy, SQN + Tharp bands"
```

---

### Task 2: Bootstrap Monte-Carlo — `bootstrapObjective`

**Files:**
- Modify: `frontend/src/components/journal/lib/sizingStats.js` (append)
- Test: `frontend/src/components/journal/lib/sizingStats.test.js` (append)

**Interfaces:**
- Consumes: `mulberry32` from Task 1.
- Produces: `bootstrapObjective(rs: number[], opts: { riskPct, horizon, paths?, targetReturnPct, maxDDPct, seed? }): null | { endReturns: number[] (sorted %), pReachTarget: number (%), pBreachDD: number (%), medianReturn: number (%), p5: number, p95: number, medianMaxDD: number (%), histogram: { x: number, count: number }[] }`

- [ ] **Step 1: Write the failing tests (append to sizingStats.test.js)**

```js
import { bootstrapObjective } from './sizingStats'

describe('bootstrapObjective', () => {
  const rs = [2, -1, -1, 3, -0.5, 1, -1, 5, -1, -0.8] // right-tail, +EV
  const base = { riskPct: 0.25, horizon: 300, paths: 500, targetReturnPct: 50, maxDDPct: 20, seed: 42 }

  it('is deterministic given a seed', () => {
    const a = bootstrapObjective(rs, base)
    const b = bootstrapObjective(rs, base)
    expect(a.medianReturn).toBe(b.medianReturn)
    expect(a.endReturns).toEqual(b.endReturns)
  })

  it('returns null for empty distribution', () => {
    expect(bootstrapObjective([], base)).toBeNull()
    expect(bootstrapObjective(undefined, base)).toBeNull()
  })

  it('higher risk % widens the ending-return spread', () => {
    const lo = bootstrapObjective(rs, { ...base, riskPct: 0.25 })
    const hi = bootstrapObjective(rs, { ...base, riskPct: 2.0 })
    expect(hi.p95 - hi.p5).toBeGreaterThan(lo.p95 - lo.p5)
  })

  it('all-positive R distribution never draws down', () => {
    const out = bootstrapObjective([1, 2, 3], { ...base, paths: 100 })
    expect(out.pBreachDD).toBe(0)
    expect(out.medianMaxDD).toBe(0)
  })

  it('endReturns is sorted ascending and sized to paths', () => {
    const out = bootstrapObjective(rs, { ...base, paths: 200 })
    expect(out.endReturns).toHaveLength(200)
    const sorted = [...out.endReturns].sort((a, b) => a - b)
    expect(out.endReturns).toEqual(sorted)
  })

  it('histogram counts sum to paths', () => {
    const out = bootstrapObjective(rs, { ...base, paths: 200 })
    expect(out.histogram.reduce((s, b) => s + b.count, 0)).toBe(200)
  })

  it('probabilities are consistent with the sorted returns', () => {
    const out = bootstrapObjective(rs, base)
    const share = out.endReturns.filter(r => r >= 50).length / out.endReturns.length * 100
    expect(out.pReachTarget).toBeCloseTo(share, 10)
  })
})
```

- [ ] **Step 2: Run tests to verify the new ones fail**

Run: `cd frontend && npx vitest run src/components/journal/lib/sizingStats.test.js`
Expected: FAIL — `bootstrapObjective` is not exported

- [ ] **Step 3: Write the implementation (append to sizingStats.js)**

```js
/**
 * Tharp's position-sizing-to-objectives Monte-Carlo: bootstrap-resample the
 * account's own R-distribution at a given risk % per trade. Each path applies
 * equity *= 1 + (riskPct/100) * R for `horizon` draws, tracking max drawdown.
 * i.i.d. bootstrap — ignores serial correlation and regime shifts by design;
 * the UI must caption that caveat.
 */
export function bootstrapObjective(rs, {
  riskPct, horizon, paths = 2000, targetReturnPct, maxDDPct, seed = 42,
}) {
  if (!rs?.length) return null
  const rand = mulberry32(seed)
  const f = riskPct / 100
  const endReturns = new Array(paths)
  const maxDDs = new Array(paths)
  let reach = 0
  let breach = 0
  for (let p = 0; p < paths; p++) {
    let eq = 1
    let peak = 1
    let maxDD = 0
    for (let i = 0; i < horizon; i++) {
      const r = rs[Math.floor(rand() * rs.length)]
      eq *= 1 + f * r
      if (eq <= 0) { eq = 0; maxDD = 1; break } // busted
      if (eq > peak) peak = eq
      const dd = 1 - eq / peak
      if (dd > maxDD) maxDD = dd
    }
    const ret = (eq - 1) * 100
    endReturns[p] = ret
    maxDDs[p] = maxDD * 100
    if (ret >= targetReturnPct) reach++
    if (maxDD * 100 > maxDDPct) breach++
  }
  endReturns.sort((a, b) => a - b)
  maxDDs.sort((a, b) => a - b)
  const pct = (arr, q) => arr[Math.min(arr.length - 1, Math.floor(q * arr.length))]
  return {
    endReturns,
    pReachTarget: (reach / paths) * 100,
    pBreachDD: (breach / paths) * 100,
    medianReturn: pct(endReturns, 0.5),
    p5: pct(endReturns, 0.05),
    p95: pct(endReturns, 0.95),
    medianMaxDD: pct(maxDDs, 0.5),
    histogram: buildHistogram(endReturns, 24),
  }
}

/** Bucket a sorted array into `bins` equal-width bins; x = bin midpoint. */
function buildHistogram(sorted, bins) {
  if (!sorted.length) return []
  const lo = sorted[0]
  const hi = sorted[sorted.length - 1]
  const width = (hi - lo || 1) / bins
  const counts = new Array(bins).fill(0)
  for (const v of sorted) {
    counts[Math.min(bins - 1, Math.floor((v - lo) / width))]++
  }
  return counts.map((count, i) => ({ x: lo + (i + 0.5) * width, count }))
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/components/journal/lib/sizingStats.test.js`
Expected: PASS (all, including Task 1's)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/journal/lib/sizingStats.js frontend/src/components/journal/lib/sizingStats.test.js
git commit -m "feat(coach): bootstrap Monte-Carlo objective engine (Tharp size-to-objectives)"
```

---

### Task 3: Wrap SizingTab in PortfolioProvider

**Files:**
- Modify: `frontend/src/components/journal/SizingTab.jsx` (imports at line 1–4; `export default function SizingTab()` at line ~276)

**Interfaces:**
- Consumes: `PortfolioProvider, usePortfolio` from `../portfolio/context/PortfolioContext`.
- Produces: `SizingTab` (default export, unchanged signature) now safe without an external provider; internal `SizingContent` holds the previous body. Later tasks add sections inside `SizingContent`.

- [ ] **Step 1: Edit the import (line 2)**

```js
import { usePortfolio, PortfolioProvider } from '../portfolio/context/PortfolioContext'
```

- [ ] **Step 2: Rename the main component and add the wrapper**

Change `export default function SizingTab() {` to `function SizingContent() {` and append at the end of the file (mirroring `AnalyticsTab.jsx:26`):

```jsx
export default function SizingTab() {
  return (
    <PortfolioProvider>
      <SizingContent />
    </PortfolioProvider>
  )
}
```

- [ ] **Step 3: Verify the build and existing tests**

Run: `cd frontend && npx vitest run && npm run build`
Expected: tests PASS, build succeeds with no unused-import warnings for SizingTab

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/journal/SizingTab.jsx
git commit -m "fix(coach): wrap SizingTab in PortfolioProvider (usePortfolio needs it)"
```

---

### Task 4: `<TharpLessons>` — the 7-lesson curriculum accordion

**Files:**
- Create: `frontend/src/components/journal/sizing/TharpLessons.jsx`
- Modify: `frontend/src/components/journal/SizingTab.jsx` (import + render)

**Interfaces:**
- Consumes: nothing (static data component).
- Produces: `TharpLessons` (default export, no props). `LESSONS` array is module-local; appending a lesson = push one object `{ key, title, subtitle, principle, ourNumber: { stat, value, read }, source }`.

- [ ] **Step 1: Create the component**

```jsx
// frontend/src/components/journal/sizing/TharpLessons.jsx
import { useState } from 'react'

/*
 * Van Tharp position-sizing curriculum — living module.
 * To add a lesson: append one object to LESSONS. Nothing else to touch.
 * Sources: Van Tharp, "Definitive Guide to Position Sizing" (DGPS);
 * LordFed, "Size Matters" (lordfed.co.uk/p/size-matters).
 * Account numbers: H1 2026 audit (331 closed trades, 2025-12-31 → 2026-07-22).
 */
const LESSONS = [
  {
    key: 'r-multiples',
    title: 'R-Multiples & Expectancy',
    subtitle: 'Measure every trade in units of initial risk',
    principle: 'Express every result as a multiple of initial risk: 1R = |entry − stop| × shares. A trade risking $2,500 that makes $7,500 is +3R. Expectancy is the mean R across trades — what one unit of risk pays on average. Tharp: a system IS its R-multiple distribution; until results are in R, you cannot study sizing at all.',
    ourNumber: {
      stat: 'This book’s expectancy',
      value: '+0.88R',
      read: '331 closed trades, 39.9% win rate, 3.40× payoff — a right-tail distribution: loses often and small, gets paid on the tail (47 trades ≥3R).',
    },
    source: 'Tharp, DGPS · ch. on R-multiples',
  },
  {
    key: 'how-much-separate',
    title: '"How Much" Is a Separate Question',
    subtitle: 'Sizing is independent of entry and exit — it meets your objectives',
    principle: 'Position sizing is the part of the system that answers HOW MUCH, and it is fully separate from what to buy or when to exit. Tharp’s sharpest claim: sizing is the component through which you achieve your OBJECTIVES — the same signal stream can be sized to grind, to compound, or to blow up.',
    ourNumber: {
      stat: 'corr(position size, R) — H1',
      value: '≈ 0.00',
      read: 'His discretionary size was uncorrelated with which trades worked — the sizing layer added no edge on top of entries/exits. Exactly why it deserves separate study.',
    },
    source: 'Tharp, DGPS · audit: PositionSizeChart (Analytics → Summary)',
  },
  {
    key: 'percent-risk',
    title: 'The Percent-Risk Model',
    subtitle: 'Risk the same % of equity on every trade',
    principle: 'Tharp’s workhorse model: pick a risk fraction (e.g. 0.25% of equity), divide by stop distance, get shares. Every trade then loses the same fraction when the stop hits, and R becomes comparable across all trades. The discipline is keeping the fraction FIXED — the model fails the moment "conviction" starts inflating it.',
    ourNumber: {
      stat: 'Real 1R vs target',
      value: '0.52% vs 0.25%',
      read: 'Average initial risk ran 2× the stated target (median 0.39%). The account was running a bigger percent-risk model than the trader believed.',
    },
    source: 'Tharp, DGPS · audit: sizing section of H1 review',
  },
  {
    key: 'percent-volatility',
    title: 'The Percent-Volatility Model',
    subtitle: 'Size by ATR so every position breathes the same',
    principle: 'Instead of stop distance, divide the risk budget by the ATR: shares = (equity × vol%) ÷ ATR. Every position then contributes equal daily volatility to the book. Useful when stops vary in quality or when names differ wildly in volatility — a 2% ATR mega-cap and a 15% ATR small-cap stop being sized the same notional is a hidden bet on the wilder one.',
    ourNumber: {
      stat: 'This book’s pick profile',
      value: 'ATR 8–21%',
      read: 'ALAB, DOCN and peers ran 8–21% ATR at entry — high-volatility names. Percent-volatility sizing would have equalized what each position could do to the equity curve in a day.',
    },
    source: 'Tharp, DGPS · percent-volatility model',
  },
  {
    key: 'anti-martingale',
    title: 'Anti-Martingale: Press Winners, Cut Losers',
    subtitle: 'Never average down unless it was pre-planned',
    principle: 'Martingale sizes UP after losses (averaging down); anti-martingale sizes up only as equity grows and positions work. Tharp: all sound sizing is anti-martingale. LordFed’s Test → Core → Press ladder is the practical form — earn size with confirmation, never buy more of what’s going against you unless the add was in the plan at entry.',
    ourNumber: {
      stat: 'Re-attacks — all 148 trades',
      value: '+1.21R avg',
      read: 'Re-attacking was NOT the leak (it beat fresh entries’ +0.61R). The damage was OVERSIZING the failures — BABA’s 5-entry martingale cost −$54k. The behavior is fine; the sizing of it wasn’t.',
    },
    source: 'LordFed, Size Matters · audit: conviction_sizing.py',
  },
  {
    key: 'kelly-trap',
    title: 'The Kelly Trap',
    subtitle: 'Optimal f is only optimal if your edge estimate is real',
    principle: 'Kelly / optimal-f maximizes geometric growth — IF the R-distribution you feed it is the true, stationary one. Feed it a hot sample and it prescribes ruin. Tharp treats optimal-f as an upper bound you stay well below, not a target; half-Kelly is the common compromise, and even that assumes your sample generalizes.',
    ourNumber: {
      stat: 'Full Kelly on this sample',
      value: 'f* = 15.9%/1R',
      read: 'Computed on a +90%/6-month bull sample, Kelly says risk 15.9% of equity per trade (λ* = 5.8× leverage). That is the sample talking, not the edge — on the next regime it’s ruin. Distrust it until the edge is measured over a full cycle.',
    },
    source: 'Tharp, DGPS · audit: pipeline/portfolio/sizing.py',
  },
  {
    key: 'discipline-over-prediction',
    title: 'Discipline Beats Prediction',
    subtitle: 'You cannot forecast R at entry — so stop sizing like you can',
    principle: '"You trade your beliefs about the market." If conviction at entry could forecast outcome, conviction-weighted sizing would beat flat risk. Test it — Tharp’s whole method is turning beliefs into measurable claims. Where conviction fails the test, the percent-risk model IS the edge: equal risk, every trade, no exceptions.',
    ourNumber: {
      stat: 'Plain equal-risk vs his actual sizing',
      value: '+66.7%',
      read: 'Equal risk per trade would have beaten his discretionary sizing by 66.7% (robust: +27% even dropping the top-10 winners). Conviction score ANTI-predicted outcome (corr −0.16; Test tier +1.48R > Press +0.53R). His edge is discipline, not prediction.',
    },
    source: 'Audit: conviction_sizing.py · LordFed, Size Matters',
  },
]

export default function TharpLessons() {
  const [expanded, setExpanded] = useState(null)

  return (
    <div>
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-1">
        Van Tharp — The Study of Position Sizing
      </h3>
      <p className="text-[10px] text-[var(--color-text-muted)] mb-3">
        His framework, lesson by lesson — each checked against this account's audited H1 2026 numbers. A living module: new lessons get appended over time.
      </p>
      <div className="space-y-2">
        {LESSONS.map(lesson => {
          const isExpanded = expanded === lesson.key
          return (
            <div key={lesson.key} className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
              <button
                onClick={() => setExpanded(isExpanded ? null : lesson.key)}
                className="w-full flex items-center justify-between px-4 py-3 text-left cursor-pointer hover:bg-[var(--color-hover-bg)] transition-colors"
              >
                <div>
                  <span className="text-xs font-semibold text-[var(--color-text)]">{lesson.title}</span>
                  <span className="text-[10px] text-[var(--color-text-muted)] ml-2 hidden sm:inline">{lesson.subtitle}</span>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-[10px] font-mono font-semibold text-[var(--color-text-secondary)]">{lesson.ourNumber.value}</span>
                  <span className="text-[var(--color-text-muted)] text-xs">{isExpanded ? '−' : '+'}</span>
                </div>
              </button>

              {isExpanded && (
                <div className="px-4 pb-4 space-y-3 border-t border-[var(--color-border-light)]">
                  <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed pt-3">
                    {lesson.principle}
                  </p>
                  <div className="bg-[var(--color-bg)] rounded px-3 py-2">
                    <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block mb-1">
                      {lesson.ourNumber.stat}
                    </span>
                    <span className="text-sm font-semibold font-mono text-[var(--color-text)]">{lesson.ourNumber.value}</span>
                    <p className="text-[10px] text-[var(--color-text-secondary)] leading-relaxed mt-1">
                      {lesson.ourNumber.read}
                    </p>
                  </div>
                  <p className="text-[9px] text-[var(--color-text-muted)]">{lesson.source}</p>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Wire into SizingTab**

In `SizingTab.jsx`, add import:

```js
import TharpLessons from './sizing/TharpLessons'
```

Inside `SizingContent`'s returned `<div className="space-y-6">`, insert `<TharpLessons />` immediately after the existing "Section 1: Framework Education" `</div>` (before `<SizingCalculator …/>`).

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: build succeeds

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/journal/sizing/TharpLessons.jsx frontend/src/components/journal/SizingTab.jsx
git commit -m "feat(coach): Van Tharp 7-lesson sizing curriculum tied to H1 audit numbers"
```

---

### Task 5: `<SqnReadout>` — live SQN + expectancy panel

**Files:**
- Create: `frontend/src/components/journal/sizing/SqnReadout.jsx`
- Modify: `frontend/src/components/journal/SizingTab.jsx` (import + render + compute `rs`)

**Interfaces:**
- Consumes: `rs: number[]` prop; `expectancyStats`, `sqn`, `sqnBand` from `../lib/sizingStats`.
- Produces: `SqnReadout({ rs })` (default export).

- [ ] **Step 1: Create the component**

```jsx
// frontend/src/components/journal/sizing/SqnReadout.jsx
import { useMemo } from 'react'
import { expectancyStats, sqn, sqnBand } from '../lib/sizingStats'

const TONE_CLASS = {
  bad: 'text-red-600 dark:text-red-400',
  warn: 'text-amber-600 dark:text-amber-400',
  neutral: 'text-[var(--color-text)]',
  good: 'text-green-700 dark:text-green-400',
  muted: 'text-[var(--color-text-muted)]',
}

export default function SqnReadout({ rs }) {
  const stats = useMemo(() => expectancyStats(rs), [rs])
  const sqnValue = useMemo(() => sqn(rs), [rs])
  const band = sqnBand(sqnValue)

  if (!stats.n) {
    return (
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-2">
          System Quality — SQN & Expectancy
        </h3>
        <p className="text-xs text-[var(--color-text-muted)]">No closed trades with a defined stop yet.</p>
      </div>
    )
  }

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          System Quality — SQN & Expectancy
        </h3>
        <code className="text-[9px] font-mono text-[var(--color-text-muted)]">SQN = √N × (mean R ÷ stdev R)</code>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div>
          <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">Closed Trades</span>
          <span className="text-sm font-semibold font-mono text-[var(--color-text)]">{stats.n}</span>
        </div>
        <div>
          <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">Expectancy</span>
          <span className={`text-sm font-semibold font-mono ${stats.meanR >= 0 ? 'text-green-700 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
            {stats.meanR >= 0 ? '+' : ''}{stats.meanR.toFixed(2)}R
          </span>
        </div>
        <div>
          <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">Stdev R</span>
          <span className="text-sm font-medium font-mono text-[var(--color-text)]">{stats.stdevR.toFixed(2)}</span>
        </div>
        <div>
          <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">SQN</span>
          <span className="text-sm font-semibold font-mono text-[var(--color-text)]">
            {sqnValue == null ? '—' : sqnValue.toFixed(2)}
          </span>
        </div>
        <div>
          <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">Tharp Band</span>
          <span className={`text-sm font-semibold ${TONE_CLASS[band.tone]}`}>{band.label}</span>
        </div>
      </div>

      <p className="text-[10px] text-[var(--color-text-secondary)] leading-relaxed border-t border-[var(--color-border-light)] pt-2">
        Tharp grades systems by SQN, not by return: it rewards a consistent R-stream, and the grade sets how much sizing freedom you've earned.
        Raising it means tightening the loss tail and letting the payoff work — not betting bigger. Bands: &lt;1.6 poor · 1.6–1.9 below avg · 2.0–2.4 average · 2.5–2.9 good · 3.0–5.0 excellent · 5.1–6.9 superb.
        {stats.n < 20 && ' ⚠ Fewer than 20 closed trades — SQN is noisy at this sample size.'}
      </p>
    </div>
  )
}
```

- [ ] **Step 2: Wire into SizingTab**

In `SizingTab.jsx`:

```js
import SqnReadout from './sizing/SqnReadout'
import { closedR } from './lib/sizingStats'
```

Inside `SizingContent`, after the `enriched` memo, add:

```js
const rs = useMemo(() => closedR(enriched), [enriched])
```

Render `<SqnReadout rs={rs} />` directly after `<TharpLessons />`.

- [ ] **Step 3: Verify build + tests**

Run: `cd frontend && npx vitest run && npm run build`
Expected: PASS + build succeeds

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/journal/sizing/SqnReadout.jsx frontend/src/components/journal/SizingTab.jsx
git commit -m "feat(coach): live SQN + expectancy readout with Tharp quality bands"
```

---

### Task 6: `<ObjectiveSimulator>` — Monte-Carlo size-to-objectives tool

**Files:**
- Create: `frontend/src/components/journal/sizing/ObjectiveSimulator.jsx`
- Modify: `frontend/src/components/journal/SizingTab.jsx` (import + render)

**Interfaces:**
- Consumes: `rs: number[]` prop; `bootstrapObjective` from `../lib/sizingStats`; recharts (`BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell`) — same import style as `SummarySection.jsx`.
- Produces: `ObjectiveSimulator({ rs })` (default export).

- [ ] **Step 1: Create the component**

```jsx
// frontend/src/components/journal/sizing/ObjectiveSimulator.jsx
import { useState, useMemo } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { bootstrapObjective } from '../lib/sizingStats'

const RISK_CHIPS = [
  { value: 0.25, label: '0.25% target' },
  { value: 0.52, label: '0.52% his actual' },
  { value: 1.0, label: '1.0%' },
  { value: 2.0, label: '2.0%' },
]

function NumField({ label, value, onChange, step = 1, suffix }) {
  return (
    <div>
      <label className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block mb-1">
        {label}{suffix ? ` (${suffix})` : ''}
      </label>
      <input
        type="number"
        value={value}
        step={step}
        onChange={e => onChange(parseFloat(e.target.value) || 0)}
        className="w-full text-xs bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1.5 text-[var(--color-text)] focus:outline-none focus:ring-1 focus:ring-[var(--color-input-border)]"
      />
    </div>
  )
}

export default function ObjectiveSimulator({ rs }) {
  const [riskPct, setRiskPct] = useState(0.25)
  const [horizon, setHorizon] = useState(300)
  const [targetReturnPct, setTargetReturnPct] = useState(50)
  const [maxDDPct, setMaxDDPct] = useState(20)

  const sim = useMemo(() => {
    if (!rs?.length || riskPct <= 0 || horizon <= 0) return null
    return bootstrapObjective(rs, { riskPct, horizon, paths: 2000, targetReturnPct, maxDDPct, seed: 42 })
  }, [rs, riskPct, horizon, targetReturnPct, maxDDPct])

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 space-y-4">
      <div>
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          Size to Objectives — Monte-Carlo
        </h3>
        <p className="text-[10px] text-[var(--color-text-muted)] mt-1">
          Tharp's key move: don't size to maximize — size to hit YOUR objective with an acceptable chance of YOUR worst drawdown.
          This resamples this account's own {rs?.length ?? 0} closed-trade R-distribution.
        </p>
      </div>

      {/* Risk chips + inputs */}
      <div className="flex flex-wrap gap-1.5">
        {RISK_CHIPS.map(chip => (
          <button
            key={chip.value}
            onClick={() => setRiskPct(chip.value)}
            className={`px-2 py-1 text-[10px] font-medium rounded cursor-pointer transition-colors ${
              riskPct === chip.value
                ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)]'
                : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] bg-[var(--color-surface-raised)]'
            }`}
          >
            {chip.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <NumField label="Risk / Trade" suffix="%" value={riskPct} step={0.05} onChange={setRiskPct} />
        <NumField label="Horizon" suffix="trades" value={horizon} step={50} onChange={setHorizon} />
        <NumField label="Target Return" suffix="%" value={targetReturnPct} step={10} onChange={setTargetReturnPct} />
        <NumField label="Max Acceptable DD" suffix="%" value={maxDDPct} step={5} onChange={setMaxDDPct} />
      </div>

      {!sim ? (
        <p className="text-xs text-[var(--color-text-muted)]">Not enough closed trades with stops to simulate.</p>
      ) : (
        <>
          {/* Verdict */}
          <p className="text-xs text-[var(--color-text)] leading-relaxed bg-[var(--color-bg)] rounded px-3 py-2">
            At <span className="font-semibold font-mono">{riskPct}%</span> risk over <span className="font-mono">{horizon}</span> trades:
            median <span className={`font-semibold font-mono ${sim.medianReturn >= 0 ? 'text-green-700 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>{sim.medianReturn >= 0 ? '+' : ''}{sim.medianReturn.toFixed(0)}%</span>,
            hits +{targetReturnPct}% <span className="font-semibold font-mono">{sim.pReachTarget.toFixed(0)}%</span> of the time,
            with a <span className={`font-semibold font-mono ${sim.pBreachDD > 25 ? 'text-red-600 dark:text-red-400' : 'text-[var(--color-text)]'}`}>{sim.pBreachDD.toFixed(0)}%</span> chance of a &gt;{maxDDPct}% drawdown.
          </p>

          {/* Stat tiles */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div>
              <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">Median Return</span>
              <span className="text-sm font-semibold font-mono text-[var(--color-text)]">{sim.medianReturn >= 0 ? '+' : ''}{sim.medianReturn.toFixed(0)}%</span>
            </div>
            <div>
              <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">5th – 95th pctile</span>
              <span className="text-xs font-mono text-[var(--color-text)]">{sim.p5.toFixed(0)}% … {sim.p95.toFixed(0)}%</span>
            </div>
            <div>
              <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">Median Max DD</span>
              <span className="text-sm font-medium font-mono text-[var(--color-text)]">−{sim.medianMaxDD.toFixed(1)}%</span>
            </div>
            <div>
              <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">P(≥ Target)</span>
              <span className="text-sm font-semibold font-mono text-green-700 dark:text-green-400">{sim.pReachTarget.toFixed(0)}%</span>
            </div>
            <div>
              <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">P(DD &gt; {maxDDPct}%)</span>
              <span className={`text-sm font-semibold font-mono ${sim.pBreachDD > 25 ? 'text-red-600 dark:text-red-400' : 'text-[var(--color-text)]'}`}>{sim.pBreachDD.toFixed(0)}%</span>
            </div>
          </div>

          {/* Ending-return histogram; bars at/above target tinted green */}
          <div className="h-36">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sim.histogram} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
                <XAxis
                  dataKey="x"
                  tickFormatter={v => `${Math.round(v)}%`}
                  tick={{ fontSize: 9, fill: 'var(--color-text-muted)' }}
                  interval="preserveStartEnd"
                  tickLine={false}
                />
                <YAxis hide />
                <Tooltip
                  formatter={(v) => [`${v} paths`, 'Count']}
                  labelFormatter={v => `~${Math.round(v)}% ending return`}
                  contentStyle={{ fontSize: 10, background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}
                />
                <Bar dataKey="count" isAnimationActive={false}>
                  {sim.histogram.map((b, i) => (
                    <Cell key={i} fill={b.x >= targetReturnPct ? '#15803d' : 'var(--color-border)'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <p className="text-[9px] text-[var(--color-text-muted)] leading-relaxed">
            Model note: i.i.d. bootstrap of realized R — ignores serial correlation, regime shifts, and that this R-sample comes from a bull half-year (it overstates the forward edge). That limitation is Tharp's point too: size to objectives, and respect what the sample can't tell you.
          </p>
        </>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Wire into SizingTab**

In `SizingTab.jsx`:

```js
import ObjectiveSimulator from './sizing/ObjectiveSimulator'
```

Render `<ObjectiveSimulator rs={rs} />` directly after `<SqnReadout rs={rs} />`.

Final `SizingContent` render order (spec §Page layout):

```jsx
return (
  <div className="space-y-6">
    {/* 1. Method accordions (existing) */}
    {/* 2. <TharpLessons /> */}
    {/* 3. <SqnReadout rs={rs} /> */}
    {/* 4. <ObjectiveSimulator rs={rs} /> */}
    {/* 5. <SizingCalculator …/> (existing) */}
    {/* 6. <PortfolioAudit …/> (existing) */}
  </div>
)
```

- [ ] **Step 3: Verify build + tests**

Run: `cd frontend && npx vitest run && npm run build`
Expected: PASS + build succeeds

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/journal/sizing/ObjectiveSimulator.jsx frontend/src/components/journal/SizingTab.jsx
git commit -m "feat(coach): Monte-Carlo size-to-objectives simulator on the live R-distribution"
```

---

### Task 7: Preview verification

**Files:** none (verification only)

- [ ] **Step 1: Start the preview**

Use browser tool `preview_start` with name `fluxus-dashboard`; navigate to `#/journal`, click the **Sizing** tab.

- [ ] **Step 2: Verify each section**

- Tab renders with no console errors (check `read_console_messages` — especially no "usePortfolio must be used within PortfolioProvider").
- All 6 sections present in order: methods accordions → Van Tharp lessons → SQN readout → Monte-Carlo → calculator → audit.
- Expand 2–3 lessons; numbers match the spec table (+0.88R, 0.52% vs 0.25%, +1.21R, f*=15.9%, +66.7%).
- SQN readout shows N > 0 and a band label (with the live book, N should be in the hundreds).
- Simulator: click the `0.52% his actual` chip → verdict + tiles + histogram update; raise risk to 2% → spread and P(DD) visibly increase; results stable across re-renders (seeded).
- Toggle light/dark theme; check token colors hold.

- [ ] **Step 3: Fix anything found, re-run tests, commit fixes**

Run: `cd frontend && npx vitest run && npm run build`

```bash
git add -A frontend/src
git commit -m "fix(coach): sizing tab polish from preview verification"
```

(Skip the commit if nothing needed fixing.)

---

### Task 8: Deploy to main (gated on user confirmation)

**Files:** none (git operations)

- [ ] **Step 1: Ask the user before deploying** — confirm they want the cherry-pick to `main` now.

- [ ] **Step 2: Cherry-pick the frontend commits (per memory git-safety rules — never touch the dirty main working tree)**

```bash
cd /Users/taolezhu/Documents/AI-Trading-System/.claude/worktrees/trusting-burnell-bde353
git fetch origin
git worktree add /private/tmp/claude-501/deploy-sizing origin/main
cd /private/tmp/claude-501/deploy-sizing
git cherry-pick <task1..task7 commit SHAs, oldest first>
git push origin HEAD:main
cd /Users/taolezhu/Documents/AI-Trading-System/.claude/worktrees/trusting-burnell-bde353
git worktree remove /private/tmp/claude-501/deploy-sizing
```

- [ ] **Step 3: Verify Vercel deploy** — after push, check https://fluxus-dashboard.vercel.app `#/journal` → Sizing tab renders the new sections.

---

## Self-Review Notes

- Spec coverage: 7 lessons (Task 4), SQN readout (Tasks 1+5), Monte-Carlo objective tool (Tasks 2+6), provider wrap (Task 3), live client-side data (Task 5 Step 2 `closedR(enriched)`), append-friendly structure (LESSONS array), preview verification (Task 7), deploy pattern (Task 8). ✓
- Type consistency: `rs: number[]` flows Task 1 → 5 → 6; `bootstrapObjective` opts/return shape identical in Task 2 tests, impl, and Task 6 usage. ✓
- No placeholders: all code blocks complete. ✓
