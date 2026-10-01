import { describe, it, expect, vi, afterEach } from 'vitest'
import { render } from '@testing-library/react'
import TickerQuickStats from './TickerQuickStats'

// T-1001-118: the Next ER stat must flag when next_earnings was carried
// forward by a vendor outage (next_earnings_asof), same grace/threshold as
// DataFreshnessBadge -- silent unless the reading is 2+ weekdays stale.
const NOW = new Date('2026-10-02T02:57:00Z') // ET "today" = 2026-10-01

describe('TickerQuickStats next_earnings_asof staleness', () => {
  afterEach(() => vi.useRealTimers())

  it('says nothing when there is no asof', () => {
    const { container } = render(
      <TickerQuickStats tickerData={{ next_earnings: { date: '2026-10-15' } }} />
    )
    expect(container.textContent).not.toContain('asof')
  })

  it('flags a carried reading once it is 2+ weekdays stale', () => {
    vi.useFakeTimers()
    vi.setSystemTime(NOW)
    const { container } = render(
      <TickerQuickStats tickerData={{
        next_earnings: { date: '2026-10-15' },
        next_earnings_asof: '2026-09-28',
      }} />
    )
    expect(container.textContent).toContain('asof 09-28')
  })
})
