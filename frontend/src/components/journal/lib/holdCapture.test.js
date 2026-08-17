/**
 * The view has to be able to say "these buckets are not comparable", because
 * on the real book they are not: opportunity rises with holding time, so a
 * higher capture in the long bucket is partly winners lasting longer.
 */
import { describe, expect, it } from 'vitest'
import { holdCapture } from './holdCapture'

const t = (hold, realized, optimal) => ({
  closed: true, hold_days: hold, realized_R: realized, optimal_R: optimal,
})
const many = (n, ...a) => Array.from({ length: n }, () => t(...a))

describe('buckets', () => {
  it('splits on holding days and takes medians', () => {
    const { rows } = holdCapture([...many(6, 1, 0.5, 2), ...many(6, 10, 4, 8)])
    expect(rows.map((r) => r.label)).toEqual(['1', '8–20'])
    expect(rows[0].capture).toBeCloseTo(0.25, 6)
    expect(rows[1].capture).toBeCloseTo(0.5, 6)
  })

  it('drops a bucket too small to mean anything', () => {
    const { rows } = holdCapture([...many(6, 1, 1, 2), ...many(3, 30, 1, 2)])
    expect(rows.map((r) => r.label)).toEqual(['1'])
  })

  it('ignores trades that had nothing on offer — capture of ~0R is noise', () => {
    const { rows } = holdCapture([...many(6, 1, 0.05, 0.1), ...many(6, 1, 1, 2)])
    expect(rows[0].n).toBe(6)
  })

  it('excludes a split artefact, same rule the head coach uses', () => {
    const { rows } = holdCapture([...many(6, 1, 1, 2), t(1, 1, 4827)])
    expect(rows[0].n).toBe(6)
  })
})

describe('the confound', () => {
  it('flags buckets whose opportunity itself grows with holding time', () => {
    const { confounded } = holdCapture([
      ...many(6, 1, 0.5, 1), ...many(6, 5, 1, 2), ...many(6, 30, 3, 6),
    ])
    expect(confounded).toBe(true)
  })

  it('stays quiet when the opportunity is flat across buckets', () => {
    const { confounded } = holdCapture([
      ...many(6, 1, 0.5, 2), ...many(6, 5, 1, 2), ...many(6, 30, 1.5, 2),
    ])
    expect(confounded).toBe(false)
  })
})
