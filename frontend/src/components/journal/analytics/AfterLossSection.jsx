import { useMemo } from 'react'
import { useTradeJournal } from '../../../hooks/useTradeJournal'
import { useLanguage } from '../../../i18n/LanguageContext'
import Empty from '../Empty'
import { orderMatters, sequence, streakRows } from '../lib/afterLoss'

const r1 = (v) => `${v >= 0 ? '+' : ''}${v.toFixed(2)}R`
const p0 = (v) => `${(v * 100).toFixed(0)}%`

/**
 * When to step away.
 *
 * Every stopping rule is a belief about this, and it is usually held without
 * ever being checked. The decay is shown, and then the page immediately tries
 * to talk itself out of it: losses cluster by arithmetic, so "the last two
 * lost" selects an unusual window for reasons that have nothing to do with the
 * trader. The permutation line is the part that decides.
 */
export default function AfterLossSection() {
  const { t } = useLanguage()
  const { trades, loading } = useTradeJournal()
  const rows = useMemo(() => streakRows(trades), [trades])
  const test = useMemo(() => orderMatters(trades), [trades])
  const seq = useMemo(() => sequence(trades), [trades])

  if (loading) return null
  if (rows.length < 3) return <Empty k="empty.needMore" />

  const base = rows.find((r) => r.key === 'all')
  const worst = Math.min(...rows.map((r) => r.win))
  const best = Math.max(...rows.map((r) => r.win))
  const span = Math.max(best - worst, 0.01)

  return (
    <section>
      <h3 className="text-[17px] font-semibold m-0">{t('loss.title')}</h3>
      <p className="text-[13px] text-[var(--color-text-muted)] mt-1 mb-5 max-w-[64ch]">
        {t('loss.lede')}
      </p>

      {/* Main visual: every trade in time. The outlined ones followed two
          losses — the reading is how much red sits inside those outlines
          against the strip as a whole. Same shape as the overview card. */}
      <div className="flex flex-wrap gap-[3px] mb-2">
        {seq.map((r, i) => (
          <i key={i}
             className={`w-[9px] h-[18px] rounded-sm ${r > 0
               ? 'bg-[var(--color-took)]' : 'bg-[var(--color-refused)]'} ${
               i >= 2 && seq[i - 1] < 0 && seq[i - 2] < 0
                 ? 'opacity-100 outline outline-1 outline-offset-1 outline-[var(--color-text)]'
                 : 'opacity-40'}`} />
        ))}
      </div>
      <p className="text-[11px] font-mono text-[var(--color-text-muted)] mb-6">
        {t('loss.strip')}
      </p>

      <p className="text-[11px] font-mono uppercase tracking-[.16em]
                    text-[var(--color-text-muted)] mb-2">{t('loss.byStreak')}</p>
      <div>
        {rows.map((r) => {
          const isBase = r.key === 'all'
          const w = (r.win - worst) / span
          return (
            <div key={r.key}
                 className={`grid grid-cols-[130px_46px_1fr_74px] items-center gap-3.5 py-2.5
                             border-b border-[var(--color-border-light)]
                             ${isBase ? 'text-[var(--color-text-muted)]' : ''}`}>
              <span className="text-[13px]">{t(`loss.row.${r.key}`)}</span>
              <span className="text-[11px] font-mono text-[var(--color-text-muted)] text-right">
                {r.n}
              </span>
              {/* Win rate as the bar, because the decay is monotone in it and
                  expectancy is not — expectancy on a fat-tailed book jumps
                  around on single trades. */}
              <span className="relative h-3 rounded-sm bg-[var(--color-hover-bg)]">
                <i className={`absolute inset-y-0 left-0 rounded-sm ${
                  isBase ? 'bg-[var(--color-untested)]' : 'bg-[var(--color-took)]'}`}
                   style={{ width: `${Math.max(4, w * 100)}%` }} />
                <em className="absolute -top-0.5 text-[11px] font-mono not-italic
                               text-[var(--color-text-secondary)]"
                    style={{ left: `calc(${Math.max(4, w * 100)}% + 7px)` }}>
                  {p0(r.win)}
                </em>
              </span>
              <span className={`text-[11px] font-mono text-right ${
                r.mean < (base?.mean ?? 0) * 0.5
                  ? 'text-[var(--color-refused)]'
                  : 'text-[var(--color-text-secondary)]'}`}>
                {r1(r.mean)}
              </span>
            </div>
          )
        })}
      </div>

      <p className="text-[11px] text-[var(--color-text-muted)] mt-3.5 max-w-[64ch]">
        {t('loss.legend')}
      </p>

      {/* The line that decides. Without it the table above is a hot-hand story. */}
      {test && (
        <p className="text-[11px] mt-2 max-w-[64ch] border-l-2 pl-3
                      border-[var(--color-border)] text-[var(--color-text-secondary)]">
          {t(test.p < 0.05 ? 'loss.real' : 'loss.noise', {
            p: test.p < 0.001 ? '<0.001' : test.p.toFixed(3),
            runs: test.runs.toLocaleString(),
            gap: Math.abs(test.observed).toFixed(2),
          })}
        </p>
      )}
    </section>
  )
}
