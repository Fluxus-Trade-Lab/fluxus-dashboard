import { describe, it, expect } from 'vitest'
import { buildEquityCurve, computeDrawdown, computeRiskRatios } from './equityCurve'
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

describe('buildEquityCurve — split-table un-adjust kills the reverse-split phantom spike', () => {
  // SOXS long held before TWO reverse splits: the feed is inflated ~90×, so
  // qty(as-traded) × feed would fabricate ~$17M of equity (the ~6000% May hump).
  const startingCapital = 1_000_000
  const trades = [{
    ticker: 'SOXS', direction: 'long',
    entryDate: '2026-06-04T15:00:00.000Z',
    entryPrice: 5.91, originalQty: 32031, trims: [],
  }]
  const dailyPrices = {}
  for (let day = 4; day <= 9; day++) {
    dailyPrices[`SOXS:2026-06-0${day}`] = 5.91 * 90 // feed inflated 90× by later reverse splits
  }
  // Both reverse splits are AFTER the held window → cumFactor 1/90 throughout.
  const splitTable = { SOXS: [{ exDate: '2026-07-15', factor: 1 / 10 }, { exDate: '2026-07-16', factor: 1 / 9 }] }

  it('spikes without correction (reproduces the bug)', () => {
    const curve = buildEquityCurve(trades, startingCapital, dailyPrices) // default table has SOXS unconfirmed → no fix
    const pt = curve.find(p => p.date === '2026-06-04')
    expect(pt.returnPct).toBeGreaterThan(500) // phantom > +500%
  })

  it('stays flat (~0%) once the split table is applied', () => {
    const curve = buildEquityCurve(trades, startingCapital, dailyPrices, null, { splitTable })
    const pt = curve.find(p => p.date === '2026-06-04')
    expect(pt.returnPct).toBeGreaterThan(-2)
    expect(pt.returnPct).toBeLessThan(2)
  })

  it('prefers the frozen snapshot over the feed', () => {
    // Frozen truth says SOXS was $5.91 on 06-05; feed (even uncorrected) is ignored.
    const frozenPrices = { 'SOXS:2026-06-04': 5.91 }
    const curve = buildEquityCurve(trades, startingCapital, dailyPrices, null, { frozenPrices })
    const pt = curve.find(p => p.date === '2026-06-04')
    expect(pt.returnPct).toBeGreaterThan(-2)
    expect(pt.returnPct).toBeLessThan(2)
  })
})

describe('computeDrawdown / computeRiskRatios', () => {
  const curve = [
    { date: '2026-01-01', value: 1_000_000 },
    { date: '2026-01-02', value: 1_100_000 }, // peak
    { date: '2026-01-03', value: 900_000 },   // trough: -200k from peak = -18.18%
    { date: '2026-01-04', value: 1_050_000 },
  ]
  it('finds peak-to-trough max drawdown', () => {
    const dd = computeDrawdown(curve)
    expect(dd.maxDrawdown).toBeCloseTo(-200_000, 0)
    expect(dd.maxDrawdownPct).toBeCloseTo(-18.18, 1)
    expect(dd.peakDate).toBe('2026-01-02')
    expect(dd.troughDate).toBe('2026-01-03')
  })
  it('computes finite risk ratios and negative max DD', () => {
    const r = computeRiskRatios(curve)
    expect(Number.isFinite(r.sharpe)).toBe(true)
    expect(Number.isFinite(r.sortino)).toBe(true)
    expect(r.maxDrawdownPct).toBeLessThan(0)
  })
})
