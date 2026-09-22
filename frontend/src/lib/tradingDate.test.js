import { describe, it, expect } from 'vitest'
import { toJstDate } from './tradingDate'

// GAS returns a Sheet Date cell as `YYYY-MM-DDT15:00:00.000Z` — midnight JST
// restated in UTC. slice(0, 10) on that string used to read one day early
// (T-0922-44, frontend sibling of the pipeline fix in T-0922-43).
describe('toJstDate', () => {
  it('converts a GAS UTC timestamp to the JST calendar date', () => {
    expect(toJstDate('2026-09-20T15:00:00.000Z')).toBe('2026-09-21')
  })

  it('converts a timestamp just before JST midnight to the prior day', () => {
    expect(toJstDate('2026-09-20T14:59:59.999Z')).toBe('2026-09-20')
  })

  it('leaves a plain YYYY-MM-DD date unchanged', () => {
    expect(toJstDate('2026-09-21')).toBe('2026-09-21')
  })

  it('handles a timestamp carrying an explicit +09:00 offset', () => {
    expect(toJstDate('2026-09-21T00:00:00.000+09:00')).toBe('2026-09-21')
  })

  it('returns an empty string for null/undefined', () => {
    expect(toJstDate(null)).toBe('')
    expect(toJstDate(undefined)).toBe('')
  })
})
