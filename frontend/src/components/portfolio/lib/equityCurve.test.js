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

    // RAW trades now stay flat too: the built-in fill-anchored correction detects
    // entry $72 vs feed ~$9 (ratio 8) and marks the feed × 8 = as-traded. No crater.
    const rawCurve = buildEquityCurve(trades, startingCapital, dailyPrices)
    const rawPt = rawCurve.find(p => p.date === '2026-01-15')
    expect(rawPt.returnPct).toBeGreaterThan(-2)
    expect(rawPt.returnPct).toBeLessThan(2)

    // Pre-adjusted trades also stay flat (correction is a no-op: fills ≈ closes).
    const { trades: adj, detected } = adjustTradesForSplits(trades, dailyPrices)
    expect(detected[0].ratioLabel).toBe('8:1')
    const fixedCurve = buildEquityCurve(adj, startingCapital, dailyPrices)
    const fixedPt = fixedCurve.find(p => p.date === '2026-01-15')
    expect(fixedPt.returnPct).toBeGreaterThan(-2)
    expect(fixedPt.returnPct).toBeLessThan(2)
  })

  it('kills the residual straddle-flag phantom (RAW unadjusted reverse split)', () => {
    // The live 05-17 spike: a SOXS trade the per-trade detector FALSE-flagged as a
    // straddle → left unadjusted → marked at the ~136× inflated feed. Fill-anchored
    // correction fixes it with no split-table or detection needed.
    const startingCapital = 1_000_000
    const trades = [{
      ticker: 'SOXS', direction: 'long', entryDate: '2026-05-14T15:00:00.000Z',
      entryPrice: 9.12, originalQty: 17290, currentQty: 0, initialStop: 8.2,
      trims: [
        { date: '2026-05-19', price: 11.0, qty: 5763 },
        { date: '2026-05-19', price: 10.87, qty: 8645 },
        { date: '2026-05-19', price: 10.12, qty: 2882 },
      ],
    }]
    const dailyPrices = {
      'SOXS:2026-05-14': 1240.5, 'SOXS:2026-05-15': 1384.5,
      'SOXS:2026-05-18': 1492.5, 'SOXS:2026-05-19': 1489.5,
    }
    const curve = buildEquityCurve(trades, startingCapital, dailyPrices)
    const peak = Math.max(...curve.map(p => p.returnPct))
    // Unfixed: 17290 × $1492 = ~$25M = +2500%+. Fixed: within a few % of flat.
    expect(peak).toBeLessThan(5)
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
  it('stays flat by default — fill-anchored, no split table needed', () => {
    // entry $5.91 vs feed $531.9 → ratio 1/90 → feed marked back to ~$5.91.
    const curve = buildEquityCurve(trades, startingCapital, dailyPrices)
    const pt = curve.find(p => p.date === '2026-06-04')
    expect(pt.returnPct).toBeGreaterThan(-2)
    expect(pt.returnPct).toBeLessThan(2)
  })

  it('prefers the frozen snapshot over the feed', () => {
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
