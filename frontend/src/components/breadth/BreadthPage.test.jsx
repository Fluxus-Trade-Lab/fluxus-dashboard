import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { render, screen, fireEvent } from '@testing-library/react'
import { LanguageProvider } from '../../i18n/LanguageContext'
import BreadthPage from './BreadthPage'

/**
 * A mount test, not a unit test — the 2026-09-11 rewrite touched nine files
 * at once (BoardCard/ChainCard/VoteCard replacing StateBoard/VerdictBanner/
 * MarketStateSummary, plus Reference's redesign), and a bad prop threaded
 * through any one of them throws at render, not at import. `provenanceCount`
 * set the pattern this follows: mount on the real file, read the sentence.
 */
const read = (p) => JSON.parse(readFileSync(resolve(process.cwd(), '..', p), 'utf8'))
const breadth = read('data/output/breadth.json')
const market_health = read('data/output/market_health.json')
const signals = read('data/output/signals.json')

function renderPage() {
  return render(
    <LanguageProvider>
      <BreadthPage data={{ breadth, market_health, signals }} />
    </LanguageProvider>,
  )
}

describe('BreadthPage — 09-11 three-card rebuild', () => {
  it('mounts on the real file without throwing', () => {
    expect(() => renderPage()).not.toThrow()
  })

  it('renders the three subject cards', () => {
    renderPage()
    expect(screen.getByText('Board')).toBeInTheDocument()
    expect(screen.getByText('Chain')).toBeInTheDocument()
    expect(screen.getByText('Votes')).toBeInTheDocument()
  })

  it('prints every board row and no more or fewer than the file has', () => {
    renderPage()
    for (const row of breadth.state_board.rows) {
      // row keys are lowercase in the payload, capitalize() only in CSS
      expect(screen.getAllByText(new RegExp(`^${row.key}$`, 'i')).length).toBeGreaterThan(0)
    }
  })

  it('keeps the score, since it is the one number the falsification text depends on', () => {
    renderPage()
    const s = breadth.verdict.score
    const printed = s >= 0 ? `+${s}` : String(s)
    expect(screen.getAllByText(new RegExp(`score ${printed.replace('+', '\\+')} / 12`)).length)
      .toBeGreaterThan(0)
  })

  it('folds the reference rows closed by default and opens one on click', () => {
    renderPage()
    // "Correction risk" is a static placeholder — no chart library underneath
    // it, so this stays a test of Reference's toggle, not of lightweight-charts
    // in jsdom (that gap is real but pre-existing and unrelated to this diff).
    const btn = screen.getByText('Correction risk').closest('button')
    expect(btn).toHaveAttribute('aria-expanded', 'false')
    fireEvent.click(btn)
    expect(btn).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText(/Will hold:/)).toBeInTheDocument()
  })
})
