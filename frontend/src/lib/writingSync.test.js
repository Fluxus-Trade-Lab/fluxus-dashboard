/**
 * The pure half of the Sheet mirror: how entries become Meta rows, how they
 * come back, and which side wins when both have an opinion.
 *
 * The network half is not mocked here — what is worth pinning is the shape,
 * because a wrong split writes a month into the wrong cell and nothing errors.
 */
import { beforeEach, describe, expect, it } from 'vitest'
import { fromMeta, metaKey, monthOf, toMetaRows } from './writingSync'
import { loadEntries, mergeRemote, saveEntry } from './writingStore'

describe('meta rows', () => {
  it('splits entries into one row per month', () => {
    const rows = toMetaRows('trading-recap', {
      '2026-08-17': 'a', '2026-08-03': 'b', '2026-07-30': 'c',
    })
    expect(Object.keys(rows).sort()).toEqual([
      'writing:trading-recap:2026-07', 'writing:trading-recap:2026-08',
    ])
    expect(rows['writing:trading-recap:2026-08']).toEqual({
      '2026-08-17': 'a', '2026-08-03': 'b',
    })
  })

  it('keys are stable and readable in the sheet', () => {
    expect(metaKey('founders-weekly', monthOf('2026-08-17'))).toBe(
      'writing:founders-weekly:2026-08')
  })

  it('round-trips through the meta object', () => {
    const entries = { '2026-08-17': 'a', '2026-07-30': 'c' }
    const meta = Object.fromEntries(
      Object.entries(toMetaRows('trading-recap', entries))
        .map(([k, v]) => [k, JSON.stringify(v)]))     // the sheet stores strings
    expect(fromMeta(meta)['trading-recap']).toEqual(entries)
  })

  it('ignores meta keys that are not ours', () => {
    expect(fromMeta({ startingCapital: '1000000', optionsCapital: '0' })).toEqual({})
  })

  it('survives a corrupt cell without losing the other months', () => {
    const meta = {
      'writing:trading-recap:2026-08': '{"2026-08-17":"kept"}',
      'writing:trading-recap:2026-07': '{not json',
    }
    expect(fromMeta(meta)['trading-recap']).toEqual({ '2026-08-17': 'kept' })
  })

  it('structured records ride the same path as text', () => {
    const rec = { '2026-08-17': { answers: { rules: 'Yes' }, note: 'n' } }
    const meta = Object.fromEntries(
      Object.entries(toMetaRows('premarket-checklist', rec))
        .map(([k, v]) => [k, JSON.stringify(v)]))
    expect(fromMeta(meta)['premarket-checklist']).toEqual(rec)
  })
})

describe('merge on pull', () => {
  beforeEach(() => localStorage.clear())

  it('takes the sheet for past days', () => {
    saveEntry('k', '2026-08-10', 'stale local')
    mergeRemote('k', { '2026-08-10': 'newer remote' }, '2026-08-17')
    expect(loadEntries('k')['2026-08-10']).toBe('newer remote')
  })

  it('keeps the local copy of the day being written', () => {
    saveEntry('k', '2026-08-17', 'what I am typing')
    mergeRemote('k', { '2026-08-17': 'what the sheet had' }, '2026-08-17')
    expect(loadEntries('k')['2026-08-17']).toBe('what I am typing')
  })

  it('accepts today from the sheet when there is nothing local', () => {
    mergeRemote('k', { '2026-08-17': 'written on the other machine' }, '2026-08-17')
    expect(loadEntries('k')['2026-08-17']).toBe('written on the other machine')
  })

  it('never deletes a local day the sheet has not seen', () => {
    saveEntry('k', '2026-08-16', 'only here so far')
    mergeRemote('k', { '2026-08-10': 'x' }, '2026-08-17')
    expect(loadEntries('k')['2026-08-16']).toBe('only here so far')
  })
})
