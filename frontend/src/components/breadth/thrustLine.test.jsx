import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MarketStateSummary from './MarketStateSummary'
import VoteGlyphs from './VoteGlyphs'

/* DATA ALEX 09-18 (§七, ①): the tile used to re-derive thrust on the page, and
   on 6 of 8 judgeable sessions it read the opposite of the engine. It now
   prints the engine's vote (Stockbee: back-to-back 300+ days on his 4% count,
   breadth_signals.py THRESHOLDS['thrust']) and the Stockbee counts. */
const thrustDetail = (measurable = true) => ({ key: 'thrust', side: 'neutral', label: 'Thrust', value: 384, line: 300, margin: 84, unit: 'names', measurable })
const renderTile = ({ vote = 'neutral', notes = [], lastRow = { up_4pct_stockbee: 384, down_4pct_stockbee: 88 }, measurable = true, t2108 = 50 } = {}) => render(
  <MarketStateSummary
    mm={{ up_4pct: 781, down_4pct: 213, ratio_5d: 1.2, ratio_10d: 0.7, up_25pct_qtr: 1, down_25pct_qtr: 1 }}
    breadth={{ t2108 }}
    verdict={{ guidance: '', context: {}, notes,
      votes: { thrust: vote, ratio_5d: 'bull', ratio_10d: 'neutral', qtr_spread: 'bull' },
      vote_detail: [thrustDetail(measurable)] }}
    lastRow={lastRow} />)

describe('thrust tile prints the engine vote', () => {
  it('bull vote → bullish thrust', () => {
    renderTile({ vote: 'bull' })
    expect(screen.getByText('bullish thrust')).toBeInTheDocument()
  })
  it('bear vote → bearish thrust', () => {
    renderTile({ vote: 'bear' })
    expect(screen.getByText('bearish thrust')).toBeInTheDocument()
  })
  it('neutral vote → no thrust, even with 781 price-only up names', () => {
    renderTile({ vote: 'neutral' })
    expect(screen.getByText('no thrust')).toBeInTheDocument()
  })
  it('churn comes from the engine notes', () => {
    renderTile({ vote: 'neutral', notes: ['Churn/volatile: back-to-back 300+ both ways'] })
    expect(screen.getByText('churn / volatile')).toBeInTheDocument()
  })
  it('unmeasurable → not measured', () => {
    renderTile({ measurable: false })
    expect(screen.getByText('not measured')).toBeInTheDocument()
  })
  it('shows the Stockbee counts (384 / 88), not the price-only 781 / 213', () => {
    const { container } = renderTile({ vote: 'bull' })
    expect(container.textContent).toContain('384')
    expect(container.textContent).not.toContain('781')
  })
  it('ratio note reads the two votes, not a ≥1 split', () => {
    const { container } = renderTile()
    expect(container.textContent).toContain('5D bull · 10D neutral')
  })
  it('T2108 40/60 bands are marked as ours', () => {
    const { container } = renderTile({ t2108: 50 })
    expect(container.textContent).toContain('our band')
  })
})

describe('the thrust glyph is drawn inside its own line, not pinned to the frame', () => {
  it('margin −150 on a 300 line sits about half-way down, not at the bottom edge', () => {
    const d = { key: 'thrust', side: 'neutral', label: 'Thrust', value: 150, line: 300, margin: -150, unit: 'names', measurable: true }
    const { container } = render(<VoteGlyphs detail={[d]} />)
    const dot = [...container.querySelectorAll('div')].find((x) => x.className.includes('w-[11px]'))
    const bottom = parseFloat(dot.style.bottom)
    expect(bottom).toBeGreaterThan(20)
    expect(bottom).toBeLessThan(40)
  })
})
