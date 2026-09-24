import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PortfolioProvider } from '../context/PortfolioContext'
import { LanguageProvider } from '../../../i18n/LanguageContext'
import OverviewTab from './OverviewTab'
import { enrichTrades } from '../lib/calculations'
import { computeQtyMismatches } from '../lib/qtyMismatch'

/**
 * Headless proof that the Portfolio page surfaces a qty/trim-log mismatch
 * (T-0924-103) without printing a share count. Shaped on the real 2026-09-24
 * ARM incident (originalQty 300, one 160-share trim, currentQty hand-edited
 * to 100 → Sheet reads -13.3% of position light) — live GAS data no longer
 * reproduces this (Andy fixed the row directly, 31b35bed), so this is the
 * synthetic positive control that proves the detector still fires.
 *
 * entryDate is a GAS Date-cell timestamp ("...T15:00:00.000Z"), not a plain
 * date string — a real pre-fix snapshot reads exactly this for ARM's row.
 * The Qty column's own date cell renders it through toJstDate (2026-09-18);
 * a mismatch UI that skipped that conversion would name the row a calendar
 * day behind the one shown right next to it (the T-0922-44 bug class), so
 * this fixture is timestamp-shaped on purpose rather than a bare '2026-09-17'.
 */
function renderOverview(rawTrades) {
  const enrichedTrades = enrichTrades(rawTrades, 100000, {})
  const qtyMismatches = computeQtyMismatches(rawTrades)
  render(
    <PortfolioProvider>
      <LanguageProvider>
        <OverviewTab
          performanceData={[]}
          totalReturnPct={0}
          monthlyStats={[]}
          ytdStats={null}
          enrichedTrades={enrichedTrades}
          qtyMismatches={qtyMismatches}
          onTrim={() => {}}
        />
      </LanguageProvider>
    </PortfolioProvider>,
  )
}

const armMismatched = {
  id: 'arm-1', ticker: 'ARM', direction: 'long', sector: 'Tech',
  entryDate: '2026-09-17T15:00:00.000Z', entryPrice: 180, originalQty: 300, currentQty: 100,
  stopPrice: 170, initialStop: 170, isClosed: false,
  trims: [{ date: '2026-09-20', price: 200, qty: 160, type: 'trim' }],
}

const clean = {
  id: 'clean-1', ticker: 'MSFT', direction: 'long', sector: 'Tech',
  entryDate: '2026-08-01', entryPrice: 400, originalQty: 50, currentQty: 50,
  stopPrice: 380, initialStop: 380, isClosed: false, trims: [],
}

describe('OverviewTab qty/trim-log mismatch warning', () => {
  it('shows the mismatched ticker, entry date and gap%, with no share count', () => {
    renderOverview([armMismatched, clean])

    // Ticker + entry date + gap% name the row without a screenshot. The date
    // must be the JST calendar day (2026-09-18), matching the Qty column's
    // own toJstDate rendering of the same timestamp — not the raw UTC string.
    const banner = screen.getByTestId('qty-mismatch-banner')
    expect(banner.textContent).toMatch(/ARM/)
    expect(banner.textContent).toMatch(/2026-09-18/)
    expect(banner.textContent).not.toMatch(/2026-09-17T/)
    // Gap reported as a % of position (Andy 2026-09-13: never a share count).
    expect(banner.textContent).toMatch(/-13\.3%/)

    // The two raw quantities (300, 100) must never appear as bare numbers in
    // the warning banner — only inside the ordinary Qty column, which already
    // prints them for every row regardless of mismatch status.
    expect(banner.textContent).not.toMatch(/\b100\b/)
    expect(banner.textContent).not.toMatch(/\b300\b/)

    // Inline per-row badge on the mismatched trade's Qty cell, same JST date.
    expect(screen.getByTitle(/ARM 2026-09-18.*-13\.3%/)).toBeInTheDocument()
  })

  it('stays silent when every row reconciles', () => {
    renderOverview([clean])
    expect(screen.queryByText(/don't reconcile with the trim log/)).not.toBeInTheDocument()
  })
})
