import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import ThemeBoardCard from './ThemeBoardCard'
import { resetThemeBoardCache } from '../../hooks/useThemeBoard'

/**
 * theme_board.json hasn't run through the pipeline yet on this branch
 * (proxy_board.py ships in the same PR but the nightly cron hasn't fired),
 * so this mounts on a fixture shaped like `build()`'s real output — same
 * keys, same 2026-09-21 Cloud Software case the pipeline docstring cites.
 */
const FIXTURE = {
  asof: '2026-09-23',
  members_asof: '2026-09-23',
  benchmark: 'SPY',
  bucket_days: 14,
  parallel_until: '2026-10-08',
  counts: { leading: 1, weakening: 1, improving: 1, lagging: 1 },
  themes: [
    {
      theme: 'Cloud Software', etf: 'WCLD', state: 'leading', state_prev: 'weakening',
      rs: 4.2, momentum: 1.1,
      buckets: [{ weeks: 2, from: '2026-09-09', to: '2026-09-23', rs: 4.2, momentum: 1.1, state: 'leading' }],
      members: { leading: 27, weakening: 20, improving: 15, lagging: 8, 'n/a': 0 },
      member_count: 70,
    },
    {
      theme: 'Semiconductors', etf: 'SOXX', state: 'weakening', state_prev: 'weakening',
      rs: 2.1, momentum: -0.6,
      buckets: [{ weeks: 2, from: '2026-09-09', to: '2026-09-23', rs: 2.1, momentum: -0.6, state: 'weakening' }],
      members: { leading: 10, weakening: 18, improving: 6, lagging: 4, 'n/a': 0 },
      member_count: 38,
    },
    {
      theme: 'Regional Banks', etf: 'KRE', state: 'improving', state_prev: 'lagging',
      rs: -1.3, momentum: 2.0,
      buckets: [{ weeks: 2, from: '2026-09-09', to: '2026-09-23', rs: -1.3, momentum: 2.0, state: 'improving' }],
      members: { leading: 3, weakening: 2, improving: 30, lagging: 15, 'n/a': 1 },
      member_count: 51,
    },
    {
      theme: 'Tobacco Redux', etf: 'NOPROXY', state: 'lagging', state_prev: null,
      rs: -6.4, momentum: -3.2,
      buckets: [{ weeks: 2, from: '2026-09-09', to: '2026-09-23', rs: -6.4, momentum: -3.2, state: 'lagging' }],
      members: { leading: 0, weakening: 1, improving: 0, lagging: 12, 'n/a': 0 },
      member_count: 13,
    },
  ],
}

const withFetch = (payload) => {
  resetThemeBoardCache()
  return vi.stubGlobal('fetch', () => Promise.resolve({ ok: !!payload, json: () => Promise.resolve(payload) }))
}

describe('ThemeBoardCard — Proxy Board (T-0924-90)', () => {
  it('mounts on a real-shaped payload without throwing', async () => {
    withFetch(FIXTURE)
    expect(() => render(<ThemeBoardCard />)).not.toThrow()
    expect(await screen.findByText('Cloud Software')).toBeTruthy()
  })

  it('shows the was-marker and changed tag during the parallel window', async () => {
    withFetch(FIXTURE)
    render(<ThemeBoardCard />)
    await screen.findByText('Cloud Software')
    expect(screen.getAllByText('was').length).toBeGreaterThan(0)
    // Cloud Software (leading←weakening) and Regional Banks (improving←lagging) flipped;
    // Semiconductors stayed weakening and Tobacco Redux has no state_prev at all.
    expect(screen.getAllByText('changed').length).toBe(2)
  })

  it('renders the member distribution count for every row, not collapsed', async () => {
    withFetch(FIXTURE)
    render(<ThemeBoardCard />)
    await screen.findByText('Cloud Software')
    expect(screen.getByText('70')).toBeTruthy()
    expect(screen.getByText('38')).toBeTruthy()
    expect(screen.getByText('51')).toBeTruthy()
    expect(screen.getByText('13')).toBeTruthy()
  })

  it('falls back to a plain sentence when the payload fails to load', async () => {
    withFetch(null)
    render(<ThemeBoardCard />)
    expect(await screen.findByText(/did not load/)).toBeTruthy()
  })
})
