import { describe, it, expect } from 'vitest'
import { gateWords, tradeableCount } from './WatchlistPage'
import { translations } from '../../i18n/translations'

/**
 * The provenance line names the universe the list below was drawn from.
 *
 * It got both halves wrong between 2026-08-25 and 2026-08-29:
 *
 *   - the sentence listed two gates while the pipeline was running three
 *     (`MIN_ADR_PCT = 3.5` shipped 08-25 in e260757d), and
 *   - the number was `universe_gated`, which stops counting at the liquidity
 *     gate, while every panel below drew from the post-ADR pool.
 *
 * On the 2026-08-29 file those are 2,055 and 975 — the line overstated the
 * reader's universe by 2.1x. The fixture below is that real file's gate block,
 * not an invented one, so these tests fail if the shipped shape moves.
 */
const GATE_2026_08_29 = {
  min_market_cap: 1000000000.0,
  min_dollar_volume: 20000000.0,
  min_adr_pct: 3.5,
  adr_exempt_zones: ['trouble'],
  adr_unmeasured: 0,
  gated_rows: 2055,
}

describe('gateWords', () => {
  it('names the ADR gate the pipeline is actually running', () => {
    // The regression this file exists for: the clause was simply missing.
    expect(gateWords(GATE_2026_08_29)).toContain('ADR')
    expect(gateWords(GATE_2026_08_29)).toContain('3.5')
  })

  it('says the exempt zone is exempt, so the sentence does not over-claim', () => {
    // The overview page shows trouble panels alongside the others, and those
    // are drawn from the pre-ADR pool. Without this the line claims a floor
    // that demonstrably does not hold for names visible on the same screen.
    expect(gateWords(GATE_2026_08_29)).toContain('trouble')
  })

  it('still describes the two liquidity gates', () => {
    const out = gateWords(GATE_2026_08_29)
    expect(out).toContain('$1B cap')
    expect(out).toContain('$20M/day traded')
  })

  it('drops the ADR clause entirely on a file that has no such gate', () => {
    // Same doctrine as the 08-17 unit swap: a clause we cannot describe is
    // absent, never present as NaN or as an invented default.
    const out = gateWords({ min_market_cap: 1e9, min_dollar_volume: 2e7 })
    expect(out).not.toContain('ADR')
    expect(out).not.toContain('NaN')
    expect(out).not.toContain('undefined')
  })

  it('names the ADR gate without an exemption clause when nothing is exempt', () => {
    const out = gateWords({ min_adr_pct: 3.5, adr_exempt_zones: [] })
    expect(out).toContain('ADR')
    expect(out).not.toContain('except')
  })

  it('keeps the shares/day fallback for pre-08-17 files', () => {
    expect(gateWords({ min_avg_volume: 1e6 })).toContain('1M shares/day')
  })
})

describe('tradeableCount', () => {
  it('reports the pool the panels drew from, not the liquidity count', () => {
    // The 2.1x bug, pinned to the real numbers off the 08-29 file.
    expect(tradeableCount({ universe_gated: 2055, universe_tradeable: 975 })).toBe(975)
  })

  it('falls back rather than printing NaN on a pre-08-27 file', () => {
    expect(tradeableCount({ universe_gated: 1981 })).toBe(1981)
    expect(Number.isNaN(tradeableCount({ universe_gated: 1981 }))).toBe(false)
  })

  it('does not treat a legitimate zero as missing', () => {
    // `??` and not `||`: a day where nothing clears the ADR floor is a real
    // reading, and must not silently fall back to the larger number.
    expect(tradeableCount({ universe_gated: 2055, universe_tradeable: 0 })).toBe(0)
  })
})

describe('wl.provenance', () => {
  it('calls the count tradeable, not gate-cleared, in both languages', () => {
    // v1b's one-word change: the names cut by the ADR floor are not "worse",
    // they are untradeable under an ATR-sized stop. The word carries the
    // reason, and the reason is what decides position size.
    expect(translations.en['wl.provenance']).toContain('tradeable')
    expect(translations.en['wl.provenance']).not.toContain('cleared the gate')
    expect(translations.zh['wl.provenance']).toContain('可交易')
    expect(translations.zh['wl.provenance']).not.toContain('过闸')
  })

  it('still interpolates the same three slots', () => {
    for (const lang of ['en', 'zh']) {
      for (const slot of ['{date}', '{n}', '{gate}']) {
        expect(translations[lang]['wl.provenance'], `${lang}/${slot}`).toContain(slot)
      }
    }
  })
})
