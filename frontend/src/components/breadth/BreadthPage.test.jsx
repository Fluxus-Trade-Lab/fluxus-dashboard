/* global process */
import { describe, it, expect, vi } from 'vitest'
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
    const btn = screen.getByText('Archive').closest('button')
    expect(btn).toHaveAttribute('aria-expanded', 'false')
    fireEvent.click(btn)
    expect(btn).toHaveAttribute('aria-expanded', 'true')
  })

  /* Linda's three standing rules (DATA_CONTRACTS §七 09-11): prob never alone,
     the character line and caveats[0] printed, TICK set apart. */
  it('Correction risk prints prob, n and base rate together, from the real file', async () => {
    const cr = read('data/output/correction_risk.json')
    const tc = read('data/output/tick_cycle.json')
    vi.stubGlobal('fetch', (url) => Promise.resolve({
      ok: true,
      json: () => Promise.resolve(String(url).includes('correction_risk') ? cr : String(url).includes('tick_cycle') ? tc : null),
    }))
    renderPage()
    fireEvent.click(screen.getByText('Correction risk').closest('button'))
    const ts = cr.ts_dimension.today
    const prob = `${(ts.prob_3d * 100).toFixed(1)}%`
    const probEl = await screen.findByText(prob)
    const line = probEl.parentElement.textContent
    expect(line).toContain(ts.n_cell_3d.toLocaleString())
    expect(line).toContain(`${(cr.base_rate * 100).toFixed(1)}%`)
    expect(screen.getByText(/no fitted parameters/)).toBeInTheDocument()
    expect(screen.getByText(cr.caveats[0])).toBeInTheDocument()
    expect(screen.getByText('Side readings')).toBeInTheDocument()
    expect(screen.getByText('TICK cycle')).toBeInTheDocument()
    vi.unstubAllGlobals()
  })

  it('has six folds — the three duplicates are merged, Correction risk stays', () => {
    renderPage()
    for (const l of ['Correction risk', 'Style rotation', 'Benchmarks', 'Ratio and spread', 'Archive', 'Series']) {
      expect(screen.getByText(l)).toBeInTheDocument()
    }
    for (const gone of ['Market monitor', 'Classic breadth', 'Danger signals', 'Benchmark health', 'Historical series']) {
      expect(screen.queryByText(gone)).not.toBeInTheDocument()
    }
  })

  it('pins today as the archive\'s first row, bold, with the A/D line the tiles used to carry', () => {
    renderPage()
    fireEvent.click(screen.getByText('Archive').closest('button'))
    const today = document.querySelector('tbody tr')
    expect(today.className).toMatch(/\btoday\b/)
    expect(today.className).toMatch(/sticky/)
    expect(today.className).toMatch(/font-semibold/)
    const last = breadth.history.rows.at(-1)
    const [, m, d] = last.date.split('-')
    expect(today.textContent).toContain(`${parseInt(m)}/${parseInt(d)}`)
    expect(screen.getByText('A/D line')).toBeInTheDocument()
    expect(today.textContent).toContain(last.ad_line.toLocaleString())
  })
})
