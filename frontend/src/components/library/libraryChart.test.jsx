import { describe, it, expect } from 'vitest'
import { act, render } from '@testing-library/react'
import LibraryPage from './LibraryPage'

/**
 * The shelf, the piece, and the chart inside it.
 *
 * Andy: these read like books — a cover with a plain title and a picture, and
 * you click through. Two views over one route.
 *
 * The article is typed blocks, not prose to be parsed (DATA_CONTRACTS §四点十一).
 * What matters here is that a cover never claims more than the payload gave it,
 * that a block type nobody taught this page is VISIBLE rather than dropped, and
 * that a link to a piece that is not there says so.
 */
const series = (n = 40) => ({
  d: Array.from({ length: n }, (_, i) => `2026-06-${String((i % 28) + 1).padStart(2, '0')}`),
  c: Array.from({ length: n }, (_, i) => 100 + i),
  e21: Array.from({ length: n }, (_, i) => 99 + i),
  s50: Array.from({ length: n }, (_, i) => 95 + i),
  v: Array.from({ length: n }, () => 1e6),
})

function withFetch(files) {
  globalThis.fetch = (url) => {
    const key = String(url).split('/').pop()
    if (!(key in files)) return Promise.resolve({ ok: false })
    return Promise.resolve({ ok: true, json: async () => files[key] })
  }
}
const draw = async (props) => {
  let c
  await act(async () => { c = render(<LibraryPage page="offense" title="Offense" {...props} />) })
  await act(async () => { await new Promise((r) => setTimeout(r, 0)) })
  return c
}
const ART = { slug: 'offense_ep_mrna', page: 'offense', title: 'EP 标本',
              subtitle: '以 MRNA 为例', summary: '一句摘要。',
              blocks: [{ type: 'p', text: '正文很长的一段。' }] }

describe('the shelf', () => {
  it('shows a cover per piece, not the prose', async () => {
    withFetch({ 'offense_ep_mrna.json': ART })
    const c = await draw({ willHold: ['一条预留'] })
    expect(c.container.textContent).toContain('EP 标本')
    expect(c.container.textContent).toContain('一句摘要。')
    expect(c.container.textContent).not.toContain('正文很长的一段')
    expect(c.container.textContent).toContain('一条预留')     // reserved stays
  })

  it('makes the title the art when there is no chart, and says it once', async () => {
    withFetch({ 'offense_ep_mrna.json': ART })
    const c = await draw()
    const cover = [...c.container.querySelectorAll('button')].find((b) => /读全文/.test(b.textContent))
    expect([...cover.querySelectorAll('h3')]).toHaveLength(1)
    expect(cover.textContent).not.toContain('OFFENSE')
  })

  it('draws the piece’s own chart as its cover, without the signal marks', async () => {
    withFetch({ 'offense_ep_mrna.json': { ...ART,
      chart: { ticker: 'MRNA', series: series(), marks: [{ d: '2026-06-05', kinds: ['EP'] }] } } })
    const c = await draw()
    expect(c.container.querySelector('polyline')).not.toBeNull()
    expect(c.container.querySelectorAll('svg[viewBox="0 0 8 8"]')).toHaveLength(0)
  })
})

describe('a piece', () => {
  it('draws its chart with the payload’s own legend', async () => {
    withFetch({ 'offense_ep_mrna.json': { ...ART,
      chart: { ticker: 'MRNA', series: series(), marks: [{ d: '2026-06-05', kinds: ['EP'] }],
               legend: { EP: '≥10%×量≥3×' } } } })
    const c = await draw({ entry: 'ep_mrna' })
    expect(c.container.querySelector('figure')).not.toBeNull()
    expect(c.container.textContent).toContain('≥10%×量≥3×')
    expect(c.container.textContent).toContain('MRNA')
  })

  it('reaches for a log axis when one bar would flatten the rest, and says so', async () => {
    const s = series(); s.c[s.c.length - 1] = 500
    withFetch({ 'offense_ep_mrna.json': { ...ART, chart: { ticker: 'X', series: s } } })
    const c = await draw({ entry: 'ep_mrna' })
    expect(c.container.textContent).toContain('纵轴对数')
  })

  it('renders every declared block type', async () => {
    withFetch({ 'offense_ep_mrna.json': { ...ART, blocks: [
      { type: 'h2', text: '二级' }, { type: 'h3', text: '三级' },
      { type: 'p', text: '段落' },
      { type: 'table', columns: ['日期', '脚印'], rows: [['08-19', 'EP']] },
      { type: 'list', ordered: true, items: ['第一条'] },
      { type: 'note', text: '出处' },
    ] } })
    const c = await draw({ entry: 'ep_mrna' })
    const t = c.container.textContent
    for (const x of ['二级', '三级', '段落', '日期', '脚印', '08-19', '第一条', '出处'])
      expect(t, x).toContain(x)
    expect(c.container.querySelector('h2')).not.toBeNull()
    expect(c.container.querySelector('ol')).not.toBeNull()
    // the wide table scrolls inside itself
    expect(c.container.querySelector('table').closest('.overflow-x-auto')).not.toBeNull()
  })

  it('shows a block type it has never heard of instead of dropping it', async () => {
    withFetch({ 'offense_ep_mrna.json': { ...ART,
      blocks: [{ type: 'quote', text: '将来某天的新块' }] } })
    const c = await draw({ entry: 'ep_mrna' })
    expect(c.container.textContent).toContain('未知的块类型')
    expect(c.container.textContent).toContain('quote')
  })

  it('says which piece is missing rather than rendering an empty article', async () => {
    withFetch({ 'offense_ep_mrna.json': ART })
    const c = await draw({ entry: 'nope' })
    expect(c.container.textContent).toContain('No such piece')
    expect(c.container.textContent).toContain('nope')
    expect(c.container.querySelector('article')).toBeNull()
  })

  it('calls a failed fetch a failed read, not an empty article', async () => {
    withFetch({})
    const c = await draw({ entry: 'ep_mrna' })
    expect(c.container.textContent).toContain('没取到')
  })
})

/**
 * The caption is the point of the picture.
 *
 * It was being dropped: the payload carried "截到 08-18（EP 前夜）：08-07 收复
 * 21EMA → 08-12 20日新高 → …" and the figure printed a ticker and a legend
 * instead. Those are the reading vocabulary — what the marks mean — and they
 * are not what this particular chart is FOR. An article that places two charts
 * places them for different reasons, and the caption is where it says so.
 */
describe('a chart caption', () => {
  const withCharts = (charts) => ({ ...ART, blocks: [{ type: 'chart', key: 'a' }], charts })

  it('is rendered, and above the legend rather than lost in it', async () => {
    withFetch({ 'offense_ep_mrna.json': withCharts({
      a: { series: series(), caption: '截到 08-18（EP 前夜）', legend: { EP: '≥10%' } } }) })
    const c = await draw({ entry: 'ep_mrna' })
    const caps = [...c.container.querySelectorAll('figcaption')]
    expect(caps[0].textContent).toContain('截到 08-18')
    expect(caps[0].textContent).not.toContain('≥10%')     // the legend is its own line
  })

  it('leaves no empty caption behind when the article did not write one', async () => {
    withFetch({ 'offense_ep_mrna.json': withCharts({ a: { series: series() } }) })
    const c = await draw({ entry: 'ep_mrna' })
    expect(c.container.querySelectorAll('figcaption')).toHaveLength(1)
  })
})
