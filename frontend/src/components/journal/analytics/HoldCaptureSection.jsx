import { useMemo, useState } from 'react'
import { useTradeJournal } from '../../../hooks/useTradeJournal'
import { useLanguage } from '../../../i18n/LanguageContext'
import TickerLink from '../../ticker/TickerLink'
import Empty from '../Empty'
import { holdCapture } from '../lib/holdCapture'
import { usable } from '../lib/headCoach'

const pct = (v) => `${(v * 100).toFixed(0)}%`

/**
 * Does holding longer actually capture more?
 *
 * The head coach names holding as the leak. "So hold longer" is the assumption
 * that follows, and this checks it instead of repeating it — which is the whole
 * reason this view belongs on a page rather than in the periodic report. A
 * report tells you what happened; a page has to be something you can act on and
 * then go look at the trades behind.
 *
 * The right column is not decoration. If the opportunity itself grows with
 * holding time then the buckets are not comparable, and the page says so rather
 * than letting the bars imply a cause they cannot support.
 */
export default function HoldCaptureSection() {
  const { t } = useLanguage()
  const { trades, loading } = useTradeJournal()
  const { rows, confounded } = useMemo(() => holdCapture(trades), [trades])
  const [open, setOpen] = useState(null)

  if (loading) return null
  if (rows.length < 2) return <Empty k="empty.needMore" />

  const maxOpp = Math.max(...rows.map((r) => r.opportunity))

  // The journey: entry to the high it reached, one line per trade, exit marked.
  // This is the same shape the overview card shows — a thumbnail that opens
  // into a different chart is a promise the page cannot keep.
  const journey = trades
    .filter((x) => usable(x) && x.optimal_R > 0.2)
    .sort((a, b) => b.optimal_R - a.optimal_R)
    .slice(0, 140)
  const X = (j) => ((Math.max(-0.35, Math.min(1.15, j)) + 0.35) / 1.5) * 100
  const ENTRY = X(0), TOP = X(1)

  return (
    <section>
      <h3 className="text-[17px] font-semibold m-0">{t('hold.title')}</h3>
      <p className="text-[13px] text-[var(--color-text-muted)] mt-1 mb-5 max-w-[64ch]">
        {t('hold.lede')}
      </p>

      {/* Main visual: where you got off, against how far it went. */}
      <div className="flex flex-col gap-px mb-2">
        {journey.map((x, i) => {
          const xe = X(x.realized_R / x.optimal_R)
          const [l, r] = xe >= ENTRY ? [ENTRY, xe] : [xe, ENTRY]
          return (
            <div key={i} className="relative h-[3px]">
              <i className="absolute top-px h-px bg-[var(--color-border)]"
                 style={{ left: `${ENTRY}%`, width: `${TOP - ENTRY}%` }} />
              <i className={`absolute top-0 h-[3px] ${xe >= ENTRY
                ? 'bg-[var(--color-took)]' : 'bg-[var(--color-refused)]'}`}
                 style={{ left: `${l}%`, width: `${Math.max(0.4, r - l)}%`, opacity: 0.62 }} />
              <i className="absolute -top-px w-0.5 h-[5px] bg-[var(--color-refused)]"
                 style={{ left: `${xe}%`, transform: 'translateX(-1px)' }} />
            </div>
          )
        })}
      </div>
      <div className="flex justify-between text-[11px] font-mono
                      text-[var(--color-text-muted)] mb-6">
        <span>{t('hold.ax.loss')}</span><span>{t('hold.ax.entry')}</span><span>{t('hold.ax.top')}</span>
      </div>

      {/* Supporting evidence, compact: the same trades bucketed by days held. */}
      <p className="text-[11px] font-mono uppercase tracking-[.16em]
                    text-[var(--color-text-muted)] mb-2">{t('hold.byDays')}</p>
      <div>
        {rows.map((r) => {
          const w = Math.max(0, Math.min(1, r.capture ?? 0))
          const neg = (r.capture ?? 0) < 0
          const isOpen = open === r.key
          return (
            <div key={r.key} className="border-b border-[var(--color-border-light)]">
              <button
                type="button"
                onClick={() => setOpen(isOpen ? null : r.key)}
                className="w-full grid grid-cols-[62px_44px_1fr_auto] items-center gap-3.5
                           py-2.5 bg-transparent border-none cursor-pointer text-left
                           hover:bg-[var(--color-hover-bg)]">
                <span className="text-[13px] font-semibold">{r.label}{t('hold.days')}</span>
                <span className="text-[11px] font-mono text-[var(--color-text-muted)] text-right">
                  {r.n}
                </span>
                {/* Negative capture is not a short bar, it is a bar the other
                    way — a trade that gave back more than it took is not a
                    small win. */}
                <span className="relative h-3 rounded-sm bg-[var(--color-hover-bg)]">
                  <i className={`absolute inset-y-0 left-0 rounded-sm ${
                    neg ? 'bg-[var(--color-refused)]' : 'bg-[var(--color-took)]'}`}
                     style={{ width: neg ? '3px' : `${w * 100}%` }} />
                  <em className="absolute -top-0.5 text-[11px] font-mono not-italic
                                 text-[var(--color-text-secondary)]"
                      style={{ left: neg ? '6px' : `calc(${w * 100}% + 7px)` }}>
                    {pct(r.capture ?? 0)}
                  </em>
                </span>
                <span className="text-[11px] font-mono text-[var(--color-text-muted)]
                                 whitespace-nowrap">
                  <i className="inline-block h-1.5 rounded-sm bg-[var(--color-untested)]
                                align-middle mr-2"
                     style={{ width: `${(r.opportunity / maxOpp) * 44}px` }} />
                  {r.opportunity.toFixed(1)}R
                </span>
              </button>

              {isOpen && (
                <div className="pb-3 pl-[62px] flex flex-wrap gap-x-3 gap-y-1">
                  {r.trades.slice(0, 40).map((x) => (
                    <span key={x.trade_id} className="text-[11px] font-mono">
                      <TickerLink symbol={x.ticker} />
                      <span className="text-[var(--color-text-muted)]">
                        {' '}{x.realized_R.toFixed(1)}/{x.optimal_R.toFixed(1)}R
                      </span>
                    </span>
                  ))}
                  {r.trades.length > 40 && (
                    <span className="text-[11px] font-mono text-[var(--color-text-muted)]">
                      +{r.trades.length - 40}
                    </span>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      <p className="text-[11px] text-[var(--color-text-muted)] mt-3.5 max-w-[64ch]">
        {t('hold.legend')}
      </p>
      {confounded && (
        <p className="text-[11px] text-[var(--color-text-secondary)] mt-2 max-w-[64ch]
                      border-l-2 border-[var(--color-border)] pl-3">
          {t('hold.confound')}
        </p>
      )}
    </section>
  )
}
