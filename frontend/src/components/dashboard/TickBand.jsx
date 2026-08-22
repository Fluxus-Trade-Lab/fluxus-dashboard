/**
 * The TICK band — a width, drawn as a width.
 *
 * WHY THIS IS NOT A COLOURED LIGHT. The data side proposed grind = red,
 * washout = green. Both halves of that are wrong for this page, and the
 * payload's own numbers say so:
 *
 *   Entering the contracted band cuts the next 21 days' median return roughly
 *   in half (+1.1% vs +1.6%) and CUTS the probability of a 5% drawdown — 9.9%
 *   against a 15.4% baseline over 17 years. A red light next to a sentence
 *   reading "磨，不是崩" would contradict the sentence it sits on.
 *
 *   And red is already spoken for here. Six inches above, the regime badge
 *   turns red only when the band itself binds what you may carry. A second red
 *   meaning "returns thin out while drawdown risk falls" makes one token do two
 *   jobs, which is the failure this design system has a rule about.
 *
 *   Green/red as bad/good is the dopamine grammar the whole dashboard refuses.
 *
 * So: draw the measurement. The reading IS a spread — the TICK's high and low
 * envelope contracting or opening — so it is two rules whose gap is the value,
 * with the 252-day percentile placing that gap against its own year. Nothing
 * here can be mistaken for an alarm, because nothing here is a side.
 */
import { useTickCycle } from '../../hooks/useTickCycle'

const LABEL = { grind: '收缩', washout: '张开', neutral: '中性' }
const STALE_AFTER = 7

/** Two rules, and the gap between them. Width is the whole reading, so width
 *  is what moves; the frame stays put so two days are comparable by eye. */
function Spread({ rank }) {
  const W = 88, H = 34, PAD = 3
  // rank 0 = tightest in a year, 1 = widest. Floor the gap so a contracted
  // band is still legibly two lines and not one thick one.
  const gap = 3 + (rank ?? 0.5) * (H - PAD * 2 - 3)
  const mid = H / 2
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} aria-hidden="true" className="shrink-0">
      {[mid - gap / 2, mid + gap / 2].map((y, i) => (
        <line key={i} x1={PAD} x2={W - PAD} y1={y} y2={y} strokeWidth="1.6"
              stroke="var(--color-text)" vectorEffect="non-scaling-stroke" />
      ))}
      {/* the year's own extremes, so the gap is placed rather than just drawn */}
      {[PAD, H - PAD].map((y, i) => (
        <line key={`e${i}`} x1={PAD} x2={W - PAD} y1={y} y2={y} strokeWidth="1"
              stroke="var(--color-border)" strokeDasharray="2 3"
              vectorEffect="non-scaling-stroke" />
      ))}
    </svg>
  )
}

export default function TickBand() {
  const { data, loading } = useTickCycle()
  if (loading || !data) return null

  const stale = (data.stale_days ?? 0) > STALE_AFTER
  const rankPct = data.spread_rank252 == null ? null : data.spread_rank252 * 100

  return (
    <section className="rounded-3xl bg-[var(--color-surface)] px-6 py-5">
      <div className="flex items-start gap-5 flex-wrap">
        <div className="flex items-center gap-4">
          <Spread rank={stale ? null : data.spread_rank252} />
          <div>
            <div className="text-[10px] font-mono uppercase tracking-[.24em]
                            text-[var(--color-text-muted)]">TICK 带</div>
            <div className="text-[19px] font-semibold leading-tight tracking-tight
                            text-[var(--color-text-bold)]"
                 style={{ fontFamily: 'var(--font-cond)' }}>
              {LABEL[data.band] ?? data.band}
              {rankPct != null && !stale && (
                <span className="ml-2 text-[12.5px] font-mono font-normal tabular-nums
                                 text-[var(--color-text-muted)]">
                  {/* the payload's own sentence says "一年 2% 分位"; the
                      badge beside it must not say "2 分位" and read as a rank */}
                  一年 {rankPct < 1 ? rankPct.toFixed(1) : Math.round(rankPct)}% 分位
                </span>
              )}
            </div>
            {data.band_since && !stale && (
              <div className="text-[11px] font-mono text-[var(--color-text-muted)] mt-0.5">
                {data.band_since} 入带
              </div>
            )}
          </div>
        </div>

        {stale ? (
          /* the site's rule: absent is not zero, and a reading nobody took
             today is not a reading of "neutral" */
          <p className="m-0 flex-1 min-w-[260px] text-[12.5px] leading-relaxed
                        text-[var(--color-text-muted)] italic">
            未测量 —— tick_cycle.json 已经 {data.stale_days} 天没更新
            （{data.as_of}）。上面的形状是占位，不是今天的读数。
          </p>
        ) : (
          <>
            {/* the engine's own sentence, printed. It already carries the thing
                a colour would have got wrong: 磨，不是崩。 */}
            <p className="m-0 flex-1 min-w-[280px] text-[12.5px] leading-relaxed
                          text-[var(--color-text-secondary)]">
              {data.reading}
            </p>
          </>
        )}
      </div>
    </section>
  )
}
