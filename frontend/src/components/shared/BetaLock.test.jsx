import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import BetaLock from './BetaLock'

describe('BetaLock', () => {
  it('shows the Beta banner and keeps the wrapped content in the DOM (blurred, not removed)', () => {
    const { container, getByText } = render(
      <BetaLock label="Portfolio Review">
        <button>Real feature button</button>
      </BetaLock>
    )
    expect(getByText('Beta — opening soon')).toBeInTheDocument()
    expect(getByText('Portfolio Review')).toBeInTheDocument()
    // Content stays mounted (aria-hidden + blurred), it isn't torn down —
    // opening the section later needs no data refetch.
    expect(getByText('Real feature button')).toBeInTheDocument()
    expect(container.querySelector('[aria-hidden] button')).toBeTruthy()
  })

  it('works without a label — no member group gets named "who this is for"', () => {
    const { getByText, queryByText } = render(
      <BetaLock>
        <div>content</div>
      </BetaLock>
    )
    expect(getByText('Beta — opening soon')).toBeInTheDocument()
    expect(queryByText('undefined')).not.toBeInTheDocument()
  })
})
