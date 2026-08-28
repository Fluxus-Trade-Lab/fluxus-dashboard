import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { enrichTrades } from './calculations'

/**
 * The 1D columns, against the trade that exposed them.
 *
 * Andy noticed it, the data side reproduced it against the real MRNA
 * 2026-08-19 shape and handed the diagnosis over (DATA_CONTRACTS §七,
 * 2026-08-28): prev close 62.96 → gapped → entered 106.34 → closed 174.38,
 * 1,000 shares. Charging the whole gap to the day we bought read +$111,420
 * where the truth was +$68,040.
 *
 * The fixture is that trade, held still. If someone re-anchors this column on
 * yesterday's close again, these numbers move by $43,380 and say so.
 */
const TODAY = '2026-08-19'
beforeEach(() => { vi.useFakeTimers(); vi.setSystemTime(new Date(`${TODAY}T12:00:00Z`)) })
afterEach(() => vi.useRealTimers())

const MRNA = {
  ticker: 'MRNA', direction: 'long', entryPrice: 106.34, originalQty: 1000,
  currentQty: 1000, entryDate: '2026-08-19', trims: [],
}
const prices = (over = {}) => ({
  'MRNA:2026-08-19': 174.38,   // today's close
  'MRNA:2026-08-18': 62.96,    // the close we did NOT hold through
  ...over,
})
const one = (trade, dp) => enrichTrades([trade], 1_000_000, dp)[0]

describe('1D baseline on a position opened today', () => {
  it('counts only what we held — not the gap that happened before we were in', () => {
    const t = one(MRNA, prices())
    expect(t.pl1D).toBeCloseTo(68_040, 0)          // (174.38 − 106.34) × 1000
    expect(t.change1D).toBeCloseTo(63.98, 2)
  })

  it('does not report the number the old code did', () => {
    const t = one(MRNA, prices())
    expect(t.pl1D).not.toBeCloseTo(111_420, 0)     // the $43,380 overstatement
    expect(t.change1D).not.toBeCloseTo(176.97, 1)
  })

  it('is symmetric — buying a gap DOWN must not show a loss we never took', () => {
    const t = one({ ...MRNA, entryPrice: 50 },
                  prices({ 'MRNA:2026-08-19': 55, 'MRNA:2026-08-18': 90 }))
    expect(t.pl1D).toBeCloseTo(5_000, 0)           // +5 × 1000, not −35 × 1000
    expect(t.change1D).toBeGreaterThan(0)
  })

  it('leaves unrealizedPL alone — it was anchored on entry and always right', () => {
    expect(one(MRNA, prices()).unrealizedPL).toBeCloseTo(68_040, 0)
  })
})

describe('1D baseline on a position held from before', () => {
  it('uses yesterday\'s close, which is what 1D means once you held overnight', () => {
    const t = one({ ...MRNA, entryDate: '2026-08-11', entryPrice: 60 }, prices())
    expect(t.pl1D).toBeCloseTo((174.38 - 62.96) * 1000, 0)
    expect(t.change1D).toBeCloseTo(((174.38 - 62.96) / 62.96) * 100, 2)
  })

  it('a short reverses the sign', () => {
    const t = one({ ...MRNA, entryDate: '2026-08-11', direction: 'short' }, prices())
    expect(t.pl1D).toBeCloseTo(-(174.38 - 62.96) * 1000, 0)
  })
})

describe('not measured, never zero', () => {
  it('reports null when today has no price at all — 0 would read as "flat"', () => {
    // only stale prices on file: the walk-back would have found them and the
    // old code would have printed 0
    const t = one({ ...MRNA, entryDate: '2026-08-11' },
                  { 'MRNA:2026-08-15': 100 })
    expect(t.change1D).toBe(null)
    expect(t.pl1D).toBe(null)
    expect(t.marketVal).toBeCloseTo(100_000, 0)   // market value still resolves
  })

  it('reports null when both ends walk back to the same session', () => {
    const t = one({ ...MRNA, entryDate: '2026-08-11' }, { 'MRNA:2026-08-19': 174.38 })
    expect(t.change1D).toBe(null)
    expect(t.pl1D).toBe(null)
  })

  it('a closed position keeps its zeros — it has no 1D to not-measure', () => {
    const closed = one({ ...MRNA, isClosed: true, currentQty: 0,
                         trims: [{ qty: 1000, price: 174.38, date: TODAY }] }, prices())
    expect(closed.pl1D).toBe(0)
    expect(closed.change1D).toBe(0)
  })
})
