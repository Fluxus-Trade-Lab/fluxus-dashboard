/**
 * A cover, derived from the article itself.
 *
 * Andy: the Library reads like a shelf of books — each piece gets a cover with
 * a plain title and a picture, and you click through to read it. A cover needs
 * a title, a line of what it is, and an image, and none of those need a new
 * data contract: the title is the article's own H1, the line is its first
 * paragraph, and the picture is the chart the article already carries. Art that
 * is the actual content beats art chosen to decorate it — and it means a piece
 * shipped tonight has a cover tonight.
 *
 * The slug is how the URL names a piece. It is computed by STRIPPING the page
 * prefix and matched back by lookup, never by reversing the surgery — a file
 * named in a shape this did not expect still gets a working link instead of a
 * dead one.
 */
import { parse } from '../../lib/markdown'

const flat = (spans) => spans.map((s) => s.s).join('')

export function slugOf(name, page) {
  const base = name.replace(/\.md$/, '')
  const prefix = `${page}_`
  return base.startsWith(prefix) ? base.slice(prefix.length) : base
}

/** @returns {{ slug, name, title, lede, cover, blocks, missing }} */
export function toEntry({ name, text, assets }, page) {
  const slug = slugOf(name, page)
  if (text == null) {
    return { slug, name, title: name, lede: null, cover: null, blocks: [], missing: true }
  }
  const blocks = parse(text)
  const h1 = blocks.find((b) => b.type === 'h' && b.level === 1)
  const lede = blocks.find((b) => b.type === 'p')
  const firstChart = blocks.find((b) => b.type === 'chart')
  return {
    slug, name, missing: false, blocks,
    title: h1 ? flat(h1.spans) : name,
    lede: lede ? flat(lede.spans) : null,
    // the cover is the article's first chart, if it has one and it shipped
    cover: firstChart ? (assets?.charts?.[firstChart.key] ?? null) : null,
    assets,
  }
}

export const toEntries = (articles, page) => (articles ?? []).map((a) => toEntry(a, page))
