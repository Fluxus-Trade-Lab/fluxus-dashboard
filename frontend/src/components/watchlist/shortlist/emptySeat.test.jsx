import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { EmptySeat } from './ShortListPage'

/**
 * The four states of a seat with nobody in it.
 *
 * Three of them are real answers — the panel did not run, it ran and found
 * nobody, it found somebody a gate then stopped — and they have to look
 * different, because "not measured", "found none" and "blocked by a threshold"
 * are the three the rest of this dashboard refuses to blur together.
 *
 * The fourth is the one that is live today: `seats[]` has no `empty_reason`
 * yet, so the page cannot tell which of the three it is looking at. It says so
 * and draws a fourth mark rather than guessing. When the field ships
 * (DATA_CONTRACTS §七) three of these light up and this test stops needing its
 * last case.
 *
 * Shape carries it, never hue — an empty seat is not a side, and the colour
 * budget on this page belongs to the took/refused pair.
 */
const draw = (seat) => render(<EmptySeat seat={seat} label="入场 · 今天最好的入场刀" />)
const shape = (c) => c.container.querySelector('svg[viewBox="0 0 20 20"]')?.innerHTML
const text = (c) => c.container.textContent.replace(/\s+/g, ' ')

describe('an empty seat', () => {
  it('says the panel did not run, and never that it found nothing', () => {
    const t = text(draw({ seat: 'entry', empty_reason: 'not_measured' }))
    expect(t).toContain('那格今晚没跑')
    expect(t).toContain('不是没找到人，是没测')
  })

  it('says it ran and found nobody — which is a reading', () => {
    expect(text(draw({ seat: 'entry', empty_reason: 'none_found' }))).toContain('跑了，一个都没有')
  })

  it('puts the blame on the gate, and counts what it stopped', () => {
    const t = text(draw({ seat: 'entry', empty_reason: 'all_excluded', excluded_n: 7 }))
    expect(t).toContain('被闸挡了')
    expect(t).toContain('被挡下 7 个')
  })

  it('admits it cannot tell, while the field has not shipped', () => {
    const t = text(draw({ seat: 'entry', why: '今日无 EP' }))
    expect(t).toContain('不知道是哪一种')
    expect(t).toContain('empty_reason')
    // and it must not have picked one of the three and sounded sure
    expect(t).not.toContain('是没测')
    expect(t).not.toContain('跑了，一个都没有')
  })

  it('draws four different marks, and no colour', () => {
    const shapes = ['not_measured', 'none_found', 'all_excluded', undefined]
      .map((empty_reason) => shape(draw({ seat: 'entry', empty_reason })))
    expect(new Set(shapes).size).toBe(4)
    for (const s of shapes) expect(s).not.toMatch(/#[0-9a-f]{3,6}|rgb\(/i)
  })

  it('keeps the seat′s own reason visible when it gave one', () => {
    expect(text(draw({ seat: 'entry', why: '今日无 EP' }))).toContain('今日无 EP')
  })
})
