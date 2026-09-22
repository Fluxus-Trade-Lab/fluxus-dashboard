import { describe, it, expect } from 'vitest'
import { computeStopSim } from './stopSim'

// entryDate is a GAS timestamp (JST midnight restated in UTC), so the trade's
// real entry day is one JST day after the raw UTC date. Before T-0922-44 the
// stop-trigger walk started from the raw (one-day-early) date and would scan a
// day the trade was never open on.
describe('computeStopSim — entry date is read as JST, not the raw GAS UTC date', () => {
  it('does not scan the day before the JST entry date for a stop trigger', () => {
    const trades = [{
      id: 't1', ticker: 'TICK', direction: 'long',
      entryDate: '2026-05-15T15:00:00.000Z', // JST entry day is 2026-05-16
      entryPrice: 100, initialStop: 95, originalQty: 100, isClosed: true,
      trims: [{ date: '2026-05-18', price: 97, qty: 100 }],
    }]
    const dailyPrices = {
      // Pre-entry (raw UTC) day — a price that WOULD trigger the stop if the
      // buggy one-day-early window included it.
      'TICK:2026-05-15': 90,
      // Real JST entry day onward — never touches the stop.
      'TICK:2026-05-16': 98,
      'TICK:2026-05-17': 98,
      'TICK:2026-05-18': 97,
    }
    const { rows } = computeStopSim(trades, dailyPrices, 1)
    expect(rows[0].hasHistory).toBe(true)
    expect(rows[0].triggered).toEqual([false])
  })
})
