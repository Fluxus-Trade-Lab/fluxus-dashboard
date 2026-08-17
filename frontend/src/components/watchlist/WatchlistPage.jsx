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

const go = (zone) => { window.location.hash = zone ? `#/watchlist/${zone}` : '#/watchlist' }

/** One name, with the number the file says sits beside it. */
function Name({ row, showGroup, size = 'sm' }) {
  return (
    <span className="inline-flex items-baseline gap-1 mr-2.5 mb-1">
      <TickerLink symbol={row.ticker}
                  className={`${size === 'sm' ? 'text-[11.5px]' : 'text-[12px]'}
                              font-mono font-semibold text-[var(--color-text-bold)]`} />
      <span className="text-[10px] font-mono tabular-nums text-[var(--color-text-muted)]">
        {row.rs_1m}
      </span>
      {showGroup && row.group && (
        <span className="text-[10px] text-[var(--color-text-muted)] opacity-70">{row.group}</span>
      )}
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
  const max = Math.max(1, ...live.map((p) => p.count))
  // A taste, not the list. Taken from the biggest panel, because that is the
  // one the question is mostly answered by.
  const lead = [...live].sort((a, b) => b.count - a.count)[0]
  const taste = (lead?.tickers || []).slice(0, 8)

  return (
    <button type="button" onClick={() => go(zone.key)}
            className="text-left flex flex-col rounded-3xl px-4 py-3.5 border border-transparent
                       cursor-pointer transition-colors bg-[var(--color-surface)]
                       hover:bg-[var(--color-hover-bg)]">
      <span className="flex items-baseline gap-2.5">
        <span className="text-[10px] font-mono tabular-nums text-[var(--color-text-muted)]">
          {String(index + 1).padStart(2, '0')}
        </span>
        <b className="text-[16px] font-bold">{tr(t, `wlz.${zone.key}`, zone.label)}</b>
        <span className="ml-auto text-[9.5px] font-mono uppercase tracking-[.14em]
                         text-[var(--color-text-muted)]">
          {live.length}/{zone.panels.length}
        </span>
      </span>

      {/* Each panel a row: what it is, how many, and how many relative to the
          others in the same question. The bar is within-card only — comparing
          "37 entries" against "372 pocket pivots" across questions would be
          comparing two different nets. */}
      <span className="block mt-3 mb-3">
        {zone.panels.map((p) => (
          <span key={p.key} className="grid grid-cols-[1fr_auto_46px] items-center gap-2 py-[3px]">
            <span className="text-[11.5px] text-[var(--color-text-secondary)] truncate">
              {tr(t, `wlp.${p.key}`, p.label)}
            </span>
            <Count panel={p} />
            <span className="h-1.5 rounded-sm bg-[var(--color-hover-bg)] relative">
              {p.measured && p.count > 0 && (
                <i className="absolute inset-y-0 left-0 rounded-sm bg-[var(--color-took)] opacity-70"
                   style={{ width: `${Math.max(6, (p.count / max) * 100)}%` }} />
              )}
            </span>
          </span>
        ))}
      </span>

      <span className="mt-auto pt-2.5 border-t border-[var(--color-border-light)] block">
        {taste.length > 0 ? (
          <span className="block leading-relaxed">
            {taste.map((r) => <Name key={r.ticker} row={r} />)}
          </span>
        ) : (
          <span className="text-[11px] text-[var(--color-text-muted)]">{t('wl.none.short')}</span>
        )}
        <span className="block text-[10px] font-mono tracking-[.1em] mt-1.5
                         text-[var(--color-text-muted)]">{t('wl.open')} →</span>
      </span>
    </button>
  )
}

/* ── Detail: one question, every name ────────────────────────────────────── */

function Panel({ panel, showGroup, explainPending }) {
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
        <div className="leading-relaxed">
          {rows.map((r) => <Name key={r.ticker} row={r} showGroup={showGroup} size="md" />)}
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
  const live = zone.panels.filter((p) => p.measured).length
  // One fact, said once: when the whole question is waiting, the question says
  // so; in a mixed question the first waiting panel carries it.
  const allPending = live === 0
  const firstPending = zone.panels.find((p) => !p.measured)?.key

  return (
    <div className="max-w-5xl mx-auto py-6 px-4">
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

      <div className="rounded-3xl bg-[var(--color-surface)] px-4 py-1">
        {zone.panels.map((p) => (
          <Panel key={p.key} panel={p} showGroup={zone.key === 'leaders'}
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
      <div className="max-w-5xl mx-auto py-6 px-4">
        <PageHeader group="market" title={t('nav.watchlist')} />
        <p className="text-[13px] text-[var(--color-text-muted)]">{t('wl.nofile')}</p>
      </div>
    )
  }
  if (!data) return null

  const at = zones.findIndex((z) => z.key === routeZone)
  if (at >= 0) return <ZoneDetail zone={zones[at]} index={at} total={zones.length} />

  const cross = data.cross_zone || []

  return (
    <div className="max-w-5xl mx-auto py-6 px-4">
      <PageHeader group="market" title={t('nav.watchlist')} />

      {/* Provenance first: which close this is, and how many names were even
          eligible. A list without its universe is a list you cannot size up. */}
      <p className="text-[12px] font-mono text-[var(--color-text-muted)] mt-1 mb-5">
        {t('wl.provenance', {
          date: data.date,
          n: nf(data.universe_gated),
          cap: `$${(data.gate.min_market_cap / 1e9).toFixed(0)}B`,
          vol: `${(data.gate.min_avg_volume / 1e6).toFixed(0)}M`,
        })}
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
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
          </div>
        </details>
      )}

      <p className="text-[11px] text-[var(--color-text-muted)] mt-5 max-w-[72ch]">
        {t('wl.foot')}
      </p>
    </div>
  )
}
