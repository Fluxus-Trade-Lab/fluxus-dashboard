import { useMemo } from 'react'
import { useTradeJournal } from '../../hooks/useTradeJournal'
import { headline, stageLeaks, STAGES } from './lib/headCoach'

const pct1 = (v) => `${v.toFixed(1)}R`

/**
 * One sentence: which of the four stages to work on, and the number that says so.
 *
 * Not a fifth analysis. The other four each answer a question about a part of
 * a trade; this one only decides which question is worth Andy's attention this
 * period, because he is one person and changes one thing at a time.
 */
export default function HeadCoach({ onGo }) {
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
                         text-[var(--color-text-muted)]">This period</span>
        <p className="text-[12.5px] text-[var(--color-text-muted)] m-0 mt-1.5">
          Not enough closed trades in two or more stages to rank them yet.
        </p>
      </section>
    )
  }

  const p = verdict.parts
  const worst = STAGES.find((s) => s.key === verdict.stage)

  return (
    <section className="rounded-3xl px-5 py-4 mb-4 bg-[var(--color-accent-solid)]">
      <span className="text-[10px] font-mono uppercase tracking-[.24em]
                       text-white/70">This period</span>
      <p className="text-[15px] leading-relaxed text-white m-0 mt-1.5">
        Your leak is not in <b className="font-semibold">{p.bestLabel}</b>{' '}
        ({p.bestN} trades, {pct1(p.bestPerTrade)} left on the table each) —
        it is in{' '}
        <button type="button" onClick={() => onGo?.(verdict.stage)}
                className="bg-transparent border-none p-0 cursor-pointer text-white
                           font-semibold underline underline-offset-4
                           decoration-white/50 hover:decoration-white">
          {worst?.label}
        </button>
        : {p.worstN} trades, <b className="font-semibold">{pct1(p.worstPerTrade)}</b> each.
        {verdict.lesson && (
          <> Mostly <b className="font-semibold">{verdict.lesson.lesson}</b>{' '}
            ({verdict.lesson.n}).</>
        )}
      </p>
      {/* The ranking is shown, not just its winner — a verdict you cannot check
          is an opinion. */}
      <div className="mt-3 pt-3 border-t border-white/20 flex flex-wrap gap-x-5 gap-y-1">
        {rows.map((r) => {
          const s = STAGES.find((x) => x.key === r.stage)
          return (
            <span key={r.stage}
                  className={`text-[11px] font-mono ${
                    r.stage === verdict.stage ? 'text-white' : 'text-white/60'}`}>
              {s?.label} {pct1(r.perTrade)}<span className="text-white/45"> ·{r.n}</span>
            </span>
          )
        })}
        <span className="text-[10px] font-mono text-white/45">
          左侧为每笔未吃到的 R = Σ(最优 − 已实现) ÷ 笔数
        </span>
      </div>
    </section>
  )
}
