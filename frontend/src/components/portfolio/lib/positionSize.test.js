import { describe, it, expect } from 'vitest'
import { positionSizeStats } from './positionSize'

/**
 * The card and the chart read these numbers from here, so a change that moves
 * one has to move both. The cases below are the ones that would let them drift
 * apart quietly: the equity denominator, and what happens to trades with no R.
 */

const trade = (o) => ({
  isClosed: true, ticker: 'X', direction: 'long',
  entryDate: '2026-01-05', entryPrice: 100, originalQty: 100,
  initialStop: 90, realizedPL: 1000, trims: [{ date: '2026-01-20', price: 110, qty: 100 }],
  ...o,
})

describe('positionSizeStats', () => {
  it('divides by equity at entry, not by starting capital', () => {
    // Same $10,000 notional, taken a year apart on a book that doubled.
    const trades = [
      trade({ ticker: 'A', entryDate: '2026-01-05', trims: [{ date: '2026-01-20', price: 110, qty: 100 }] }),
      trade({ ticker: 'B', entryDate: '2026-06-05', trims: [{ date: '2026-06-20', price: 110, qty: 100 }] }),
      trade({ ticker: 'C', entryDate: '2026-06-06', trims: [{ date: '2026-06-21', price: 110, qty: 100 }] }),
    ]
    const curve = [
      { date: '2026-01-01', value: 100000 },
      { date: '2026-06-01', value: 200000 },
    ]
    const { data } = positionSizeStats(trades, curve, 100000)
    expect(data.map((d) => d.size)).toEqual([10, 5, 5])
  })

  it('falls back to starting capital when there is no curve', () => {
    const trades = [trade({ ticker: 'A' }), trade({ ticker: 'B' }), trade({ ticker: 'C' })]
    const { data, avg } = positionSizeStats(trades, [], 100000)
    expect(avg).toBe(10)
    expect(data).toHaveLength(3)
  })

  it('leaves trades without a stop out of the correlation, not in it as zeros', () => {
    const withStop = [1, 2, 3].map((i) =>
      trade({ ticker: `S${i}`, originalQty: 100 * i, entryDate: `2026-01-0${i}`,
              trims: [{ date: `2026-02-0${i}`, price: 110, qty: 100 * i }] }))
    const noStop = [4, 5, 6].map((i) =>
      trade({ ticker: `N${i}`, initialStop: null, originalQty: 100 * i, entryDate: `2026-01-0${i}`,
              trims: [{ date: `2026-02-0${i}`, price: 110, qty: 100 * i }] }))

    const both = positionSizeStats([...withStop, ...noStop], [], 1000000)
    const only = positionSizeStats(withStop, [], 1000000)

    // Six bars are drawn, three are paired, and the correlation is the one
    // computed on the three — adding unpaired rows must not move it.
    expect(both.data).toHaveLength(6)
    expect(both.pairedN).toBe(3)
    expect(both.corr).toBeCloseTo(only.corr, 10)
  })

  it('reports nothing rather than a shape on fewer than three trades', () => {
    const { data, avg, corr } = positionSizeStats([trade({}), trade({})], [], 100000)
    expect(data).toEqual([])
    expect(avg).toBeNull()
    expect(corr).toBeNull()
  })

  it('measures the loss share of the biggest quartile against gross loss', () => {
    // Four trades: the biggest is the only loser, so it owns all of the loss.
    const trades = [
      trade({ ticker: 'BIG', originalQty: 400, realizedPL: -4000, entryDate: '2026-01-01',
              trims: [{ date: '2026-02-01', price: 90, qty: 400 }] }),
      ...[2, 3, 4].map((i) => trade({ ticker: `S${i}`, originalQty: 100, realizedPL: 500,
              entryDate: `2026-01-0${i}`, trims: [{ date: `2026-02-0${i}`, price: 110, qty: 100 }] })),
    ]
    const { lossShareTopQ } = positionSizeStats(trades, [], 1000000)
    expect(lossShareTopQ).toBe(100)
  })
})
