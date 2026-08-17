import { useMemo, useState } from 'react'
import PageHeader from '../PageHeader'
import TickerLink from '../ticker/TickerLink'
import { useLanguage } from '../../i18n/LanguageContext'
import { useWatchlist } from '../../hooks/useWatchlist'

/**
 * Today's watchlist — six questions, already asked.
 *
 * WHY THIS IS NOT THE SCREENER. The Screener is a posture: a table, my filters,
 * my sort, and I go looking. This page is the opposite posture — the questions
 * were asked overnight and what is here is the answer. You do not tune it; you
 * read it and take names away. Two postures, so two formats: the Screener is
 * rows and columns, and this is question → recipe → names.
 *
 * The pipeline already wrote the zones as questions ("Who leads?", "Can I enter
 * today?"), so the page leads with the question and not with a list title. That
 * is the whole reason the page can be read in a minute: you are not scanning
 * fourteen list names, you are picking which of six questions you care about
 * this morning.
 *
 * THREE THINGS THE PAGE MUST NOT DO, all of which the data makes possible:
 *
 *   1. A panel with `measured: false` shows as NOT MEASURED, never as zero.
 *      Four of the fourteen panels are waiting on fields that have not run yet;
 *      drawing them as "0 today" would report an absence of measurement as a
 *      measurement of absence.
 *   2. A truncated panel says what it truncated. VCS shows 25 of 62 and Liquid
 *      Leaders 25 of 181 — a silent cap reads as "this is all of them".
 *   3. The cross-zone block is described, not ranked. A name that answers four
 *      questions is not thereby a better trade; nobody has measured that. It is
 *      "on four lists", which is a fact, and the wording stays that literal.
 */

const ZONE_ORDER = ['leaders', 'entries', 'compression', 'accumulation', 'moving', 'trouble']

const nf = (n) => n.toLocaleString()

/** Translate by key, fall back to whatever the file called it. */
const tr = (t, key, fallback) => {
  const out = t(key)
  return out === key ? fallback : out
}

/** One name, with the number the file says sits beside it. */
function Name({ t: row, showGroup }) {
  return (
    <span className="inline-flex items-baseline gap-1 mr-3 mb-1">
      <TickerLink symbol={row.ticker}
                  className="text-[12px] font-mono font-semibold text-[var(--color-text-bold)]" />
      <span className="text-[10px] font-mono tabular-nums text-[var(--color-text-muted)]">
        {row.rs_1m}
      </span>
      {showGroup && row.group && (
        <span className="text-[10px] text-[var(--color-text-muted)] opacity-70">
          {row.group}
        </span>
      )}
    </span>
  )
}

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

        {/* Not measured is not zero. The distinction is the point of the flag. */}
        {!panel.measured ? (
          <span className="text-[10px] font-mono uppercase tracking-[.14em]
                           text-[var(--color-text-muted)]">{t('wl.unmeasured')}</span>
        ) : (
          <span className="text-[11px] font-mono tabular-nums text-[var(--color-text-secondary)]">
            {panel.truncated > 0
              ? t('wl.showing', { shown: rows.length, total: nf(panel.count) })
              : nf(panel.count)}
          </span>
        )}

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
          {rows.map((r) => <Name key={r.ticker} t={r} showGroup={showGroup} />)}
        </div>
      ) : panel.measured ? (
        <p className="text-[11.5px] text-[var(--color-text-muted)] m-0">{t('wl.none')}</p>
      ) : explainPending ? (
        <p className="text-[11.5px] text-[var(--color-text-muted)] m-0">{t('wl.pending')}</p>
      ) : null}
    </div>
  )
}

function Zone({ zone, index }) {
  const { t } = useLanguage()
  const live = zone.panels.filter((p) => p.measured).length
  // Four panels each repeating the same "not measured" sentence is four copies
  // of one fact. When the whole zone is waiting, the zone says it once.
  const allPending = live === 0
  // In a mixed zone the sentence still only needs saying once, so it goes on
  // the first waiting panel and the rest just carry the tag.
  const firstPending = zone.panels.find((p) => !p.measured)?.key
  return (
    <section className="mt-9 first:mt-6">
      <div className="flex items-baseline gap-3 mb-1">
        <span className="text-[11px] font-mono tabular-nums text-[var(--color-text-muted)]">
          {String(index + 1).padStart(2, '0')}
        </span>
        <h2 className="text-[21px] font-bold m-0">{tr(t, `wlz.${zone.key}`, zone.label)}</h2>
        <span className="ml-auto text-[10px] font-mono uppercase tracking-[.16em]
                         text-[var(--color-text-muted)]">
          {live}/{zone.panels.length}
        </span>
      </div>
      {allPending && (
        <p className="text-[11.5px] text-[var(--color-text-muted)] mt-1 mb-2 max-w-[70ch]">
          {t('wl.pending')}
        </p>
      )}
      <div className="rounded-3xl bg-[var(--color-surface)] px-4 py-1">
        {zone.panels.map((p) => (
          <Panel key={p.key} panel={p} showGroup={zone.key === 'leaders'}
                 explainPending={!allPending && p.key === firstPending} />
        ))}
      </div>
    </section>
  )
}

export default function WatchlistPage() {
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

  const cross = data.cross_zone || []

  return (
    <div className="max-w-5xl mx-auto py-6 px-4">
      <PageHeader group="market" title={t('nav.watchlist')} />

      {/* Provenance first: which close this is, and how many names were even
          eligible. A list without its universe is a list you cannot size up. */}
      <p className="text-[12px] font-mono text-[var(--color-text-muted)] mt-1 mb-6">
        {t('wl.provenance', {
          date: data.date,
          n: nf(data.universe_gated),
          cap: `$${(data.gate.min_market_cap / 1e9).toFixed(0)}B`,
          vol: `${(data.gate.min_avg_volume / 1e6).toFixed(0)}M`,
        })}
      </p>

      {/* Names that answer more than one question. Described, not ranked. */}
      {cross.length > 0 && (
        <section className="rounded-3xl bg-[var(--color-surface)] px-4 py-3.5">
          <div className="flex items-baseline gap-3 mb-2">
            <b className="text-[11px] font-mono uppercase tracking-[.18em]
                          text-[var(--color-text-secondary)]">{t('wl.cross')}</b>
            <span className="text-[11px] font-mono tabular-nums text-[var(--color-text-muted)]">
              {cross.length}
            </span>
          </div>
          <div className="leading-relaxed mb-2">
            {cross.slice(0, 40).map((c) => (
              <span key={c.ticker} className="inline-flex items-baseline gap-1 mr-3.5 mb-1">
                <TickerLink symbol={c.ticker}
                            className="text-[12.5px] font-mono font-semibold
                                       text-[var(--color-text-bold)]" />
                <span className="text-[10px] font-mono tabular-nums
                                 text-[var(--color-text-muted)]">×{c.count}</span>
              </span>
            ))}
          </div>
          <p className="text-[11.5px] text-[var(--color-text-muted)] m-0 max-w-[70ch]">
            {t('wl.cross.legend')}
          </p>
        </section>
      )}

      {zones.map((z, i) => <Zone key={z.key} zone={z} index={i} />)}

      <p className="text-[11px] text-[var(--color-text-muted)] mt-10 max-w-[72ch]">
        {t('wl.foot')}
      </p>
    </div>
  )
}
