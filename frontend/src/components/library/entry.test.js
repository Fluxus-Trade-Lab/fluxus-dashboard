import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { toEntry, toEntries, slugOf, axisFor } from './entry'

/**
 * A cover comes off the article's own fields, and the axis off its own range.
 */
describe('the slug', () => {
  it('drops the page prefix so the URL does not say it twice', () => {
    expect(slugOf('offense_ep_mrna.json', 'offense')).toBe('ep_mrna')
    expect(toEntry({ name: 'offense_ep_mrna.json',
                     doc: { slug: 'offense_ep_mrna', page: 'offense', title: 'T' } },
                   'offense').slug).toBe('ep_mrna')
  })

  it('leaves a name that does not follow the convention addressable', () => {
    expect(slugOf('stray.json', 'offense')).toBe('stray')
    expect(toEntry({ name: 'stray.json', doc: { title: 'T' } }, 'offense').slug).toBe('stray')
  })
})

describe('a cover', () => {
  const doc = { title: 'EP（Episodic Pivot）', subtitle: '以 MRNA 为标本',
                summary: '一天之内改变定价前提的事件。', blocks: [{ type: 'p', text: 'x' }] }

  it('takes the fields written to be a cover', () => {
    const e = toEntry({ name: 'a.json', doc }, 'offense')
    expect(e.title).toBe('EP（Episodic Pivot）')
    expect(e.subtitle).toBe('以 MRNA 为标本')
    expect(e.summary).toBe('一天之内改变定价前提的事件。')
  })

  it('has art only when the chart actually carries bars', () => {
    expect(toEntry({ name: 'a.json', doc }, 'offense').chart).toBeNull()
    expect(toEntry({ name: 'a.json', doc: { ...doc, chart: { series: { c: [] } } } },
                   'offense').chart).toBeNull()
    expect(toEntry({ name: 'a.json', doc: { ...doc, chart: { series: { c: [1, 2] } } } },
                   'offense').chart).not.toBeNull()
  })

  it('is a failed read, not an empty article, when the fetch died', () => {
    const e = toEntry({ name: 'a.json', doc: null }, 'offense')
    expect(e.missing).toBe(true)
    expect(e.blocks).toEqual([])
  })

  it('survives a payload with no blocks array at all', () => {
    expect(toEntry({ name: 'a.json', doc: { title: 'T' } }, 'offense').blocks).toEqual([])
  })

  it('maps a list without dropping anything', () => {
    expect(toEntries([{ name: 'a.json', doc: { title: 'A' } },
                      { name: 'b.json', doc: null }], 'x')).toHaveLength(2)
  })
})

describe('the axis', () => {
  it('obeys the payload when it says', () => {
    expect(axisFor({ scale: 'linear', series: { c: [1, 100] } })).toBe('linear')
    expect(axisFor({ scale: 'log', series: { c: [1, 1.1] } })).toBe('log')
  })

  it('stays linear on an ordinary range', () => {
    expect(axisFor({ series: { c: [50, 60, 55, 70] } })).toBe('linear')
  })

  it('goes log when one bar would flatten the rest', () => {
    expect(axisFor({ series: { c: [50, 55, 60, 174] } })).toBe('log')
  })

  it('does not reach for log on nothing', () => {
    expect(axisFor(null)).toBe('linear')
    expect(axisFor({ series: { c: [] } })).toBe('linear')
    expect(axisFor({ series: { c: [0, -1] } })).toBe('linear')
  })
})

/* The real article — the case the threshold was measured on. */
const doc = (() => {
  try { return JSON.parse(readFileSync(resolve(process.cwd(), '..',
    'data/output/library/offense_ep_mrna.json'), 'utf8')) } catch { return null }
})()

/**
 * Does the file the data side shipped still LOOK like an article?
 *
 * This is a conformance check on someone else's output, so it reports rather
 * than fails: a red frontend suite is the wrong instrument for "the pipeline
 * changed its mind", and a suite that is red for a week stops being read. What
 * must never regress is the frontend's own behaviour on a non-conformant file
 * — that is the test below it, and it is unconditional.
 *
 * It earned its place on 2026-08-21: `offense_ep_mrna.json` became a bare
 * `{mrna_runup, mrna_ep}` chart map with no title and no blocks, because the
 * data-side session that reverted the contract had been asleep through the
 * afternoon when the article-as-JSON route was agreed and the markdown parser
 * deleted (`42ec619d`). The page went to "没取到" — honestly, but down.
 */
const conforms = doc && Array.isArray(doc.blocks) && doc.blocks.length > 0 && doc.title

describe.skipIf(!conforms)('the shipped article, when it conforms', () => {
  it('has every field a cover needs', () => {
    const e = toEntry({ name: 'offense_ep_mrna.json', doc }, 'offense')
    expect(e.title).toBeTruthy()
    expect(e.summary).toBeTruthy()
    expect(e.blocks.length).toBeGreaterThan(5)
  })

  it('uses only block types the page knows how to draw', () => {
    const known = new Set(['h2', 'h3', 'p', 'table', 'list', 'note', 'chart'])
    for (const b of doc.blocks) expect(known.has(b.type), b.type).toBe(true)
  })

  it('places every chart its blocks ask for', () => {
    const asked = doc.blocks.filter((b) => b.type === 'chart').map((b) => b.key)
    for (const k of asked) expect(doc.charts?.[k]?.series?.c?.length, k).toBeTruthy()
  })
})

describe('a payload that is not an article', () => {
  it('is called malformed, which is neither a failed read nor an empty article', () => {
    // the bare chart map that shipped on 2026-08-21
    const e = toEntry({ name: 'x.json', doc: { mrna_runup: { series: { c: [1, 2] } } } }, 'offense')
    expect(e.malformed).toBe(true)
    expect(e.missing).toBe(false)        // the fetch worked; blaming it would be wrong
    expect(e.keys).toContain('mrna_runup')   // and the page can say what it DID find
    expect(e.blocks).toEqual([])
  })

  it('does not call a short but real article malformed', () => {
    expect(toEntry({ name: 'x.json', doc: { title: 'T', blocks: [] } }, 'x').malformed).toBe(false)
    expect(toEntry({ name: 'x.json', doc: { blocks: [{ type: 'p', text: 'a' }] } }, 'x')
      .malformed).toBe(false)
  })

  it('still finds a cover in a charts map, so the shelf is not blank', () => {
    const e = toEntry({ name: 'x.json',
      doc: { title: 'T', blocks: [], charts: { a: { series: { c: [1, 2] } } } } }, 'offense')
    expect(e.charts.a).toBeTruthy()
  })
})
