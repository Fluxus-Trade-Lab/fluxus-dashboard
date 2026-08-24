import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { act, render, screen } from '@testing-library/react'

/**
 * A successful Test Connection IS a successful sync.
 *
 * The second half of the same bug (2026-08-24, DATA_CONTRACTS §七). The panel
 * could report "connected, 367 trades" while the header kept the ✕ that a
 * morning cold start had lit, because the handler only ever set its own local
 * result. Nothing else clears that mark: clearing it takes a push, and a push
 * takes a data change, so the page can sit wrong all day while being right.
 */
const dispatch = vi.fn()
const state = { gasUrl: 'https://x', syncToken: 't', startingCapital: 100000 }
const testConnection = vi.fn()

vi.mock('./context/PortfolioContext', () => ({
  usePortfolio: () => ({ state, dispatch }),
}))
vi.mock('./services/sheetsSync', () => ({
  testConnection: (...a) => testConnection(...a),
  pullFromSheets: vi.fn(),
}))

const { default: SettingsPanel } = await import('./SettingsPanel')

const clickTest = async () => {
  const btn = [...document.querySelectorAll('button')]
    .find((b) => /test connection/i.test(b.textContent))
  await act(async () => { btn.click() })
  await act(async () => { await Promise.resolve() })
}

beforeEach(() => { dispatch.mockClear(); testConnection.mockReset() })
afterEach(() => { document.body.innerHTML = '' })

describe('Test Connection', () => {
  it('clears the sync mark when the test succeeds', async () => {
    testConnection.mockResolvedValue({ ok: true, stockTradeCount: 367, optionsTradeCount: 4 })
    render(<SettingsPanel onClose={() => {}} />)
    await clickTest()
    expect(dispatch).toHaveBeenCalledWith({ type: 'SET_SYNC_STATUS', status: 'success' })
    expect(screen.getByText(/367/)).toBeTruthy()
  })

  it('leaves the mark alone when the test fails — a failure is not new information', async () => {
    testConnection.mockResolvedValue({ ok: false, error: 'Timeout' })
    render(<SettingsPanel onClose={() => {}} />)
    await clickTest()
    expect(dispatch).not.toHaveBeenCalledWith(
      expect.objectContaining({ type: 'SET_SYNC_STATUS' }))
  })
})
