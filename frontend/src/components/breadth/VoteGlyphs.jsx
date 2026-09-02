/**
 * The twelve votes, each carrying four things instead of one.
 *
 * Design: Fluxus_Brand/visual/explorations/2026-08-08/today_glyphs.html
 *
 *   fill      which side the vote is on
 *   the rule  the line it flips at
 *   height    how far it sits from that line, in its own unit
 *   dashed    it could not be counted at all
 *
 * Why this exists: with one bit per cell the reasoning had to be written out
 * underneath — "three of the nine are close to turning" was a sentence. It is
 * now three ringed dots and no sentence.
 *
 * Two rules the drawing holds:
 *
 *   · Heights are normalised inside each vote's own range and are never
 *     compared across two of them. A McClellan of 3.2 and 1.31 points of
 *     200-day breadth are not the same distance.
 *   · Up is always safer. The danger counts arrive as margin rather than as raw
 *     count for exactly this reason — plotted raw, fewer warnings would point
 *     down while every other mark points up.
 *
 * `vote_detail` comes from pipeline/screeners/breadth_signals.py, which owns the
 * thresholds. This file must not re-derive them; a second copy in JavaScript
 * drifts the first time one changes. When the payload predates that field this
 * renders nothing and the caller falls back.
 */

/** Below this share of its own range, a vote is sitting on its line. */
const ON_THE_LINE = 0.08

/** Per-vote half-range, in the vote's own unit — the frame each mark is drawn
 *  inside. Chosen to be wide enough that an ordinary day does not peg the top. */
const RANGE = {
  ratio_5d: 1.5, ratio_10d: 1.5, thrust: 300,
  qtr_spread: 400, spread_13_34: 400, nh_nl: 200,
  mcclellan: 70, pct200: 20, t2108_zone: 20,
  spy_danger: 5, qqq_danger: 5, bench_trend: 1,
}

/**
 * `stretch` lets the row spend all the width it is given instead of sitting at
 * its natural 12 × 58px. The dashboard's verdict card is the widest card on the
 * site since Andy's size grading (2026-08-18), and a fixed-width row inside it
 * left the most important graphic on the page occupying half its own card.
 * Off by default so the Market State page keeps the density it was drawn at.
 */
export default function VoteGlyphs({ detail, stretch = false }) {
  if (!detail?.length) return null

  return (
    <div>
      <div className="flex gap-2 items-end overflow-x-auto pb-1">
        {detail.map((d) => <Glyph key={d.key} d={d} stretch={stretch} />)}
      </div>
      <div className="flex flex-wrap gap-x-5 gap-y-1 mt-2 text-[11px] text-[var(--color-text-muted)]">
        <span className="flex items-center gap-1.5">
          <i className="block w-4 h-px bg-[var(--color-text)]" />the line it flips at
        </span>
        <span className="flex items-center gap-1.5">
          <i className="block w-2.5 h-2.5" style={{ background: 'var(--color-took)' }} />for
        </span>
        <span className="flex items-center gap-1.5">
          <i className="block w-2.5 h-2.5" style={{ background: 'var(--color-refused)' }} />against
        </span>
        <span className="flex items-center gap-1.5">
          <i className="block w-2.5 h-2.5 border border-dashed"
             style={{ borderColor: 'var(--color-untested)' }} />could not be counted
        </span>
        <span className="flex items-center gap-1.5">
          <i className="block w-2.5 h-2.5" style={{
            background: 'var(--color-took)',
            boxShadow: '0 0 0 2.5px rgba(184,134,11,.4)' }} />within a hair of its line
        </span>
        <span>height is inside each vote&rsquo;s own range — <b>up is always safer</b></span>
      </div>
    </div>
  )
}

function Glyph({ d, stretch }) {
  const range = RANGE[d.key] ?? 1
  const frac = d.margin == null ? 0 : Math.max(-1, Math.min(1, d.margin / range))
  const onLine = d.measurable && Math.abs(frac) < ON_THE_LINE
  const fill = !d.measurable ? 'transparent'
    : d.side === 'bear' ? 'var(--color-refused)'
    : d.side === 'bull' ? 'var(--color-took)' : 'var(--color-untested)'

  // 0 is the line, at mid-height; the dot rides above or below it
  const dotBottom = 50 + frac * 42

  return (
    <div className={stretch ? 'flex-1 min-w-[52px]' : 'w-[58px] shrink-0'}
         title={`${d.label} · ${d.side}`}>
      <div className="relative h-[62px] border-b border-[var(--color-border-light)]">
        <div className="absolute left-0 right-0 h-px bg-[var(--color-text)] opacity-50"
             style={{ bottom: '50%' }} />
        {d.measurable && (
          <div className="absolute left-1/2 -translate-x-1/2 w-[2px]"
               style={{
                 background: fill, opacity: .55,
                 bottom: `${Math.min(50, dotBottom)}%`,
                 height: `${Math.abs(dotBottom - 50)}%`,
               }} />
        )}
        <div className="absolute left-1/2 -translate-x-1/2 translate-y-1/2 w-[11px] h-[11px]"
             style={{
               bottom: `${d.measurable ? dotBottom : 50}%`,
               background: fill,
               border: d.measurable ? undefined : '1px dashed var(--color-untested)',
               boxShadow: onLine ? '0 0 0 2.5px rgba(184,134,11,.4)' : undefined,
             }} />
      </div>
      <div className="text-[11px] font-mono leading-[1.25] text-center mt-1.5
                      text-[var(--color-text-muted)] break-words">
        {d.label}
      </div>
      <div className="text-[13px] font-bold text-center leading-none mt-0.5"
           style={{ fontFamily: 'var(--font-cond)',
                    // v3: sitting exactly on the line is the vote nearest to
                    // turning — the binding one on this board, so it is red,
                    // not a gold nobody declared.
                    color: onLine ? 'var(--color-refused)'
                      : d.measurable ? 'var(--color-text)' : 'var(--color-text-muted)' }}>
        {d.margin == null ? '—' : fmt(d.margin)}
      </div>
      <div className="text-[11px] font-mono text-center text-[var(--color-text-muted)] leading-tight">
        {d.margin == null ? 'not counted' : d.unit}
      </div>
    </div>
  )
}

function fmt(v) {
  const a = Math.abs(v)
  const s = a >= 100 ? v.toFixed(0) : a >= 10 ? v.toFixed(1) : v.toFixed(2)
  return v > 0 ? `+${s}` : s
}


/* ------------------------------------------------------------------ */

/** Display labels for the flat fallback. vote_detail carries its own labels;
 *  until the pipeline emits it, the keys are the pipeline's and these are ours. */
const VOTE_LABEL = {
  ratio_5d: '5D ratio', ratio_10d: '10D ratio', thrust: 'Thrust',
  qtr_spread: 'Qtr spread', spread_13_34: '13/34', nh_nl: 'NH/NL',
  mcclellan: 'McClellan', pct200: '%>200d', t2108_zone: 'T2108',
  spy_danger: 'SPY risk regime', qqq_danger: 'QQQ risk regime', bench_trend: 'Bench trend',
}

/**
 * The twelve votes with three states and nothing else — the fallback for
 * payloads that predate `vote_detail`.
 *
 * Three states, not four, because three is what this payload measures. The
 * fourth dimension (distance from each vote's own line) exists only in
 * vote_detail; drawing it off data that is not there is the exact failure this
 * dashboard exists to avoid. When the field lands, the caller renders the full
 * glyphs instead and this stays as the degraded mode for old archives.
 *
 * No channel carries a vote alone: for = solid, against = hatched, undecided =
 * dashed outline — all three survive greyscale.
 */
export function VoteMarks({ votes }) {
  if (!votes) return null
  const entries = Object.entries(votes)
  const tally = entries.reduce((a, [, v]) => ({ ...a, [v]: (a[v] ?? 0) + 1 }), {})
  const HATCH = 'repeating-linear-gradient(45deg,rgba(0,0,0,.45) 0 1.7px,transparent 1.7px 5px)'
  const style = (v) =>
    v === 'bull' ? { background: 'var(--color-took)' }
    : v === 'bear' ? { background: 'var(--color-refused)', backgroundImage: HATCH }
    : { border: '1px dashed var(--color-untested)', background: 'transparent' }

  return (
    <div>
      {/* Six across, two rows. Twelve on one wrapping line broke at whatever
          width the column happened to be, so the grid changed shape as the
          layout did and the marks stopped being a fixed, countable object.
          Six and six also splits the ballot the way it is actually read:
          the breadth rules on top, the benchmark ones underneath. */}
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-x-2.5 gap-y-3">
        {entries.map(([key, v]) => (
          <span key={key} className="flex flex-col gap-1.5" title={`${VOTE_LABEL[key] ?? key}: ${v}`}>
            <i className="block w-full h-[32px]" style={style(v)} />
            <span className="text-[11px] font-mono leading-tight
                             text-[var(--color-text-muted)]">{VOTE_LABEL[key] ?? key}</span>
          </span>
        ))}
      </div>
      <div className="flex flex-wrap gap-x-5 gap-y-1 mt-4 text-[11px] text-[var(--color-text-muted)]">
        <span className="flex items-center gap-1.5">
          <i className="block w-3.5 h-[10px]" style={style('bull')} />for {tally.bull ?? 0}
        </span>
        <span className="flex items-center gap-1.5">
          <i className="block w-3.5 h-[10px]" style={style('bear')} />against {tally.bear ?? 0}
        </span>
        <span className="flex items-center gap-1.5">
          <i className="block w-3.5 h-[10px]" style={style('neutral')} />undecided {tally.neutral ?? 0}
        </span>

      </div>
    </div>
  )
}
