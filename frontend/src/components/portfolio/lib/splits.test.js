import { describe, it, expect } from 'vitest'
import { snapToCleanRatio, detectSplitFactor, applySplitFactor, adjustTradesForSplits } from './splits'

// Real SNXX (2x SNDK) data: 8:1 forward split on 2026-06-03 retroactively divided
// the whole feed by 8. April fills ~$72 now read ~$9 in the feed.
const SNXX_FEED = {
  'SNXX:2026-04-21': 8.81,
  'SNXX:2026-04-22': 10.27,
  'SNXX:2026-04-23': 9.30,
}
const SNXX_TRADE = {
  ticker: 'SNXX', direction: 'long', entryDate: '2026-04-21T15:00:00.000Z',
  entryPrice: 71.78, originalQty: 1773, currentQty: 0, stopPrice: 69.5, initialStop: 69.5,
  trims: [
    { date: '2026-04-22', price: 80.58, qty: 354, type: 'trim_1_5' },
    { date: '2026-04-23', price: 77.23, qty: 1419, type: 'sell_rest' },
  ],
}

describe('snapToCleanRatio', () => {
  it('snaps a measured ~8.15 to 8', () => expect(snapToCleanRatio(8.15)).toBe(8))
  it('snaps a reverse ~0.099 to 1/10', () => expect(snapToCleanRatio(0.099)).toBeCloseTo(0.1, 5))
  it('returns null for a non-clean factor (e.g. 2.5, between 2 and 3)', () => expect(snapToCleanRatio(2.5)).toBeNull())
  it('returns null near 1 (no split)', () => expect(snapToCleanRatio(1.03)).toBeNull())
})

describe('detectSplitFactor', () => {
  it('detects SNXX 8:1 from the feed mismatch', () => {
    const r = detectSplitFactor(SNXX_TRADE, SNXX_FEED)
    expect(r.factor).toBe(8)
    expect(r.ratioLabel).toBe('8:1')
  })

  it('returns factor 1 for a normal trade (fill ≈ same-day close)', () => {
    const t = { ticker: 'AAPL', entryDate: '2026-04-21', entryPrice: 200, trims: [] }
    expect(detectSplitFactor(t, { 'AAPL:2026-04-21': 201.5 }).factor).toBe(1)
  })

  it('returns factor 1 when no feed price exists', () => {
    expect(detectSplitFactor(SNXX_TRADE, {}).factor).toBe(1)
  })

  it('flags (does not adjust) a trade that straddles the ex-date', () => {
    // entry pre-split (~$72 vs feed $9 → ×8) but a trim already on adjusted scale (~$10).
    const straddle = {
      ticker: 'SNXX', entryDate: '2026-04-21', entryPrice: 71.78,
      trims: [{ date: '2026-06-10', price: 10.5, qty: 100 }],
    }
    const feed = { ...SNXX_FEED, 'SNXX:2026-06-10': 10.4 }
    const r = detectSplitFactor(straddle, feed)
    expect(r.factor).toBe(1)
    expect(r.straddle).toBe(true)
  })
})

describe('applySplitFactor — dollar/ratio invariants', () => {
  const adj = applySplitFactor(SNXX_TRADE, 8)

  it('scales qty up and price down by the factor', () => {
    expect(adj.originalQty).toBe(1773 * 8)
    expect(adj.entryPrice).toBeCloseTo(71.78 / 8, 6)
    expect(adj.trims[0].qty).toBe(354 * 8)
    expect(adj.trims[0].price).toBeCloseTo(80.58 / 8, 6)
  })

  it('preserves cost basis (qty × price) exactly', () => {
    expect(adj.originalQty * adj.entryPrice).toBeCloseTo(1773 * 71.78, 4)
  })

  it('preserves realized P&L (qty × (exit − entry)) exactly', () => {
    const pl = (t) => t.trims.reduce((s, tr) => s + tr.qty * (tr.price - t.entryPrice), 0)
    expect(pl(adj)).toBeCloseTo(pl(SNXX_TRADE), 3)
  })

  it('preserves risk unit / R scale (entry − stop scales with price)', () => {
    expect(adj.initialStop).toBeCloseTo(69.5 / 8, 6)
    // R = (exit-entry)/(entry-stop) is unitless and unchanged
    const R = (t) => (t.trims[1].price - t.entryPrice) / (t.entryPrice - t.initialStop)
    expect(R(adj)).toBeCloseTo(R(SNXX_TRADE), 6)
  })

  it('values correctly against the adjusted feed (the whole point)', () => {
    // On 4/21 the full position marks near cost, not at 1/8 of it.
    const mv = adj.originalQty * SNXX_FEED['SNXX:2026-04-21']
    expect(mv).toBeGreaterThan(120_000) // ~125k, not ~15.6k
  })
})

describe('adjustTradesForSplits', () => {
  it('adjusts SNXX and leaves a normal trade untouched, reporting detections', () => {
    const normal = { ticker: 'AAPL', entryDate: '2026-04-21', entryPrice: 200, originalQty: 10, trims: [] }
    const { trades, detected } = adjustTradesForSplits([SNXX_TRADE, normal], { ...SNXX_FEED, 'AAPL:2026-04-21': 201 })
    expect(trades[0]._splitFactor).toBe(8)
    expect(trades[1].originalQty).toBe(10) // untouched
    expect(detected).toEqual([{ ticker: 'SNXX', entryDate: SNXX_TRADE.entryDate, factor: 8, ratioLabel: '8:1' }])
  })
})
