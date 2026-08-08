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
