import { describe, it, expect } from 'vitest'
import { chips } from './emaProximity'

describe('emaProximity.chips', () => {
  it('returns empty array when no EMA data', () => {
    expect(chips({ price: 100, direction: 'long' }, {})).toEqual([])
  })

  it('adds 10EMA chip when within 1.5% of price', () => {
    const out = chips({ price: 100, direction: 'long' }, { ema10: 99, ema20: 80 })
    expect(out).toContainEqual({ label: '10EMA', tone: 'amber' })
  })

  it('adds 20EMA chip when within 2% of price', () => {
    const out = chips({ price: 100, direction: 'long' }, { ema20: 98.5 })
    expect(out).toContainEqual({ label: '20EMA', tone: 'red' })
  })

  it('adds T2 chip when weekly close < wk_ema10 for long', () => {
    const out = chips({ price: 100, direction: 'long', wkClose: 99 }, { wk_ema10: 100 })
    expect(out).toContainEqual({ label: 'T2', tone: 'orange' })
  })

  it('adds STOP chip when weekly close < wk_ema20 for long', () => {
    const out = chips({ price: 100, direction: 'long', wkClose: 95 }, { wk_ema20: 100 })
    expect(out).toContainEqual({ label: 'STOP', tone: 'red' })
  })

  it('inverts for shorts: T2 fires when wk_close > wk_ema10', () => {
    const out = chips({ price: 100, direction: 'short', wkClose: 101 }, { wk_ema10: 100 })
    expect(out).toContainEqual({ label: 'T2', tone: 'orange' })
  })
})
