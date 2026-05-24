# Phase 1 — Live Trailing-Stop / Leg-State UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add per-position leg state, suggested trail stops based on v3 optimizer defaults, EMA reference data per ticker, trim target hints, EMA proximity chips, and campaign grouping for pyramids to the Portfolio Tracker + Exposure tabs.

**Architecture:** Pipeline change adds `ema10`/`ema20`/`wk_ema10`/`wk_ema20` to `universe.json` (piggybacks on already-fetched 1y OHLC). Frontend reads them via the existing `useUniverse` hook. Pure JS helper modules derive leg state, stop suggestion, trim targets, proximity, and campaign grouping from trade + universe data. New small React components render the UI affordances; existing tab files wire them in. No new persisted fields on trades — everything is derived.

**Tech Stack:** Python 3.11 (pipeline), React 19 + Vite + Tailwind 4 (frontend), pandas/yfinance (data), Vitest (frontend tests — note: codebase has no test runner yet, so plan adds one as Task 0).

---

### Task 0: Set up frontend test runner (Vitest)

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/vitest.config.js`
- Create: `frontend/src/test-setup.js`

The codebase has no frontend tests yet. We add Vitest because Vite is already the bundler and Vitest shares its config. Pure-JS helper modules are the bulk of Phase 1 logic and they must be tested.

- [ ] **Step 1: Add Vitest + RTL deps**

Run:
```bash
cd frontend && npm install --save-dev vitest@^2.1.0 @testing-library/react@^16.1.0 @testing-library/jest-dom@^6.6.0 jsdom@^25.0.0
```

Expected: `package.json` devDependencies gains the four packages, `package-lock.json` updated.

- [ ] **Step 2: Add test script to package.json**

Modify `frontend/package.json` — add to `"scripts"`:
```json
"test": "vitest run",
"test:watch": "vitest"
```

- [ ] **Step 3: Create vitest config**

Create `frontend/vitest.config.js`:
```js
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.js'],
    globals: true,
  },
})
```

- [ ] **Step 4: Create test setup**

Create `frontend/src/test-setup.js`:
```js
import '@testing-library/jest-dom/vitest'
```

- [ ] **Step 5: Verify with a smoke test**

Create `frontend/src/__test__.smoke.test.js`:
```js
import { describe, it, expect } from 'vitest'
describe('smoke', () => {
  it('runs', () => { expect(1 + 1).toBe(2) })
})
```

Run: `cd frontend && npm test`
Expected: 1 passed.

- [ ] **Step 6: Delete smoke test, commit**

```bash
rm frontend/src/__test__.smoke.test.js
git add frontend/package.json frontend/package-lock.json frontend/vitest.config.js frontend/src/test-setup.js
git commit -m "chore(frontend): add Vitest + RTL for unit testing"
```

---

### Task 1: Pipeline — add EMA fields to universe.json

**Files:**
- Modify: `pipeline/adapters/yfinance_adapter.py` (around line 419, in `enrich_universe`'s `enriched[ticker] = {...}` dict)
- Modify: `pipeline/screeners/run_all.py` (around line 367, the `universe_cols` whitelist)

- [ ] **Step 1: Add EMA computations in yfinance_adapter**

In `enrich_universe`, locate the existing `enriched[ticker] = {...}` dict near line 419. Above it, after the existing `ema21 = ...` line, add:
```python
ema10 = float(hist['Close'].ewm(span=10, adjust=False).mean().iloc[-1])
ema20 = float(hist['Close'].ewm(span=20, adjust=False).mean().iloc[-1])
weekly_closes = hist['Close'].resample('W-FRI').last().dropna()
wk_ema10 = float(weekly_closes.ewm(span=10, adjust=False).mean().iloc[-1]) if len(weekly_closes) >= 1 else None
wk_ema20 = float(weekly_closes.ewm(span=20, adjust=False).mean().iloc[-1]) if len(weekly_closes) >= 1 else None
```

Then in the `enriched[ticker] = {...}` dict (alongside `'bo_count_1m': bo_1m,` etc.), add:
```python
'ema10': ema10,
'ema20': ema20,
'wk_ema10': wk_ema10,
'wk_ema20': wk_ema20,
```

- [ ] **Step 2: Add columns to universe_cols whitelist**

In `pipeline/screeners/run_all.py`, locate the `universe_cols = [...]` list. Append to the last row:
```python
'ema10', 'ema20', 'wk_ema10', 'wk_ema20',
```

- [ ] **Step 3: Verify pipeline still runs**

Run:
```bash
python3 -c "from pipeline.adapters.yfinance_adapter import YfinanceAdapter; print('OK')"
```

Expected: `OK`.

- [ ] **Step 4: Regenerate universe.json on a small subset (optional but recommended)**

Use the existing optimizer's debug snippet to fetch one ticker and verify the new fields appear:
```bash
python3 -c "
from datetime import date
from pipeline.portfolio.ohlc_cache import fetch_ohlc
import pandas as pd
df = fetch_ohlc('MU', date(2025, 11, 1), date(2026, 5, 1))
close = df['Close']
print('ema10:', round(close.ewm(span=10).mean().iloc[-1], 2))
print('ema20:', round(close.ewm(span=20).mean().iloc[-1], 2))
wk = close.resample('W-FRI').last().dropna()
print('wk_ema10:', round(wk.ewm(span=10).mean().iloc[-1], 2))
print('wk_ema20:', round(wk.ewm(span=20).mean().iloc[-1], 2))
"
```

Expected: prints four positive numbers.

- [ ] **Step 5: Commit**

```bash
git add pipeline/adapters/yfinance_adapter.py pipeline/screeners/run_all.py
git commit -m "feat(pipeline): export ema10/ema20/wk_ema10/wk_ema20 to universe.json"
```

---

### Task 2: legState pure helper + tests

**Files:**
- Create: `frontend/src/components/portfolio/lib/legState.js`
- Create: `frontend/src/components/portfolio/lib/legState.test.js`

- [ ] **Step 1: Write failing tests**

Create `frontend/src/components/portfolio/lib/legState.test.js`:
```js
import { describe, it, expect } from 'vitest'
import { derive } from './legState'

describe('legState.derive', () => {
  it('returns CLOSED if currentQty is 0', () => {
    expect(derive({ currentQty: 0, originalQty: 100, trims: [] })).toBe('CLOSED')
  })

  it('returns CLOSED if any trim is sell_rest', () => {
    expect(derive({ currentQty: 50, originalQty: 100, trims: [{ type: 'sell_rest' }] })).toBe('CLOSED')
  })

  it('returns PRE_TRIM when no trims and qty > 0', () => {
    expect(derive({ currentQty: 100, originalQty: 100, trims: [] })).toBe('PRE_TRIM')
  })

  it('returns POST_T1 with exactly 1 partial trim', () => {
    expect(derive({ currentQty: 70, originalQty: 100, trims: [{ type: 'trim_1_3' }] })).toBe('POST_T1')
  })

  it('returns POST_T2 with exactly 2 partial trims', () => {
    expect(derive({
      currentQty: 40, originalQty: 100,
      trims: [{ type: 'trim_1_3' }, { type: 'trim_1_3' }],
    })).toBe('POST_T2')
  })

  it('returns POST_T3 with 3+ partial trims', () => {
    expect(derive({
      currentQty: 10, originalQty: 100,
      trims: [{ type: 'trim_1_3' }, { type: 'trim_1_5' }, { type: 'trim_1_5' }],
    })).toBe('POST_T3')
  })
})
```

Run: `cd frontend && npm test legState`
Expected: 6 FAIL (module not found).

- [ ] **Step 2: Implement legState**

Create `frontend/src/components/portfolio/lib/legState.js`:
```js
/**
 * Derive a position's leg state from its current quantity and trim history.
 * @param {{currentQty: number, originalQty: number, trims: Array<{type: string}>}} trade
 * @returns {'PRE_TRIM'|'POST_T1'|'POST_T2'|'POST_T3'|'CLOSED'}
 */
export function derive(trade) {
  if (trade.currentQty <= 0) return 'CLOSED'
  const trims = trade.trims || []
  if (trims.some(t => t.type === 'sell_rest')) return 'CLOSED'
  const n = trims.length
  if (n === 0) return 'PRE_TRIM'
  if (n === 1) return 'POST_T1'
  if (n === 2) return 'POST_T2'
  return 'POST_T3'
}

/** Color hint for a leg-state badge, used by LegStateBadge. */
export const STATE_COLORS = {
  PRE_TRIM: 'amber',
  POST_T1: 'blue',
  POST_T2: 'teal',
  POST_T3: 'green',
  CLOSED: 'gray',
}
```

Run: `cd frontend && npm test legState`
Expected: 6 PASS.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/portfolio/lib/legState.js frontend/src/components/portfolio/lib/legState.test.js
git commit -m "feat(portfolio): add legState derivation helper + tests"
```

---

### Task 3: trimTargets pure helper + tests

**Files:**
- Create: `frontend/src/components/portfolio/lib/trimTargets.js`
- Create: `frontend/src/components/portfolio/lib/trimTargets.test.js`

Computes R-multiple price targets anchored to the CSV initial stop.

- [ ] **Step 1: Write failing tests**

Create `frontend/src/components/portfolio/lib/trimTargets.test.js`:
```js
import { describe, it, expect } from 'vitest'
import { compute, isHit } from './trimTargets'

describe('trimTargets.compute', () => {
  it('returns +4R and +8R for a long', () => {
    const t = { entryPrice: 100, stopPrice: 95, direction: 'long', trims: [] }
    const out = compute(t)
    expect(out.targetR4).toBe(120)
    expect(out.targetR8).toBe(140)
  })
  it('inverts price math for a short', () => {
    const t = { entryPrice: 100, stopPrice: 105, direction: 'short', trims: [] }
    const out = compute(t)
    expect(out.targetR4).toBe(80)
    expect(out.targetR8).toBe(60)
  })
  it('returns null when stopPrice equals entryPrice (no R)', () => {
    const t = { entryPrice: 100, stopPrice: 100, direction: 'long', trims: [] }
    expect(compute(t)).toBeNull()
  })
})

describe('trimTargets.isHit', () => {
  it('returns true for long when any trim is at or above the level', () => {
    const trims = [{ price: 121 }]
    expect(isHit(trims, 120, 'long')).toBe(true)
    expect(isHit(trims, 140, 'long')).toBe(false)
  })
  it('returns true for short when any trim is at or below the level', () => {
    const trims = [{ price: 79 }]
    expect(isHit(trims, 80, 'short')).toBe(true)
    expect(isHit(trims, 60, 'short')).toBe(false)
  })
})
```

Run: `cd frontend && npm test trimTargets`
Expected: 5 FAIL.

- [ ] **Step 2: Implement trimTargets**

Create `frontend/src/components/portfolio/lib/trimTargets.js`:
```js
/**
 * Compute price levels for +4R and +8R targets anchored to the trade's
 * CSV initial stop. Direction-aware.
 *
 * @returns {{targetR4: number, targetR8: number}|null} null when R is undefined.
 */
export function compute(trade) {
  const { entryPrice, stopPrice, direction } = trade
  const rPerShare = Math.abs(entryPrice - stopPrice)
  if (rPerShare <= 0) return null
  const sign = direction === 'long' ? 1 : -1
  return {
    targetR4: entryPrice + sign * 4 * rPerShare,
    targetR8: entryPrice + sign * 8 * rPerShare,
  }
}

/**
 * Returns true if any trim in the array has crossed (at-or-beyond) the level
 * in the direction of the trade.
 */
export function isHit(trims, level, direction) {
  if (!trims || trims.length === 0) return false
  return trims.some(t => {
    if (direction === 'long') return t.price >= level
    return t.price <= level
  })
}
```

Run: `cd frontend && npm test trimTargets`
Expected: 5 PASS.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/portfolio/lib/trimTargets.js frontend/src/components/portfolio/lib/trimTargets.test.js
git commit -m "feat(portfolio): add trimTargets helper for +4R/+8R levels"
```

---

### Task 4: stopSuggestion pure helper + tests

**Files:**
- Create: `frontend/src/components/portfolio/lib/stopSuggestion.js`
- Create: `frontend/src/components/portfolio/lib/stopSuggestion.test.js`

Suggests a trail stop based on leg state and per-ticker EMA data.

- [ ] **Step 1: Write failing tests**

Create `frontend/src/components/portfolio/lib/stopSuggestion.test.js`:
```js
import { describe, it, expect } from 'vitest'
import { suggest } from './stopSuggestion'

describe('stopSuggestion.suggest', () => {
  it('returns null when leg state is CLOSED', () => {
    expect(suggest({ state: 'CLOSED' }, {}, {})).toBeNull()
  })

  it('returns CSV initial stop for PRE_TRIM', () => {
    const trade = { state: 'PRE_TRIM', stopPrice: 95, entryPrice: 100, direction: 'long' }
    const out = suggest(trade, {}, { atr: 2 })
    expect(out.suggestedStop).toBe(95)
    expect(out.basis).toBe('csv-initial')
  })

  it('returns max(entry, wk_ema20 - 0.25*ATR) for POST_T1 long when EMA available', () => {
    const trade = { state: 'POST_T1', stopPrice: 95, entryPrice: 100, direction: 'long' }
    const ema = { wk_ema20: 110 }
    const out = suggest(trade, ema, { atr: 4 })
    // 110 - 0.25*4 = 109; max(100, 109) = 109
    expect(out.suggestedStop).toBe(109)
    expect(out.basis).toBe('wk20ema')
  })

  it('uses breakeven when wk_ema20 - buffer is below entry (long)', () => {
    const trade = { state: 'POST_T1', stopPrice: 95, entryPrice: 100, direction: 'long' }
    const ema = { wk_ema20: 95 }  // below entry
    const out = suggest(trade, ema, { atr: 4 })
    expect(out.suggestedStop).toBe(100)
    expect(out.basis).toBe('breakeven')
  })

  it('inverts for shorts: min(entry, wk_ema20 + 0.25*ATR)', () => {
    const trade = { state: 'POST_T1', stopPrice: 105, entryPrice: 100, direction: 'short' }
    const ema = { wk_ema20: 90 }
    const out = suggest(trade, ema, { atr: 4 })
    // 90 + 0.25*4 = 91; min(100, 91) = 91
    expect(out.suggestedStop).toBe(91)
    expect(out.basis).toBe('wk20ema')
  })

  it('returns null suggestion when no EMA data available for POST_T1+', () => {
    const trade = { state: 'POST_T1', stopPrice: 95, entryPrice: 100, direction: 'long' }
    const out = suggest(trade, {}, { atr: 4 })
    expect(out.suggestedStop).toBeNull()
    expect(out.basis).toBe('no-data')
  })
})
```

Run: `cd frontend && npm test stopSuggestion`
Expected: 6 FAIL.

- [ ] **Step 2: Implement stopSuggestion**

Create `frontend/src/components/portfolio/lib/stopSuggestion.js`:
```js
/**
 * Suggest a trail stop based on the position's leg state and per-ticker EMA data.
 *
 * Rules (v3 optimizer defaults):
 *   PRE_TRIM                → CSV initial stop (don't override user's risk decision)
 *   POST_T1/POST_T2/POST_T3 → max(entry, wk_ema20 - 0.25 ATR)  for longs
 *                              min(entry, wk_ema20 + 0.25 ATR)  for shorts
 *
 * @param {{state: string, stopPrice: number, entryPrice: number, direction: string}} trade
 * @param {{ema10?: number, ema20?: number, wk_ema10?: number, wk_ema20?: number}} ema
 * @param {{atr: number}} stats
 * @returns {{suggestedStop: number|null, basis: string, rationale: string}|null}
 */
export function suggest(trade, ema, stats) {
  if (trade.state === 'CLOSED') return null

  if (trade.state === 'PRE_TRIM') {
    return {
      suggestedStop: trade.stopPrice,
      basis: 'csv-initial',
      rationale: 'Initial risk stop from trade entry',
    }
  }

  // POST_T1, POST_T2, POST_T3 — patient trailing
  const wk20 = ema?.wk_ema20
  if (wk20 == null || !Number.isFinite(wk20)) {
    return {
      suggestedStop: null,
      basis: 'no-data',
      rationale: 'No weekly-20EMA data — set manually',
    }
  }

  const atr = stats?.atr ?? 0
  const buffer = 0.25 * atr

  if (trade.direction === 'long') {
    const wk20Stop = wk20 - buffer
    if (wk20Stop > trade.entryPrice) {
      return {
        suggestedStop: round2(wk20Stop),
        basis: 'wk20ema',
        rationale: `wk-20EMA ($${round2(wk20)}) − 0.25×ATR buffer`,
      }
    }
    return {
      suggestedStop: trade.entryPrice,
      basis: 'breakeven',
      rationale: 'wk-20EMA below entry — hold breakeven floor',
    }
  }

  // short
  const wk20Stop = wk20 + buffer
  if (wk20Stop < trade.entryPrice) {
    return {
      suggestedStop: round2(wk20Stop),
      basis: 'wk20ema',
      rationale: `wk-20EMA ($${round2(wk20)}) + 0.25×ATR buffer`,
    }
  }
  return {
    suggestedStop: trade.entryPrice,
    basis: 'breakeven',
    rationale: 'wk-20EMA above entry — hold breakeven floor',
  }
}

function round2(n) { return Math.round(n * 100) / 100 }
```

Run: `cd frontend && npm test stopSuggestion`
Expected: 6 PASS.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/portfolio/lib/stopSuggestion.js frontend/src/components/portfolio/lib/stopSuggestion.test.js
git commit -m "feat(portfolio): add stopSuggestion engine (v3 defaults)"
```

---

### Task 5: emaProximity pure helper + tests

**Files:**
- Create: `frontend/src/components/portfolio/lib/emaProximity.js`
- Create: `frontend/src/components/portfolio/lib/emaProximity.test.js`

Returns the list of proximity chips a row should display.

- [ ] **Step 1: Write failing tests**

Create `frontend/src/components/portfolio/lib/emaProximity.test.js`:
```js
import { describe, it, expect } from 'vitest'
import { chips } from './emaProximity'

describe('emaProximity.chips', () => {
  it('returns empty array when no EMA data', () => {
    expect(chips({ price: 100, direction: 'long' }, {})).toEqual([])
  })

  it('adds 10EMA chip when within 1.5% of price', () => {
    const out = chips({ price: 100, direction: 'long' }, { ema10: 99, ema20: 80 })
    expect(out).toContainEqual({ label: '10EMA', tone: 'amber' })
  })

  it('adds 20EMA chip when within 2% of price', () => {
    const out = chips({ price: 100, direction: 'long' }, { ema20: 98.5 })
    expect(out).toContainEqual({ label: '20EMA', tone: 'red' })
  })

  it('adds T2 chip when weekly close < wk_ema10 for long', () => {
    const out = chips({ price: 100, direction: 'long', wkClose: 99 }, { wk_ema10: 100 })
    expect(out).toContainEqual({ label: 'T2', tone: 'orange' })
  })

  it('adds STOP chip when weekly close < wk_ema20 for long', () => {
    const out = chips({ price: 100, direction: 'long', wkClose: 95 }, { wk_ema20: 100 })
    expect(out).toContainEqual({ label: 'STOP', tone: 'red' })
  })

  it('inverts for shorts: T2 fires when wk_close > wk_ema10', () => {
    const out = chips({ price: 100, direction: 'short', wkClose: 101 }, { wk_ema10: 100 })
    expect(out).toContainEqual({ label: 'T2', tone: 'orange' })
  })
})
```

Run: `cd frontend && npm test emaProximity`
Expected: 6 FAIL.

- [ ] **Step 2: Implement emaProximity**

Create `frontend/src/components/portfolio/lib/emaProximity.js`:
```js
/**
 * Compute the proximity chips a row should display.
 * @param {{price: number, direction: string, wkClose?: number}} ctx
 * @param {{ema10?: number, ema20?: number, wk_ema10?: number, wk_ema20?: number}} ema
 * @returns {Array<{label: string, tone: string}>}
 */
export function chips(ctx, ema) {
  if (!ema) return []
  const out = []
  const price = ctx.price
  const long = ctx.direction === 'long'

  // 10EMA proximity (within 1.5%)
  if (ema.ema10 != null && price > 0) {
    if (Math.abs(price - ema.ema10) / price < 0.015) {
      out.push({ label: '10EMA', tone: 'amber' })
    }
  }

  // 20EMA proximity (within 2%)
  if (ema.ema20 != null && price > 0) {
    if (Math.abs(price - ema.ema20) / price < 0.02) {
      out.push({ label: '20EMA', tone: 'red' })
    }
  }

  // T2 signal: weekly close vs wk_ema10
  if (ctx.wkClose != null && ema.wk_ema10 != null) {
    const fired = long ? ctx.wkClose < ema.wk_ema10 : ctx.wkClose > ema.wk_ema10
    if (fired) out.push({ label: 'T2', tone: 'orange' })
  }

  // STOP signal: weekly close vs wk_ema20
  if (ctx.wkClose != null && ema.wk_ema20 != null) {
    const fired = long ? ctx.wkClose < ema.wk_ema20 : ctx.wkClose > ema.wk_ema20
    if (fired) out.push({ label: 'STOP', tone: 'red' })
  }

  return out
}
```

Run: `cd frontend && npm test emaProximity`
Expected: 6 PASS.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/portfolio/lib/emaProximity.js frontend/src/components/portfolio/lib/emaProximity.test.js
git commit -m "feat(portfolio): add emaProximity chip computation + tests"
```

---

### Task 6: campaign grouping pure helper + tests

**Files:**
- Create: `frontend/src/components/portfolio/lib/campaign.js`
- Create: `frontend/src/components/portfolio/lib/campaign.test.js`

Groups trades into pyramid campaigns by `(ticker, direction)` within a 60-business-day window.

- [ ] **Step 1: Write failing tests**

Create `frontend/src/components/portfolio/lib/campaign.test.js`:
```js
import { describe, it, expect } from 'vitest'
import { groupByCampaigns } from './campaign'

const t = (id, ticker, direction, entryDate, entryPrice, originalQty, stopPrice, currentQty) =>
  ({ id, ticker, direction, entryDate, entryPrice, originalQty, stopPrice, currentQty, trims: [] })

describe('campaign.groupByCampaigns', () => {
  it('returns singletons when nothing overlaps', () => {
    const trades = [
      t('a', 'MU', 'long', '2026-01-01', 100, 100, 95, 100),
      t('b', 'TSLA', 'long', '2026-01-02', 200, 50, 190, 50),
    ]
    const groups = groupByCampaigns(trades)
    expect(groups).toHaveLength(2)
    expect(groups[0].layers).toHaveLength(1)
  })

  it('groups same-ticker same-direction trades within 60 business days', () => {
    const trades = [
      t('a', 'DOCN', 'long', '2026-03-15', 70, 100, 65, 100),
      t('b', 'DOCN', 'long', '2026-04-14', 82, 50, 78, 50),
    ]
    const groups = groupByCampaigns(trades)
    expect(groups).toHaveLength(1)
    expect(groups[0].layers).toHaveLength(2)
    expect(groups[0].ticker).toBe('DOCN')
  })

  it('does not group across 60-business-day gap', () => {
    const trades = [
      t('a', 'AAPL', 'long', '2026-01-01', 100, 100, 95, 0),
      t('b', 'AAPL', 'long', '2026-06-01', 110, 100, 105, 100),  // ~5 months later
    ]
    const groups = groupByCampaigns(trades)
    expect(groups).toHaveLength(2)
  })

  it('does not group long and short of same ticker', () => {
    const trades = [
      t('a', 'PLTR', 'long', '2026-01-01', 100, 100, 95, 100),
      t('b', 'PLTR', 'short', '2026-01-02', 100, 100, 105, 100),
    ]
    const groups = groupByCampaigns(trades)
    expect(groups).toHaveLength(2)
  })

  it('aggregates blended entry, total qty, total R$ at campaign level', () => {
    const trades = [
      t('a', 'DOCN', 'long', '2026-03-15', 70, 100, 65, 50),
      t('b', 'DOCN', 'long', '2026-04-14', 82, 100, 78, 100),
    ]
    const groups = groupByCampaigns(trades)
    const c = groups[0]
    // blended entry over original qty: (70*100 + 82*100) / 200 = 76
    expect(c.blendedEntry).toBe(76)
    expect(c.totalOriginalQty).toBe(200)
    expect(c.totalRDollars).toBe(5 * 100 + 4 * 100)  // 900
  })
})
```

Run: `cd frontend && npm test campaign`
Expected: 5 FAIL.

- [ ] **Step 2: Implement campaign helper**

Create `frontend/src/components/portfolio/lib/campaign.js`:
```js
/**
 * Group trades into pyramid campaigns.
 * Same (ticker, direction); consecutive entries within 60 business days.
 *
 * @param {Array} trades  expects fields: id, ticker, direction, entryDate (ISO),
 *                        entryPrice, originalQty, stopPrice, currentQty, trims
 * @returns {Array<Campaign>}  campaign = { id, ticker, direction, layers, blendedEntry,
 *                                          totalOriginalQty, totalCurrentQty, totalRDollars,
 *                                          openLayersCount, firstEntry, lastEntry }
 */
export function groupByCampaigns(trades) {
  const byKey = new Map()
  for (const t of trades) {
    const key = `${t.ticker}__${t.direction}`
    if (!byKey.has(key)) byKey.set(key, [])
    byKey.get(key).push(t)
  }

  const campaigns = []
  for (const [, list] of byKey) {
    const sorted = [...list].sort((a, b) => a.entryDate.localeCompare(b.entryDate))
    let cur = [sorted[0]]
    for (let i = 1; i < sorted.length; i++) {
      const prev = cur[cur.length - 1]
      if (businessDaysBetween(prev.entryDate, sorted[i].entryDate) <= 60) {
        cur.push(sorted[i])
      } else {
        campaigns.push(buildCampaign(cur))
        cur = [sorted[i]]
      }
    }
    campaigns.push(buildCampaign(cur))
  }
  return campaigns
}

function buildCampaign(layers) {
  const first = layers[0]
  const totalOriginalQty = layers.reduce((s, l) => s + l.originalQty, 0)
  const totalCurrentQty = layers.reduce((s, l) => s + l.currentQty, 0)
  const blendedEntry = totalOriginalQty > 0
    ? layers.reduce((s, l) => s + l.entryPrice * l.originalQty, 0) / totalOriginalQty
    : 0
  const totalRDollars = layers.reduce(
    (s, l) => s + Math.abs(l.entryPrice - l.stopPrice) * l.originalQty,
    0
  )
  const openLayersCount = layers.filter(l => l.currentQty > 0).length
  return {
    id: `campaign__${first.ticker}__${first.direction}__${first.entryDate}`,
    ticker: first.ticker,
    direction: first.direction,
    layers,
    blendedEntry,
    totalOriginalQty,
    totalCurrentQty,
    totalRDollars,
    openLayersCount,
    firstEntry: first.entryDate,
    lastEntry: layers[layers.length - 1].entryDate,
  }
}

/** Naive business-days approximation: total days × 5/7. */
function businessDaysBetween(a, b) {
  const ad = new Date(a)
  const bd = new Date(b)
  const days = Math.abs(Math.round((bd - ad) / 86400000))
  return Math.round(days * 5 / 7)
}
```

Run: `cd frontend && npm test campaign`
Expected: 5 PASS.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/portfolio/lib/campaign.js frontend/src/components/portfolio/lib/campaign.test.js
git commit -m "feat(portfolio): add campaign grouping helper for pyramid campaigns"
```

---

### Task 7: LegStateBadge component

**Files:**
- Create: `frontend/src/components/portfolio/ui/LegStateBadge.jsx`

Tiny presentational component — no tests; visual review only.

- [ ] **Step 1: Create the component**

Create `frontend/src/components/portfolio/ui/LegStateBadge.jsx`:
```jsx
const COLORS = {
  PRE_TRIM:  { bg: 'bg-amber-500/15',  text: 'text-amber-600',  ring: 'ring-amber-500/30' },
  POST_T1:   { bg: 'bg-blue-500/15',   text: 'text-blue-600',   ring: 'ring-blue-500/30' },
  POST_T2:   { bg: 'bg-teal-500/15',   text: 'text-teal-600',   ring: 'ring-teal-500/30' },
  POST_T3:   { bg: 'bg-green-500/15',  text: 'text-green-600',  ring: 'ring-green-500/30' },
  CLOSED:    { bg: 'bg-gray-500/10',   text: 'text-gray-500',   ring: 'ring-gray-500/20' },
}

const LABELS = {
  PRE_TRIM: 'PRE-T1',
  POST_T1: 'POST-T1',
  POST_T2: 'POST-T2',
  POST_T3: 'POST-T3',
  CLOSED: '—',
}

export default function LegStateBadge({ state }) {
  if (!state || state === 'CLOSED') return null
  const c = COLORS[state] || COLORS.PRE_TRIM
  return (
    <span
      className={`inline-block px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wide ring-1 ${c.bg} ${c.text} ${c.ring}`}
      title={`Leg state: ${LABELS[state]}`}
    >
      {LABELS[state]}
    </span>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/portfolio/ui/LegStateBadge.jsx
git commit -m "feat(portfolio): add LegStateBadge UI component"
```

---

### Task 8: StopCell component (editable + suggestion + Accept)

**Files:**
- Create: `frontend/src/components/portfolio/ui/StopCell.jsx`

Replaces the bare `<EditablePrice>` for the Stop column. Shows the editable input + a small suggestion line + Accept link.

- [ ] **Step 1: Create the component**

Create `frontend/src/components/portfolio/ui/StopCell.jsx`:
```jsx
import EditablePrice from './EditablePrice'

export default function StopCell({ stopPrice, suggestion, onChange }) {
  const sug = suggestion?.suggestedStop
  const showSuggestion = sug != null && Math.abs(sug - stopPrice) > 0.01
  return (
    <div className="flex flex-col gap-0.5">
      <EditablePrice value={stopPrice} onChange={onChange} />
      {showSuggestion && (
        <div className="text-[10px] text-[var(--color-text-muted)] flex items-center gap-1.5" title={suggestion.rationale}>
          <span>sug ${sug.toFixed(2)}</span>
          <button
            onClick={() => onChange(sug)}
            className="text-[var(--color-accent)] hover:underline cursor-pointer"
          >
            Accept
          </button>
        </div>
      )}
      {suggestion?.basis === 'no-data' && (
        <div className="text-[10px] text-[var(--color-text-muted)]" title={suggestion.rationale}>
          no wk-20EMA data
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/portfolio/ui/StopCell.jsx
git commit -m "feat(portfolio): add StopCell with suggestion + accept link"
```

---

### Task 9: TrimTargetsLine component

**Files:**
- Create: `frontend/src/components/portfolio/ui/TrimTargetsLine.jsx`

- [ ] **Step 1: Create the component**

Create `frontend/src/components/portfolio/ui/TrimTargetsLine.jsx`:
```jsx
import { compute, isHit } from '../lib/trimTargets'

export default function TrimTargetsLine({ trade }) {
  const targets = compute(trade)
  if (!targets) return null
  const hit4 = isHit(trade.trims, targets.targetR4, trade.direction)
  const hit8 = isHit(trade.trims, targets.targetR8, trade.direction)
  return (
    <div className="text-[10px] text-[var(--color-text-muted)] mt-0.5">
      <span className={hit4 ? 'line-through text-[var(--color-profit)]' : ''}>
        +4R ${targets.targetR4.toFixed(2)}
      </span>
      {' · '}
      <span className={hit8 ? 'line-through text-[var(--color-profit)]' : ''}>
        +8R ${targets.targetR8.toFixed(2)}
      </span>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/portfolio/ui/TrimTargetsLine.jsx
git commit -m "feat(portfolio): add TrimTargetsLine inline component"
```

---

### Task 10: ProximityChips component

**Files:**
- Create: `frontend/src/components/portfolio/ui/ProximityChips.jsx`

- [ ] **Step 1: Create the component**

Create `frontend/src/components/portfolio/ui/ProximityChips.jsx`:
```jsx
const TONE = {
  amber:  'bg-amber-500/15 text-amber-600 ring-amber-500/30',
  red:    'bg-red-500/15 text-red-600 ring-red-500/30',
  orange: 'bg-orange-500/15 text-orange-600 ring-orange-500/30',
}

export default function ProximityChips({ chips }) {
  if (!chips || chips.length === 0) return null
  return (
    <span className="inline-flex gap-0.5">
      {chips.map((c, i) => (
        <span
          key={i}
          className={`px-1 py-0.5 rounded text-[8.5px] font-bold uppercase tracking-wider ring-1 ${TONE[c.tone] || TONE.amber}`}
        >
          {c.label}
        </span>
      ))}
    </span>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/portfolio/ui/ProximityChips.jsx
git commit -m "feat(portfolio): add ProximityChips component"
```

---

### Task 11: Wire it all into OverviewTab

**Files:**
- Modify: `frontend/src/components/portfolio/tabs/OverviewTab.jsx`

Add imports, compute per-row leg state / suggestion / chips / targets, replace the bare Stop cell with `<StopCell>`, add badge + targets line + chips next to the ticker.

- [ ] **Step 1: Add imports at top of file**

In `OverviewTab.jsx`, locate the existing imports block. Add:
```jsx
import LegStateBadge from '../ui/LegStateBadge'
import StopCell from '../ui/StopCell'
import TrimTargetsLine from '../ui/TrimTargetsLine'
import ProximityChips from '../ui/ProximityChips'
import { derive as deriveLegState } from '../lib/legState'
import { suggest as suggestStop } from '../lib/stopSuggestion'
import { chips as proximityChipsFn } from '../lib/emaProximity'
import { useUniverse } from '../../../hooks/useUniverse'
```

- [ ] **Step 2: Pull universe data into the component**

In the `OverviewTab` function body, near the existing `usePortfolio` line, add:
```jsx
const { universe } = useUniverse()
const universeByTicker = useMemo(() => {
  const out = {}
  if (!universe) return out
  for (const r of universe) {
    out[r.ticker] = {
      ema10: r.ema10, ema20: r.ema20,
      wk_ema10: r.wk_ema10, wk_ema20: r.wk_ema20,
      atr_pct: r.adr_pct,  // ADR is the closest proxy already on universe
    }
  }
  return out
}, [universe])
```

- [ ] **Step 3: Compute per-row derived data**

In the trade-row `.map((t, idx) => ...)` (currently around line 127 after sortedFiltered map), at the top of the callback (before the `<tr>` return), add:
```jsx
const legState = deriveLegState({
  currentQty: t.currentQty,
  originalQty: t.originalQty,
  trims: t.trims,
})
const u = universeByTicker[t.ticker] || {}
const px = t.lastPrice || t.entryPrice
const atrDollars = (u.atr_pct ?? 0) * 0.01 * px
const stopSugg = suggestStop(
  { state: legState, stopPrice: t.stopPrice, entryPrice: t.entryPrice, direction: t.direction },
  u,
  { atr: atrDollars },
)
const chipsList = proximityChipsFn(
  { price: px, direction: t.direction, wkClose: px },
  u,
)
```

- [ ] **Step 4: Replace the Ticker cell with badge + targets + chips**

Find the current Ticker `<td>` (currently `<td ...>{t.ticker}</td>` near line 128). Replace its inner content:
```jsx
<td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] font-bold whitespace-nowrap">
  <div className="flex items-center gap-1.5">
    <span>{t.ticker}</span>
    <LegStateBadge state={legState} />
    <ProximityChips chips={chipsList} />
  </div>
  <TrimTargetsLine trade={t} />
</td>
```

- [ ] **Step 5: Replace the Stop cell with StopCell**

Find the current Stop column cell — currently:
```jsx
<td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">
  <EditablePrice value={t.stopPrice} onChange={v => updateStop(t.id, v)} />
</td>
```

Replace with:
```jsx
<td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">
  <StopCell stopPrice={t.stopPrice} suggestion={stopSugg} onChange={v => updateStop(t.id, v)} />
</td>
```

- [ ] **Step 6: Visual verification**

Run: `cd frontend && npm run dev` (or use Claude Preview), navigate to `#/portfolio`, click "Try Sample", confirm:
- Each row shows a leg-state badge next to the ticker
- Each row shows "+4R $X · +8R $Y" under the ticker
- Stop column shows the editable input plus a "sug $X → Accept" line for trades with EMA data
- No console errors

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/portfolio/tabs/OverviewTab.jsx
git commit -m "feat(portfolio): wire leg-state + stop suggestion + trim targets + chips into Tracker"
```

---

### Task 12: Wire campaign grouping into ExposureTab

**Files:**
- Modify: `frontend/src/components/portfolio/tabs/ExposureTab.jsx`

Replace the current ticker-only grouping with the new `groupByCampaigns` call. Campaign parent row shows blended entry, total R$, open layer count.

- [ ] **Step 1: Add import + replace grouping logic**

In `ExposureTab.jsx`, add to imports:
```jsx
import { groupByCampaigns } from '../lib/campaign'
```

Find the existing `groupedTrades = useMemo(...)` block (around line 36-58). Replace its body with:
```jsx
const groupedTrades = useMemo(() => {
  const campaigns = groupByCampaigns(openTrades)
  return campaigns.map(c => {
    const totalQty = c.layers.reduce((s, t) => s + t.currentQty, 0)
    const totalCostBasis = c.layers.reduce((s, t) => s + t.entryPrice * t.currentQty, 0)
    const avgEntry = totalQty > 0 ? totalCostBasis / totalQty : c.blendedEntry
    return {
      ticker: c.ticker,
      trades: c.layers,
      isGroup: c.layers.length > 1,
      direction: c.direction,
      totalQty,
      avgEntry,
      lastPrice: c.layers[0].lastPrice,
      weight: c.layers.reduce((s, t) => s + t.weight, 0),
      marketVal: c.layers.reduce((s, t) => s + t.marketVal, 0),
      totalPL: c.layers.reduce((s, t) => s + t.totalPL, 0),
      totalReturnPct: c.layers.reduce((s, t) => s + t.totalPL, 0) /
        c.layers.reduce((s, t) => s + t.entryPrice * t.currentQty, 0) * 100,
      _campaignLayers: c.openLayersCount,
      _totalRDollars: c.totalRDollars,
    }
  })
}, [openTrades])
```

- [ ] **Step 2: Update group ticker cell to surface campaign info**

Find the group-row Ticker `<td>` (currently shows `{g.ticker} ({g.trades.length})` for groups). Replace its inner content:
```jsx
<td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] font-bold">
  {g.isGroup && <span className="inline-block w-3.5 text-[var(--color-text-muted)] text-[10px]">{expanded ? '▼' : '▶'}</span>}
  {g.ticker}
  {g.isGroup && (
    <span className="ml-1 text-[10px] text-[var(--color-text-muted)]">
      campaign · {g.trades.length} layers
    </span>
  )}
</td>
```

- [ ] **Step 3: Visual verification**

Run the dev server, navigate to Portfolio → Exposure, expand a multi-entry campaign (e.g., DOCN, BE, NBIS in the sample data), confirm:
- The grouped row shows "campaign · N layers" label
- Aggregate values are sensible (weighted blended entry, total qty, total weight)
- Expanding shows individual layer rows
- No console errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/portfolio/tabs/ExposureTab.jsx
git commit -m "feat(portfolio): campaign grouping in Exposure Detail table"
```

---

### Task 13: Run optimizer to regenerate universe.json with new EMA fields

**Files:** none modified

The pipeline change in Task 1 means the next `universe.json` will contain the new EMA fields. The frontend components rely on those fields. Regenerate now so dev preview works.

- [ ] **Step 1: Run the pipeline**

Run:
```bash
python3 -m pipeline.screeners.run_all
```

Expected: finishes in ~3-5 min, writes `data/output/universe.json`.

- [ ] **Step 2: Sanity-check the new fields are present**

Run:
```bash
python3 -c "
import json
data = json.load(open('data/output/universe.json'))
sample = data['rows'][0]
for k in ('ema10','ema20','wk_ema10','wk_ema20'):
    print(k, '=', sample.get(k))
"
```

Expected: four numeric values (or `None` for tickers with insufficient history).

- [ ] **Step 3: Commit**

```bash
git add data/output/universe.json
git commit -m "chore: regenerate universe.json with EMA fields for Phase 1 UI"
```

---

### Task 14: End-to-end verification + push

**Files:** none modified

- [ ] **Step 1: Run all frontend tests**

Run: `cd frontend && npm test`
Expected: all tests pass (legState, trimTargets, stopSuggestion, emaProximity, campaign).

- [ ] **Step 2: Build the frontend**

Run: `cd frontend && npm run build`
Expected: build succeeds with no errors.

- [ ] **Step 3: Manual end-to-end check via preview server**

Start the preview server (existing `.claude/launch.json` has `fluxus-dashboard` defined). Navigate to `#/portfolio` and:
- Load Try Sample
- Confirm Tracker rows show: leg-state badge, trim targets line, proximity chips (where applicable), stop suggestion ghost-text + Accept link
- Click Accept on one row, confirm the Stop value updates to the suggested value
- Navigate to Exposure tab, confirm multi-entry campaigns are grouped under a single parent row with "campaign · N layers" label
- Expand a campaign, confirm individual layers shown
- Verify no console errors

- [ ] **Step 4: Push**

```bash
git push origin main
```

---

## Acceptance criteria — final checklist

- [ ] `universe.json` includes `ema10`, `ema20`, `wk_ema10`, `wk_ema20` per ticker
- [ ] Portfolio Tracker rows show leg-state badge next to ticker
- [ ] Portfolio Tracker rows show "+4R $X · +8R $Y" target line under ticker (strike-through when hit)
- [ ] Portfolio Tracker rows show EMA proximity chips when applicable
- [ ] Stop column shows editable input plus "sug $X → Accept" link when suggestion differs from current
- [ ] Exposure Detail table groups multi-entry same-ticker open trades into a campaign parent row
- [ ] All Vitest unit tests pass
- [ ] Frontend build succeeds
- [ ] No console errors during dev-preview interaction
- [ ] Plan and code committed; main pushed to origin

---

## Out-of-scope reminders (NOT in this plan)

- **Capital-at-Risk widget** — that's Phase 2; will live in the empty Exposure slot we already cleared
- **"Add layer" button** on campaign parent row — deferred until trade-form refactor is scoped separately
- **Per-ticker live (intraday) EMA refresh** — universe.json is daily; Phase 1 explicitly uses prior-day close EMAs

If Phase 1 is shipping clean and Phase 2 is ready, the "Add layer" button can be tacked onto Phase 2 since both touch the Exposure tab.
