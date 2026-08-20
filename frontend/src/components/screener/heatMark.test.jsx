import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { HeatCell } from './StockTable'

/**
 * The mark says a thing the score cannot.
 *
 * `score` counts appearances across the whole window. `confluence_days` counts
 * SESSIONS on which four or more screens lit at once. A name can reach a high
 * score by turning up on many screens over many weeks; another can reach a
 * lower one by lighting four in a single day. Only the second is what the MRNA
 * case calls a detonation, and a number alone puts them side by side.
 *
 * The field ships with tonight's cron. Until then the mark must be ABSENT, not
 * off — the same distinction this cell already draws by printing a dash for a
 * name carrying no ledger at all. A `0` would be a claim we cannot make yet.
 */
const cell = (heat) => render(<table><tbody><tr><HeatCell heat={heat} /></tr></tbody></table>)
const mark = (c) => c.container.querySelector('svg')

describe('the confluence mark', () => {
  const base = { score: 7.5, screeners: [{ name: 'x', hits: 2 }] }

  it('is absent while the field has not shipped', () => {
    expect(mark(cell(base))).toBeNull()
  })

  it('is absent when the name simply never detonated', () => {
    expect(mark(cell({ ...base, confluence_days: 0 }))).toBeNull()
  })

  it('appears once the name has one such session, and counts it', () => {
    const c = cell({ ...base, confluence_days: 1 })
    expect(mark(c)).not.toBeNull()
    expect(c.container.querySelector('[title]').getAttribute('title')).toContain('1 session ')
  })

  it('says sessions, plural, for more than one', () => {
    const c = cell({ ...base, confluence_days: 3 })
    expect(c.container.querySelector('[title]').getAttribute('title')).toContain('3 sessions')
  })

  it('never displaces the score', () => {
    expect(screen.queryByText('7.5')).toBeNull()
    const c = cell({ ...base, confluence_days: 3 })
    expect(c.getByText('7.5')).toBeTruthy()
  })
})
