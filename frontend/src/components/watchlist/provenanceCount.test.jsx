import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'

/**
 * The number the provenance line actually paints.
 *
 * `tradeableCount` being right is not the same claim as the header USING it:
 * the 2.1x bug lived at the render site, in one token (`data.universe_gated`),
 * and a unit test on a selector the page never calls would have stayed green
 * through the whole four days this was wrong. So this test mounts the page and
 * reads the sentence.
 *
 * Fixture numbers are the real 2026-08-29 file: 2,055 past the liquidity gate,
 * 975 past the ADR floor the panels below actually draw from.
 */
vi.mock('../../hooks/useWatchlist', () => ({
  useWatchlist: () => ({ data: DOC, failed: false }),
}))

const DOC = {
  date: '2026-08-29',
  gate: {
    min_market_cap: 1000000000.0,
    min_dollar_volume: 20000000.0,
    min_adr_pct: 3.5,
    adr_exempt_zones: ['trouble'],
    adr_unmeasured: 0,
    gated_rows: 2055,
  },
  universe_gated: 2055,
  universe_tradeable: 975,
  universe_tradeable_exempt: 2055,
  zones: [],
  cross_zone: [],
}

beforeEach(() => { localStorage.clear() })

const provenance = () => screen.getByText(/2026-08-29/).textContent

describe('watchlist provenance line', () => {
  it('prints the tradeable pool, not the liquidity count', async () => {
    const { default: WatchlistPage } = await import('./WatchlistPage')
    const { LanguageProvider } = await import('../../i18n/LanguageContext')
    render(<LanguageProvider><WatchlistPage /></LanguageProvider>)

    const line = provenance()
    expect(line).toContain('975')
    // The bug, stated as the thing that must not appear: the page must not
    // print the pre-ADR count beside a list built from the post-ADR pool.
    expect(line).not.toContain('2,055')
    expect(line).not.toContain('2055')
  })

  it('names all three gates the pipeline ran, and the trouble exemption', async () => {
    const { default: WatchlistPage } = await import('./WatchlistPage')
    const { LanguageProvider } = await import('../../i18n/LanguageContext')
    render(<LanguageProvider><WatchlistPage /></LanguageProvider>)

    const line = provenance()
    expect(line).toContain('$1B cap')
    expect(line).toContain('$20M/day traded')
    expect(line).toContain('ADR')
    expect(line).toContain('3.5')
    expect(line).toContain('trouble')
    expect(line).not.toContain('NaN')
  })
})
