/* global process */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { stepCounts, setupCards, panelScans, PANEL_SCANS, rowsPassingGate, isWater, byRs } from './stepMath'

// The step bar's arithmetic on the real files (Andy 2026-10-04, plan A).
const read = (...p) => JSON.parse(readFileSync(resolve(process.cwd(), ...p), 'utf8'))
const FOCUS = read('public/data/focus.json')
const WL = read('..', 'data/output/watchlist.json')
const UNI = read('..', 'data/output/universe.json')

describe('stepCounts', () => {
  for (const k of Object.keys(FOCUS.setups)) {
    it(`${k}: setup ≥ qualified ≥ focus ≥ water, each the file's own filter`, () => {
      const c = stepCounts(FOCUS, k)
      const rows = FOCUS.setups[k].rows
      expect(c.gate).toBe(FOCUS.counts.gate)
      expect(c.setup).toBe(rows.length)
      expect(c.qual).toBe(setupCards(FOCUS, k, 'qual').length)
      expect(c.focus).toBe(setupCards(FOCUS, k, 'focus').length)
      expect(c.setup).toBeGreaterThanOrEqual(c.qual)
      expect(c.qual).toBeGreaterThanOrEqual(c.focus)
      expect(c.focus).toBeGreaterThanOrEqual(c.water)
      // focus is gate ∧ 4/4, so every focus row is also a 4/4 row
      for (const r of setupCards(FOCUS, k, 'focus')) expect(r.qn).toBe(4)
    })
  }

  it('a missing file reads as no numbers, not zeros of a real day', () => {
    expect(stepCounts(null, 'pullback').gate).toBeNull()
  })
})

describe('panelScans', () => {
  it('lists only the agreed panels, in order, and never the exit panels', () => {
    const keys = panelScans(WL).map((p) => p.key)
    expect(keys).toEqual(PANEL_SCANS.filter((k) => keys.includes(k)))
    for (const k of ['stop_hit', 'll_break', 'extended', 'ep_stockbee', 'ep_qullamaggie']) expect(keys).not.toContain(k)
  })

  it('includes Liquid Leader Pullback with its tickers', () => {
    const p = panelScans(WL).find((x) => x.key === 'liquid_leader_pullback')
    const raw = WL.zones.flatMap((z) => z.panels).find((x) => x.key === 'liquid_leader_pullback')
    expect(p.tickers.length).toBe(raw.tickers.length)
    expect(p.tickers.length).toBeGreaterThan(0)
  })

  it('carries each panel\'s tickers as the file lists them', () => {
    const tml = WL.zones.flatMap((z) => z.panels).find((p) => p.key === 'true_market_leaders')
    expect(panelScans(WL).find((p) => p.key === 'true_market_leaders').tickers).toEqual(tml.tickers.map((r) => r.ticker))
  })
})

describe('helpers', () => {
  // only comparable while focus.json was built off this very universe.json;
  // the two files are written by different runs and can be a session apart
  it.skipIf(FOCUS.universe_timestamp !== UNI.timestamp)('the gate rule reproduces counts.gate on the same universe file', () => {
    expect(rowsPassingGate(UNI.rows, FOCUS.rule.gate).length).toBe(FOCUS.counts.gate)
  })
  it('water is Leading or Improving only', () => {
    expect(['Leading', 'Improving', 'Weakening', 'Lagging', null].map(isWater)).toEqual([true, true, false, false, false])
  })
  it('RS descending, ties by ticker, missing RS last', () => {
    const r = [{ t: 'B', rs: 90 }, { t: 'A', rs: 90 }, { t: 'C', rs: null }, { t: 'D', rs: 99 }].sort(byRs)
    expect(r.map((x) => x.t)).toEqual(['D', 'A', 'B', 'C'])
  })
})
