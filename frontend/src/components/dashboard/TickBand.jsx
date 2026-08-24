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
 *   reading "a grind, not a break" would contradict the sentence it sits on.
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

const LABEL = { grind: 'Contracted', washout: 'Open', neutral: 'Neutral' }
const STALE_AFTER = 7

/** `2026-08-06` → `Aug 6`. Parsed as UTC so the date string keeps its day. */
function niceDate(iso) {
  if (!iso) return null
  const d = new Date(`${iso}T00:00:00Z`)
  return Number.isNaN(d.getTime()) ? iso : new Intl.DateTimeFormat('en-US', {
    month: 'short', day: 'numeric', timeZone: 'UTC' }).format(d)
}

const pc = (v) => (v == null ? null : `${v > 0 ? '+' : ''}${(v * 100).toFixed(1)}%`)
const pp = (v) => (v == null ? null : `${(v * 100).toFixed(1)}%`)

/**
 * The reading, in English, said as a conclusion.
 *
 * The payload ships its own sentence in Chinese (`data.reading`). Andy asked
 * for English here on 2026-08-24, and rather than wait on the data side this
 * builds the sentence from the same structured fields the Chinese one is built
 * from — `band`, `band_since`, `spread_rank252` and the `evidence` block — so
 * there is one source of numbers, not a translation that can drift from it.
 *
 * WHAT IT HAS TO GET ACROSS, because a colour would get it wrong: entering the
 * contracted band halves the next 21 days' median return AND lowers the odds
 * of a 5% drawdown. Thinner, not more dangerous. The last clause says so in
 * five words because that is the only part a reader must not miss.
 */
function englishReading(d) {
  const e = d.evidence ?? {}
  const since = niceDate(d.band_since)
  const rank = d.spread_rank252 == null ? null
    : (d.spread_rank252 * 100 < 1 ? (d.spread_rank252 * 100).toFixed(1)
                                  : Math.round(d.spread_rank252 * 100))
  if (d.band === 'grind') {
    return [
      since && `Since ${since} the TICK's high–low band has been contracted`,
      rank != null && `${since ? ' — ' : "The TICK's high–low band is "}the tightest ${rank}% of the past year`,
      '. ',
      e.n_sell_entries && e.window_years
        && `In ${e.window_years} years there are ${e.n_sell_entries} entries into this band: `,
      e.sell_fwd21_med != null && e.base_fwd21_med != null
        && `the next 21 sessions returned ${pc(e.sell_fwd21_med)} at the median against ${pc(e.base_fwd21_med)} normally`,
      e.sell_p_dd5 != null && e.base_p_dd5 != null
        && `, and a 5% drawdown followed ${pp(e.sell_p_dd5)} of the time against ${pp(e.base_p_dd5)}`,
      '. Returns thin out; risk does not rise. A grind, not a break.',
    ].filter(Boolean).join('')
  }
  if (d.band === 'washout') {
    return [
      since && `Since ${since} the TICK's high–low band has been wide open`,
      rank != null && ` — the widest ${100 - rank}% of the past year`,
      '. That is the flush end of the cycle, where this indicator has historically been a buy window rather than a warning.',
    ].filter(Boolean).join('')
  }
  return `The TICK's high–low band is neither contracted nor open${
    since ? `, and has been since ${since}` : ''}. No timing read from this one today.`
}

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
                            text-[var(--color-text-muted)]">TICK band</div>
            <div className="text-[19px] font-semibold leading-tight tracking-tight
                            text-[var(--color-text-bold)]"
                 style={{ fontFamily: 'var(--font-cond)' }}>
              {LABEL[data.band] ?? data.band}
              {rankPct != null && !stale && (
                <span className="ml-2 text-[12.5px] font-mono font-normal tabular-nums
                                 text-[var(--color-text-muted)]">
                  {/* a percentile of its own year, not a rank out of anything —
                      "2nd percentile" would read as second-place */}
                  {rankPct < 1 ? rankPct.toFixed(1) : Math.round(rankPct)}% of its year
                </span>
              )}
            </div>
            {data.band_since && !stale && (
              <div className="text-[11px] font-mono text-[var(--color-text-muted)] mt-0.5">
                since {data.band_since}
              </div>
            )}
          </div>
        </div>

        {stale ? (
          /* the site's rule: absent is not zero, and a reading nobody took
             today is not a reading of "neutral" */
          <p className="m-0 flex-1 min-w-[260px] text-[12.5px] leading-relaxed
                        text-[var(--color-text-muted)] italic">
            Not measured — tick_cycle.json has not updated in {data.stale_days} days
            (last {data.as_of}). The shape above is a placeholder, not today's reading.
          </p>
        ) : (
          <>
            <p className="m-0 flex-1 min-w-[280px] text-[12.5px] leading-relaxed
                          text-[var(--color-text-secondary)]">
              {englishReading(data)}
            </p>
          </>
        )}
      </div>
    </section>
  )
}
