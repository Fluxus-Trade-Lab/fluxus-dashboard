import { useMemo } from 'react'
import { useTradeJournal } from '../../hooks/useTradeJournal'
import { useLanguage } from '../../i18n/LanguageContext'
import { headline, stageLeaks } from './lib/headCoach'

const pct1 = (v) => `${v.toFixed(1)}R`

/**
 * One sentence: which of the four stages to work on, and the number that says so.
 *
 * Not a fifth analysis. The other four each answer a question about a part of
 * a trade; this one only decides which question is worth Andy's attention this
 * period, because he is one person and changes one thing at a time.
 */
export default function HeadCoach({ onGo }) {
  const { t } = useLanguage()
  const { trades, loading } = useTradeJournal()
  const verdict = useMemo(() => headline(trades), [trades])
  const rows = useMemo(() => stageLeaks(trades), [trades])

  if (loading) return null

  if (!verdict) {
    // Deliberately not a cheerful default. A page that always has a verdict is
    // not measuring anything.
    return (
      <section className="rounded-3xl border border-dashed border-[var(--color-border)]
                          px-5 py-4 mb-4">
        <span className="text-[10px] font-mono uppercase tracking-[.24em]
                         text-[var(--color-text-muted)]">{t('rev.period')}</span>
        <p className="text-[12.5px] text-[var(--color-text-muted)] m-0 mt-1.5">
          {t('rev.verdict.none')}
        </p>
      </section>
    )
  }

  const p = verdict.parts
  const best = { stage: rows[rows.length - 1]?.stage }

  return (
    <section className="rounded-3xl px-5 py-4 mb-4 bg-[var(--color-accent-solid)]">
      <span className="text-[10px] font-mono uppercase tracking-[.24em]
                       text-white/70">{t('rev.period')}</span>
      {/* The sentence is one translated string with a {worst} placeholder, split
          here to put the link in. Assembling it from fragments instead would fix
          the word order to whichever language was written first. */}
      <p className="text-[15px] leading-relaxed text-white m-0 mt-1.5">
        {(() => {
          const sentence = t('rev.verdict', {
            best: t(`rev.stage.${best.stage}`), bestN: p.bestN, bestR: pct1(p.bestPerTrade),
            worstN: p.worstN, worstR: pct1(p.worstPerTrade), worst: '\u0000',
          })
          const [head, tail] = sentence.split('\u0000')
          return (
            <>
              {head}
              <button type="button" onClick={() => onGo?.(verdict.stage)}
                      className="bg-transparent border-none p-0 cursor-pointer text-white
                                 font-semibold underline underline-offset-4
                                 decoration-white/50 hover:decoration-white">
                {t(`rev.stage.${verdict.stage}`)}
              </button>
              {tail}
            </>
          )
        })()}
        {verdict.lesson && ' ' + t('rev.verdict.lesson', {
          lesson: t(`rev.lesson.${verdict.lesson.lesson}`), lessonN: verdict.lesson.n,
        })}
      </p>
      {/* The ranking is shown, not just its winner — a verdict you cannot check
          is an opinion. */}
      <div className="mt-3 pt-3 border-t border-white/20 flex flex-wrap gap-x-5 gap-y-1">
        {rows.map((r) => (
            <span key={r.stage}
                  className={`text-[11px] font-mono ${
                    r.stage === verdict.stage ? 'text-white' : 'text-white/60'}`}>
              {t(`rev.stage.${r.stage}`)} {pct1(r.perTrade)}<span className="text-white/45"> ·{r.n}</span>
            </span>
        ))}
        <span className="text-[10px] font-mono text-white/45">
          {t('rev.verdict.method')}
        </span>
      </div>
    </section>
  )
}
