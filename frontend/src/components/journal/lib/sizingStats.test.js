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
  it('drops trades whose rr is non-finite', () => {
    expect(closedR([mk({ rr: Infinity })])).toEqual([])
    expect(closedR([mk({ rr: -Infinity })])).toEqual([])
    expect(closedR([mk({ rr: NaN })])).toEqual([])
    expect(closedR([mk({ rr: undefined })])).toEqual([])
    // and keeps the finite ones alongside them
    expect(closedR([mk({ rr: 2 }), mk({ rr: Infinity }), mk({ rr: -1 })])).toEqual([2, -1])
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

  // Tharp caps the trade count at 100 — that cap is what keeps the quality
  // bands calibrated. Expected values come from expectancyStats on the SAME
  // array, so these assertions pin the cap rather than re-deriving the mean.
  it('caps N at 100: a 200-trade sample uses sqrt(100), not sqrt(200)', () => {
    const rs = Array.from({ length: 200 }, (_, i) => (i % 2 === 0 ? 2 : -1))
    const { n, meanR, stdevR } = expectancyStats(rs)
    expect(n).toBe(200) // expectancyStats keeps the TRUE count
    expect(sqn(rs)).toBeCloseTo(Math.sqrt(100) * meanR / stdevR, 10)
    expect(sqn(rs)).not.toBeCloseTo(Math.sqrt(200) * meanR / stdevR, 6)
  })

  it('uses sqrt(n) untouched below the cap', () => {
    const rs = Array.from({ length: 40 }, (_, i) => (i % 2 === 0 ? 2 : -1))
    const { n, meanR, stdevR } = expectancyStats(rs)
    expect(n).toBe(40)
    expect(sqn(rs)).toBeCloseTo(Math.sqrt(40) * meanR / stdevR, 10)
  })

  it('pins the boundary: exactly n = 100 uses sqrt(100)', () => {
    const rs = Array.from({ length: 100 }, (_, i) => (i % 2 === 0 ? 2 : -1))
    const { meanR, stdevR } = expectancyStats(rs)
    expect(sqn(rs)).toBeCloseTo(Math.sqrt(100) * meanR / stdevR, 10)
    // n = 101 must not exceed it
    const rs101 = Array.from({ length: 101 }, (_, i) => (i % 2 === 0 ? 2 : -1))
    const s101 = expectancyStats(rs101)
    expect(sqn(rs101)).toBeCloseTo(Math.sqrt(100) * s101.meanR / s101.stdevR, 10)
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

  // Single-element rs makes the PRNG draw irrelevant: every path is the same
  // deterministic sequence, so the arithmetic can be pinned exactly.
  it('pins exact drawdown on a monotonically losing path', () => {
    // multiplier = 1 + (10/100) * -0.5 = 0.95 per step, peak stays at 1
    const out = bootstrapObjective([-0.5], {
      ...base, riskPct: 10, horizon: 3, paths: 10, maxDDPct: 20,
    })
    expect(out.endReturns[0]).toBeCloseTo((0.95 ** 3 - 1) * 100, 10)
    expect(out.medianReturn).toBeCloseTo((0.95 ** 3 - 1) * 100, 10)
    expect(out.medianMaxDD).toBeCloseTo((1 - 0.95 ** 3) * 100, 10)
    expect(out.pBreachDD).toBe(0) // 14.26% max DD does not breach the 20% cap
  })

  it('a new equity high resets the drawdown to zero', () => {
    // multiplier = 1 + (100/100) * 1 = 2 per step: equity 1 → 32, peak tracks it
    const out = bootstrapObjective([1], {
      ...base, riskPct: 100, horizon: 5, paths: 10,
    })
    expect(out.endReturns[0]).toBeCloseTo(3100, 10)
    expect(out.medianMaxDD).toBeCloseTo(0, 10)
    expect(out.pBreachDD).toBe(0)
  })

  // The two tests above are monotone, so they alone cannot tell correct
  // peak-tracking apart from a fixed `peak = 1`. This one can: it needs a
  // drawdown measured from a running high that is ABOVE the starting equity.
  it('measures drawdown from the running high, not from starting equity', () => {
    // multipliers 2 (up) and 0.5 (down). Over 3 steps only the all-up path
    // (1 of 8) never dips below its running peak, so ~87.5% of paths draw down.
    // A fixed peak = 1 would only see paths that dip below the START (~62.5%).
    const out = bootstrapObjective([1, -0.5], {
      ...base, riskPct: 100, horizon: 3, paths: 800, maxDDPct: 0,
    })
    expect(out.pBreachDD).toBeGreaterThan(80)
    expect(out.pBreachDD).toBeLessThan(95)
  })

  it('flags a drawdown that breaches the cap', () => {
    // 0.95^20 ≈ 0.3585 → max DD ≈ 64.2%, well past the 20% cap
    const out = bootstrapObjective([-0.5], {
      ...base, riskPct: 10, horizon: 20, paths: 10, maxDDPct: 20,
    })
    expect(out.medianMaxDD).toBeCloseTo((1 - 0.95 ** 20) * 100, 10)
    expect(out.pBreachDD).toBe(100)
  })
})
