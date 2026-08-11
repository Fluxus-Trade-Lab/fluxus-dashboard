import { describe, it, expect } from 'vitest'
import { enrichTrades } from './calculations'
import { closedR, rDenominatorStop } from '../../journal/lib/sizingStats'
import { compute as trimTargets } from './trimTargets'
import { rRisk } from './diagnosticsR'

/**
 * The acceptance test for the backfill defect, stated the way it was found:
 *
 *   "Take a closed trade, change its stopPrice, reload, and look at its R.
 *    If it did not move, it is fixed."
 *
 * The defect was a backfill — `initialStop ??= stopPrice` — sitting in nine
 * places across the client, the GAS reader, and six analytics helpers. It was
 * correct exactly once, on the day the field was introduced, because no stop
 * had ever been trailed and so every live stop WAS its entry stop. It becomes
 * wrong the first time a stop moves, and it fails silently: the R still prints
 * a number, just a different one than the trade was sized against.
 *
 * These tests do not check the backfill is gone. They check the property the
 * backfill violated, which stays true however the code is later rearranged.
 */

const closed = (over = {}) => ({
  id: 't1', ticker: 'AAA', direction: 'long',
  entryDate: '2026-01-05', entryPrice: 100,
  originalQty: 100, currentQty: 0,
  initialStop: 95, stopPrice: 95,
  isClosed: true,
  trims: [{ date: '2026-02-02', price: 110, qty: 100, type: 'exit' }],
  ...over,
})

describe('trailing the live stop cannot move a recorded R', () => {
  it('enrichTrades keeps rr anchored when stopPrice is dragged up', () => {
    const at = (stopPrice) => enrichTrades([closed({ stopPrice })], {})[0].rr
    expect(at(99)).toBeCloseTo(at(95), 10)
    // And the anchored value is the one the trade was sized on: risked $5,
    // made $10, so +2R — not the +10R a $0.50 trailed stop would imply.
    expect(at(99.5)).toBeCloseTo(2, 6)
  })

  it('closedR is unchanged by a trailed stop', () => {
    const at = (stopPrice) => closedR(enrichTrades([closed({ stopPrice })], {}))
    expect(at(99)).toEqual(at(95))
  })

  it('trim targets stay where entry put them', () => {
    const at = (stopPrice) => trimTargets(closed({ stopPrice, isClosed: false }))
    expect(at(99)).toEqual(at(95))
  })

  it('rRisk stays anchored', () => {
    expect(rRisk(closed({ stopPrice: 99 }))).toBeCloseTo(rRisk(closed()), 10)
  })
})

describe('a trade with no recorded entry stop has no R', () => {
  const orphan = (over = {}) => closed({ initialStop: undefined, ...over })

  it('rDenominatorStop reports null rather than the live stop', () => {
    expect(rDenominatorStop(orphan())).toBeNull()
  })

  it('it leaves the R sample instead of joining it with a guessed value', () => {
    expect(closedR(enrichTrades([orphan()], {}))).toEqual([])
  })

  it('rRisk and trim targets are null, not measured from zero', () => {
    // Guards a specific slip: `entryPrice - null` is `entryPrice - 0` in JS, so
    // a null anchor that is only propagated arithmetically produces a
    // full-price risk unit instead of nothing.
    expect(rRisk(orphan())).toBeNull()
    expect(trimTargets(orphan({ isClosed: false }))).toBeNull()
  })

  it('a live stop of any value does not rescue it', () => {
    for (const stopPrice of [50, 95, 99, 150]) {
      expect(closedR(enrichTrades([orphan({ stopPrice })], {}))).toEqual([])
    }
  })
})
