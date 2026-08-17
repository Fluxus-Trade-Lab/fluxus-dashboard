/**
 * This section's usual answer is "no signal", and the tests exist to make sure
 * it can still say "yes" — a check that never fires and a check that always
 * fires are equally useless.
 */
import { describe, expect, it } from 'vitest'
import { setupEdge } from './setupEdge'

const t = (setup, r) => ({ closed: true, setup_type: setup, realized_R: r, optimal_R: 5 })
const many = (n, setup, r) => Array.from({ length: n }, () => t(setup, r))

describe('setup edge', () => {
  it('finds no separation when every label performs alike', () => {
    // Same distribution under three labels, jittered so the bootstrap has
    // something to resample.
    const mix = (s) => Array.from({ length: 40 }, (_, i) => t(s, i % 5 === 0 ? 4 : -1))
    const res = setupEdge([...mix('A'), ...mix('B'), ...mix('C')])
    expect(res.rows).toHaveLength(3)
    expect(res.signal).toBe(false)
  })

  it('separates a label that really is different', () => {
    const res = setupEdge([...many(60, 'flat', 0), ...many(60, 'good', 5)])
    expect(res.rows.find((r) => r.setup === 'good').separates).toBe(true)
  })

  it('drops labels too small to say anything about', () => {
    const res = setupEdge([...many(60, 'big', 1), ...many(3, 'tiny', 40)])
    expect(res.rows.map((r) => r.setup)).toEqual(['big'])
  })

  it('reports how concentrated the labels are', () => {
    const res = setupEdge([...many(80, 'one', 1), ...many(20, 'two', 1)])
    expect(res.concentration).toBeCloseTo(0.8, 2)
  })

  it('counts hits against what chance alone would give', () => {
    const mix = (s) => Array.from({ length: 40 }, (_, i) => t(s, i % 5 === 0 ? 4 : -1))
    const res = setupEdge([...mix('A'), ...mix('B'), ...mix('C')])
    expect(res.expectedByChance).toBeCloseTo(0.3, 6)
  })

  it('is deterministic', () => {
    const book = [...many(60, 'a', 1), ...many(60, 'b', 2)]
    expect(setupEdge(book).rows[0].lo).toBe(setupEdge(book).rows[0].lo)
  })

  it('says nothing at all on a short book', () => {
    expect(setupEdge(many(20, 'a', 1))).toBeNull()
  })
})
