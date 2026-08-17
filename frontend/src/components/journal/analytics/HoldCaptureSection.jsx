import { useMemo, useState } from 'react'
import { useTradeJournal } from '../../../hooks/useTradeJournal'
import { useLanguage } from '../../../i18n/LanguageContext'
import TickerLink from '../../ticker/TickerLink'
import Empty from '../Empty'
import { holdCapture } from '../lib/holdCapture'

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

  return (
    <section>
      <h3 className="text-[15px] font-semibold m-0">{t('hold.title')}</h3>
      <p className="text-[12.5px] text-[var(--color-text-muted)] mt-1 mb-5 max-w-[64ch]">
        {t('hold.lede')}
      </p>

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
                <span className="text-[13.5px] font-semibold">{r.label}{t('hold.days')}</span>
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

      <p className="text-[11.5px] text-[var(--color-text-muted)] mt-3.5 max-w-[64ch]">
        {t('hold.legend')}
      </p>
      {confounded && (
        <p className="text-[11.5px] text-[var(--color-text-secondary)] mt-2 max-w-[64ch]
                      border-l-2 border-[var(--color-border)] pl-3">
          {t('hold.confound')}
        </p>
      )}
    </section>
  )
}
