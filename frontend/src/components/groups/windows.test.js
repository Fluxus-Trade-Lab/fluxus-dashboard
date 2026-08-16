/**
 * The window buttons read precomputed excess, not raw performance.
 *
 * 1M used to be derived in the browser because the pipeline shipped no
 * excess_1m. It ships one now; this pins which field each button reads, and
 * pins the fallback's precedence for the hours when live data predates it.
 */
import { describe, it, expect } from 'vitest'
import { WINDOWS } from './GroupsPage'

const win = (k) => WINDOWS.find((w) => w.key === k)
// Distinct values throughout, so a button wired to the wrong field fails
// instead of quietly agreeing.
const SPY = { perf_1w: 0.01, perf_1m: 0.04, perf_3m: 0.05 }
const ROW = { rs_0_1w: 0.02, excess_1m: 0.06, excess_3m: 0.15, perf_1m: 0.10 }

describe('window → field', () => {
  it('offers exactly the three windows the page draws', () => {
    expect(WINDOWS.map((w) => w.key)).toEqual(['1W', '1M', '3M'])
  })

  it('1W reads the shipped one-week excess', () => {
    expect(win('1W').value(ROW, SPY)).toBe(0.02)
  })

  it('3M reads the shipped quarter excess', () => {
    expect(win('3M').value(ROW, SPY)).toBe(0.15)
  })

  it('1M prefers the pipeline field over deriving it', () => {
    // 0.06 is the shipped field; 0.10 − 0.04 = 0.06 too if derived, so the
    // fixture makes them differ to prove which one is actually read.
    expect(win('1M').value({ ...ROW, excess_1m: 0.99 }, SPY)).toBe(0.99)
  })

  it('1M falls back to the derivation while data predates the field', () => {
    const { excess_1m, ...old } = ROW
    expect(win('1M').value(old, SPY)).toBeCloseTo(0.10 - 0.04, 10)
  })

  it('1M yields null rather than a wrong zero line with neither source', () => {
    expect(win('1M').value({ rs_0_1w: 0.02 }, null)).toBeNull()
  })
})
