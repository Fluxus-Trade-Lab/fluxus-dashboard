import { describe, it, expect } from 'vitest'
import { act, render } from '@testing-library/react'
import { parse } from '../../lib/markdown'
import LibraryPage from './LibraryPage'

/**
 * An article can carry a chart, and says so when it cannot.
 *
 * The prose cannot hold 130 bars and their signal days, so the markdown marks
 * WHERE (`[[chart:key]]`) and a sidecar JSON holds WHAT. The failure that
 * matters is the quiet one: an article asking for a chart nobody shipped must
 * not render a hole — the reader would read the surrounding paragraphs as if
 * nothing were missing.
 *
 * Drawn by the Short List's own CardChart. The 12 case charts the validation
 * report made were static SVGs against that report's variables, sitting in
 * data/research where nothing serves them; one component means one chart on
 * this site, and it takes the page's tokens instead of freezing a palette.
 */
describe('the chart marker', () => {
  it('is a block of its own, not a paragraph of brackets', () => {
    expect(parse('a\n\n[[chart:mrna_month]]\n\nb').map((b) => b.type))
      .toEqual(['p', 'chart', 'p'])
    expect(parse('[[chart:mrna_month]]')[0].key).toBe('mrna_month')
  })

  it('leaves a line that merely mentions brackets alone', () => {
    expect(parse('见 [[chart:x]] 这种写法').map((b) => b.type)).toEqual(['p'])
  })
})

const series = (n = 40) => ({
  d: Array.from({ length: n }, (_, i) => `2026-06-${String((i % 28) + 1).padStart(2, '0')}`),
  c: Array.from({ length: n }, (_, i) => 100 + i),
  e21: Array.from({ length: n }, (_, i) => 99 + i),
  s50: Array.from({ length: n }, (_, i) => 95 + i),
  v: Array.from({ length: n }, () => 1e6),
})

/* The page fetches; these drive the render through it with a stubbed fetch so
   the article path is exercised end to end rather than in pieces. */
function withFetch(files) {
  globalThis.fetch = (url) => {
    const key = String(url).split('/').pop()
    if (!(key in files)) return Promise.resolve({ ok: false })
    const body = files[key]
    return Promise.resolve({ ok: true, text: async () => body, json: async () => JSON.parse(body) })
  }
}
/* The page fetches on mount, so the state lands after render returns. Wrapped
   in act so the warning wall does not bury a real one. */
/* The chart lives inside a piece, so these open the piece. `#/offense` is the
   shelf now; `#/offense/ep_mrna` is the article. */
const draw = async (entry = 'ep_mrna', page = 'offense') => {
  let c
  await act(async () => {
    c = render(<LibraryPage page={page} entry={entry} title="Offense" />)
  })
  await act(async () => { await new Promise((r) => setTimeout(r, 0)) })
  return c
}

describe('an article that asks for a chart', () => {
  it('draws it when the sidecar holds it', async () => {
    withFetch({
      'offense_ep_mrna.md': '# T\n\n[[chart:mrna_month]]\n\ntail',
      'offense_ep_mrna.json': JSON.stringify({
        charts: { mrna_month: { series: series(), marks: [{ d: '2026-06-05', kinds: ['EP'], chg: 177 }],
                                caption: '一个月的脚印' } },
      }),
    })
    const c = await draw()
    expect(c.container.querySelector('figure')).not.toBeNull()
    expect(c.container.textContent).toContain('一个月的脚印')
    expect(c.container.textContent).not.toContain('Chart not shipped')
  })

  it('says the chart is missing, at the spot it would have filled', async () => {
    withFetch({ 'offense_ep_mrna.md': '# T\n\n[[chart:mrna_month]]\n\ntail' })
    const c = await draw()
    const t = c.container.textContent
    expect(t).toContain('Chart not shipped')
    expect(t).toContain('mrna_month')
    // and it must not blame the drawing — the engine is fine, the bars are not
    expect(t).toContain('引擎在，缺的是这只票的日线')
    expect(c.container.querySelector('figure')).toBeNull()
  })

  it('renders an article with no sidecar as an ordinary article', async () => {
    withFetch({ 'offense_ep_mrna.md': '# T\n\nplain prose' })
    const c = await draw()
    expect(c.container.textContent).toContain('plain prose')
    expect(c.container.textContent).not.toContain('Chart not shipped')
  })
})

/**
 * The shelf, and the piece.
 *
 * Andy: these read like books — a cover with a plain title and a picture, and
 * you click through. Two views over one route. What matters is that a cover
 * never claims more than the article gave it, and that a link to a piece that
 * is not there says so instead of rendering an empty page.
 */
describe('the shelf', () => {
  const shelf = async () => {
    let c
    await act(async () => { c = render(<LibraryPage page="offense" title="Offense"
                                                    willHold={['一条预留']} />) })
    await act(async () => { await new Promise((r) => setTimeout(r, 0)) })
    return c
  }

  it('makes the title the art when there is no chart, and says it once', async () => {
    withFetch({ 'offense_ep_mrna.md': '# EP 标本\n\n开头这一句。' })
    const c = await shelf()
    const cover = [...c.container.querySelectorAll('button')].find((b) => /读全文/.test(b.textContent))
    // one title, not a wordmark above a repeat of it
    expect([...cover.querySelectorAll('h3')]).toHaveLength(1)
    expect(cover.textContent).not.toContain('OFFENSE')
  })

  it('shows a cover per piece, not the prose', async () => {
    withFetch({ 'offense_ep_mrna.md': '# EP 标本\n\n开头这一句。\n\n后面很长的正文段落。' })
    const c = await shelf()
    expect(c.container.textContent).toContain('EP 标本')
    expect(c.container.textContent).toContain('开头这一句。')
    expect(c.container.textContent).not.toContain('后面很长的正文段落')
    expect(c.container.querySelectorAll('button').length).toBeGreaterThan(0)
  })

  it('draws the piece’s own chart as its cover, without the signal marks', async () => {
    withFetch({
      'offense_ep_mrna.md': '# T\n\nlede\n\n[[chart:runup]]',
      'offense_ep_mrna.json': JSON.stringify({
        charts: { runup: { series: series(), marks: [{ d: '2026-06-05', kinds: ['EP'] }] } } }),
    })
    const c = await shelf()
    expect(c.container.querySelector('polyline')).not.toBeNull()
    // marks are noise at cover size — the shape is the message
    expect(c.container.querySelectorAll('svg[viewBox="0 0 8 8"]')).toHaveLength(0)
  })

  it('keeps the reserved list under the shelf', async () => {
    withFetch({ 'offense_ep_mrna.md': '# T\n\nlede' })
    expect((await shelf()).container.textContent).toContain('一条预留')
  })
})

describe('a link to a piece that is not there', () => {
  it('names it and does not render an empty article', async () => {
    withFetch({ 'offense_ep_mrna.md': '# T\n\nlede' })
    const c = await draw('nope')
    expect(c.container.textContent).toContain('No such piece')
    expect(c.container.textContent).toContain('nope')
    expect(c.container.querySelector('article')).toBeNull()
  })
})
