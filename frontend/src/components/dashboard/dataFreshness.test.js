import { describe, it, expect } from 'vitest'
import { weekdaysBetween, todayET, freshness } from './dataFreshness'

const at = (iso) => new Date(iso)

describe('weekdaysBetween', () => {
  it('counts the weekdays crossed, not the calendar days', () => {
    // Fri 2026-08-21 → Mon 2026-08-24 is three calendar days and one weekday
    expect(weekdaysBetween('2026-08-21', '2026-08-24')).toBe(1)
    expect(weekdaysBetween('2026-08-24', '2026-08-25')).toBe(1)
    expect(weekdaysBetween('2026-08-24', '2026-08-28')).toBe(4)
  })

  it('is zero for the same day and never negative', () => {
    expect(weekdaysBetween('2026-08-26', '2026-08-26')).toBe(0)
    expect(weekdaysBetween('2026-08-28', '2026-08-26')).toBe(0)
  })

  it('a weekend on its own crosses nothing', () => {
    // Sat → Sun
    expect(weekdaysBetween('2026-08-22', '2026-08-23')).toBe(0)
  })

  it('returns 0 rather than NaN when a date is missing or malformed', () => {
    expect(weekdaysBetween(undefined, '2026-08-26')).toBe(0)
    expect(weekdaysBetween('2026-08-26', 'not-a-date')).toBe(0)
  })
})

describe('todayET', () => {
  it('reads the market\'s day, not the host\'s', () => {
    // 2026-08-28 02:57 UTC is still 2026-08-27 in New York — the JST machine
    // this runs on would have said the 28th, and named the wrong session.
    expect(todayET(at('2026-08-28T02:57:00Z'))).toBe('2026-08-27')
    expect(todayET(at('2026-08-27T21:00:00Z'))).toBe('2026-08-27')
  })
})

describe('freshness', () => {
  const now = at('2026-08-28T02:57:00Z')   // Thu 2026-08-27 in New York

  it('says nothing when today\'s close simply has not been published yet', () => {
    // one weekday back is the normal state for most of any day
    expect(freshness('2026-08-26', now)).toBe(null)
    expect(freshness('2026-08-27', now)).toBe(null)
  })

  it('speaks up at two weekdays back — the exact case nobody was told about', () => {
    const f = freshness('2026-08-25', now)
    expect(f).toEqual({ behind: 2, level: 'warn', date: '2026-08-25' })
  })

  it('turns to alarm at four', () => {
    expect(freshness('2026-08-21', now).level).toBe('alarm')
    expect(freshness('2026-08-21', now).behind).toBe(4)
  })

  it('says nothing when there is no session date at all', () => {
    // the missing-block guard owns that case; this one must not double up
    expect(freshness(null, now)).toBe(null)
    expect(freshness(undefined, now)).toBe(null)
  })

  it('does not fire on a future date', () => {
    expect(freshness('2026-09-10', now)).toBe(null)
  })
})
