import { useState } from 'react'

import { useLanguage } from '../../../i18n/LanguageContext'
import { rich } from '../../screener/richText'

/*
 * Van Tharp position-sizing curriculum — living module.
 * To add a lesson: append its key to LESSONS and its text to the dictionary
 * (frontend/src/i18n/parts/journal.js, jn.tharp.<key>.title / sub / principle /
 * stat / value / read / source), in both languages.
 * Sources: Van Tharp, "Definitive Guide to Position Sizing" (DGPS);
 * LordFed, "Size Matters" (lordfed.co.uk/p/size-matters).
 * Account numbers: H1 2026 audit (331 closed trades, 2025-12-31 → 2026-07-22).
 */
const LESSONS = [
  'r-multiples', 'how-much-separate', 'percent-risk', 'percent-volatility',
  'anti-martingale', 'kelly-trap', 'discipline-over-prediction',
]

export default function TharpLessons() {
  const { t } = useLanguage()
  const [expanded, setExpanded] = useState(null)

  return (
    <div>
      <h3 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-1">
        {t('jn.tharp.title')}
      </h3>
      <p className="text-[11px] text-[var(--color-text-muted)] mb-3">
        {t('jn.tharp.lede')}
      </p>
      <div className="space-y-2">
        {LESSONS.map(key => {
          const lesson = { key }
          const L = (f) => t(`jn.tharp.${key}.${f}`)
          const isExpanded = expanded === lesson.key
          return (
            <div key={lesson.key} className="bg-[var(--color-surface)] rounded-3xl overflow-hidden">
              <button
                onClick={() => setExpanded(isExpanded ? null : lesson.key)}
                className="w-full flex items-center justify-between px-4 py-3 text-left cursor-pointer hover:bg-[var(--color-hover-bg)] transition-colors"
              >
                <div>
                  <span className="text-[13px] font-semibold text-[var(--color-text)]">{L('title')}</span>
                  <span className="text-[11px] text-[var(--color-text-muted)] ml-2 hidden sm:inline">{L('sub')}</span>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-[11px] font-mono font-semibold text-[var(--color-text-secondary)]">{L('value')}</span>
                  <span className="text-[var(--color-text-muted)] text-[13px]">{isExpanded ? '−' : '+'}</span>
                </div>
              </button>

              {isExpanded && (
                <div className="px-4 pb-4 space-y-3 border-t border-[var(--color-border-light)]">
                  <p className="text-[13px] text-[var(--color-text-secondary)] leading-relaxed pt-3">
                    {rich(L('principle'))}
                  </p>
                  <div className="bg-[var(--color-bg)] rounded px-3 py-2">
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
                        {L('stat')}
                      </span>
                      <span className="text-[11px] font-mono uppercase tracking-wide px-1.5 py-0.5 rounded border border-[var(--color-border-light)] text-[var(--color-text-muted)] shrink-0">
                        {t('jn.tharp.ref')}
                      </span>
                    </div>
                    <span className="text-[13px] font-semibold font-mono text-[var(--color-text)]">{L('value')}</span>
                    <p className="text-[11px] text-[var(--color-text-secondary)] leading-relaxed mt-1">
                      {rich(L('read'))}
                    </p>
                  </div>
                  <p className="text-[11px] text-[var(--color-text-muted)]">{L('source')}</p>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
