import { describe, it, expect } from 'vitest'
import { applyFilters } from './screenerFilter'
import presets from '../../public/data/screener-presets.json'

/* 2026-09-18, Andy 「全部按原文」: presets now carry the authors' own keys.
   screenerFilter used to skip unknown keys silently, so the 9M preset would have
   listed every $1B name and 21EMA Watch would have lost its 50-line leg. */
const rows = [
  { ticker: 'BIG', volume: 9_500_000, avg_volume: 2_000_000, sma50_atr_dist: 1.0 },
  { ticker: 'SMALL', volume: 3_000_000, avg_volume: 12_000_000, sma50_atr_dist: 6.0 },
]

describe('author keys are applied, not skipped', () => {
  it('volumeMin reads TODAY\'s volume (Stockbee v>=8900000), not the average', () => {
    const out = applyFilters(rows, { volumeMin: 8.9 }, '')
    expect(out.map((r) => r.ticker)).toEqual(['BIG'])
  })

  it('sma50AtrDist bounds the plain ATR distance from the 50 (Alex -0.5..4)', () => {
    const out = applyFilters(rows, { sma50AtrDist: { enabled: true, min: -0.5, max: 4 } }, '')
    expect(out.map((r) => r.ticker)).toEqual(['BIG'])
  })

  it('the shipped 9M preset keeps only names that traded 8.9M shares today', () => {
    const nine = presets.find((p) => p.name === 'Stockbee 9M Setup')
    const withCap = rows.map((r) => ({ ...r, market_cap: 5e9 }))
    expect(applyFilters(withCap, nine.filters, '').map((r) => r.ticker)).toEqual(['BIG'])
  })

  it('Sugar Babies keeps only the top-30 rank (Stockbee 9M EPs, 2026-09-21)', () => {
    const sb = presets.find((p) => p.name === 'Sugar Babies')
    const u = [
      { ticker: 'IN', market_cap: 5e9, sugar_rank: 3 },
      { ticker: 'OUT', market_cap: 5e9, sugar_rank: null },
    ]
    expect(applyFilters(u, sb.filters, '').map((r) => r.ticker)).toEqual(['IN'])
  })
})
