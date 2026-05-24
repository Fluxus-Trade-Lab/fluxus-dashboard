import { describe, it, expect } from 'vitest'
import { suggest } from './stopSuggestion'

describe('stopSuggestion.suggest', () => {
  it('returns null when leg state is CLOSED', () => {
    expect(suggest({ state: 'CLOSED' }, {}, {})).toBeNull()
  })

  it('returns CSV initial stop for PRE_TRIM', () => {
    const trade = { state: 'PRE_TRIM', stopPrice: 95, entryPrice: 100, direction: 'long' }
    const out = suggest(trade, {}, { atr: 2 })
    expect(out.suggestedStop).toBe(95)
    expect(out.basis).toBe('csv-initial')
  })

  it('returns max(entry, wk_ema20 - 0.25*ATR) for POST_T1 long when EMA available', () => {
    const trade = { state: 'POST_T1', stopPrice: 95, entryPrice: 100, direction: 'long' }
    const ema = { wk_ema20: 110 }
    const out = suggest(trade, ema, { atr: 4 })
    // 110 - 0.25*4 = 109; max(100, 109) = 109
    expect(out.suggestedStop).toBe(109)
    expect(out.basis).toBe('wk20ema')
  })

  it('uses breakeven when wk_ema20 - buffer is below entry (long)', () => {
    const trade = { state: 'POST_T1', stopPrice: 95, entryPrice: 100, direction: 'long' }
    const ema = { wk_ema20: 95 }
    const out = suggest(trade, ema, { atr: 4 })
    expect(out.suggestedStop).toBe(100)
    expect(out.basis).toBe('breakeven')
  })

  it('inverts for shorts: min(entry, wk_ema20 + 0.25*ATR)', () => {
    const trade = { state: 'POST_T1', stopPrice: 105, entryPrice: 100, direction: 'short' }
    const ema = { wk_ema20: 90 }
    const out = suggest(trade, ema, { atr: 4 })
    expect(out.suggestedStop).toBe(91)
    expect(out.basis).toBe('wk20ema')
  })

  it('returns null suggestion when no EMA data available for POST_T1+', () => {
    const trade = { state: 'POST_T1', stopPrice: 95, entryPrice: 100, direction: 'long' }
    const out = suggest(trade, {}, { atr: 4 })
    expect(out.suggestedStop).toBeNull()
    expect(out.basis).toBe('no-data')
  })
})
