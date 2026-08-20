import { describe, it, expect } from 'vitest'
import { cardFromTray, manualCards } from './manualCards'

/**
 * The tray and the six seats are one page.
 *
 * A hand-added name has no chart and no verdict — nobody built it a card, and
 * the pipeline has not even heard of it. It still has real readings, because
 * universe.json is rebuilt nightly over every name. These pin the seam: what
 * carries over, what stays absent, and who wins when both halves hold the same
 * ticker.
 */
const tray = { ticker: 'MRNA', from: 'True Market Leaders', group: 'Biotechnology',
               group_state: 'Leading', rs_1m: 99 }
const u = { ticker: 'MRNA', close: 174.38, change_pct: 1.7697, rs_1m: 99, rs_3m: 99,
            atr_from_sma50: 9.6048, vcs: 20.7, sp_signal: 'tp2_hit', sector: 'Healthcare',
            h_score: 81, market_cap: 6.9e10 }

describe('a hand-added name', () => {
  it('gets real readings off universe, under the card’s own field names', () => {
    const c = cardFromTray(tray, u)
    expect(c.readings.close).toBe(174.38)
    expect(c.readings.atr_from_sma50).toBeCloseTo(9.6, 1)
    expect(c.readings.sp_signal).toBe('tp2_hit')
  })

  it('does not carry a field universe never had, even as null', () => {
    const c = cardFromTray(tray, u)
    expect('high_52w_dist' in c.readings).toBe(false)
    expect('market_cap' in c.readings).toBe(false)   // not a card reading
  })

  it('has no verdict, because the engine has not judged it', () => {
    expect(cardFromTray(tray, u).verdict).toBeNull()
    expect(cardFromTray(tray, u).series).toBeNull()
  })

  it('keeps where it was taken from, which cannot be reconstructed later', () => {
    expect(cardFromTray(tray, u).takenFrom).toBe('True Market Leaders')
    expect(cardFromTray(tray, u).state).toBe('Leading')
  })

  it('survives a name universe does not hold, and says so', () => {
    const c = cardFromTray({ ticker: 'ZZZZ' }, null)
    expect(c.inUniverse).toBe(false)
    expect(c.readings).toEqual({})
  })
})

describe('merging the tray with the engine’s manual cards', () => {
  const doc = { cards: [
    { ticker: 'MRNA', source: 'manual', verdict: '水域✓', series: { c: [1] } },
    { ticker: 'NVDA', source: 'manual', verdict: '水域✗' },
    { ticker: 'CBZ', source: 'auto', seat: 'burning' },
  ] }

  it('prefers the engine’s card, which has the chart and the verdict', () => {
    const [first] = manualCards([tray], doc, { MRNA: u })
    expect(first.verdict).toBe('水域✓')
    expect(first.series).not.toBeNull()
    expect(first.takenFrom).toBe('True Market Leaders')   // and keeps the tray's provenance
  })

  it('brings in an engine manual card the tray does not hold', () => {
    const out = manualCards([tray], doc, { MRNA: u })
    expect(out.map((c) => c.ticker)).toEqual(['MRNA', 'NVDA'])
  })

  it('never pulls a seat card into the manual half', () => {
    expect(manualCards([], doc, {}).map((c) => c.ticker)).toEqual(['MRNA', 'NVDA'])
  })

  it('de-duplicates a tray that somehow holds a name twice', () => {
    expect(manualCards([tray, tray], doc, { MRNA: u })).toHaveLength(2)
  })

  it('is empty, not broken, before either half exists', () => {
    expect(manualCards([], null, {})).toEqual([])
  })
})
