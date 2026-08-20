import PageHeader from '../PageHeader'
import { useLibrary } from '../../hooks/useLibrary'
import { parse } from '../../lib/markdown'
import CardChart from '../watchlist/shortlist/CardChart'

/**
 * A Library page: whatever the data side has written for it, and an honest
 * account of what is still reserved.
 *
 * The five Library pages have been Placeholders since they were routed, on the
 * rule this design system already holds — a slot that disappears when unfilled
 * was never reserved. The first article landing does not repeal that rule; it
 * just means one page now has an article ABOVE its reserved block instead of
 * only the block. What is written shows; what is not still says so.
 *
 * Nothing here builds HTML. `parse` returns a block list and this turns it into
 * React elements, so every character of a fetched file is text by construction.
 */

function Spans({ spans }) {
  return spans.map((s, i) =>
    s.t === 'b' ? <b key={i} className="font-semibold text-[var(--color-text-bold)]">{s.s}</b>
    : s.t === 'i' ? <i key={i}>{s.s}</i>
    : s.t === 'code' ? <code key={i} className="font-mono text-[.92em]
        bg-[var(--color-bg)] px-1 py-[1px] rounded">{s.s}</code>
    : <span key={i}>{s.s}</span>)
}

/* The type ladder is the page's, not markdown's: an article is prose, so the
   measure is capped near 70 characters and the headings step by weight and
   space rather than by size alone. */
const H = {
  1: 'text-[27px] leading-tight font-semibold mt-0 mb-3 tracking-tight',
  2: 'text-[17px] leading-snug font-semibold mt-7 mb-2',
  3: 'text-[14px] leading-snug font-semibold mt-5 mb-1.5',
  4: 'text-[13px] leading-snug font-semibold mt-4 mb-1.5',
}

/**
 * The chart an article asked for.
 *
 * Drawn by the same component the Short List cards use — one price chart on
 * this site, not two. That matters more than it sounds: the 12 case charts the
 * validation report made were static SVGs written against that report's own
 * `var(--grid)` / `var(--muted)`, so they carry a fixed palette, live in
 * data/research where nothing serves them, and cannot follow a theme flip. A
 * payload plus this component gives the article a chart that takes the page's
 * tokens and flips for free.
 */
function ChartBlock({ chart, chartKey }) {
  if (!chart?.series?.c?.length) {
    return (
      <div className="my-4 rounded-2xl px-5 py-5"
           style={{ backgroundImage:
             'repeating-linear-gradient(45deg,var(--color-border-light) 0 1px,transparent 1px 7px)' }}>
        <div className="text-[10px] font-mono uppercase tracking-[.24em]
                        text-[var(--color-text-muted)] mb-2">Chart not shipped</div>
        <p className="m-0 text-[12.5px] leading-relaxed text-[var(--color-text-secondary)]">
          这篇文章要一张图（<code className="font-mono">{chartKey}</code>），但配套的
          <code className="font-mono"> .json</code> 里没有它的 K 线。图不是画不出来 ——
          引擎在，缺的是这只票的日线。
        </p>
      </div>
    )
  }
  return (
    <figure className="my-5 mx-0">
      <CardChart series={chart.series} marks={chart.marks ?? []} />
      {chart.caption && (
        <figcaption className="mt-2 text-[11.5px] leading-relaxed text-[var(--color-text-muted)]">
          {chart.caption}
        </figcaption>
      )}
    </figure>
  )
}

function Block({ b, assets }) {
  if (b.type === 'h') {
    const Tag = `h${Math.min(b.level + 1, 6)}`
    return <Tag className={H[b.level] ?? H[4]}
                style={b.level === 1 ? { fontFamily: 'var(--font-cond)' } : undefined}>
      <Spans spans={b.spans} />
    </Tag>
  }
  if (b.type === 'p') {
    return <p className="my-2.5 text-[13.5px] leading-relaxed text-[var(--color-text-secondary)]">
      <Spans spans={b.spans} /></p>
  }
  if (b.type === 'chart') {
    return <ChartBlock chartKey={b.key} chart={assets?.charts?.[b.key]} />
  }
  if (b.type === 'hr') {
    return <hr className="my-6 border-0 border-t border-[var(--color-border-light)]" />
  }
  if (b.type === 'list') {
    const Tag = b.ordered ? 'ol' : 'ul'
    return (
      <Tag className={`my-2.5 pl-5 space-y-2 text-[13.5px] leading-relaxed
                       text-[var(--color-text-secondary)] ${b.ordered ? 'list-decimal' : 'list-disc'}`}>
        {b.items.map((spans, i) => <li key={i}><Spans spans={spans} /></li>)}
      </Tag>
    )
  }
  if (b.type === 'table') {
    return (
      /* wide content scrolls inside its own box; the page never scrolls sideways */
      <div className="overflow-x-auto my-4 -mx-1 px-1">
        <table className="w-full min-w-[420px] text-[12.5px] border-collapse">
          <thead>
            <tr className="text-left text-[10px] font-mono uppercase tracking-wide
                           text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
              {b.head.map((spans, i) => <th key={i} className="px-2 py-1.5 font-medium">
                <Spans spans={spans} /></th>)}
            </tr>
          </thead>
          <tbody>
            {b.rows.map((cells, r) => (
              <tr key={r} className="border-b border-[var(--color-border-light)] align-top">
                {cells.map((spans, c) => (
                  <td key={c} className={`px-2 py-1.5 ${c === 0
                    ? 'font-mono tabular-nums whitespace-nowrap text-[var(--color-text-bold)]'
                    : 'text-[var(--color-text-secondary)]'}`}>
                    <Spans spans={spans} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }
  return null
}

function Article({ name, text, assets }) {
  if (text == null) {
    return (
      <section className="border border-dashed border-[var(--color-untested)] rounded-3xl p-6
                          max-w-[74ch] mb-6">
        <div className="text-[10px] font-mono uppercase tracking-[.24em]
                        text-[var(--color-text-muted)] mb-2">Not fetched</div>
        <p className="m-0 text-[13px] text-[var(--color-text-secondary)]">
          <span className="font-mono">{name}</span> 没取到 —— 名单里有它，文件没到。
          这不是一篇空文章，是一次失败的读取。
        </p>
      </section>
    )
  }
  return (
    <article className="rounded-3xl bg-[var(--color-surface)] px-6 py-6 sm:px-8 sm:py-7
                        max-w-[74ch] mb-6">
      {parse(text).map((b, i) => <Block key={i} b={b} assets={assets} />)}
      <p className="mt-7 mb-0 text-[10px] font-mono text-[var(--color-text-muted)]">
        data/output/library/{name}
      </p>
    </article>
  )
}

export default function LibraryPage({ page, group = 'library', title, blurb, willHold = [] }) {
  const { articles, loading, indexed } = useLibrary(page)
  const written = (articles ?? []).filter((a) => a.text != null).length

  return (
    <div>
      <PageHeader group={group} title={title} blurb={blurb}
                  meta={loading ? ['reading'] : written
                    ? [`${written} 篇`, indexed ? 'from the index' : 'compiled-in list']
                    : ['not built yet', 'the slot is reserved, not missing']} />

      {(articles ?? []).map((a) => <Article key={a.name} {...a} />)}

      {/* Reserved stays reserved. One article arriving does not make the rest
          of the page exist, and a list of what is coming is more use than an
          empty page pretending to be finished. */}
      {!loading && willHold.length > 0 && (
        <div className="border border-dashed border-[var(--color-untested)] rounded-3xl p-6
                        max-w-[70ch]">
          <div className="text-[10px] font-mono uppercase tracking-[.24em]
                          text-[var(--color-text-muted)] mb-3">
            {written ? 'Also reserved' : 'Reserved'}
          </div>
          <ul className="m-0 pl-4 space-y-1.5 text-[12.5px] leading-relaxed
                         text-[var(--color-text-secondary)]">
            {willHold.map((w) => <li key={w}>{w}</li>)}
          </ul>
          {!indexed && (
            <p className="mt-4 mb-0 text-[10px] font-mono text-[var(--color-text-muted)]">
              这一页读的是编译进来的文件名单，不是目录 —— 新增一篇现在还需要前端发一版。
              已向数据端要 <code>library/index.json</code>（DATA_CONTRACTS §七）。
            </p>
          )}
        </div>
      )}
    </div>
  )
}
