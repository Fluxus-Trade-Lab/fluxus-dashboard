import { describe, it, expect } from 'vitest'
import { computeQtyMismatches } from './qtyMismatch'

const base = {
  id: 't1', ticker: 'AAPL', direction: 'long', entryDate: '2026-01-05',
  originalQty: 100, currentQty: 60, trims: [{ qty: 40, price: 110 }],
}

describe('computeQtyMismatches', () => {
  it('returns nothing when currentQty agrees with originalQty − Σtrims', () => {
    expect(computeQtyMismatches([base])).toEqual([])
  })

  it('flags a row where the Sheet says LESS held than the trim log implies', () => {
    // ARM shape, 2026-09-24 incident: a hand edit understated currentQty.
    const t = { ...base, id: 'arm1', ticker: 'ARM', originalQty: 300, currentQty: 100, trims: [{ qty: 160, price: 180 }] }
    // derived = 300 - 160 = 140; currentQty 100 < 140 → gap -13.3% of position
    const out = computeQtyMismatches([t])
    expect(out).toHaveLength(1)
    expect(out[0]).toMatchObject({
      id: 'arm1', ticker: 'ARM', sheetSays: 'less held than the trim log implies',
    })
    expect(out[0].gapPctOfPosition).toBeCloseTo(-13.3, 1)
  })

  it('flags a row where the Sheet says MORE held than the trim log implies', () => {
    // The opposite failure mode: a hand edit overstated currentQty instead of
    // understating it — a detector wired to only one direction would miss this.
    const t = { ...base, id: 't2', currentQty: 70 } // derived 60, currentQty 70 → +10 vs 100 original
    const out = computeQtyMismatches([t])
    expect(out).toHaveLength(1)
    expect(out[0].sheetSays).toBe('more held than the trim log implies')
    expect(out[0].gapPctOfPosition).toBeCloseTo(10, 1)
  })

  it('checks every logged trim, not just ones before some as-of date (currentQty is live)', () => {
    const t = {
      ...base,
      originalQty: 100, currentQty: 0,
      trims: [{ qty: 40, price: 110 }, { qty: 60, price: 120 }],
    }
    expect(computeQtyMismatches([t])).toEqual([])
  })

  it('is silent on a fully closed position that nets to zero cleanly', () => {
    const t = { ...base, originalQty: 50, currentQty: 0, trims: [{ qty: 50, price: 90 }], isClosed: true }
    expect(computeQtyMismatches([t])).toEqual([])
  })

  it('never reports a raw share count field', () => {
    const t = { ...base, currentQty: 55 }
    const out = computeQtyMismatches([t])
    expect(out[0]).not.toHaveProperty('currentQty')
    expect(out[0]).not.toHaveProperty('originalQty')
    expect(out[0]).not.toHaveProperty('derived')
  })

  it('sorts by entryDate then ticker', () => {
    const t1 = { ...base, id: 'a', ticker: 'ZZZ', entryDate: '2026-02-01', currentQty: 61 }
    const t2 = { ...base, id: 'b', ticker: 'AAA', entryDate: '2026-01-01', currentQty: 61 }
    const out = computeQtyMismatches([t1, t2])
    expect(out.map(r => r.id)).toEqual(['b', 'a'])
  })

  it('handles an empty or missing trade list', () => {
    expect(computeQtyMismatches([])).toEqual([])
    expect(computeQtyMismatches(undefined)).toEqual([])
  })
})
