import { describe, it, expect } from 'vitest'
import { verdictParts, indexCards, breadthTiles, crossAsset, recapNotes, boldParts } from './marketStateMinMath'

const ml = { verdict: 'dim', spy: { light: 'green', checks_passed: 3 }, qqq: { light: 'green', checks_passed: 3 },
  brightness: { leaders: Array.from({ length: 10 }, () => ({ status: 'holding' })), breadth: { env: 'MIXED' } } }

describe('verdictParts', () => {
  it('shows the readings the verdict is made of, not just the word', () => {
    const v = verdictParts(ml)
    expect(v.verdict).toBe('dim')
    expect(v.parts.map((p) => p.key)).toEqual(['spy', 'qqq', 'leaders', 'breadth'])
    expect(v.parts[2].value).toBe('10/10')
    expect(v.parts[3].value).toBe('MIXED')
  })
  it('is null without a market-light file', () => { expect(verdictParts(null)).toBeNull() })
})

describe('breadthTiles', () => {
  // 2026-10-02 real values
  const rows = [
    { advances: 2000, declines: 3000, pct_above_20sma: 25.3, pct_above_200sma: 36.4, mcclellan_osc_ndx: 36.7 },
    { advances: 3080, declines: 2273, high_low_index: 17.0, record_high_pct: 20.59, new_highs_common: 7, new_lows_common: 27,
      pct_above_20sma: 28.91, pct_above_200sma: 37.5, mcclellan_osc_ndx: 50.21, up_4pct_stockbee: 215, down_4pct_stockbee: 129, t2108: 26.01 },
  ]
  const t = Object.fromEntries(breadthTiles(rows).map((x) => [x.key, x]))
  it('leads new highs with the standard High-Low Index, counts underneath', () => {
    expect(t.hli.value).toBe(17)
    expect(t.hli.sub).toBe('7 highs · 27 lows · today 21%')
    expect(t.hli.sign).toBeLessThan(0)
  })
  it('net advances and deltas vs the prior session', () => {
    expect(t.adv.value).toBe(807)
    expect(t.p20.delta).toBeCloseTo(3.61, 2)
    expect(t.up4.value).toBe('215 / 129')
  })
  it('empty rows give no tiles', () => { expect(breadthTiles([])).toEqual([]) })
})

describe('indexCards / crossAsset', () => {
  const etfs = [{ ticker: 'SPY', close: 769.64, change_pct: 0.0074, perf_1w: 0.0053, high_52w_dist: -0.008, dist_sma50_atr: 1.11 },
    { ticker: 'IWM', close: 281.5, change_pct: 0.009, perf_1w: 0.005, high_52w_dist: -0.075, dist_sma50_atr: -2.81 },
    { ticker: 'TLT', close: 86, change_pct: -0.003, perf_1w: -0.011 }]
  it('lists the six index ETFs in order, skipping any the file lacks', () => {
    const all = ['SPY', 'QQQ', 'QQQE', 'DIA', 'IWM', 'RSP'].map((t) => ({ ticker: t, close: 1, change_pct: 0 }))
    expect(indexCards(all.reverse(), ml).map((c) => c.ticker)).toEqual(['SPY', 'QQQ', 'QQQE', 'DIA', 'IWM', 'RSP'])
    expect(indexCards(etfs, ml).map((c) => c.ticker)).toEqual(['SPY', 'IWM'])
  })
  it('carries the light where the pipeline has one, the 50-day side otherwise', () => {
    const c = Object.fromEntries(indexCards(etfs, ml).map((x) => [x.ticker, x]))
    expect(c.SPY.light).toBe('green')
    expect(c.IWM.light).toBeNull()
    expect(c.IWM.aboveSma50).toBe(false)
  })
  it('cross-asset reads the week against SPY', () => {
    const x = crossAsset(etfs, { '^VIX': { close: 15.31 } })
    expect(x[0]).toMatchObject({ ticker: 'VIX', last: 15.31 })
    expect(x.find((r) => r.ticker === 'TLT').vsSpy).toBeCloseTo(-0.0163, 4)
  })
})

describe('recap cross-asset notes', () => {
  const doc = { asof: '2026-10-02', notes: { en: [{ ticker: 'UUP', text: '<b>The dollar</b> held.' }], zh: [{ ticker: 'UUP', text: '<b>美元</b>守住。' }] } }
  it('shows the recap only for the same session as the data', () => {
    expect(recapNotes(doc, '2026-10-02')).toHaveLength(1)
    expect(recapNotes(doc, '2026-10-05')).toEqual([])
    expect(recapNotes(null, '2026-10-02')).toEqual([])
  })
  it('picks the page language, falls back to English', () => {
    expect(recapNotes(doc, '2026-10-02', 'zh')[0].text).toContain('美元')
    expect(recapNotes({ asof: 'x', notes: { en: doc.notes.en } }, 'x', 'zh')[0].ticker).toBe('UUP')
  })
  it('turns <b> into parts and never passes other markup through as HTML', () => {
    expect(boldParts('<b>The dollar</b> held.')).toEqual([{ b: true, t: 'The dollar' }, { b: false, t: ' held.' }])
    expect(boldParts('<i>x</i>')).toEqual([{ b: false, t: '<i>x</i>' }])
  })
})
