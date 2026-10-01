import { describe, it, expect, vi, afterEach } from 'vitest'
import { render } from '@testing-library/react'
import TickerEarnings from './TickerEarnings'

// T-1001-118: next_earnings_asof marks a carried (vendor-outage) reading --
// the badge must stay silent for a fresh reading and only speak up once it
// is old enough to matter, same grace period as DataFreshnessBadge.
const NOW = new Date('2026-10-02T02:57:00Z') // ET "today" = 2026-10-01

describe('TickerEarnings next_earnings_asof staleness', () => {
  afterEach(() => vi.useRealTimers())

  it('says nothing when there is no asof (normal nightly confirmation)', () => {
    const { container } = render(
      <TickerEarnings tickerData={{ next_earnings: { date: '2026-10-15' } }} />
    )
    expect(container.textContent).not.toContain('asof')
  })

  it('says nothing when the carried reading is only one weekday old (grace period)', () => {
    vi.useFakeTimers()
    vi.setSystemTime(NOW)
    const { container } = render(
      <TickerEarnings tickerData={{
        next_earnings: { date: '2026-10-15' },
        next_earnings_asof: '2026-09-30',
      }} />
    )
    expect(container.textContent).not.toContain('asof')
  })

  it('flags a carried reading once it is 2+ weekdays stale', () => {
    vi.useFakeTimers()
    vi.setSystemTime(NOW)
    const { container } = render(
      <TickerEarnings tickerData={{
        next_earnings: { date: '2026-10-15' },
        next_earnings_asof: '2026-09-28',
      }} />
    )
    expect(container.textContent).toContain('asof 2026-09-28')
  })
})
