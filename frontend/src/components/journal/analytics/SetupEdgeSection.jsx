import { useMemo } from 'react'
import { useTradeJournal } from '../../../hooks/useTradeJournal'
import { useLanguage } from '../../../i18n/LanguageContext'
import Empty from '../Empty'
import { setupEdge } from '../lib/setupEdge'

const r2 = (v) => `${v >= 0 ? '+' : ''}${v.toFixed(2)}`

/**
 * Do the setup labels separate winners from losers?
 *
 * The selection stage assumes they do — that is what "take more of these, fewer
 * of those" means. On this book they do not, and a section that says so is more
 * use than one that ranks seven labels by expectancy and lets the top of a
 * seven-trade sample look like a strategy.
 */
export default function SetupEdgeSection() {
  const { t } = useLanguage()
  const { trades, loading } = useTradeJournal()
  const res = useMemo(() => setupEdge(trades), [trades])

  if (loading) return null
  if (!res || res.rows.length < 2) return <Empty k="empty.needMore" />

  // One shared scale, so an interval's width means the same on every row —
  // per-row scaling would make the smallest sample look the most precise.
  const all = res.rows.flatMap((r) => r.trades)
  const lo = Math.max(-3, Math.min(...all, res.book))
  const hi = Math.min(8, Math.max(...all, res.book))
  const x = (v) => ((v - lo) / (hi - lo)) * 100

  return (
    <section>
      <h3 className="text-[15px] font-semibold m-0">{t('setup.title')}</h3>
      <p className="text-[12.5px] text-[var(--color-text-muted)] mt-1 mb-5 max-w-[64ch]">
        {t('setup.lede')}
      </p>

      <div>
        {res.rows.map((r) => (
          <div key={r.setup}
               className="grid grid-cols-[168px_44px_1fr] items-center gap-2 py-2.5
                          border-b border-[var(--color-border-light)]">
            <span className="text-[12px] leading-tight">{r.setup}</span>
            <span className="text-[11px] font-mono text-[var(--color-text-muted)] text-right">
              {r.n}
            </span>
            <span className="relative h-5">
              {/* The book average, one segment per row: adjacent rows read as
                  one continuous line. */}
              <i className="absolute -top-2.5 bottom-[-10px] w-px
                            bg-[var(--color-text-muted)] opacity-45"
                 style={{ left: `${x(res.book)}%` }} />
              {/* Every trade as a dot, not a bootstrap interval.
                  The interval was a statistic restating what overlapping point
                  clouds already show, and the rule this page keeps is that a
                  picture which can be read is not also computed. Reading: do
                  the clouds separate, or is that one cloud drawn five times. */}
              {r.trades.map((v, i) => (
                <i key={i}
                   className={`absolute top-1.5 w-[3px] h-2 rounded-sm ${v > 0
                     ? 'bg-[var(--color-took)]' : 'bg-[var(--color-refused)]'}`}
                   style={{ left: `${x(v)}%`, opacity: 0.75 }} />
              ))}
              <i className="absolute top-0.5 w-0.5 h-4 bg-[var(--color-text)]"
                 style={{ left: `${x(r.mean)}%` }} />
            </span>
          </div>
        ))}
      </div>

      <p className="text-[11.5px] text-[var(--color-text-muted)] mt-3.5 max-w-[64ch]">
        {t('setup.legend', { book: r2(res.book) })}
      </p>

      <p className="text-[11.5px] mt-2 max-w-[64ch] border-l-2 pl-3
                    border-[var(--color-border)] text-[var(--color-text-secondary)]">
        {t(res.signal ? 'setup.signal' : 'setup.nosignal', {
          hits: res.hits,
          rows: res.rows.length,
          chance: res.expectedByChance.toFixed(1),
          conc: `${(res.concentration * 100).toFixed(0)}%`,
        })}
      </p>
    </section>
  )
}
