import { describe, it, expect } from 'vitest'
import { toEntry, slugOf, toEntries } from './entry'

/**
 * A cover is derived, not authored twice.
 *
 * Title, lede and art all come out of the article — so a piece the data side
 * ships tonight has a cover tonight, with no second file to keep in step and
 * nothing to go stale against the prose.
 */
describe('the slug', () => {
  it('drops the page prefix so the URL does not say it twice', () => {
    expect(slugOf('offense_ep_mrna.md', 'offense')).toBe('ep_mrna')
  })

  it('leaves a name that does not follow the convention addressable', () => {
    expect(slugOf('stray.md', 'offense')).toBe('stray')
    expect(slugOf('defense_x.md', 'offense')).toBe('defense_x')
  })
})

describe('a cover', () => {
  const md = '# EP · 以 MRNA 为标本\n\n一天之内改变定价前提的事件。\n\n[[chart:runup]]\n\n后文'

  it('takes the title from the article and the line from its first paragraph', () => {
    const e = toEntry({ name: 'offense_ep_mrna.md', text: md }, 'offense')
    expect(e.title).toBe('EP · 以 MRNA 为标本')
    expect(e.lede).toBe('一天之内改变定价前提的事件。')
  })

  it('uses the article’s own first chart as its art', () => {
    const assets = { charts: { runup: { series: { c: [1, 2] } } } }
    expect(toEntry({ name: 'a.md', text: md, assets }, 'offense').cover).toBe(assets.charts.runup)
  })

  it('has no art when the chart it asks for has not shipped', () => {
    expect(toEntry({ name: 'a.md', text: md }, 'offense').cover).toBeNull()
  })

  it('has no art when the article never asked for a chart', () => {
    expect(toEntry({ name: 'a.md', text: '# T\n\nprose' }, 'offense').cover).toBeNull()
  })

  it('is a failed read, not an empty article, when the fetch died', () => {
    const e = toEntry({ name: 'a.md', text: null }, 'offense')
    expect(e.missing).toBe(true)
    expect(e.blocks).toEqual([])
  })

  it('falls back to the filename rather than an untitled cover', () => {
    expect(toEntry({ name: 'a.md', text: 'no heading here' }, 'offense').title).toBe('a.md')
  })

  it('maps a list without dropping anything', () => {
    expect(toEntries([{ name: 'a.md', text: '# A' }, { name: 'b.md', text: '# B' }], 'x'))
      .toHaveLength(2)
  })
})
