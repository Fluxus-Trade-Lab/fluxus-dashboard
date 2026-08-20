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

describe('the log axis', () => {
  /* MRNA's real shape: a month between 53.86 and 64.46, then one day to 174.38.
     Measured on the actual 130 bars, the month the article is ABOUT occupies
     7.9% of a linear chart's height and 12.2% of a log one — a 1.5x rescue, and
     not enough on its own. The fix for that article is a window that ends the
     day BEFORE the repricing (37.9% at 40 bars); log is what makes a chart that
     must show both days readable at all. Both facts belong in the same test so
     neither gets remembered without the other. */
  const mrna = () => {
    const base = Array.from({ length: 40 }, (_, i) => 54 + (i * 10.5) / 39)
    return { d: base.map((_, i) => `2026-07-${String((i % 28) + 1).padStart(2, '0')}`),
             c: [...base, 174.38], e21: [...base, 150], s50: [...base, 120],
             v: Array.from({ length: 41 }, () => 1e6) }
  }
  const spread = (c) => {
    const pts = [...c.container.querySelectorAll('polyline')]
      .find((p) => p.getAttribute('stroke') === 'var(--color-text)')
      .getAttribute('points').split(' ').map((p) => +p.split(',')[1])
    const month = pts.slice(0, 40)
    return (Math.max(...month) - Math.min(...month)) / (Math.max(...pts) - Math.min(...pts))
  }

  it('gives the month back some of its height when one day dwarfs it', () => {
    const lin = spread(render(<CardChart series={mrna()} />))
    const lg = spread(render(<CardChart series={mrna()} scale="log" />))
    expect(lin).toBeLessThan(0.12)             // squashed, as the real bars are
    expect(lg / lin).toBeGreaterThan(1.4)      // the real rescue is 1.5x
    expect(lg / lin).toBeLessThan(2.5)         // and it is only that — not a cure
  })

  it('says the axis changed, because a silent log axis lies about proportion', () => {
    expect(render(<CardChart series={mrna()} scale="log" />).container.textContent).toContain('log')
    expect(render(<CardChart series={mrna()} />).container.textContent).not.toContain('log')
  })

  it('falls back rather than dropping points a log axis cannot take', () => {
    const s = mrna(); s.c[0] = 0
    const c = render(<CardChart series={s} scale="log" />)
    expect(c.container.textContent).not.toContain('log')
    expect([...c.container.querySelectorAll('polyline')]
      .find((p) => p.getAttribute('stroke') === 'var(--color-text)')
      .getAttribute('points').split(' ')).toHaveLength(41)
  })
})

describe('bare, for a cover', () => {
  const s = () => ({ d: ['2026-06-01', '2026-07-01', '2026-08-01'],
                     c: [10, 12, 11], e21: [10, 11, 11], s50: [9, 10, 10], v: [1, 2, 3] })

  it('keeps the shape and drops the numbers', () => {
    const full = render(<CardChart series={s()} />)
    const cover = render(<CardChart series={s()} bare />)
    expect(full.container.textContent).toContain('11')      // last close, and month ticks
    expect(cover.container.textContent.trim()).toBe('')
    expect(cover.container.querySelectorAll('polyline').length)
      .toBe(full.container.querySelectorAll('polyline').length)
  })

  it('still says the axis changed, because that is not decoration', () => {
    expect(render(<CardChart series={s()} bare scale="log" />).container.textContent)
      .toContain('log')
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
