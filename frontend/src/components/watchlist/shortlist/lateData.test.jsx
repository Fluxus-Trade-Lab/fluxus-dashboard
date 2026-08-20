import { describe, it, expect, vi, beforeEach } from 'vitest'
import { act, render } from '@testing-library/react'

/**
 * The page must survive its own data arriving late.
 *
 * This crashed twice in one day, the same way both times: hooks below an early
 * return, a file that resolves a tick after the first paint, and a second render
 * running more hooks than the first. Every other test passed through both
 * incidents, because none of them mounted this page before its fetch settled —
 * which is precisely the sequence a real browser always performs.
 *
 * So this test IS that sequence: mount with nothing, let the fetch land, assert
 * the page is still standing. It is not about hooks; it is about the only
 * ordering that ever happens in production.
 */
beforeEach(() => { localStorage.clear(); vi.restoreAllMocks() })

const DOC = {
  date: '2026-08-19',
  seats: [{ seat: 'burning', ticker: 'AAA', why: 'heat 第 1 名' },
          { seat: 'entry', ticker: null, why: '今日无 EP' }],
  cards: [{ ticker: 'AAA', source: 'auto', seat: 'burning', group: 'G', state: 'Leading',
            readings: { close: 10, change_pct: 0.05, rs_1m: 90 },
            heat: { rank: 1, score: 9 }, verdict: '水域✓', marks: [], panels: [], events: [],
            flags: {}, series: null }],
  legend: { EP: '≥10%×量≥3×' },
}

/** resolve on a later TASK, so the first render genuinely sees nothing —
 *  a microtask would already be flushed by the time `act` returns, and the
 *  whole point is the gap a real network leaves. */
const later = (v) => new Promise((r) => setTimeout(() => r(v), 5))
const lateFetch = (payload) => {
  globalThis.fetch = (url) => String(url).includes('shortlist.json')
    ? later({ ok: true, json: async () => payload })
    : later({ ok: false })
}

describe('ShortListPage mounting before its file lands', () => {
  it('renders nothing, then the page, without tearing down', async () => {
    lateFetch(DOC)
    const { default: ShortListPage } = await import('./ShortListPage')
    let c
    await act(async () => { c = render(<ShortListPage />) })
    expect(c.container.textContent).toBe('')              // the file has not landed
    await act(async () => { await new Promise((r) => setTimeout(r, 20)) })
    const t = c.container.textContent
    expect(t).toContain('2026-08-19')
    expect(t).toContain('今日六席')
    expect(t).toContain('这一席今天没有名字')             // the empty seat still drawn
  })

  it('says the file is absent rather than rendering an empty shell', async () => {
    globalThis.fetch = () => later({ ok: false })
    vi.resetModules()
    const { default: ShortListPage } = await import('./ShortListPage')
    let c
    await act(async () => { c = render(<ShortListPage />) })
    await act(async () => { await new Promise((r) => setTimeout(r, 20)) })
    expect(c.container.textContent).toContain('shortlist.json 还没有')
  })
})
