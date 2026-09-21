import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import TickerStats from './TickerStats'

// rs_21d / rs_63d are aliases of rs_1m / rs_3m, which rank CALENDAR-month
// returns (METRIC_SOURCES rs_1m row) -- the label says what is computed.
describe('TickerStats RS labels', () => {
  it('labels the RS cells by calendar window, not session count', () => {
    const { container } = render(<TickerStats universe={{ rs_21d: 81, rs_63d: 77 }} />)
    const t = container.textContent
    expect(t).toContain('RS 1M')
    expect(t).toContain('RS 3M')
    expect(t).not.toContain('RS 21D')
    expect(t).not.toContain('RS 63D')
  })
})
