import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { tickSeries } from './tickCycleMath'

const row = (date, h, c, l, band = 'neutral') => ({ date, ma_high: h, ma_close: c, ma_low: l, spread_rank252: 0.5, band })
const DOC = { history: [
  row('2026-09-28', 800, 10, -800, 'grind'), row('2026-09-29', 790, 0, -790, 'grind'),
  row('2026-09-30', 850, -20, -860), row('2026-10-01', 900, 30, -900, 'washout'), row('2026-10-02', 865.5, -20.2, -870.5),
] }

describe('tickSeries', () => {
  it('needs two complete rows', () => {
    expect(tickSeries(null)).toBeNull()
    expect(tickSeries({ history: [row('2026-10-02', 1, 0, -1)] })).toBeNull()
  })
  it('fixes the y-range over the window, zero included', () => {
    const s = tickSeries(DOC)
    expect(s.lo).toBe(-900)
    expect(s.hi).toBe(900)
  })
  it('groups contiguous non-neutral bands into runs', () => {
    expect(tickSeries(DOC).runs).toEqual([[0, 1, 'grind'], [3, 3, 'washout']])
  })
})

describe('TickCycleChart', () => {
  afterEach(() => vi.unstubAllGlobals())
  it('draws three lines and reads the last session by default', async () => {
    vi.resetModules()
    vi.stubGlobal('fetch', () => Promise.resolve({ ok: true, json: () => Promise.resolve(DOC) }))
    const { default: TickCycleChart } = await import('./TickCycleChart')
    let c
    await act(async () => { c = render(<TickCycleChart />) })
    expect(c.container.querySelectorAll('path')).toHaveLength(3)
    expect(screen.getByTestId('tick-readout').textContent).toBe('2026-10-02 · high 866 · close -20 · low -870')
    expect(c.container.querySelectorAll('rect')).toHaveLength(2)
  })
})
