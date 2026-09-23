import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import TickerXHeat from './TickerXHeat'

// Fixture taken from the T-0923-104 task file's 09-23 sample rows.
const X_HEAT = {
  window_days: 7,
  window: { start: '2026-09-16', end: '2026-09-22' },
  count: 414,
  rows: [
    { ticker: 'MU', people_7d: 22, posts_7d: 74, days_7d: 7, peak_day: '2026-09-22', peak_people: 13, is_index: false },
    { ticker: 'INTC', people_7d: 19, posts_7d: 62, days_7d: 7, peak_day: '2026-09-21', peak_people: 11, is_index: false },
  ],
}

describe('TickerXHeat', () => {
  it('renders people_7d and the peak day for a ticker present in rows', () => {
    const { container } = render(<TickerXHeat symbol="MU" xHeat={X_HEAT} />)
    const t = container.textContent
    expect(t).toContain('22 人提及')
    expect(t).toContain('09-22')
    expect(t).toContain('13 人')
  })

  it('shows the file\'s own window range, not a recomputed one', () => {
    const { container } = render(<TickerXHeat symbol="MU" xHeat={X_HEAT} />)
    expect(container.textContent).toContain('09-16–09-22')
  })

  it('shows "无数据", never "0 人", for a ticker missing from rows', () => {
    const { container } = render(<TickerXHeat symbol="AAPL" xHeat={X_HEAT} />)
    const t = container.textContent
    expect(t).toContain('无数据')
    expect(t).not.toContain('0 人')
  })

  it('renders nothing while the file has not loaded yet', () => {
    const { container } = render(<TickerXHeat symbol="MU" xHeat={null} />)
    expect(container.textContent).toBe('')
  })

  it('never uses sentiment/bullish language', () => {
    const { container } = render(<TickerXHeat symbol="MU" xHeat={X_HEAT} />)
    const t = container.textContent
    expect(t).not.toMatch(/sentiment/i)
    expect(t).not.toContain('看涨')
    expect(t).not.toContain('看多')
    expect(t).not.toContain('看空')
    expect(t).not.toContain('人气')
  })
})
