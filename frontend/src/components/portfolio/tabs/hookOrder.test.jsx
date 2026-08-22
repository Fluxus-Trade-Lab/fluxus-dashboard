/**
 * Regression: tabs that early-return on an empty open-positions list must still
 * call every hook first. When a hook sits after the early return, React throws
 * "Rendered fewer hooks than expected" the moment openTrades flips between
 * empty and non-empty on a mounted component.
 *
 * Uses createElement rather than JSX — vitest.config.js sets no JSX runtime.
 */
import { describe, it, expect, vi } from 'vitest'
import { createElement as h } from 'react'
import { render } from '@testing-library/react'

vi.mock('../context/PortfolioContext', () => ({
  usePortfolio: () => ({ state: { privacyMode: false } }),
}))

import ExposureTab from './ExposureTab'
import RiskSection from '../../journal/analytics/RiskSection'

const trade = {
  id: 'a',
  ticker: 'AAPL',
  direction: 'long',
  entryDate: '2026-01-05',
  entryPrice: 200,
  originalQty: 50,
  currentQty: 50,
  stopPrice: 190,
  trims: [],
  lastPrice: 210,
  weight: 10,
  marketVal: 10500,
  totalPL: 500,
  totalReturnPct: 5,
}

describe('ExposureTab hook order', () => {
  it('survives empty → non-empty → empty without changing hook count', () => {
    const props = (openTrades) => ({
      openTrades,
      mergedHoldingsData: [],
      performanceData: [],
      capitalEfficiency: null,
    })

    const { rerender, container } = render(h(ExposureTab, props([])))
    expect(container.textContent).toContain('No open positions')

    rerender(h(ExposureTab, props([trade])))
    expect(container.textContent).toContain('AAPL')

    rerender(h(ExposureTab, props([])))
    expect(container.textContent).toContain('No open positions')
  })
})

describe('RiskSection hook order', () => {
  it('survives empty → non-empty → empty without changing hook count', () => {
    const props = (openTrades) => ({
      openTrades,
      enriched: [],
      heatData: { positions: [] },
      sectorData: [],
      dailyPrices: {},
      spyHistory: [],
      portfolioValue: 100000,
    })

    const { rerender, container } = render(h(RiskSection, props([])))
    expect(container.textContent).toContain('No open positions to analyze')

    rerender(h(RiskSection, props([trade])))
    expect(container.textContent).toContain('AAPL')

    rerender(h(RiskSection, props([])))
    expect(container.textContent).toContain('No open positions to analyze')
  })
})
