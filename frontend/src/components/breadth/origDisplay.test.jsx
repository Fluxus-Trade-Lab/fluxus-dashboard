import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import BreadthTable from './BreadthTable'
import MarketStateSummary from './MarketStateSummary'

// DATA ALEX 09-18: votes read Stockbee's own columns; the old counts keep their
// history but are never what voted. The page shows them greyed, never tinted.
const rows = [
  { date: '2026-09-17', ratio_5d: 0.85, ratio_10d: 0.72, up_25pct_qtr: 643, down_25pct_qtr: 921 },
  { date: '2026-09-18', ratio_5d: 0.85, ratio_5d_stockbee: 1.40, up_25pct_qtr: 643, down_25pct_qtr: 921,
    up_25pct_qtr_stockbee: 700, down_25pct_qtr_stockbee: 500 },
]

describe('archive table prints the author column, old counts greyed', () => {
  it('today reads the Stockbee ratio and tints it; yesterday the old ratio, grey and untinted', () => {
    const { container } = render(<BreadthTable data={{ history: { rows } }} />)
    const cells = [...container.querySelectorAll('td')]
    const sb = cells.find((c) => c.textContent === '1.40')
    const old = cells.find((c) => c.textContent === '0.85')
    expect(sb.className).toMatch(/bg-\[color-mix/)
    expect(old.className).toMatch(/italic/)
    expect(old.className).not.toMatch(/bg-\[color-mix/)
  })
})

describe('summary tiles say which count they print', () => {
  const props = { mm: { ratio_5d: 0.85, ratio_10d: 0.72 }, breadth: { t2108: 50 }, verdict: { votes: {}, context: {} } }
  it('old columns only → "(old count)"', () => {
    const { container } = render(<MarketStateSummary {...props} lastRow={rows[0]} />)
    expect(container.textContent).toContain('5-day / 10-day ratio (old count)')
  })
  it('Stockbee quarter columns → "(Stockbee)" and their numbers', () => {
    const { container } = render(<MarketStateSummary {...props} lastRow={rows[1]} />)
    expect(container.textContent).toContain('Quarterly breadth (25%+) (Stockbee)')
    expect(container.textContent).toContain('700 / 500')
  })
})
