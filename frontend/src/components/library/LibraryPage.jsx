import PageHeader from '../PageHeader'
import { useLibrary } from '../../hooks/useLibrary'
import CardChart from '../watchlist/shortlist/CardChart'
import { toEntries, axisFor } from './entry'

/**
 * A Library page: a shelf of covers, and a page per piece.
 *
 * Andy: these read like books or journal entries, so each one gets a cover —
 * a plain title and a picture — and you click through to read it. Two views,
 * one route: `#/offense` is the shelf, `#/offense/ep_mrna` is the piece. The
 * sub-route already existed for the drill-downs elsewhere, so a piece is a
 * PLACE: linkable, back-button-able, reachable from outside.
 *
 * A cover is derived from the article, never authored separately — title from
 * its H1, line from its first paragraph, art from the chart it already carries.
 * Nothing to keep in step, and a piece written tonight has a cover tonight.
 *
 * An honest account of what is still reserved.
 *
 * The five Library pages have been Placeholders since they were routed, on the
 * rule this design system already holds — a slot that disappears when unfilled
 * was never reserved. The first article landing does not repeal that rule; it
 * just means one page now has an article ABOVE its reserved block instead of
 * only the block. What is written shows; what is not still says so.
 *
 * Nothing here builds HTML. The article arrives as typed blocks and this turns
 * them into React elements, so every character of a fetched file is text by
 * construction — there is no path from file contents to markup.
 */

/* The type ladder is the page's, not a document format's: an article is prose,
   so the measure is capped near 70 characters and the headings step by weight
   and space rather than by size alone. */
const H = {
  h2: 'text-[17px] leading-snug font-semibold mt-7 mb-2',
  h3: 'text-[14px] leading-snug font-semibold mt-5 mb-1.5',
}

/**
 * One typed block.
 *
 * The article arrives as a list of these, so nothing is parsed out of prose and
 * there is no path from a fetched file to markup — every string below is text
 * by construction. A type this page has never heard of prints as a paragraph
 * with its type named: visible and wrong-looking, which is the right failure.
 * Silence would hide that an article had stopped rendering half of itself.
 */
function Block({ b, charts }) {
  /* An article may place MORE THAN ONE chart, and where it places them is part
     of the argument — the MRNA piece wants the run-up before the discipline and
     the repricing after it. So a chart can be a block naming a key, with the
     payloads in a `charts` map beside `blocks`. A key nobody shipped says so at
     the spot it would have filled, rather than leaving a hole the surrounding
     paragraphs read straight past. */
  if (b.type === 'chart') {
    const c = charts?.[b.key]
    if (!c?.series?.c?.length) {
      return (
        <div className="my-4 rounded-2xl px-5 py-5"
             style={{ backgroundImage:
               'repeating-linear-gradient(45deg,var(--color-border-light) 0 1px,transparent 1px 7px)' }}>
          <div className="text-[10px] font-mono uppercase tracking-[.24em]
                          text-[var(--color-text-muted)] mb-2">Chart not shipped</div>
          <p className="m-0 text-[12.5px] leading-relaxed text-[var(--color-text-secondary)]">
            这篇文章要一张图（<code className="font-mono">{b.key}</code>），但
            <code className="font-mono"> charts</code> 里没有它的 K 线。
          </p>
        </div>
      )
    }
    return <ArticleChart chart={c} />
  }
  if (b.type === 'h2' || b.type === 'h3') {
    const Tag = b.type
    return <Tag className={H[b.type]}>{b.text}</Tag>
  }
  if (b.type === 'p') {
    return <p className="my-2.5 text-[13.5px] leading-relaxed
                         text-[var(--color-text-secondary)]">{b.text}</p>
  }
  if (b.type === 'note') {
    /* the provenance register: where the number came from, set apart and quiet */
    return (
      <p className="mt-6 mb-0 pl-3 border-l border-[var(--color-border)]
                    text-[11.5px] leading-relaxed text-[var(--color-text-muted)]">
        {b.text}
      </p>
    )
  }
  if (b.type === 'list') {
    const Tag = b.ordered ? 'ol' : 'ul'
    return (
      <Tag className={`my-2.5 pl-5 space-y-2 text-[13.5px] leading-relaxed
                       text-[var(--color-text-secondary)]
                       ${b.ordered ? 'list-decimal' : 'list-disc'}`}>
        {(b.items ?? []).map((t, i) => <li key={i}>{t}</li>)}
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
              {(b.columns ?? []).map((c, i) =>
                <th key={i} className="px-2 py-1.5 font-medium">{c}</th>)}
            </tr>
          </thead>
          <tbody>
            {(b.rows ?? []).map((cells, r) => (
              <tr key={r} className="border-b border-[var(--color-border-light)] align-top">
                {cells.map((v, c) => (
                  <td key={c} className={`px-2 py-1.5 ${c === 0
                    ? 'font-mono tabular-nums whitespace-nowrap text-[var(--color-text-bold)]'
                    : 'text-[var(--color-text-secondary)]'}`}>{v}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }
  return (
    <p className="my-2.5 text-[13.5px] leading-relaxed text-[var(--color-text-muted)] italic">
      未知的块类型 <span className="font-mono not-italic">{String(b.type)}</span> —— 前端还不会画它。
    </p>
  )
}

/**
 * The article's chart, and its legend.
 *
 * Same component the Short List cards use — one price chart on this site, not
 * two. The legend ships with the payload, so the marks are explained in the
 * data side's own words rather than in a copy of them kept here.
 */
function ArticleChart({ chart }) {
  const scale = axisFor(chart)
  return (
    <figure className="my-5 mx-0">
      <CardChart series={chart.series} marks={chart.marks ?? []} scale={scale} />
      <figcaption className="mt-2 flex flex-wrap gap-x-4 gap-y-1
                             text-[11px] text-[var(--color-text-muted)]">
        {chart.ticker && <span className="font-mono font-semibold
                                          text-[var(--color-text-secondary)]">{chart.ticker}</span>}
        {Object.entries(chart.legend ?? {}).map(([k, v]) => (
          <span key={k}><b className="font-semibold font-mono">{k}</b> {v}</span>
        ))}
        {scale === 'log' && (
          <span title="纵轴按对数：等距离 = 等百分比">
            纵轴对数 —— 线性下，最后一天会把它之前的几个月压成一条线
          </span>
        )}
      </figcaption>
    </figure>
  )
}

function Article({ entry }) {
  const { name, title, subtitle, summary, chart, charts, blocks, updated,
          missing, malformed, keys } = entry
  if (malformed) {
    /* The file arrived and is not an article. Saying "not fetched" would blame
       the network for a shape problem; rendering it as an empty article would
       hide the problem entirely. */
    return (
      <section className="border border-dashed border-[var(--color-untested)] rounded-3xl p-6
                          max-w-[74ch] mb-6">
        <div className="text-[10px] font-mono uppercase tracking-[.24em]
                        text-[var(--color-text-muted)] mb-2">Not an article</div>
        <p className="m-0 text-[13px] leading-relaxed text-[var(--color-text-secondary)]">
          <span className="font-mono">{name}</span> 取到了，但里面没有文章 —— 没有
          <code className="font-mono"> title</code>，也没有
          <code className="font-mono"> blocks</code>。顶层只有：
          <span className="font-mono text-[var(--color-text-bold)]">{keys.join(', ')}</span>。
        </p>
        <p className="m-0 mt-2 text-[12px] leading-relaxed text-[var(--color-text-muted)]">
          文章正文走这一个 JSON（`title` / `summary` / `blocks`），图放同文件的
          <code className="font-mono"> charts</code> 里、由
          <code className="font-mono"> {'{type:"chart", key}'}</code> 块定位。
          markdown 解析器 2026-08-20 已按数据端要求删除（`42ec619d`），前端不再读 `.md`。
        </p>
      </section>
    )
  }
  if (missing) {
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
      <h1 className="m-0 text-[27px] leading-tight font-semibold tracking-tight"
          style={{ fontFamily: 'var(--font-cond)' }}>{title}</h1>
      {subtitle && (
        <p className="m-0 mt-1 text-[15px] leading-snug
                      text-[var(--color-text-secondary)]">{subtitle}</p>
      )}
      {summary && (
        <p className="m-0 mt-3 text-[13.5px] leading-relaxed
                      text-[var(--color-text-bold)]">{summary}</p>
      )}

      {chart && <ArticleChart chart={chart} />}

      {blocks.map((b, i) => <Block key={i} b={b} charts={charts} />)}

      <p className="mt-7 mb-0 text-[10px] font-mono text-[var(--color-text-muted)]">
        data/output/library/{name}{updated ? ` · ${updated.slice(0, 10)}` : ''}
      </p>
    </article>
  )
}

/**
 * A cover.
 *
 * The art is the article's own chart — the actual content rather than
 * decoration — drawn small and without its signal marks: at cover size the
 * glyphs are noise, and the shape is the whole message. A piece with no chart
 * gets a typographic cover instead of a grey rectangle standing in for a
 * picture that does not exist. That is what a spine looks like anyway.
 */
function Cover({ entry, onOpen }) {
  const { title, subtitle, summary, chart, charts, missing, name } = entry
  // an article that places its charts still deserves a cover — the first one
  const cover = chart ?? Object.values(charts ?? {}).find((c) => c?.series?.c?.length) ?? null
  const art = !!cover
  return (
    <button type="button" onClick={onOpen}
            className="group text-left w-full bg-[var(--color-surface)] rounded-3xl
                       border-0 p-0 overflow-hidden cursor-pointer flex flex-col
                       focus:outline-none focus:ring-1 focus:ring-[var(--color-text-muted)]">
      {art ? (
        <>
          <div className="h-[128px] flex items-end px-5 pt-5 overflow-hidden
                          border-b border-[var(--color-border-light)]">
            <div className="w-full -mb-2 opacity-80 group-hover:opacity-100 transition-opacity">
              <CardChart series={cover.series} marks={[]} height={108} bare
                         scale={axisFor(cover)} />
            </div>
          </div>
          <h3 className="m-0 px-5 pt-4 text-[16.5px] leading-snug font-semibold
                         tracking-tight text-[var(--color-text-bold)]">{title}</h3>
        </>
      ) : (
        /* No chart: the TITLE is the art, set large in the cover's own space —
           which is what a book cover is. The first version put the page's own
           word up there instead, so every cover on a shelf read the same and
           the title got said twice; a cover has to be about the piece. */
        <div className="px-5 pt-6 pb-1 min-h-[128px] flex items-end
                        border-b border-[var(--color-border-light)]">
          <h3 className="m-0 pb-4 text-[25px] leading-[1.12] font-bold tracking-tight
                         text-[var(--color-text-bold)] line-clamp-3"
              style={{ fontFamily: 'var(--font-cond)' }}>{title}</h3>
        </div>
      )}

      <div className="px-5 pt-3 pb-4 flex-1 flex flex-col">
        {subtitle && (
          <p className="m-0 mb-1 text-[12px] leading-snug
                        text-[var(--color-text-muted)]">{subtitle}</p>
        )}
        {summary && (
          <p className="m-0 text-[12.5px] leading-relaxed
                        text-[var(--color-text-secondary)] line-clamp-3">{summary}</p>
        )}
        <p className="m-0 mt-3 pt-0 text-[10px] font-mono uppercase tracking-[.16em]
                      text-[var(--color-text-muted)] group-hover:text-[var(--color-text)]
                      transition-colors">
          {missing ? `${name} 没取到` : '读全文 →'}
        </p>
      </div>
    </button>
  )
}

function Reserved({ willHold, indexed, anyWritten }) {
  if (!willHold.length) return null
  return (
    /* Reserved stays reserved. One piece arriving does not make the rest of the
       shelf exist, and a list of what is coming is more use than a page
       pretending to be finished. */
    <div className="border border-dashed border-[var(--color-untested)] rounded-3xl p-6
                    max-w-[70ch] mt-6">
      <div className="text-[10px] font-mono uppercase tracking-[.24em]
                      text-[var(--color-text-muted)] mb-3">
        {anyWritten ? 'Also reserved' : 'Reserved'}
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
  )
}

export default function LibraryPage({ page, entry: slug, group = 'library',
                                      title, blurb, willHold = [] }) {
  const { articles, loading, indexed } = useLibrary(page)
  const entries = toEntries(articles, page)
  const written = entries.filter((e) => !e.missing).length
  const go = (s) => { window.location.hash = s ? `#/${page}/${s}` : `#/${page}` }

  /* ── one piece ───────────────────────────────────────────────────────── */
  if (slug) {
    const one = entries.find((e) => e.slug === slug)
    return (
      <div>
        <button type="button" onClick={() => go(null)}
                className="text-[11px] font-mono uppercase tracking-[.16em] mb-3
                           bg-transparent border-0 p-0 cursor-pointer
                           text-[var(--color-text-muted)] hover:text-[var(--color-text)]">
          ← {title}
        </button>
        {loading ? null : one ? <Article entry={one} /> : (
          /* A link that resolves to nothing says which piece and offers the
             shelf — a 404 inside our own product is a dead end we control. */
          <div className="border border-dashed border-[var(--color-untested)] rounded-3xl
                          p-6 max-w-[70ch]">
            <div className="text-[10px] font-mono uppercase tracking-[.24em]
                            text-[var(--color-text-muted)] mb-2">No such piece</div>
            <p className="m-0 text-[13px] text-[var(--color-text-secondary)]">
              这一页没有叫 <span className="font-mono">{slug}</span> 的篇目。
              {!indexed && ' 也可能它刚写好，而前端读的还是编译进来的名单。'}
            </p>
          </div>
        )}
      </div>
    )
  }

  /* ── the shelf ───────────────────────────────────────────────────────── */
  return (
    <div>
      <PageHeader group={group} title={title} blurb={blurb}
                  meta={loading ? ['reading'] : written
                    ? [`${written} 篇`, indexed ? 'from the index' : 'compiled-in list']
                    : ['not built yet', 'the slot is reserved, not missing']} />

      {entries.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {entries.map((e) => (
            <Cover key={e.name} entry={e} onOpen={() => go(e.slug)} />
          ))}
        </div>
      )}

      {!loading && <Reserved willHold={willHold} indexed={indexed} anyWritten={written > 0} />}
    </div>
  )
}
