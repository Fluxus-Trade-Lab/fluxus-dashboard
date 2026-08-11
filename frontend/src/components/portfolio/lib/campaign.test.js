import { describe, it, expect } from 'vitest'
import { groupByCampaigns } from './campaign'

const t = (id, ticker, direction, entryDate, entryPrice, originalQty, stopPrice, currentQty) =>
  ({ id, ticker, direction, entryDate, entryPrice, originalQty, stopPrice,
    // Real trades always carry this — TradeForm writes it at entry. The
    // fixture predates the field.
    initialStop: stopPrice,
    currentQty, trims: [] })

describe('campaign.groupByCampaigns', () => {
  it('returns singletons when nothing overlaps', () => {
    const trades = [
      t('a', 'MU', 'long', '2026-01-01', 100, 100, 95, 100),
      t('b', 'TSLA', 'long', '2026-01-02', 200, 50, 190, 50),
    ]
    const groups = groupByCampaigns(trades)
    expect(groups).toHaveLength(2)
    expect(groups[0].layers).toHaveLength(1)
  })

  it('groups same-ticker same-direction trades within 60 business days', () => {
    const trades = [
      t('a', 'DOCN', 'long', '2026-03-15', 70, 100, 65, 100),
      t('b', 'DOCN', 'long', '2026-04-14', 82, 50, 78, 50),
    ]
    const groups = groupByCampaigns(trades)
    expect(groups).toHaveLength(1)
    expect(groups[0].layers).toHaveLength(2)
    expect(groups[0].ticker).toBe('DOCN')
  })

  it('does not group across 60-business-day gap', () => {
    const trades = [
      t('a', 'AAPL', 'long', '2026-01-01', 100, 100, 95, 0),
      t('b', 'AAPL', 'long', '2026-06-01', 110, 100, 105, 100),
    ]
    const groups = groupByCampaigns(trades)
    expect(groups).toHaveLength(2)
  })

  it('does not group long and short of same ticker', () => {
    const trades = [
      t('a', 'PLTR', 'long', '2026-01-01', 100, 100, 95, 100),
      t('b', 'PLTR', 'short', '2026-01-02', 100, 100, 105, 100),
    ]
    const groups = groupByCampaigns(trades)
    expect(groups).toHaveLength(2)
  })

  it('aggregates blended entry, total qty, total R$ at campaign level', () => {
    const trades = [
      t('a', 'DOCN', 'long', '2026-03-15', 70, 100, 65, 50),
      t('b', 'DOCN', 'long', '2026-04-14', 82, 100, 78, 100),
    ]
    const groups = groupByCampaigns(trades)
    const c = groups[0]
    expect(c.blendedEntry).toBe(76)
    expect(c.totalOriginalQty).toBe(200)
    expect(c.totalRDollars).toBe(5 * 100 + 4 * 100)
  })
})
