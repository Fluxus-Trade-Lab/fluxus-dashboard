import { describe, it, expect, afterEach } from 'vitest'
import { act, renderHook, cleanup } from '@testing-library/react'
import { useShortlist } from './useShortlist'

const KEY = 'page3-shortlist'

/**
 * "移出" on a name the Sheet pushed in did nothing you could see (Andy,
 * 2026-09-11). `manualCards` merges two lists — the tray (this hook) and
 * whatever `shortlist.json` carries as `source: 'manual'` — and `remove()`
 * only ever touched the first. The button deleted a name from a list the
 * name was never on.
 *
 * `remove` now always records the ticker in `dropped`, whether or not it was
 * in `names` — that is the suppression `manualCards`'s caller filters the
 * merged list through, since the Sheet-origin half has no local record for
 * `remove` to delete in the first place. `add` clears the ticker back out,
 * so re-adding the same name un-suppresses it.
 *
 * The store is a module-level singleton (see useShortlist.js's own comment on
 * why), so `freshHook` clears it before each test rather than trusting a
 * fresh import — the same reason `localStorage.clear()` alone is not enough.
 */
function freshHook() {
  const rendered = renderHook(() => useShortlist())
  act(() => rendered.result.current.clear())
  return rendered
}

describe('useShortlist — 移出', () => {
  afterEach(() => { cleanup(); localStorage.clear() })

  it('removes a tray-added name outright', () => {
    const { result } = freshHook()
    act(() => result.current.add('AAA'))
    expect(result.current.names.map((n) => n.ticker)).toContain('AAA')

    act(() => result.current.remove('AAA'))
    expect(result.current.names.map((n) => n.ticker)).toEqual([])
  })

  it('drops a name that was never in the tray — the Sheet-origin case', () => {
    const { result } = freshHook()
    // never added — this is a manual card `manualCards()` built from
    // shortlist.json's own `source: 'manual'` entries, not from the tray
    act(() => result.current.remove('BFLY'))
    expect(result.current.names).toEqual([])
    expect(result.current.dropped).toEqual(['BFLY'])
  })

  it('re-adding a dropped name clears the suppression', () => {
    const { result } = freshHook()
    act(() => result.current.remove('BFLY'))
    expect(result.current.dropped).toContain('BFLY')

    act(() => result.current.add('BFLY'))
    expect(result.current.dropped).not.toContain('BFLY')
    expect(result.current.names.map((n) => n.ticker)).toContain('BFLY')
  })

  it('persists dropped tickers to localStorage, not just tray names', () => {
    const { result } = freshHook()
    act(() => result.current.remove('USO'))
    const stored = JSON.parse(localStorage.getItem(KEY))
    expect(stored.dropped).toEqual(['USO'])
  })

  it('a drop with nothing else in the store still persists (does not clear)', () => {
    const { result } = freshHook()
    act(() => result.current.remove('GLD'))
    // names is empty, but dropped is not — the store must not be wiped
    expect(result.current.names).toEqual([])
    expect(localStorage.getItem(KEY)).not.toBeNull()
    expect(JSON.parse(localStorage.getItem(KEY)).dropped).toEqual(['GLD'])
  })
})
