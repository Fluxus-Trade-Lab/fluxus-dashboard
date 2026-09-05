import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import PowerTrend from './PowerTrend'

/**
 * Guards the one thing the page must never get wrong again: the section headed
 * "Power Trend" shows Mike Webster's conditions, and our own MA checks live
 * under a heading that does not claim to be his.
 */

const signals = {
  SPY: {
    power_trend: {
      low_gt_ema21_10d: true,
      ema21_gt_sma50_5d: true,
      sma50_rising: true,
      close_gt_open: false,
      is_power_trend: true,
    },
    ma_structure: { '3d_gt_50sma': true, '3d_gt_200sma': true, '50sma_gt_200sma': false },
  },
}

describe('PowerTrend', () => {
  it('lists Webster’s four conditions', () => {
    render(<PowerTrend signals={signals} />)
    for (const label of [
      'Low > 21 EMA (10d)', '21 EMA > 50 SMA (5d)', '50 SMA rising', 'Close > open',
    ]) {
      expect(screen.getByText(label)).toBeTruthy()
    }
  })

  it('shows the ON/OFF state, which is not the conjunction of the checks', () => {
    // close_gt_open is false above, yet the trend is on -- exactly the case a
    // daily recompute would render wrong.
    render(<PowerTrend signals={signals} />)
    expect(screen.getByText('ON')).toBeTruthy()
  })

  it('does not show the old non-standard checks as Power Trend rows', () => {
    render(<PowerTrend signals={signals} />)
    expect(screen.queryByText('Close > 20 SMA (3d)')).toBeNull()
    expect(screen.queryByText('20 SMA > 50 SMA')).toBeNull()
  })

  it('keeps our own MA checks under their own heading', () => {
    render(<PowerTrend signals={signals} />)
    expect(screen.getByText('MA Structure')).toBeTruthy()
    expect(screen.getByText('Close > 50 SMA (3d)')).toBeTruthy()
  })

  it('renders nothing without signals', () => {
    const { container } = render(<PowerTrend signals={null} />)
    expect(container.firstChild).toBeNull()
  })
})
