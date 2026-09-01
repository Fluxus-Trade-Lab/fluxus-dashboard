import { describe, it, expect } from 'vitest'
import { stopNotMoved, stopBufferPct, NUDGE_AT_R } from './stopDiscipline'
import { suggest } from './stopSuggestion'

const open = (o = {}) => ({
  isClosed: false, rr: 2, stopPrice: 90, initialStop: 90,
  lastPrice: 120, direction: 'long', ...o,
})

describe('stopNotMoved — the 373 trades that never had their stop touched', () => {
  it('fires on a winner still sitting on its initial stop', () => {
    expect(stopNotMoved(open())).toBe(true)
  })

  it('goes quiet the moment the stop is actually trailed', () => {
    expect(stopNotMoved(open({ stopPrice: 100 }))).toBe(false)
  })

  it('treats a cent of float noise as the same number', () => {
    expect(stopNotMoved(open({ stopPrice: 90.004 }))).toBe(true)
    expect(stopNotMoved(open({ stopPrice: 90.5 }))).toBe(false)
  })

  it('says nothing below the threshold — a position that has not earned it yet', () => {
    expect(stopNotMoved(open({ rr: 0.9 }))).toBe(false)
    expect(stopNotMoved(open({ rr: 1 }))).toBe(true)     // at, not above
  })

  it('the threshold is tunable, as §十四 asked', () => {
    expect(NUDGE_AT_R).toBe(1)
    expect(stopNotMoved(open({ rr: 1.5 }), 2)).toBe(false)
    expect(stopNotMoved(open({ rr: 2.5 }), 2)).toBe(true)
  })

  it('refuses to guess when there is no R anchor at all', () => {
    // no initialStop -> calculations.js leaves rr null. Unknown is not "fine".
    expect(stopNotMoved(open({ rr: null, initialStop: null }))).toBe(false)
    expect(stopNotMoved(open({ rr: null }))).toBe(false)
  })

  it('never fires on a closed trade — there is no stop left to move', () => {
    expect(stopNotMoved(open({ isClosed: true }))).toBe(false)
  })
})

describe('stopBufferPct — distance to the stop you actually have', () => {
  it('measures against the CURRENT stop, not the initial one', () => {
    // trailed to 108 with price at 120: 10% of room left, not 25%
    expect(stopBufferPct(open({ stopPrice: 108 }))).toBeCloseTo(10, 6)
  })

  it('reverses for a short', () => {
    expect(stopBufferPct(open({ direction: 'short', stopPrice: 132 }))).toBeCloseTo(10, 6)
  })

  it('reports a crossed stop rather than clamping it — that is a real state', () => {
    expect(stopBufferPct(open({ stopPrice: 130 }))).toBeLessThan(0)
  })

  it('returns null, not 0, when a price is missing — 0% means "the stop is here"', () => {
    expect(stopBufferPct(open({ lastPrice: null }))).toBe(null)
    expect(stopBufferPct(open({ stopPrice: null }))).toBe(null)
    expect(stopBufferPct(open({ lastPrice: 0 }))).toBe(null)
    expect(stopBufferPct(open({ isClosed: true }))).toBe(null)
  })
})

/* §十四 request 2 asked us to confirm the breakeven suggestion only appears
   after a first trim. It already did — Qullamaggie's order (sell some, THEN
   move to breakeven) was the rule this module was written on. Muninn's 829
   trades put a number on the other order: moving to breakeven while still full
   size cost −69R by day 3. These pin it so it cannot quietly regress. */
describe('breakeven is never suggested before the first trim', () => {
  const ema = { wk_ema20: 50 }, stats = { atr: 4 }
  const t = (state) => ({ state, stopPrice: 90, entryPrice: 100, direction: 'long' })

  it('PRE_TRIM hands back the risk stop the trade came in with', () => {
    const s = suggest(t('PRE_TRIM'), ema, stats)
    expect(s.basis).toBe('csv-initial')
    expect(s.suggestedStop).toBe(90)
    expect(s.basis).not.toBe('breakeven')
  })

  it('breakeven becomes available only once a trim exists', () => {
    // wk-20EMA (50) is far below entry (100), so the floor is breakeven
    for (const st of ['POST_T1', 'POST_T2', 'POST_T3']) {
      const s = suggest(t(st), ema, stats)
      expect(s.basis).toBe('breakeven')
      expect(s.suggestedStop).toBe(100)
    }
  })
})
