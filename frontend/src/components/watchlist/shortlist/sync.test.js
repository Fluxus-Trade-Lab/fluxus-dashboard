import { describe, it, expect, vi, beforeEach } from 'vitest'
import { credentials, record, pushOne, state } from './sync'

/**
 * The half of the loop that leaves this machine.
 *
 * Two things have to hold or the learning set is worse than empty. A veto must
 * never ride `sync_all` — that call replaces every tab in the sheet with this
 * browser's copy, so one click could revert a portfolio edit made in another
 * tab. And a push that did not land must not look like one that did: the GAS
 * action does not exist yet, and an unknown action comes back 200.
 */
beforeEach(() => { localStorage.clear(); vi.restoreAllMocks() })

const creds = { url: 'https://script.example/exec', token: 'tk' }

describe('credentials', () => {
  it('reads the portfolio store, and refuses a half-configured one', () => {
    expect(credentials()).toBeNull()
    localStorage.setItem('portfolio-v4', JSON.stringify({ gasUrl: 'u' }))
    expect(credentials()).toBeNull()
    localStorage.setItem('portfolio-v4', JSON.stringify({ gasUrl: 'u', syncToken: 't' }))
    expect(credentials()).toEqual({ url: 'u', token: 't' })
  })

  it('survives a corrupt store rather than taking the page down', () => {
    localStorage.setItem('portfolio-v4', '{not json')
    expect(credentials()).toBeNull()
  })
})

describe('a record', () => {
  it('always carries the two fields the server needs to be idempotent', () => {
    const r = record('2026-08-19', 'MRNA', { mark: 'vetoed' }, 'burning', { close: 174 })
    expect(r.ticker).toBe('MRNA')
    expect(r.added_date).toBe('2026-08-19')
  })

  it('calls a note with no verdict `noted`, not a veto', () => {
    expect(record('d', 'T', { note: '想说句话' }).status).toBe('noted')
  })
})

describe('pushing one', () => {
  it('sends its own action and nothing else — never sync_all', async () => {
    const spy = vi.fn(async () => ({ ok: true, json: async () => ({ ok: true }) }))
    globalThis.fetch = spy
    await pushOne(record('2026-08-19', 'MRNA', { mark: 'vetoed' }), creds)
    const body = JSON.parse(spy.mock.calls[0][1].body)
    expect(body.action).toBe('shortlist_upsert')
    expect(body).not.toHaveProperty('stockTrades')
    expect(body).not.toHaveProperty('optionsTrades')
    expect(JSON.stringify(body)).not.toContain('sync_all')
  })

  it('does not call out at all without credentials', async () => {
    const spy = vi.fn()
    globalThis.fetch = spy
    expect(await pushOne(record('d', 'T', {}), null)).toEqual({ ok: false, error: 'no-credentials' })
    expect(spy).not.toHaveBeenCalled()
  })

  it('treats a 200 that does not say ok as a failure', async () => {
    // this is what GAS returns today for an action it has never heard of
    globalThis.fetch = async () => ({ ok: true, json: async () => ({ result: 'unknown action' }) })
    expect(await pushOne(record('d', 'T', {}), creds))
      .toEqual({ ok: false, error: 'action-not-implemented' })
  })

  it('reports a transport failure instead of throwing into the page', async () => {
    globalThis.fetch = async () => { throw new Error('offline') }
    expect(await pushOne(record('d', 'T', {}), creds)).toEqual({ ok: false, error: 'offline' })
  })
})

describe('what the page says', () => {
  it('keeps three states apart', () => {
    expect(state({ hasCreds: false, unsent: 3 }).kind).toBe('off')
    expect(state({ hasCreds: true, unsent: 3, lastError: 'x' }).kind).toBe('pending')
    expect(state({ hasCreds: true, unsent: 0 }).kind).toBe('synced')
  })

  it('does not blame the network when no sheet was ever configured', () => {
    expect(state({ hasCreds: false, unsent: 3, lastError: 'boom' }).lastError).toBeNull()
  })
})

/**
 * A missing endpoint must not be hammered.
 *
 * The flush is called from an effect, so anything that changes identity every
 * render fires it every render. That happened: `rows` was rebuilt inline and
 * `day` was minted by `|| {}`, so a failing push retried in a loop — the exact
 * behaviour this module's own comment promises not to have. The guard is a
 * signature of the pending set: a failure is not retried until that set
 * actually changes.
 */
describe('backing off a failure', () => {
  it('retries only when there is something new to send', async () => {
    localStorage.setItem('portfolio-v4',
      JSON.stringify({ gasUrl: 'https://x/exec', syncToken: 't' }))
    let calls = 0
    globalThis.fetch = async () => { calls += 1; return { ok: true, json: async () => ({}) } }
    const { flush, setMark } = await import('./ShortListPage')

    setMark('2026-08-19', 'AAA', 'vetoed')
    await flush('2026-08-19')
    expect(calls).toBe(1)

    await flush('2026-08-19')          // same pending set, still failing
    await flush('2026-08-19')
    expect(calls, 'a failure must not be retried on an unchanged set').toBe(1)

    setMark('2026-08-19', 'BBB', 'starred')   // something new
    await flush('2026-08-19')
    expect(calls).toBe(2)
  })
})

/**
 * A record that reached the sheet must stay reached.
 *
 * The success stamp went through the same writer as a mark, and that writer
 * cleared `syncedAt` on every write — so a successful push immediately marked
 * itself unsent, the effect saw an unsent record, and pushed again. Forever.
 * The browser found it by freezing; the tests above did not, because they all
 * stubbed a FAILING endpoint and never exercised the success path twice.
 */
describe('after a push lands', () => {
  const configured = () => localStorage.setItem('portfolio-v4',
    JSON.stringify({ gasUrl: 'https://x/exec', syncToken: 't' }))
  const counting = () => { let n = 0
    globalThis.fetch = async () => { n += 1; return { ok: true, json: async () => ({ ok: true }) } }
    return () => n }

  it('does not send the same record again', async () => {
    configured(); const calls = counting(); vi.resetModules()
    const { flush, setMark } = await import('./ShortListPage')
    setMark('2026-08-19', 'AAA', 'vetoed')
    await flush('2026-08-19')
    expect(calls()).toBe(1)
    await flush('2026-08-19')
    await flush('2026-08-19')
    expect(calls(), 'a synced record must not be resent').toBe(1)
  })

  it('sends again when the note on a synced record changes', async () => {
    configured(); const calls = counting(); vi.resetModules()
    const { flush, setMark, setNote } = await import('./ShortListPage')
    setMark('2026-08-20', 'BBB', 'vetoed')
    await flush('2026-08-20')
    setNote('2026-08-20', 'BBB', '改了主意的理由')
    await flush('2026-08-20')
    expect(calls()).toBe(2)
  })
})
