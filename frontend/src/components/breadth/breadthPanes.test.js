import { describe, it, expect } from 'vitest'
import { zscore, softClip, buildPanes, INDICATORS, POOLS } from './breadthPanesMath'

const rows = (n, f) => Array.from({ length: n }, (_, i) => ({ date: `d${i}`, spx_close: 100 + i, ...f(i) }))

describe('zscore', () => {
  it('needs 60 sessions before it speaks, then reads against the trailing window', () => {
    const z = zscore(Array.from({ length: 70 }, (_, i) => (i % 2 ? 1 : -1)), 252, 60)
    expect(z.slice(0, 59).every((v) => v == null)).toBe(true)
    expect(Math.abs(z[69])).toBeCloseTo(1, 1)
  })
  it('skips holes without breaking the window', () => {
    const z = zscore([1, null, 1, 1, 5], 252, 3)
    expect(z[1]).toBeNull()
    expect(z[4]).toBeGreaterThan(1)
  })
})

describe('softClip', () => {
  it('is the identity inside ±3 and compresses outside', () => {
    expect(softClip(2.5)).toBe(2.5)
    expect(softClip(6)).toBeLessThan(4)
    expect(softClip(6)).toBeGreaterThan(3)
    expect(softClip(-6)).toBeGreaterThan(-4)
  })
})

describe('buildPanes', () => {
  const r = rows(300, (i) => ({ new_highs: 10, new_lows: i % 50 === 0 ? 60 : 5 + (i % 10) * 2, mcclellan_osc: Math.sin(i / 7) * 50, pct_above_20sma: 50, pct_above_20sma_sp500: i > 290 ? 60 : null }))
  it('absolute ruler: oversold = lowest 10% of the window, episodes merged and dated', () => {
    const p = buildPanes(r, { indicator: 'nhnl', window: 250, pct: 0.1 })
    expect(p.dates.length).toBe(250)
    expect(p.threshold).toBeLessThanOrEqual(-13)
    expect(p.episodes.length).toBeGreaterThanOrEqual(5)
    expect(p.episodes[0]).toHaveProperty('after')
    expect(p.rule).toMatch(/our cut/)
  })
  it('σ ruler: fixed −2σ line, axis values soft-clipped, rule names the window as ours', () => {
    const p = buildPanes(r, { indicator: 'mco', scale: 'z', window: 250, pct: 0.1 })
    expect(p.threshold).toBe(-2)
    expect(Math.max(...p.value.filter(Number.isFinite))).toBeLessThanOrEqual(4)
    expect(p.rule).toMatch(/our window/)
  })
  it('pool switch reads the S&P 500 column where it exists and says so where it does not', () => {
    const sp = buildPanes(r, { indicator: 'p20', pool: 'sp500', window: 20 })
    expect(sp.raw.filter(Number.isFinite).length).toBe(9)
    expect(sp.poolNote).toMatch(/Only 9 sessions/)
    expect(sp.threshold).toBeNull()
    const none = buildPanes(r, { indicator: 'mco', pool: 'sp500', window: 20 })
    expect(none.poolNote).toMatch(/no S&P 500 series/)
    expect(none.raw.filter(Number.isFinite).length).toBe(20)
  })
  it('empty rows do not throw', () => {
    const p = buildPanes([], {})
    expect(p.dates).toEqual([])
    expect(p.threshold).toBeNull()
  })
  it('every indicator has an all-market reader and every pool a label', () => {
    for (const k of Object.keys(INDICATORS)) expect(typeof INDICATORS[k].pools.all).toBe('function')
    expect(POOLS.map((p) => p.key)).toEqual(['all', 'sp500', 'ndx'])
  })
})
