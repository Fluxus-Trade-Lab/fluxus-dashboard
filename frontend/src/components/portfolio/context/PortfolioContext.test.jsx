import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { PortfolioProvider, usePortfolio } from './PortfolioContext'

/**
 * A nested provider must not open a second store.
 *
 * Each store pulls from Sheets on mount and runs its own debounced push, so two
 * on one page are two writers racing on the same rows — not merely duplicated
 * state. Several tabs mount their own provider (Analytics, Sizing, Risk,
 * Ticker), and the Review overview now puts one above them, so this is the
 * arrangement the app actually renders.
 */

const seen = []
function Probe({ tag }) {
  const ctx = usePortfolio()
  seen.push({ tag, ctx })
  return null
}

describe('PortfolioProvider', () => {
  it('hands a nested provider the store already above it', () => {
    seen.length = 0
    render(
      <PortfolioProvider>
        <Probe tag="outer" />
        <PortfolioProvider>
          <Probe tag="inner" />
        </PortfolioProvider>
      </PortfolioProvider>,
    )
    const outer = seen.find((s) => s.tag === 'outer')
    const inner = seen.find((s) => s.tag === 'inner')
    expect(outer).toBeTruthy()
    expect(inner).toBeTruthy()
    // Same store object, so the same reducer and the same sync effects.
    expect(inner.ctx.state).toBe(outer.ctx.state)
    expect(inner.ctx.dispatch).toBe(outer.ctx.dispatch)
  })

  it('still creates a store when there is none above it', () => {
    seen.length = 0
    render(<PortfolioProvider><Probe tag="only" /></PortfolioProvider>)
    expect(seen.find((s) => s.tag === 'only')?.ctx.state).toBeTruthy()
  })
})
