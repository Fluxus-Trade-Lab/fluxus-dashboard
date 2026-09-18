import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MarketStateSummary from './MarketStateSummary'
import VoteGlyphs from './VoteGlyphs'

/* Nighty Zac 09-18: the tile judged thrust against a flat 300 while the engine
   scales its line with the universe (0.113 × universe_size — 634 that day).
   After the 08-10 universe doubling, 20 of 27 sessions read the opposite. */
const thrust = (value, line, margin) => ({ key: 'thrust', side: 'neutral', label: 'Thrust', value, line, margin, unit: 'names', measurable: true })
const verdictWith = (line) => ({ guidance: '', context: {}, vote_detail: line == null ? [] : [thrust(500, line, 500 - line)] })
const renderTile = (up, down, line) => render(
  <MarketStateSummary mm={{ up_4pct: up, down_4pct: down, ratio_5d: 1, ratio_10d: 1, up_25pct_qtr: 1, down_25pct_qtr: 1 }}
                      breadth={{ t2108: 50 }} verdict={verdictWith(line)} />)

describe('thrust word follows the engine\'s own line', () => {
  it('500 up against a 634 line is no thrust — the flat 300 called it bullish', () => {
    renderTile(500, 100, 634)
    expect(screen.getByText('no thrust')).toBeInTheDocument()
  })

  it('09-16\'s case: 292 up / 580 down against 634 is no thrust, not "bearish thrust"', () => {
    renderTile(292, 580, 634.043)
    expect(screen.getByText('no thrust')).toBeInTheDocument()
  })

  it('clears the line the engine\'s way: up ≥ line and up > down', () => {
    renderTile(781, 213, 634.495)
    expect(screen.getByText('bullish thrust')).toBeInTheDocument()
  })

  it('falls back to 300 only when the payload predates vote_detail', () => {
    renderTile(500, 100, null)
    expect(screen.getByText('bullish thrust')).toBeInTheDocument()
  })
})

describe('the thrust glyph is drawn inside its own line, not pinned to the frame', () => {
  it('margin −342 on a 634 line sits about half-way down, not at the bottom edge', () => {
    const { container } = render(<VoteGlyphs detail={[thrust(292, 634, -342)]} />)
    const dot = [...container.querySelectorAll('div')].find((d) => d.className.includes('w-[11px]'))
    const bottom = parseFloat(dot.style.bottom)
    expect(bottom).toBeGreaterThan(20)   // clamped to the frame it would be 8%
    expect(bottom).toBeLessThan(40)
  })
})
