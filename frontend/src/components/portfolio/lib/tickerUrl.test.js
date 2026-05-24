import { describe, it, expect } from 'vitest'
import { tickerHref, parseTickerHash } from './tickerUrl'

describe('tickerUrl.tickerHref', () => {
  it('uppercases the symbol', () => {
    expect(tickerHref('aapl')).toBe('#/ticker/AAPL')
  })
  it('returns "#/" when symbol is empty', () => {
    expect(tickerHref('')).toBe('#/')
    expect(tickerHref(null)).toBe('#/')
  })
})

describe('tickerUrl.parseTickerHash', () => {
  it('extracts the symbol from a valid hash', () => {
    expect(parseTickerHash('#/ticker/AAPL')).toBe('AAPL')
    expect(parseTickerHash('#/ticker/aapl')).toBe('AAPL')
  })
  it('returns null for non-matching hashes', () => {
    expect(parseTickerHash('#/portfolio')).toBeNull()
    expect(parseTickerHash('')).toBeNull()
  })
  it('handles tickers with dots and hyphens (e.g., BRK.B)', () => {
    expect(parseTickerHash('#/ticker/BRK.B')).toBe('BRK.B')
    expect(parseTickerHash('#/ticker/BRK-B')).toBe('BRK-B')
  })
})
