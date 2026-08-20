import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { render } from '@testing-library/react'
import CardChart from './CardChart'

/**
 * A line that is partly missing is still a line.
 *
 * The first version of this required every value in a series to be present and
 * dropped the whole line otherwise. A 130-bar window carries 32 leading nulls
 * for a 50-day mean — it has no history to average yet — so THE 50-DAY WAS
 * ABSENT FROM EVERY CARD ON THE PAGE, on a chart whose whole claim is price
 * against its 21- and 50-day. Nothing said so; two lines look like two lines.
 *
 * It shipped because I checked that a chart rendered, not that it drew what it
 * said it drew. The probe here counts strokes, which is the check that would
 * have caught it.
 */
const ramp = (n, base, holes = 0) =>
  Array.from({ length: n }, (_, i) => (i < holes ? null : base + i))
const series = (n = 60, holes = 0) => ({
  d: Array.from({ length: n }, (_, i) => `2026-06-${String((i % 28) + 1).padStart(2, '0')}`),
  c: ramp(n, 100), e21: ramp(n, 99), s50: ramp(n, 95, holes), v: ramp(n, 1e6),
})
const strokes = (c) => [...c.container.querySelectorAll('polyline')]
  .map((p) => p.getAttribute('stroke'))

describe('a series with a warm-up gap', () => {
  it('draws the average over the part that exists', () => {
    const c = render(<CardChart series={series(60, 32)} />)
    expect(strokes(c)).toHaveLength(3)
    const s50 = [...c.container.querySelectorAll('polyline')]
      .find((p) => p.getAttribute('stroke') === 'var(--color-text-muted)')
    expect(s50.getAttribute('points').split(' ')).toHaveLength(28)
  })

  it('starts it where its window fills, not at the left edge', () => {
    const c = render(<CardChart series={series(60, 32)} />)
    const s50 = [...c.container.querySelectorAll('polyline')]
      .find((p) => p.getAttribute('stroke') === 'var(--color-text-muted)')
    const full = [...c.container.querySelectorAll('polyline')]
      .find((p) => p.getAttribute('stroke') === 'var(--color-text)')
    const x = (p) => +p.getAttribute('points').split(' ')[0].split(',')[0]
    expect(x(s50)).toBeGreaterThan(x(full))
  })

  it('does not bridge an interior hole, which would draw a value nobody computed', () => {
    const s = series(20)
    s.s50[10] = null
    const c = render(<CardChart series={s} />)
    // price, ema, and the 50-day in two pieces
    expect(strokes(c).filter((k) => k === 'var(--color-text-muted)')).toHaveLength(2)
  })

  it('omits a series that is missing entirely, rather than drawing a flat line', () => {
    const s = series(20); s.s50 = ramp(20, 95, 20)
    expect(strokes(render(<CardChart series={s} />))
      .filter((k) => k === 'var(--color-text-muted)')).toHaveLength(0)
  })
})

/* The file that exposed it. Every card on the page carries 32 s50 nulls; if the
   pipeline ever ships a series shape this cannot draw, this is where it shows. */
const doc = (() => {
  try { return JSON.parse(readFileSync(
    resolve(process.cwd(), '..', 'data/output/shortlist.json'), 'utf8')) } catch { return null }
})()

describe.skipIf(!doc)('every card in the real file', () => {
  it('draws all three lines', () => {
    for (const card of doc.cards) {
      const c = render(<CardChart series={card.series} marks={card.marks} />)
      const s = strokes(c)
      expect(s, card.ticker).toContain('var(--color-text)')
      expect(s, card.ticker).toContain('var(--color-text-secondary)')
      expect(s, card.ticker).toContain('var(--color-text-muted)')
      c.unmount()
    }
  })
})
