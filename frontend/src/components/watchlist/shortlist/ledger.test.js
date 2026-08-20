import { describe, it, expect } from 'vitest'
import { buildLedger, tally } from './ledger'

/**
 * What a veto-only log cannot answer.
 *
 * 在烧 fields a name every day; 入场 is empty on any day without an EP. Count
 * only the vetoes and the daily seat wins the "most rejected" title for showing
 * up. These tests pin the two rows that make the question answerable — the
 * seat that was seen and not acted on, and the seat that had nobody to field —
 * and pin them apart, because they are different denominators.
 */
const doc = {
  date: '2026-08-19',
  seats: [
    { seat: 'burning', ticker: 'CBZ', why: 'heat 第 1 名' },
    { seat: 'entry', ticker: null, why: '今日无 EP' },
    { seat: 'coiling', ticker: 'KMX', why: 'VCS 最高' },
  ],
  cards: [
    { ticker: 'CBZ', source: 'auto', readings: { close: 54.87, rs_1m: 96, vcs: 79.9 } },
    { ticker: 'KMX', source: 'auto', readings: { close: 58.95, rs_1m: 70 } },
    { ticker: 'NVDA', source: 'manual', readings: { close: 180 } },
  ],
}

describe('the daily ledger', () => {
  it('writes a row for every seat, marked or not', () => {
    const rows = buildLedger(doc, { CBZ: 'vetoed' })
    expect(rows.filter((r) => r.seat !== 'manual')).toHaveLength(3)
  })

  it('records a seat that was seen and not acted on as ignored, not as absent', () => {
    const rows = buildLedger(doc, { CBZ: 'vetoed' })
    const kmx = rows.find((r) => r.seat === 'coiling')
    expect(kmx.outcome).toBe('ignored')
    expect(kmx.shown).toBe(true)
  })

  it('keeps an empty seat out of the shown denominator', () => {
    const rows = buildLedger(doc, {})
    const entry = rows.find((r) => r.seat === 'entry')
    expect(entry.outcome).toBe('empty')
    expect(entry.shown).toBe(false)
    expect(entry.ticker).toBeNull()
    // and it keeps the reason the seat gave, so a run of empties can be read
    expect(entry.why).toBe('今日无 EP')
  })

  it('counts the two denominators apart', () => {
    const t = tally(buildLedger(doc, { CBZ: 'vetoed' }))
    expect(t).toMatchObject({ vetoed: 1, starred: 0, ignored: 2, empty: 1, shown: 3, seats: 3 })
    // 1 of 2 auto names shown was vetoed — the empty seat is not in that ratio,
    // and neither is the manual name
    const auto = buildLedger(doc, { CBZ: 'vetoed' }).filter((r) => r.seat !== 'manual' && r.shown)
    expect(auto.filter((r) => r.outcome === 'vetoed').length / auto.length).toBe(0.5)
  })

  it('keeps a manual name out of any seat rate', () => {
    const rows = buildLedger(doc, { NVDA: 'starred' })
    const manual = rows.filter((r) => r.seat === 'manual')
    expect(manual).toHaveLength(1)
    expect(manual[0].outcome).toBe('starred')
    expect(tally(rows).seats).toBe(3)
  })

  it('omits a field the payload never carried rather than calling it null', () => {
    const rows = buildLedger(doc, {})
    const kmx = rows.find((r) => r.ticker === 'KMX')
    expect('vcs' in kmx.readings).toBe(false)   // KMX has no vcs in this fixture
    expect(rows.find((r) => r.ticker === 'CBZ').readings.vcs).toBe(79.9)
  })

  it('returns nothing rather than throwing before the file arrives', () => {
    expect(buildLedger(null, {})).toEqual([])
  })
})
