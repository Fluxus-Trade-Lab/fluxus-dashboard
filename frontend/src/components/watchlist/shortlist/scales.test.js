import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { pctFromReading, pctFromMark, fmtPct, fmtAtr, fmtPctl } from './scales'

/**
 * The regression that catches a silent normalisation on the data side.
 *
 * Every chg in the real file is recomputed from `series.c`, so if
 * `readings.change_pct` ever stops being a fraction — or `marks[].chg` stops
 * being a percent — this fails instead of a card quietly printing 0.14% for a
 * 14% day. The ask to unify them is logged in DATA_CONTRACTS §七; whichever way
 * it lands, it lands here first.
 */
// Vite rewrites import.meta.url to a /@fs/... URL, which readFileSync rejects;
// the repo root is what this needs and process.cwd() is the frontend dir.
const FILE = resolve(process.cwd(), '..', 'data/output/shortlist.json')
let doc = null
try { doc = JSON.parse(readFileSync(FILE, 'utf8')) } catch { /* not built yet */ }

describe.skipIf(!doc)('the two scales, against the real file', () => {
  const move = (series, date) => {
    const i = series.d.indexOf(date)
    return i > 0 ? (series.c[i] / series.c[i - 1] - 1) * 100 : null
  }

  it('readings.change_pct is a fraction', () => {
    for (const card of doc.cards) {
      const truth = move(card.series, card.series.d[card.series.d.length - 1])
      expect(pctFromReading(card.readings.change_pct)).toBeCloseTo(truth, 1)
    }
  })

  it('marks[].chg is already a percent', () => {
    for (const card of doc.cards) {
      for (const m of card.marks) {
        const truth = move(card.series, m.d)
        if (truth == null) continue
        expect(pctFromMark(m.chg)).toBeCloseTo(truth, 0)
      }
    }
  })

  it('panels[].chg_pct is already a percent', () => {
    for (const card of doc.cards) {
      for (const p of card.panels) {
        const truth = move(card.series, p.date)
        if (truth == null) continue
        expect(pctFromMark(p.chg_pct)).toBeCloseTo(truth, 0)
      }
    }
  })
})

describe('formatting keeps absent apart from zero', () => {
  it('returns null rather than a zero for every absent reading', () => {
    expect(fmtPct(null)).toBeNull()
    expect(fmtAtr(null)).toBeNull()
    expect(fmtPctl(null)).toBeNull()
  })

  it('prints a real zero as a zero', () => {
    expect(fmtPct(0)).toBe('+0.00%')
    expect(fmtAtr(0)).toBe('+0.0')
    expect(fmtPctl(0)).toBe('0')
  })

  it('keeps the sign on a reading below the 50-day', () => {
    expect(fmtAtr(-0.3305)).toBe('-0.3')
  })

  it('drops the division noise off a percentile', () => {
    expect(fmtPctl(76.19047619047619)).toBe('76.2')
    expect(fmtPctl(96)).toBe('96')
  })
})
