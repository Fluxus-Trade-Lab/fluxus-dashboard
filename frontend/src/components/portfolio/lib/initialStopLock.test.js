/**
 * Regression tests for the initial-stop lock.
 *
 * The Stop Price column in the tracker is the LIVE / trailing stop. Once a
 * trade is created, every R-multiple denominator must anchor to `initialStop`,
 * which is locked at entry. Trailing the live stop after the fact must NEVER
 * rewrite historical R math (post-mortem, journal, trim targets, campaign
 * aggregation, demonFinder sizing/heat).
 *
 * If any of these tests fails, somebody re-introduced the original bug where
 * trailing a stop silently halved the recorded R-multiple.
 */
import { describe, it, expect } from 'vitest'
import { rRisk, rMultiple } from './diagnosticsR'
import { compute as trimTargets } from './trimTargets'
import { groupByCampaigns } from './campaign'

const baseTrade = {
  id: 't1',
  ticker: 'BE',
  direction: 'long',
  entryDate: '2026-04-08',
  entryPrice: 147.20,
  originalQty: 990,
  currentQty: 990,
  stopPrice: 137.00,
  initialStop: 137.00,  // locked at entry
  realizedPL: 7261.40,  // = +7.33R × R$
  trims: [],
  isClosed: false,
}

describe('initial-stop lock — R denominator survives trailing the live stop', () => {
  it('rRisk anchors to initialStop, not the trailed stopPrice', () => {
    const anchored = rRisk(baseTrade)
    const trailed = rRisk({ ...baseTrade, stopPrice: 145.00 })
    expect(anchored).toBeCloseTo(10098, 1)
    expect(trailed).toBeCloseTo(10098, 1)
  })

  it('rMultiple is invariant under trailing the live stop', () => {
    const anchored = rMultiple(baseTrade)
    const trailed = rMultiple({ ...baseTrade, stopPrice: 145.00 })
    expect(anchored).toBeCloseTo(0.719, 2)
    expect(trailed).toBeCloseTo(0.719, 2)
  })

  it('trimTargets +4R/+8R prices are invariant under trailing the live stop', () => {
    const anchored = trimTargets(baseTrade)
    const trailed = trimTargets({ ...baseTrade, stopPrice: 145.00 })
    expect(anchored.targetR4).toBeCloseTo(188.0, 1)
    expect(trailed.targetR4).toBeCloseTo(188.0, 1)
    expect(anchored.targetR8).toBeCloseTo(228.8, 1)
    expect(trailed.targetR8).toBeCloseTo(228.8, 1)
  })

  it('campaign totalRDollars sums initial-stop risk across layers', () => {
    const layer1 = { ...baseTrade, id: 'l1', originalQty: 500 }
    const layer2 = { ...baseTrade, id: 'l2', originalQty: 500, stopPrice: 145.00 } // trailed
    const groups = groupByCampaigns([layer1, layer2])
    expect(groups).toHaveLength(1)
    // Both layers still contribute their initial-stop risk:
    //   500 × |147.20 - 137.00| = 5,100  (×2 = 10,200)
    expect(groups[0].totalRDollars).toBeCloseTo(10200, 0)
  })

  it('rRisk falls back to stopPrice when initialStop is absent (legacy data)', () => {
    const legacy = { ...baseTrade, initialStop: undefined }
    expect(rRisk(legacy)).toBeCloseTo(10098, 1)
  })
})
