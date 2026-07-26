import { describe, it, expect } from 'vitest'
import { buildFrozenSnapshot, snapComposite, suggestSplits } from './snapshot'

describe('snapComposite — single and repeated splits', () => {
  it('snaps a single 8', () => expect(snapComposite(8.1)).toBe(8))
  it('snaps a single reverse 1/10', () => expect(snapComposite(0.101)).toBeCloseTo(0.1, 6))
  it('snaps a COMPOSITE 1/90 (=1/10 × 1/9) that the old detector missed', () =>
    expect(snapComposite(1 / 88)).toBeCloseTo(1 / 90, 6))
  it('snaps composite 72 (=8×9)', () => expect(snapComposite(71)).toBe(72))
  it('returns null near 1 (no split)', () => expect(snapComposite(1.03)).toBeNull())
})

describe('buildFrozenSnapshot — un-adjusts feed onto as-traded scale', () => {
  const table = {
    SOXS: [
      { exDate: '2026-06-10', factor: 1 / 10 },
      { exDate: '2026-07-15', factor: 1 / 9 },
    ],
    SNXX: [{ exDate: '2026-06-03', factor: 8 }],
  }
  const trades = [
    { ticker: 'SOXS', entryDate: '2026-06-04', entryPrice: 5.91, trims: [] },
    { ticker: 'SNXX', entryDate: '2026-04-21', entryPrice: 71.78, trims: [] },
    { ticker: 'AAPL', entryDate: '2026-04-21', entryPrice: 200, trims: [] },
  ]
  const feed = {
    'SOXS:2026-06-04': 531.9,   // 90× inflated by the two later reverse splits
    'SNXX:2026-04-21': 8.97,    // 1/8 of as-traded
    'AAPL:2026-04-21': 201,     // no split
    'ZZZ:2026-04-21': 5,        // not a traded ticker → excluded
  }

  const { prices, meta } = buildFrozenSnapshot(trades, feed, table)

  it('un-inflates the SOXS phantom back to ~$5.91 (kills the 6000% spike)', () => {
    expect(prices['SOXS:2026-06-04']).toBeCloseTo(531.9 / 90, 4)
  })
  it('restores SNXX to as-traded ~$71.8', () => {
    expect(prices['SNXX:2026-04-21']).toBeCloseTo(8.97 * 8, 4)
  })
  it('leaves a non-split ticker unchanged', () => {
    expect(prices['AAPL:2026-04-21']).toBe(201)
  })
  it('excludes tickers not in the trade set', () => {
    expect(prices['ZZZ:2026-04-21']).toBeUndefined()
  })
  it('reports meta', () => {
    expect(meta.pointCount).toBe(3)
    expect(meta.tickers).toContain('SOXS')
  })
})

describe('suggestSplits — detects repeated leveraged-ETF splits', () => {
  const trades = [
    { ticker: 'SOXS', entryDate: '2026-06-04', entryPrice: 5.91, trims: [] }, // before both → cum 1/90
    { ticker: 'SOXS', entryDate: '2026-06-20', entryPrice: 10, trims: [] },   // between → cum 1/9
    { ticker: 'AAPL', entryDate: '2026-04-21', entryPrice: 200, trims: [] },  // no split
  ]
  const feed = {
    'SOXS:2026-06-04': 531.9, // 5.91 × 90
    'SOXS:2026-06-20': 90,    // 10 × 9
    'AAPL:2026-04-21': 201,
  }
  const { suggestions, straddles } = suggestSplits(trades, feed)

  it('proposes TWO SOXS reverse splits (1:10 then 1:9)', () => {
    const soxs = suggestions.filter(s => s.ticker === 'SOXS')
    expect(soxs.length).toBe(2)
    const labels = soxs.map(s => s.ratioLabel).sort()
    expect(labels).toEqual(['1:10', '1:9'])
  })
  it('does not propose a split for a normal ticker', () => {
    expect(suggestions.some(s => s.ticker === 'AAPL')).toBe(false)
  })
  it('has no straddles here', () => expect(straddles.length).toBe(0))
})

describe('suggestSplits — flags a straddle instead of snapping', () => {
  const trades = [{
    ticker: 'TZA', entryDate: '2026-05-17', entryPrice: 4.97,
    trims: [{ date: '2026-07-20', price: 45, qty: 100 }], // post-reverse-split scale
  }]
  const feed = { 'TZA:2026-05-17': 49.7, 'TZA:2026-07-20': 44 } // entry 10× inflated, trim ~1×
  const { suggestions, straddles } = suggestSplits(trades, feed)
  it('flags TZA as a straddle, no auto suggestion', () => {
    expect(straddles.some(s => s.ticker === 'TZA')).toBe(true)
    expect(suggestions.some(s => s.ticker === 'TZA')).toBe(false)
  })
})
