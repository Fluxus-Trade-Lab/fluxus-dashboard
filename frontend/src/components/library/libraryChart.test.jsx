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
const draw = async (page = 'offense') => {
  let c
  await act(async () => { c = render(<LibraryPage page={page} title="Offense" />) })
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
