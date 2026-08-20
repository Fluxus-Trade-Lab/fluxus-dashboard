/**
 * A cover, off the article's own fields.
 *
 * Andy: the Library reads like a shelf of books — each piece gets a cover with
 * a plain title and a picture, and you click through to read it.
 *
 * The first version derived all three from a markdown draft: title from the H1,
 * line from the first paragraph, art from a chart marker in the prose. The data
 * side then shipped the article as structured JSON with `title`, `subtitle`,
 * `summary` and `chart` as fields, which is strictly better — a summary written
 * to BE a summary beats a first paragraph pressed into service, and nothing has
 * to be parsed out of prose to find it. That parser is gone with it; two ways to
 * render one article is one way too many.
 *
 * The slug is the payload's when it has one, and the filename's when it does
 * not — a piece named in a shape this did not expect still gets a working link.
 */

export function slugOf(name, page) {
  const base = name.replace(/\.json$/, '')
  const prefix = `${page}_`
  return base.startsWith(prefix) ? base.slice(prefix.length) : base
}

/** @returns {{ slug, name, title, subtitle, summary, chart, blocks, updated, missing }} */
export function toEntry({ name, doc }, page) {
  const fromName = slugOf(name, page)
  if (!doc) {
    return { slug: fromName, name, title: name, subtitle: null, summary: null,
             chart: null, blocks: [], updated: null, missing: true }
  }
  return {
    // the payload's slug carries the page prefix; the URL should not say it twice
    slug: doc.slug ? slugOf(`${doc.slug}.json`, doc.page ?? page) : fromName,
    name,
    missing: false,
    title: doc.title ?? name,
    subtitle: doc.subtitle ?? null,
    summary: doc.summary ?? null,
    chart: doc.chart?.series?.c?.length ? doc.chart : null,
    blocks: Array.isArray(doc.blocks) ? doc.blocks : [],
    updated: doc.updated ?? null,
  }
}

export const toEntries = (articles, page) => (articles ?? []).map((a) => toEntry(a, page))

/**
 * Which axis a chart should be drawn on, when the payload does not say.
 *
 * Choosing an axis is a display decision, so it is ours — but it is never a
 * silent one: the chart prints `log` on itself whenever it is not linear.
 *
 * The threshold is a legibility rule, not a market claim. Measured on this
 * article's own chart: 130 sessions ending on a +177% day, where the month the
 * piece is ABOUT occupies 7.9% of a linear chart's height and the last bar eats
 * 83%. Anything past roughly a tripling across the window has the same problem —
 * the early part of the picture stops being readable at all, and a chart that
 * cannot show what its text is about is worse than no chart.
 */
export function axisFor(chart) {
  if (chart?.scale) return chart.scale
  const c = (chart?.series?.c ?? []).filter((v) => v != null && v > 0)
  if (c.length < 2) return 'linear'
  return Math.max(...c) / Math.min(...c) >= 3 ? 'log' : 'linear'
}
