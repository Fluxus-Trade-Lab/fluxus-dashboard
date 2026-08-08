import { describe, it, expect } from 'vitest'
import { mulberry32, closedR, expectancyStats, sqn, sqnBand, bootstrapObjective } from './sizingStats'

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

  it('returns the matching tone for each band', () => {
    expect(sqnBand(null)).toEqual({ label: '—', tone: 'muted' })
    expect(sqnBand(1.0)).toEqual({ label: 'Poor', tone: 'bad' })
    expect(sqnBand(1.7)).toEqual({ label: 'Below average', tone: 'warn' })
    expect(sqnBand(2.2)).toEqual({ label: 'Average', tone: 'neutral' })
    expect(sqnBand(2.7)).toEqual({ label: 'Good', tone: 'good' })
    expect(sqnBand(4.0)).toEqual({ label: 'Excellent', tone: 'good' })
    expect(sqnBand(6.0)).toEqual({ label: 'Superb', tone: 'good' })
    expect(sqnBand(7.5)).toEqual({ label: 'Holy Grail', tone: 'good' })
  })

  it('pins the exact band boundaries (gap-free ladder)', () => {
    expect(sqnBand(1.6).label).toBe('Below average')
    expect(sqnBand(1.9999).label).toBe('Below average')
    expect(sqnBand(2.0).label).toBe('Average')
    expect(sqnBand(2.4999).label).toBe('Average')
    expect(sqnBand(2.5).label).toBe('Good')
    expect(sqnBand(2.9999).label).toBe('Good')
    expect(sqnBand(3.0).label).toBe('Excellent')
    // Tharp: 3.0–5.0 Excellent, 5.1+ Superb — the <= 5.0 edge is intentional
    expect(sqnBand(5.0).label).toBe('Excellent')
    expect(sqnBand(5.0000001).label).toBe('Superb')
    expect(sqnBand(6.9999).label).toBe('Superb')
    expect(sqnBand(7.0).label).toBe('Holy Grail')
  })

  it('treats non-finite input as unknown, not as the top band', () => {
    expect(sqnBand(NaN)).toEqual({ label: '—', tone: 'muted' })
    expect(sqnBand(Infinity)).toEqual({ label: '—', tone: 'muted' })
    expect(sqnBand(-Infinity)).toEqual({ label: '—', tone: 'muted' })
  })
})

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
