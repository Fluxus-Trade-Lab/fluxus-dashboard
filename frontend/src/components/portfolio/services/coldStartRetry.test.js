import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { pullFromSheets } from './sheetsSync'

/**
 * The red ✕ that was never a broken sync.
 *
 * Andy reported the Portfolio header stuck on an error mark. The data side
 * traced it (2026-08-24, DATA_CONTRACTS §七) and the sync was fine the whole
 * time: the first pull of the day boots the Apps Script container, overruns
 * the 15s budget, sets syncStatus='error' — and then nothing ever clears it,
 * because clearing it takes a push and a push takes a data change.
 *
 * So the retry is not optimism. The first request pays for the cold start; the
 * second one lands on a container that is already warm.
 */
const OK = { ok: true, stockTrades: [1, 2], optionsTrades: [], meta: {} }
const abort = () => Object.assign(new Error('aborted'), { name: 'AbortError' })

let calls
beforeEach(() => { calls = 0 })
afterEach(() => { vi.unstubAllGlobals() })

const stub = (fn) => vi.stubGlobal('fetch', (...a) => { calls += 1; return fn(...a) })

describe('pullFromSheets — cold-start retry', () => {
  it('retries once when the first attempt times out, and returns the second answer', async () => {
    stub(() => (calls === 1
      ? Promise.reject(abort())
      : Promise.resolve({ ok: true, json: async () => OK })))
    const r = await pullFromSheets('https://x', 't', { retryOnTimeout: true })
    expect(calls).toBe(2)
    expect(r.ok).toBe(true)
    expect(r.stockTrades).toHaveLength(2)
  })

  it('retries ONCE, not until it works — two timeouts still report Timeout', async () => {
    stub(() => Promise.reject(abort()))
    const r = await pullFromSheets('https://x', 't', { retryOnTimeout: true })
    expect(calls).toBe(2)
    expect(r).toEqual({ ok: false, error: 'Timeout' })
  })

  it('does not retry a real answer — an HTTP error is information, not a cold start', async () => {
    stub(() => Promise.resolve({ ok: false, status: 401 }))
    const r = await pullFromSheets('https://x', 't', { retryOnTimeout: true })
    expect(calls).toBe(1)
    expect(r.error).toBe('HTTP 401')
  })

  it('does not retry a rejected token either', async () => {
    stub(() => Promise.resolve({ ok: true, json: async () => ({ ok: false, error: 'bad token' }) }))
    const r = await pullFromSheets('https://x', 't', { retryOnTimeout: true })
    expect(calls).toBe(1)
    expect(r.error).toBe('bad token')
  })

  it('is opt-in: every other caller keeps single-shot behaviour', async () => {
    stub(() => Promise.reject(abort()))
    const r = await pullFromSheets('https://x', 't')
    expect(calls).toBe(1)
    expect(r.error).toBe('Timeout')
  })

  it('does not retry a success', async () => {
    stub(() => Promise.resolve({ ok: true, json: async () => OK }))
    await pullFromSheets('https://x', 't', { retryOnTimeout: true })
    expect(calls).toBe(1)
  })
})
