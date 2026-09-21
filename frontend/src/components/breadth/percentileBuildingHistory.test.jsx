import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import MarketStateSummary from './MarketStateSummary'
import VoteCard from './VoteCard'

/* 2026-09-21 DATA ALEX (`d8c52172`, DATA_CONTRACTS §七): up_4pct / down_4pct /
   ratio_5d / nh_nl_net / qtr_spread rank only against their own Stockbee
   column and are omitted from `context` until MIN_STOCKBEE_RANK_N=60 sessions
   accumulate. Missing must read as "building history", not the blank a
   reader takes for "no data". */
describe('percentile context reads "building history", not blank, while gated', () => {
  const summaryProps = {
    mm: { up_4pct: 10, down_4pct: 5, ratio_5d: 1.1, ratio_10d: 0.9, up_25pct_qtr: 1, down_25pct_qtr: 1 },
    breadth: { t2108: 50 },
    lastRow: { date: '2026-09-21' },
  }

  it('MarketStateSummary: empty context -> "building history" on all three gated tiles', () => {
    const { container } = render(<MarketStateSummary {...summaryProps} verdict={{ votes: {}, context: {} }} />)
    expect(container.textContent).toContain('down-4% building history')
    expect(container.textContent).toContain('5D building history')
    expect(container.textContent).toContain('spread building history')
  })

  it('MarketStateSummary: once ranked, prints the digit instead', () => {
    const { container } = render(<MarketStateSummary {...summaryProps}
      verdict={{ votes: {}, context: { down_4pct: 62, ratio_5d: 40, qtr_spread: 71 } }} />)
    expect(container.textContent).toContain('down-4% 62th pctile')
    expect(container.textContent).toContain('5D 40th pctile')
    expect(container.textContent).toContain('spread 71th pctile')
    expect(container.textContent).not.toContain('building history')
  })

  it('VoteCard: all five gated keys read "building history" when context omits them; an ungated key still prints its digit', () => {
    const { container } = render(
      <VoteCard verdict={{ env: 'MIXED', score: 0, votes: {}, vote_detail: [], guidance: '', notes: [],
        context: { t2108: 55 } }} session="2026-09-21" />,
    )
    expect(container.textContent).toContain('up 4% building history')
    expect(container.textContent).toContain('down 4% building history')
    expect(container.textContent).toContain('5-day ratio building history')
    expect(container.textContent).toContain('NH−NL building history')
    expect(container.textContent).toContain('qtr spread building history')
    expect(container.textContent).toContain('T2108 55th')
  })

  it('VoteCard: once all five rank, none print the placeholder', () => {
    const { container } = render(
      <VoteCard verdict={{ env: 'MIXED', score: 0, votes: {}, vote_detail: [], guidance: '', notes: [],
        context: { up_4pct: 10, down_4pct: 20, ratio_5d: 30, nh_nl_net: 40, qtr_spread: 50 } }} session="2026-09-21" />,
    )
    expect(container.textContent).not.toContain('building history')
    expect(container.textContent).toContain('up 4% 10th')
  })
})
