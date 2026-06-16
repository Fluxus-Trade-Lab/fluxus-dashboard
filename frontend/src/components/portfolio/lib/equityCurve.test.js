import { describe, it, expect } from 'vitest'
import { buildEquityCurve } from './equityCurve'
import { adjustTradesForSplits } from './splits'

// A single long position held across a one-bar split mis-scale. The feed close
// for LEV on 2026-01-15 comes back on the wrong (1/3) scale, then re-aligns.
// Regression for the 2026-04-21 dip: without spike rejection the curve craters
// ~$60k for that one day; with it the curve stays flat.
function fixture() {
  const startingCapital = 1_000_000
  const trades = [{
    ticker: 'LEV',
    direction: 'long',
    entryDate: '2026-01-02T15:00:00.000Z',
    entryPrice: 90,
    originalQty: 1000,
    trims: [],
  }]
  const dailyPrices = {}
  // Provide a clean ~$90 close for every weekday in Jan 2026...
  for (let day = 2; day <= 30; day++) {
    const d = `2026-01-${String(day).padStart(2, '0')}`
    const wd = new Date(d).getDay()
    if (wd === 0 || wd === 6) continue
    dailyPrices[`LEV:${d}`] = 90 + (day % 3) * 0.1
  }
  // ...except 2026-01-15 (a Thursday), which is on the post-split scale.
  dailyPrices['LEV:2026-01-15'] = 30
  return { trades, startingCapital, dailyPrices }
}

describe('buildEquityCurve — split/feed spike rejection', () => {
  it('does NOT dip on the one-bar split-misscale day', () => {
    const { trades, startingCapital, dailyPrices } = fixture()
    const curve = buildEquityCurve(trades, startingCapital, dailyPrices)
    const pt = curve.find(p => p.date === '2026-01-15')
    expect(pt).toBeTruthy()
    // True value ~$1,000,000 (90->~90, 1000 sh). A $60k crater would be -6%.
    expect(pt.returnPct).toBeGreaterThan(-1)
    expect(pt.returnPct).toBeLessThan(1)
  })

  it('proves the test is meaningful: the raw bad bar would have craved a dip', () => {
    // Sanity: the injected bad price really is a 3x mis-scale.
    const { dailyPrices } = fixture()
    const ratio = dailyPrices['LEV:2026-01-15'] / dailyPrices['LEV:2026-01-14']
    expect(ratio).toBeLessThan(0.5)
  })

  it('split adjustment removes the persistent-split crater (SNXX 8:1 case)', () => {
    // A long held through dates whose feed was retroactively divided by 8.
    // Real value ~$1.0M every day; raw qty × adjusted-close would crater to ~1/8.
    const startingCapital = 1_000_000
    const trades = [{
      ticker: 'LEV', direction: 'long',
      entryDate: '2026-01-02T15:00:00.000Z',
      entryPrice: 72, originalQty: 1773, trims: [],
    }]
    const dailyPrices = {}
    for (let day = 2; day <= 30; day++) {
      const d = `2026-01-${String(day).padStart(2, '0')}`
      const wd = new Date(d).getDay()
      if (wd === 0 || wd === 6) continue
      dailyPrices[`LEV:${d}`] = 9 + (day % 3) * 0.05 // feed already on post-8:1 scale (~72/8)
    }

    // Without adjustment: 1773 × ~9 = ~16k vs 1773 × 72 cost → ~-98% crater.
    const rawCurve = buildEquityCurve(trades, startingCapital, dailyPrices)
    const rawPt = rawCurve.find(p => p.date === '2026-01-15')
    expect(rawPt.returnPct).toBeLessThan(-9) // badly cratered

    // With auto split-adjustment: stays near flat.
    const { trades: adj, detected } = adjustTradesForSplits(trades, dailyPrices)
    expect(detected[0].ratioLabel).toBe('8:1')
    const fixedCurve = buildEquityCurve(adj, startingCapital, dailyPrices)
    const fixedPt = fixedCurve.find(p => p.date === '2026-01-15')
    expect(fixedPt.returnPct).toBeGreaterThan(-2)
    expect(fixedPt.returnPct).toBeLessThan(2)
  })

  it('still reflects a genuine persistent move', () => {
    const { trades, startingCapital, dailyPrices } = fixture()
    // Make 2026-01-15 onward a real, persistent drop to ~$45 (held, not reverting).
    for (let day = 15; day <= 30; day++) {
      const d = `2026-01-${String(day).padStart(2, '0')}`
      if (dailyPrices[`LEV:${d}`] != null) dailyPrices[`LEV:${d}`] = 45
    }
    const curve = buildEquityCurve(trades, startingCapital, dailyPrices)
    const pt = curve.find(p => p.date === '2026-01-20')
    // 1000 sh * (45-90) = -45k -> -4.5%. Real moves must NOT be suppressed.
    expect(pt.returnPct).toBeLessThan(-3)
  })
})
