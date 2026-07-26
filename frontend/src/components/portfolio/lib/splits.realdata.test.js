import { describe, it, expect } from 'vitest'
import { adjustTradesForSplits, detectSplitFactor } from './splits'
import { buildEquityCurve } from './equityCurve'

// REAL data: SOXS trade #240 + real (split-adjusted) Yahoo feed closes. The feed
// is inflated ~136x by the 2026-05-26 (~1:18) and 2026-07-15 (1:10) reverse splits.
const SOXS_TRADE = {
  ticker: 'SOXS', direction: 'long', entryDate: '2026-05-14T15:00:00.000Z',
  entryPrice: 9.12, originalQty: 17290, currentQty: 0, initialStop: 8.2,
  trims: [
    { date: '2026-05-19', price: 11.0, qty: 5763 },
    { date: '2026-05-19', price: 10.87, qty: 8645 },
    { date: '2026-05-19', price: 10.12, qty: 2882 },
  ],
}
const FEED = {
  'SOXS:2026-05-14': 1240.5, 'SOXS:2026-05-15': 1384.5, 'SOXS:2026-05-18': 1492.5,
  'SOXS:2026-05-19': 1489.5,
}

describe('REAL SOXS composite reverse-split (the live 6000% spike)', () => {
  it('detects the ~1/136 composite factor (old code gave factor 1)', () => {
    const r = detectSplitFactor(SOXS_TRADE, FEED)
    expect(r.factor).toBeGreaterThan(1 / 150)
    expect(r.factor).toBeLessThan(1 / 120)   // ~1/135, adjusted (not 1 = unadjusted)
  })

  it('equity curve does NOT spike after auto split-adjustment', () => {
    const { trades: adj } = adjustTradesForSplits([SOXS_TRADE], FEED)
    const curve = buildEquityCurve(adj, 1_000_000, FEED)
    const pk = Math.max(...curve.map(p => p.returnPct))
    // Without the fix: 17290 x ~$1240 = ~$21M of phantom = +2100%+.
    expect(pk).toBeLessThan(5)   // stays within a few % of flat
  })

  it('PROVES the test bites: raw (unadjusted) trade WOULD spike', () => {
    const curve = buildEquityCurve([SOXS_TRADE], 1_000_000, FEED) // no adjustment
    const pk = Math.max(...curve.map(p => p.returnPct))
    expect(pk).toBeGreaterThan(1000)  // massive phantom without the fix
  })
})
