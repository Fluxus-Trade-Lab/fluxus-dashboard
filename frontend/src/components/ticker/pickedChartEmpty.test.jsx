import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/react'

// Measured-and-empty and not-measured are different claims; the card used to
// print "not measured" for both. Moglen's TML is strict, so empty nights happen.
let state
vi.mock('../../hooks/useChartPick', () => ({ useChartPick: () => state }))
vi.mock('./TickerChart', () => ({ default: () => null }))

const base = { symbol: null, isDefault: true, names: [], pick: () => {} }

describe('PickedChart empty states', () => {
  it('measured, nobody found → "found nobody"', async () => {
    state = { ...base, panel: { measured: true, tickers: [] } }
    const { default: PickedChart } = await import('./PickedChart')
    const { container } = render(<PickedChart />)
    expect(container.textContent).toContain('found')
    expect(container.textContent).not.toContain('not measured')
  })
  it('not measured → "not measured"', async () => {
    state = { ...base, panel: { measured: false } }
    const { default: PickedChart } = await import('./PickedChart')
    const { container } = render(<PickedChart />)
    expect(container.textContent).toContain('not measured')
  })
})
