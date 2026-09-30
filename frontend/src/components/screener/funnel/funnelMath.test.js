import { describe, it, expect } from 'vitest'
import {
  groupOf, accelDir, blockedAt, splitSetup, noteFor, isFlagged, freshness, netHighs,
  LIVE_SETUPS, PENDING_SETUPS,
} from './funnelMath'

const card = (t, o = {}) => ({ t, rs: 50, focus: false, tight: true, qn: 4, ...o })
const doc = {
  asof: '2026-09-29',
  setups: {
    pullback: { rows: [
      card('LOW', { rs: 60, focus: true }),
      card('HIGH', { rs: 98, focus: true }),
      card('TIE_B', { rs: 90, focus: true }),
      card('TIE_A', { rs: 90, focus: true }),
      card('GATED', { rs: 99, tight: false, qn: 4 }),
      card('THREE', { rs: 95, qn: 3 }),
    ] },
    ep: { rows: [] },
  },
  notes: {
    HIGH: { zh: '组在加速（+39.5）。', en: 'Group accelerating (+39.5).' },
    ONLYZH: { zh: '只有中文。', en: '' },
    BAD: { zh: '⚠️ 两个读数互相矛盾。', en: '⚠️ Readings contradict.' },
  },
}

describe('splitSetup', () => {
  it('keeps the file’s focus flag and orders by RS, ticker breaking ties', () => {
    const s = splitSetup(doc, 'pullback')
    expect(s.focus.map((r) => r.t)).toEqual(['HIGH', 'TIE_A', 'TIE_B', 'LOW'])
    expect(s.other.map((r) => r.t)).toEqual(['GATED', 'THREE'])
    expect(s.total).toBe(6)
  })
  it('does not promote a high-RS name the file left out of Focus', () => {
    expect(splitSetup(doc, 'pullback').focus.some((r) => r.t === 'GATED')).toBe(false)
  })
  it('reads an empty or missing setup as empty, not as an error', () => {
    expect(splitSetup(doc, 'ep')).toEqual({ focus: [], other: [], total: 0 })
    expect(splitSetup(doc, 'vcp')).toEqual({ focus: [], other: [], total: 0 })
    expect(splitSetup(null, 'pullback').total).toBe(0)
  })
})

describe('groupOf', () => {
  it('prefers the theme and falls back to the industry, saying which', () => {
    expect(groupOf({ theme: { name: 'Memory & Storage' }, ind: { name: 'Hardware' } }))
      .toMatchObject({ name: 'Memory & Storage', kind: 'theme' })
    expect(groupOf({ theme: null, ind: { name: 'Oil & Gas Midstream' } }))
      .toMatchObject({ name: 'Oil & Gas Midstream', kind: 'industry' })
    expect(groupOf({ theme: null, ind: null })).toBeNull()
  })
})

describe('accelDir', () => {
  it('reads the sign', () => {
    expect(accelDir(39.5)).toBe('up')
    expect(accelDir(-26.5)).toBe('down')
    expect(accelDir(0)).toBe('flat')
    expect(accelDir(null)).toBe('flat')
  })
})

describe('blockedAt', () => {
  it('names the gate that stopped a name', () => {
    expect(blockedAt(card('X', { tight: false }))).toEqual({ layer: 'gate' })
    expect(blockedAt(card('X', { qn: 3 }))).toEqual({ layer: 's111', passed: 3 })
  })
})

describe('noteFor', () => {
  it('returns the sentence in the reader’s language', () => {
    expect(noteFor(doc, 'HIGH', 'zh')).toBe('组在加速（+39.5）。')
    expect(noteFor(doc, 'HIGH', 'en')).toBe('Group accelerating (+39.5).')
  })
  it('never falls back to the other language — one language per screen', () => {
    expect(noteFor(doc, 'ONLYZH', 'en')).toBeNull()
    expect(noteFor(doc, 'MISSING', 'zh')).toBeNull()
  })
  it('spots the contradiction marker', () => {
    expect(isFlagged(noteFor(doc, 'BAD', 'zh'))).toBe(true)
    expect(isFlagged(noteFor(doc, 'HIGH', 'zh'))).toBe(false)
  })
})

describe('freshness', () => {
  it('compares the file’s session with the site’s latest session', () => {
    expect(freshness('2026-09-29', '2026-09-29')).toBe('fresh')
    expect(freshness('2026-09-29', '2026-09-30')).toBe('stale')
    expect(freshness('2026-09-30', '2026-09-29')).toBe('ahead')
    expect(freshness(null, '2026-09-30')).toBe('unknown')
  })
})

describe('netHighs', () => {
  it('is highs minus lows, or null when either is missing', () => {
    expect(netHighs({ nh: 7, nl: 20 })).toBe(-13)
    expect(netHighs({ nh: 7 })).toBeNull()
  })
})

describe('the setup list', () => {
  it('draws three live and twelve pending — the fifteen scanners of §5.5', () => {
    expect(LIVE_SETUPS).toHaveLength(3)
    expect(PENDING_SETUPS).toHaveLength(12)
    expect(new Set([...LIVE_SETUPS, ...PENDING_SETUPS]).size).toBe(15)
  })
})
