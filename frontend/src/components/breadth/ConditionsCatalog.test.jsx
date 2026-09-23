import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ConditionsCatalog from './ConditionsCatalog'

describe('ConditionsCatalog', () => {
  it('lists all nine board rows and all fifteen conditions', () => {
    render(<ConditionsCatalog />)
    ;['damage', 'selling pressure', 'breadth', 'trend', 'thrust', 'extremes',
      'index repair', 'confirmation', 'rates'].forEach((key) => {
      expect(screen.getByText(key)).toBeInTheDocument()
    })
    ;['ratio_5d', 'ratio_10d', 't2108', 'pct_above_200sma', 'pct_above_50sma',
      'pct_above_20sma', 'mcclellan_osc', 'net_advances', 'nh_nl', 'qtr_spread',
      'spread_13_34', 'net_4pct', 'px_1m', 'px_3m', 'px_1y'].forEach((key) => {
      expect(screen.getByText(key)).toBeInTheDocument()
    })
  })

  it('tags every row standard, mixed or ours, never leaves one blank', () => {
    render(<ConditionsCatalog />)
    // 9 board + 15 conditions = 24 rows, one status badge each.
    expect(screen.getAllByTestId('status-badge').length).toBe(24)
  })
})
