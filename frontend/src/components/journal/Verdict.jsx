import { useMemo } from 'react'
import { useTradeJournal } from '../../hooks/useTradeJournal'
import { useLanguage } from '../../i18n/LanguageContext'
import { stageLeaks } from './lib/headCoach'

/**
 * One line: where you are strong, where you leak, and what to do about it.
 *
 * The first build of this was a 156px card and Andy's framework had it as a
 * layer of its own; the second build deleted it, arguing the four cards were
 * the ranking. Both were wrong in the same way — they treated "state" and
 * "what to do" as the same sentence. The cards show state. What they cannot
 * show is the action, and an action is the only thing you can start today.
 *
 * So: a compact state line naming BOTH ends — a page that only reports the
 * failure is not a reading of a book that is up 90% — and one line beneath it
 * that is an instruction.
 */
export default function Verdict({ onGo }) {
  const { t } = useLanguage()
  const { trades, loading } = useTradeJournal()
  const rows = useMemo(() => stageLeaks(trades), [trades])

  if (loading || rows.length < 2) return null

  const worst = rows[0]
  const best = rows[rows.length - 1]
  const lesson = Object.entries(worst.lessons || {}).sort((a, b) => b[1] - a[1])[0]

  return (
    <div className="mb-5">
      {/* The page fills the screen now (Andy, 2026-08-17), but a sentence still
          has a reading width — past about 75 characters the eye loses the line
          on the way back. So the page is wide and this stays a column. */}
      <p className="text-[13px] leading-relaxed m-0 max-w-[78ch]">
        <span className="text-[11px] font-mono uppercase tracking-[.2em]
                         text-[var(--color-text-muted)] mr-2.5">{t('rev.period')}</span>
        {t('verdict.state', { bestR: `${best.perTrade.toFixed(1)}R` })}
        <button type="button" onClick={() => onGo?.(worst.stage)}
                className="bg-transparent border-none p-0 mx-1 cursor-pointer font-semibold
                           text-[var(--color-text)] underline underline-offset-4
                           decoration-[var(--color-accent)]">
          {t(`rev.stage.${worst.stage}`)}
        </button>
        {/* Both halves of the sentence take their own vars. They were declared
            on one key and passed to the other, so the reader saw {worstN}. */}
        {lesson && t('verdict.mostly', {
          worstN: worst.n,
          worstR: `${worst.perTrade.toFixed(1)}R`,
          lesson: t(`rev.lesson.${lesson[0]}`),
          n: lesson[1],
        })}
      </p>
      {lesson && (
        <p className="text-[13px] text-[var(--color-text-secondary)] m-0 mt-1.5
                      border-l-2 border-[var(--color-accent)] pl-3">
          {t(`verdict.act.${lesson[0]}`)}
        </p>
      )}
    </div>
  )
}
