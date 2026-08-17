/**
 * The permutation test is the point. A streak decay shows up in random
 * sequences too — losses cluster by arithmetic — so the tests below check that
 * the machinery says "order matters" when it does and stays quiet when it does
 * not. A view that always finds tilt is not measuring tilt.
 */
import { describe, expect, it } from 'vitest'
import { orderMatters, sequence, streakRows } from './afterLoss'

let day = 0
const t = (r) => ({
  closed: true, realized_R: r, optimal_R: Math.max(r, 1), ticker: 'AAA',
  exit_date: `2026-01-${String(++day % 28 + 1).padStart(2, '0')}-${day}`,
})

/**
 * Order-carrying, and it has to actually produce streaks — the first version of
 * this fixture never put two losses together, so "after two losses" had no
 * sample and the test was asserting on null.
 *
 * Blocks of three losses, then a run of wins. The multiset is fixed; only the
 * arrangement carries the signal.
 */
function tilted(blocks) {
  const out = []
  for (let i = 0; i < blocks; i++) {
    out.push(-1, -1, -1, -1)      // the 4th follows two losses and is a loss
    out.push(3, 3, 3)
  }
  return out
}

/** The same multiset, arranged so nothing follows from anything. */
function shuffledSame(blocks, seed = 7) {
  const a = tilted(blocks)
  let s = seed
  const rnd = () => (s = (s * 1103515245 + 12345) % 2147483648) / 2147483648
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rnd() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

describe('sequence', () => {
  it('is chronological and drops trades with no exit', () => {
    day = 0
    const a = { ...t(1), exit_date: '2026-02-02' }
    const b = { ...t(2), exit_date: '2026-01-01' }
    const c = { ...t(3), exit_date: null }
    expect(sequence([a, b, c])).toEqual([2, 1])
  })
})

describe('streak rows', () => {
  it('reports each depth with its own sample', () => {
    day = 0
    const rows = streakRows(tilted(40).map(t))
    expect(rows[0].key).toBe('all')
    expect(rows.some((r) => r.key === 'L1')).toBe(true)
    expect(rows.some((r) => r.key === 'W1')).toBe(true)
  })

  it('says nothing on a short book rather than guessing', () => {
    day = 0
    expect(streakRows(Array.from({ length: 20 }, () => t(1)))).toEqual([])
  })
})

describe('order matters', () => {
  it('finds order information when the sequence carries it', () => {
    day = 0
    const res = orderMatters(tilted(60).map(t), { runs: 600 })
    expect(res.observed).toBeLessThan(0)
    expect(res.p).toBeLessThan(0.05)
  })

  it('stays quiet when the same results are in a fixed repeating order', () => {
    day = 0
    const res = orderMatters(shuffledSame(60).map(t), { runs: 600 })
    expect(res.p).toBeGreaterThan(0.05)
  })

  it('is deterministic — a p that moves on reload is not evidence', () => {
    day = 0
    const book = tilted(40).map(t)
    expect(orderMatters(book, { runs: 400 }).p)
      .toBe(orderMatters(book, { runs: 400 }).p)
  })

  it('returns null rather than a number it cannot support', () => {
    day = 0
    expect(orderMatters(Array.from({ length: 30 }, () => t(1)))).toBeNull()
  })
})
