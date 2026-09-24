import { describe, it, expect } from 'vitest'
import { computeYtdStats } from './calculations'

/* Andy 2026-09-24: 「YTD那栏改成真的年初至今」. The row used to print
   inception-to-date under a YTD label and count every closed trade ever. */

const curve = (rows) => rows.map(([date, returnPct]) => ({ date, returnPct }))
const trade = (lastTrimDate, retPct, holdingDays = 5) => ({
  isClosed: true, totalReturnPct: retPct, holdingDays,
  trims: [{ date: lastTrimDate, qty: 1, price: 1 }],
})

describe('computeYtdStats — the portfolio return', () => {
  it('chains from the prior year\'s last close, not from inception', () => {
    // +50% by the end of last year, +80% now → YTD = 1.8/1.5 − 1 = 20%
    const s = computeYtdStats([], 80, curve([
      ['2025-12-30', 49], ['2025-12-31', 50], ['2026-01-02', 55], ['2026-09-23', 80],
    ]))
    expect(s.basis).toBe('ytd')
    expect(s.year).toBe('2026')
    expect(s.portfolioRetPct).toBeCloseTo(20, 6)
  })

  it('falls back to inception — and says so — when the curve starts inside the year', () => {
    const s = computeYtdStats([], 80, curve([['2026-02-02', 5], ['2026-09-23', 80]]))
    expect(s.basis).toBe('inception')
    expect(s.portfolioRetPct).toBe(80)
  })

  it('takes the year from the curve, not from the wall clock', () => {
    const s = computeYtdStats([], 10, curve([['2024-12-31', 0], ['2025-06-30', 10]]))
    expect(s.year).toBe('2025')
    expect(s.basis).toBe('ytd')
  })
})

describe('computeYtdStats — the trade statistics', () => {
  const trades = [
    trade('2025-11-20', 40), trade('2025-12-31', -10),   // last year: excluded
    trade('2026-01-05', 20), trade('2026-03-10', -5), trade('2026-09-22', 8, 9),
  ]
  const pd = curve([['2025-12-31', 50], ['2026-09-23', 80]])

  it('counts only trades closed in the year, dated by their last trim', () => {
    const s = computeYtdStats(trades, 80, pd)
    expect(s.totalTrades).toBe(3)
    expect(s.returnPct).toBeCloseTo((20 - 5 + 8) / 3, 6)
    expect(s.winPct).toBeCloseTo((2 / 3) * 100, 6)
    expect(s.avgGain).toBeCloseTo(14, 6)
    expect(s.avgLoss).toBeCloseTo(-5, 6)
    expect(s.largestGain).toBe(20)
    expect(s.largestLoss).toBe(-5)
  })

  it('still reports the portfolio return in a year with no exits', () => {
    const s = computeYtdStats([trade('2025-06-01', 40)], 80, pd)
    expect(s.totalTrades).toBe(0)
    expect(s.portfolioRetPct).toBeCloseTo(20, 6)
    expect(s.avgGain).toBe(0)
  })

  it('is null only when there is neither a curve nor a closed trade', () => {
    expect(computeYtdStats([], 0, [])).toBeNull()
    expect(computeYtdStats([{ isClosed: false }], 0, [])).toBeNull()
  })
})
