import { describe, it, expect } from 'vitest'
import { tradeRisk, aggregate } from './openRisk'

const t = (overrides) => ({
  id: 'x', ticker: 'TST', direction: 'long',
  entryPrice: 100, stopPrice: 95, currentQty: 100,
  ...overrides,
})

describe('openRisk.tradeRisk', () => {
  it('computes risk for a long with stop below entry', () => {
    expect(tradeRisk(t())).toEqual({ riskDollars: 500, gainDollars: 0, atRisk: true })
  })

  it('computes locked gain for a long with stop above entry (post-T1 trailed)', () => {
    expect(tradeRisk(t({ stopPrice: 110 }))).toEqual({
      riskDollars: 0, gainDollars: 1000, atRisk: false,
    })
  })

  it('computes risk for a short with stop above entry', () => {
    expect(tradeRisk(t({ direction: 'short', stopPrice: 105 }))).toEqual({
      riskDollars: 500, gainDollars: 0, atRisk: true,
    })
  })

  it('computes locked gain for a short with stop below entry', () => {
    expect(tradeRisk(t({ direction: 'short', stopPrice: 90 }))).toEqual({
      riskDollars: 0, gainDollars: 1000, atRisk: false,
    })
  })

  it('returns zeros for a fully exited trade', () => {
    expect(tradeRisk(t({ currentQty: 0 }))).toEqual({
      riskDollars: 0, gainDollars: 0, atRisk: false,
    })
  })

  it('treats stop AT entry as no risk and no gain', () => {
    expect(tradeRisk(t({ stopPrice: 100 }))).toEqual({
      riskDollars: 0, gainDollars: 0, atRisk: false,
    })
  })
})

describe('openRisk.aggregate', () => {
  it('returns zero totals for empty input', () => {
    const out = aggregate([])
    expect(out.totalRiskDollars).toBe(0)
    expect(out.totalLockedDollars).toBe(0)
    expect(out.totalRiskR).toBe(0)
    expect(out.perTrade).toEqual([])
  })

  it('sums risk and locked across a mix', () => {
    const trades = [
      t({ id: 'a', ticker: 'A', stopPrice: 95 }),                      // risk 500
      t({ id: 'b', ticker: 'B', stopPrice: 110 }),                     // locked 1000
      t({ id: 'c', ticker: 'C', direction: 'short', stopPrice: 105 }), // risk 500
    ]
    const out = aggregate(trades, 2500)
    expect(out.totalRiskDollars).toBe(1000)
    expect(out.totalLockedDollars).toBe(1000)
    expect(out.totalRiskR).toBe(0.4)
    expect(out.atRiskCount).toBe(2)
    expect(out.lockedCount).toBe(1)
  })

  it('sorts at-risk first (largest), then locked-in', () => {
    const trades = [
      t({ id: 'small', ticker: 'S', stopPrice: 99 }),    // risk 100
      t({ id: 'big',   ticker: 'B', stopPrice: 90 }),    // risk 1000
      t({ id: 'lock',  ticker: 'L', stopPrice: 110 }),   // locked 1000
    ]
    const out = aggregate(trades)
    expect(out.perTrade.map(p => p.ticker)).toEqual(['B', 'S', 'L'])
  })

  it('skips trades with currentQty 0', () => {
    const trades = [t({ id: 'a', currentQty: 0 })]
    const out = aggregate(trades)
    expect(out.perTrade).toHaveLength(0)
  })
})
