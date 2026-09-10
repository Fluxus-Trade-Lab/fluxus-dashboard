import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { Bar, DivergingBars, RankedBars } from './MiniBars'

describe('Bar', () => {
  it('fills proportionally to max and clamps to [0,100]', () => {
    const { container, rerender } = render(<Bar label="Avg Trim Size" value={25} max={50} />)
    const fill = container.querySelector('.h-\\[6px\\] > div')
    expect(fill.style.width).toBe('50%')

    rerender(<Bar label="x" value={999} max={50} />)
    expect(container.querySelector('.h-\\[6px\\] > div').style.width).toBe('100%')

    rerender(<Bar label="x" value={-10} max={50} />)
    expect(container.querySelector('.h-\\[6px\\] > div').style.width).toBe('0%')
  })

  it('places the target tick at its own fraction of max, not of the bar', () => {
    const { container } = render(<Bar label="x" value={10} max={40} target={20} />)
    const tick = container.querySelector('[title="target 20%"]')
    expect(tick.style.left).toBe('50%') // 20/40
  })

  it('omits the tick when no target is given', () => {
    const { container } = render(<Bar label="x" value={10} max={40} />)
    expect(container.querySelector('[title]')).toBeNull()
  })
})

describe('DivergingBars', () => {
  it('renders nothing for an empty or missing row set', () => {
    expect(render(<DivergingBars rows={[]} />).container.firstChild).toBeNull()
    expect(render(<DivergingBars rows={null} />).container.firstChild).toBeNull()
  })

  it('grows a positive bar to the right of the zero line, a negative one to the left', () => {
    const rows = [{ key: 'AAA', value: 50 }, { key: 'BBB', value: -50 }]
    const { container } = render(<DivergingBars rows={rows} max={100} />)
    const fills = container.querySelectorAll('.rounded-sm')
    expect(fills[0].style.left).toBe('50%')   // AAA: +50/100 → starts at centre, grows right
    expect(fills[0].style.width).toBe('25%')  // half of |0.5| * 50
    expect(fills[1].style.left).toBe('25%')   // BBB: -50/100 → starts left of centre
    expect(fills[1].style.width).toBe('25%')
  })

  it('derives max from the data when none is given, so no row ever overflows its own row', () => {
    const rows = [{ key: 'A', value: 10 }, { key: 'B', value: -30 }]
    const { container } = render(<DivergingBars rows={rows} />)
    const fills = container.querySelectorAll('.rounded-sm')
    // widest row (|30|) reaches exactly to the row's own edge (50%)
    expect(fills[1].style.width).toBe('50%')
  })

  it('formats the printed value with the caller\'s formatter', () => {
    const rows = [{ key: 'AAA', value: -1234 }]
    const { getByText } = render(
      <DivergingBars rows={rows} formatValue={(v) => `$${v}`} />,
    )
    expect(getByText('$-1234')).toBeInTheDocument()
  })
})

describe('RankedBars', () => {
  it('renders nothing for an empty or missing row set', () => {
    expect(render(<RankedBars rows={[]} />).container.firstChild).toBeNull()
    expect(render(<RankedBars rows={null} />).container.firstChild).toBeNull()
  })

  it('fills a fraction of max and clamps a negative value to zero width', () => {
    const rows = [{ key: 'AAA', value: 30 }, { key: 'BBB', value: -5 }]
    const { container } = render(<RankedBars rows={rows} max={60} />)
    const fills = container.querySelectorAll('.rounded-sm > .rounded-sm')
    expect(fills[0].style.width).toBe('50%')
    expect(fills[1].style.width).toBe('0%')
  })

  it('picks the bar colour per row through colorOf', () => {
    const rows = [{ key: 'AAA', value: 90 }, { key: 'BBB', value: 10 }]
    const { container } = render(
      <RankedBars rows={rows} max={100}
                  colorOf={(r) => (r.value > 50 ? 'var(--color-profit)' : 'var(--color-loss)')} />,
    )
    const fills = container.querySelectorAll('.rounded-sm > .rounded-sm')
    expect(fills[0].style.background).toBe('var(--color-profit)')
    expect(fills[1].style.background).toBe('var(--color-loss)')
  })
})
