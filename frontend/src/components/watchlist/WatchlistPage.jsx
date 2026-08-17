import { useMemo, useState } from 'react'
import PageHeader from '../PageHeader'
import TickerLink from '../ticker/TickerLink'
import { useLanguage } from '../../i18n/LanguageContext'
import { useWatchlist } from '../../hooks/useWatchlist'

/**
 * Today's list — six questions, already asked.
 *
 * WHY THIS IS NOT THE SCREENER. The Screener is a posture: a table, my filters,
 * my sort, and I go looking. This is the opposite posture — the questions were
 * asked overnight and what is here is the answer. You do not tune it; you read
 * it and take names away. Two postures, so two formats: rows and columns there,
 * question → recipe → names here.
 *
 * WHY CARDS RATHER THAN ONE LONG PAGE. The first build printed every panel in
 * full: 362 names, 2,786px, and the sixth question three screens below the
 * first. But a morning read is a CHOICE — which of six questions matters today
 * — and a page that makes you scroll past five answers to reach the sixth has
 * already made that choice for you. So the landing is six cards, one screen,
 * each showing what its question found and a taste of the names; the full lists
 * live behind the card at #/watchlist/<zone>. Same drill-down the Review page
 * uses, for the same reason.
 *
 * THREE THINGS THE PAGE MUST NOT DO, all of which the data makes possible:
 *
 *   1. A panel with `measured: false` reads NOT MEASURED, never zero. Drawing
 *      an unrun panel as "0 today" reports an absence of measurement as a
 *      measurement of absence.
 *   2. A truncated panel says what it truncated — 25 of 372. A silent cap reads
 *      as "this is all of them".
 *   3. The cross-zone block is described, not ranked. A name on four lists is
 *      on four lists; whether that makes it work more often is not something
 *      anyone has measured, and the wording stays that literal.
 */

const ZONE_ORDER = ['leaders', 'entries', 'compression', 'accumulation', 'moving', 'trouble']

const nf = (n) => n.toLocaleString()

/** Translate by key, fall back to whatever the file called it. */
const tr = (t, key, fallback) => {
  const out = t(key)
  return out === key ? fallback : out
}

/**
 * The gate, in the words its own keys imply.
 *
 * The pipeline swapped `min_avg_volume` (shares) for `min_dollar_volume` on
 * 2026-08-17 — a name-and-unit change, not a value change — and this line was
 * reading the old key straight into a division, so it would have printed
 * "$1B cap, NaNM average volume" the moment the new file landed. Reading a
 * missing key as a number is how a page starts lying quietly.
 *
 * So each key is named explicitly and an unknown one is dropped rather than
 * formatted. A gate clause we cannot describe should be absent from the
 * sentence, never present as NaN.
 */
const gateWords = (gate = {}) => {
  const out = []
  if (gate.min_market_cap) out.push(`$${(gate.min_market_cap / 1e9).toFixed(0)}B cap`)
  if (gate.min_dollar_volume) out.push(`$${(gate.min_dollar_volume / 1e6).toFixed(0)}M/day traded`)
  else if (gate.min_avg_volume) out.push(`${(gate.min_avg_volume / 1e6).toFixed(0)}M shares/day`)
  return out.join(', ')
}

/**
 * Which number sits beside a ticker, and what it is called.
 *
 * The file may carry two, and they answer different questions:
 *
 *   rs_1m              cross-sectional — "beats 90% of the tradeable field"
 *   rs_line_pctl_21    time-series — the close/SPY ratio's own percentile over
 *                      its last 21 readings, so 100 means its strength against
 *                      SPY is at a one-month high. This is the number oratnek
 *                      prints, decoded 2026-08-17 and reproduced 29/29 exactly.
 *
 * This page prefers the time-series one, because it is the one that is NOT
 * already implied by the panel a name sits in: several recipes gate on rs_1m
 * (True Market Leaders needs >= 80, the momentum panels are percentile cuts),
 * so printing rs_1m beside those rows repeats the entry condition, while the
 * 21-day reading adds something the membership did not already say.
 *
 * Whichever is drawn, the legend names it — the label is derived from the same
 * pick, so the page cannot print one number under the other one's name. Until
 * the new column ships this falls back to rs_1m and says rs_1m.
 */
export const pickRs = (rows = []) =>
  (rows.some((r) => r?.rs_line_pctl_21 != null) ? 'rs_line_pctl_21' : 'rs_1m')

const go = (zone) => { window.location.hash = zone ? `#/watchlist/${zone}` : '#/watchlist' }

/**
 * RS 1M, inked — colour AND weight, because colour alone could not carry it.
 *
 * The page was entirely grey and nothing could be read off it at a glance. RS
 * 1M is a percentile with a real midpoint, so it is a two-pole quantity and
 * takes this site's pair: took above, refused below, muted through the middle
 * where the number is not saying much. Not green/red — this book has one pair.
 *
 * WHY WEIGHT AS WELL. Measured on the dark ground, the three inks are 8.92 /
 * 5.64 / 6.73 against #1a1715, so every one clears 4.5 — but the greyscale
 * separations are took–refused 14.4, took–muted 9.1, and refused–muted only
 * 5.3. Three identities on one channel with two of them 5.3 apart is the
 * failure this repo keeps re-finding: fine in colour, gone in greyscale, gone
 * for a red-blind reader. Dimming the middle to open the gap was measured too
 * and trades the fault for another — at 60% the middle falls to 3.24 contrast.
 *
 * So the second channel is weight. Both poles are semibold and the middle is
 * not, which separates each pole from the middle without touching either
 * colour, and the two poles are 14.4 apart from each other on their own.
 *
 * The bands are wide on purpose. A continuous ramp would put forty shades on
 * one screen and say "these are all slightly different"; the reading is
 * strong / ordinary / weak.
 */
const rsInk = (v) => (v == null
  ? 'text-[var(--color-text-muted)]'
  : v >= 80 ? 'text-[var(--color-took)] font-semibold'
    : v <= 40 ? 'text-[var(--color-refused)] font-semibold'
      : 'text-[var(--color-text-muted)]')

/**
 * One name as a CELL, not an inline run.
 *
 * Inline-wrapped names were the page's untidiness: nothing lined up, so the
 * eye had to re-find the left edge on every row. Ticker left, number right, in
 * a fixed column — which is the whole reason a table of names reads faster
 * than a paragraph of them.
 */
function Name({ row, showGroup, rsKey = 'rs_1m' }) {
  const v = row[rsKey]
  // The other measure stays reachable without taking a second column.
  const alt = rsKey === 'rs_1m' ? null
    : (row.rs_1m != null ? `RS 1M ${row.rs_1m}` : null)
  return (
    <span className="flex items-baseline gap-1.5 px-2 py-[3px] min-w-0">
      <TickerLink symbol={row.ticker}
                  className="text-[11.5px] font-mono font-semibold
                             text-[var(--color-text-bold)] truncate" />
      <span className={`ml-auto text-[10.5px] font-mono tabular-nums ${rsInk(v)}`}
            title={alt || undefined}>
        {v ?? '—'}
      </span>
      {showGroup && row.group && (
        <span className="text-[10px] text-[var(--color-text-muted)] truncate
                         basis-full">{row.group}</span>
      )}
    </span>
  )
}

/**
 * A field of names on a column grid.
 *
 * Ruled by ROW, not by column. Vertical rules have to know how many columns
 * there are, and the count changes at every breakpoint — the first version
 * pinned its nth-child rules to four and drew them in the wrong places as soon
 * as the grid went to six. A horizontal hairline is column-count-independent
 * and reads as a table either way.
 */
function Names({ rows, wide = false, showGroup, rsKey }) {
  return (
    <span className={`grid ${wide
      ? 'grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 2xl:grid-cols-8'
      : 'grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4'}
      [&>*]:border-b [&>*]:border-[var(--color-border-light)]`}>
      {rows.map((r) => <Name key={r.ticker} row={r} showGroup={showGroup} rsKey={rsKey} />)}
    </span>
  )
}

/** The count, or the reason there isn't one. */
function Count({ panel }) {
  const { t } = useLanguage()
  if (!panel.measured) {
    return <span className="text-[9.5px] font-mono uppercase tracking-[.12em]
                            text-[var(--color-text-muted)]">{t('wl.unmeasured')}</span>
  }
  return (
    <span className="text-[11px] font-mono tabular-nums text-[var(--color-text-secondary)]">
      {nf(panel.count)}
    </span>
  )
}

/* ── Landing: six cards ──────────────────────────────────────────────────── */

function ZoneCard({ zone, index }) {
  const { t } = useLanguage()
  const live = zone.panels.filter((p) => p.measured)
  // A taste, not the list. Taken from the biggest panel, because that is the
  // one the question is mostly answered by.
  const lead = [...live].sort((a, b) => b.count - a.count)[0]
  // Twelve, not eight: the cards are full-width now and eight names left the
  // bottom third of each one empty.
  const taste = (lead?.tickers || []).slice(0, 12)
  const rsKey = pickRs(taste)

  return (
    <button type="button" onClick={() => go(zone.key)}
            className="group text-left flex flex-col h-full rounded-2xl overflow-hidden
                       cursor-pointer transition-colors border border-[var(--color-border-light)]
                       bg-[var(--color-surface)] hover:border-[var(--color-border)]">
      {/* A header BAND, not a floating line. It is what makes six cards read as
          one grid rather than six paragraphs — the eye locks onto the repeated
          bar and stops re-finding each card's top edge. */}
      <span className="flex items-baseline gap-2.5 px-3 py-2
                       bg-[var(--color-hover-bg)] border-l-2 border-[var(--color-accent)]">
        <span className="text-[10px] font-mono tabular-nums text-[var(--color-text-muted)]">
          {String(index + 1).padStart(2, '0')}
        </span>
        <b className="text-[14.5px] font-semibold">{tr(t, `wlz.${zone.key}`, zone.label)}</b>
        <span className="ml-auto text-[10px] font-mono text-[var(--color-text-muted)]">
          {live.length}/{zone.panels.length}
        </span>
      </span>

      {/* Panel, count. The bars are gone: the count is printed right there, so
          a bar beside it was a second copy of one number in more ink — and six
          cards of them were most of what made the page look busy. */}
      <span className="block px-3 pt-2 pb-2.5">
        {zone.panels.map((p) => (
          <span key={p.key} className="flex items-baseline gap-2 py-[2px]">
            <span className="text-[11.5px] text-[var(--color-text-secondary)] truncate">
              {tr(t, `wlp.${p.key}`, p.label)}
            </span>
            <i className="flex-1 border-b border-dotted border-[var(--color-border-light)]
                          translate-y-[-3px]" />
            <Count panel={p} />
          </span>
        ))}
      </span>

      {/* Names follow the panels directly. Pinning them to the bottom (mt-auto)
          left a band of nothing across the middle of the short cards once the
          page went full width — equal heights should push the slack to the
          END of a card, not into the middle of it. */}
      <span className="block border-t border-[var(--color-border-light)]
                       bg-[var(--color-bg)]">
        {taste.length > 0
          ? <Names rows={taste} rsKey={rsKey} />
          : <span className="block px-3 py-2.5 text-[11px]
                             text-[var(--color-text-muted)]">{t('wl.none.short')}</span>}
      </span>
      <span className="mt-auto block px-3 py-1.5 text-[9.5px] font-mono tracking-[.12em]
                       text-[var(--color-text-muted)] group-hover:text-[var(--color-text)]
                       bg-[var(--color-bg)]">{t('wl.open')} →</span>
    </button>
  )
}

/* ── Detail: one question, every name ────────────────────────────────────── */

function Panel({ panel, showGroup, explainPending, rsKey }) {
  const { t } = useLanguage()
  const [openRecipe, setOpenRecipe] = useState(false)
  const rows = panel.tickers || []

  return (
    <div className="py-3 border-t border-[var(--color-border-light)] first:border-t-0">
      <div className="flex items-baseline gap-2.5 mb-1.5">
        {/* The file's label is English. A key we know gets the reader's
            language; one we do not gets the file's own words, so a panel the
            pipeline adds tomorrow shows up rather than disappearing. */}
        <b className="text-[13px] font-semibold">{tr(t, `wlp.${panel.key}`, panel.label)}</b>

        {panel.measured ? (
          <span className="text-[11px] font-mono tabular-nums text-[var(--color-text-secondary)]">
            {panel.truncated > 0
              ? t('wl.showing', { shown: rows.length, total: nf(panel.count) })
              : nf(panel.count)}
          </span>
        ) : <Count panel={panel} />}

        {rows.length > 0 && (
          <button type="button"
                  onClick={() => navigator.clipboard?.writeText(
                    rows.map((r) => r.ticker).join(',')).catch(() => {})}
                  className="text-[10px] font-mono uppercase tracking-[.14em] bg-transparent
                             border-none p-0 cursor-pointer text-[var(--color-text-muted)]
                             hover:text-[var(--color-text)]">
            {t('wl.copy')}
          </button>
        )}

        <button type="button" onClick={() => setOpenRecipe(!openRecipe)}
                className="ml-auto text-[10px] font-mono bg-transparent border-none p-0
                           cursor-pointer text-[var(--color-text-muted)]
                           hover:text-[var(--color-text)]">
          {t('wl.recipe')} {openRecipe ? '−' : '+'}
        </button>
      </div>

      {/* The rule that produced the list, in the pipeline's own words. A list
          you cannot audit is a list you have to take on faith. */}
      {openRecipe && (
        <p className="text-[11px] font-mono text-[var(--color-text-muted)] mb-2 max-w-[80ch]
                      border-l-2 border-[var(--color-border)] pl-3">
          {panel.recipe}
        </p>
      )}

      {rows.length > 0 ? (
        <div className="-mx-1">
          <Names rows={rows} wide showGroup={showGroup} rsKey={rsKey} />
        </div>
      ) : panel.measured ? (
        <p className="text-[11.5px] text-[var(--color-text-muted)] m-0">{t('wl.none')}</p>
      ) : explainPending ? (
        <p className="text-[11.5px] text-[var(--color-text-muted)] m-0">{t('wl.pending')}</p>
      ) : null}
    </div>
  )
}

function ZoneDetail({ zone, index, total }) {
  const { t } = useLanguage()
  const rsKey = pickRs(zone.panels.flatMap((p) => p.tickers || []))
  const live = zone.panels.filter((p) => p.measured).length
  // One fact, said once: when the whole question is waiting, the question says
  // so; in a mixed question the first waiting panel carries it.
  const allPending = live === 0
  const firstPending = zone.panels.find((p) => !p.measured)?.key

  return (
    <div className="py-6 px-1">
      <button type="button" onClick={() => go(null)}
              className="text-[11px] font-mono text-[var(--color-text-muted)] bg-transparent
                         border-none p-0 cursor-pointer hover:text-[var(--color-text)]">
        ‹ {t('nav.watchlist')}
      </button>
      <div className="flex items-baseline gap-3 mt-1 mb-4">
        <span className="text-[13px] font-mono tabular-nums text-[var(--color-text-muted)]">
          {String(index + 1).padStart(2, '0')}
        </span>
        <h1 className="text-[30px] font-bold leading-tight m-0">
          {tr(t, `wlz.${zone.key}`, zone.label)}
        </h1>
        <span className="ml-auto text-[10px] font-mono uppercase tracking-[.16em]
                         text-[var(--color-text-muted)]">{index + 1} / {total}</span>
      </div>

      {allPending && (
        <p className="text-[11.5px] text-[var(--color-text-muted)] mb-3 max-w-[70ch]">
          {t('wl.pending')}
        </p>
      )}

      <p className="text-[11px] text-[var(--color-text-muted)] mb-3">
        {t(`wl.rskey.${rsKey}`)}
      </p>
      <div className="rounded-3xl bg-[var(--color-surface)] px-4 py-1">
        {zone.panels.map((p) => (
          <Panel key={p.key} panel={p} showGroup={zone.key === 'leaders'} rsKey={rsKey}
                 explainPending={!allPending && p.key === firstPending} />
        ))}
      </div>
    </div>
  )
}

/* ── Page ────────────────────────────────────────────────────────────────── */

export default function WatchlistPage({ zone: routeZone }) {
  const { t } = useLanguage()
  const { data, failed } = useWatchlist()

  const zones = useMemo(() => {
    if (!data?.zones) return []
    const byKey = new Map(data.zones.map((z) => [z.key, z]))
    // Declared order, then anything the pipeline adds later — a new zone should
    // appear rather than vanish because this file had not heard of it.
    const known = ZONE_ORDER.map((k) => byKey.get(k)).filter(Boolean)
    const extra = data.zones.filter((z) => !ZONE_ORDER.includes(z.key))
    return [...known, ...extra]
  }, [data])

  if (failed) {
    return (
      <div className="py-6 px-1">
        <PageHeader group="market" title={t('nav.watchlist')} />
        <p className="text-[13px] text-[var(--color-text-muted)]">{t('wl.nofile')}</p>
      </div>
    )
  }
  if (!data) return null

  const at = zones.findIndex((z) => z.key === routeZone)
  if (at >= 0) return <ZoneDetail zone={zones[at]} index={at} total={zones.length} />

  const cross = data.cross_zone || []
  const rule = data.cross_zone_rule

  return (
    <div className="py-6 px-1">
      <PageHeader group="market" title={t('nav.watchlist')} />

      {/* Provenance first: which close this is, and how many names were even
          eligible. A list without its universe is a list you cannot size up. */}
      <p className="text-[12px] font-mono text-[var(--color-text-muted)] mt-1 mb-5">
        {t('wl.provenance', {
          date: data.date,
          n: nf(data.universe_gated),
          gate: gateWords(data.gate),
        })}
      </p>

      {/* auto-rows-fr: every card the same height, which is most of what
          makes a grid of cards read as a grid rather than a pile. */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 auto-rows-fr">
        {zones.map((z, i) => <ZoneCard key={z.key} zone={z} index={i} />)}
      </div>

      {/* Names that answer more than one question. Described, not ranked, and
          below the questions rather than above them — it is a by-product of the
          six answers, not a seventh answer. */}
      {cross.length > 0 && (
        <details className="mt-6">
          <summary className="text-[11px] font-mono uppercase tracking-[.18em]
                              text-[var(--color-text-muted)] cursor-pointer list-none
                              hover:text-[var(--color-text)]">
            {t('wl.cross')} · {cross.length} +
          </summary>
          <div className="rounded-3xl bg-[var(--color-surface)] px-4 py-3.5 mt-2">
            <div className="leading-relaxed mb-2">
              {cross.map((c) => (
                <span key={c.ticker} className="inline-flex items-baseline gap-1 mr-3 mb-1">
                  <TickerLink symbol={c.ticker}
                              className="text-[12px] font-mono font-semibold
                                         text-[var(--color-text-bold)]" />
                  <span className="text-[10px] font-mono tabular-nums
                                   text-[var(--color-text-muted)]">×{c.count}</span>
                </span>
              ))}
            </div>
            <p className="text-[11.5px] text-[var(--color-text-muted)] m-0 max-w-[70ch]">
              {t('wl.cross.legend')}
            </p>
            {/* The threshold is the file's to state, not this page's to
                remember: it moved from 2 zones to 3 on 2026-08-17 and a page
                carrying its own copy of the number would now be lying. */}
            {rule && (
              <p className="text-[10.5px] font-mono text-[var(--color-text-muted)] mt-1.5 m-0">
                {rule}
              </p>
            )}
          </div>
        </details>
      )}

      {/* Three hundred numbers sat beside three hundred tickers with nothing
          on the page saying what they were. The label is derived from the same
          pick that draws them, so the two cannot drift apart. */}
      <p className="text-[11px] text-[var(--color-text-muted)] mt-5 max-w-[72ch]">
        {t(`wl.rskey.${pickRs(zones.flatMap((z) => z.panels.flatMap((p) => p.tickers || [])))}`)}
        {' '}{t('wl.foot')}
      </p>
    </div>
  )
}
