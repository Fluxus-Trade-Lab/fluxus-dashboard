/**
 * The trajectory: the chosen themes' four stretches, as lines and as state.
 *
 * Two synchronised readings of the same row of groups.json:
 *
 *   the LINES answer "by how much" — excess vs SPY per disjoint stretch,
 *   drawn as straight segments between measured points. Never splined: a
 *   curve through four samples manufactures readings between them, which is
 *   the exact sin the rest of this dashboard exists to avoid. TSF's smooth
 *   waves are interpolation wearing a measurement's clothes.
 *
 *   the HEATSTRIPS answer "in what state" — each stretch classified with the
 *   site's one state grammar: tone says strong or weak against SPY, fill says
 *   the gap is widening or narrowing versus the stretch before. Leading =
 *   solid strong, Weakening = outlined strong, Improving = solid weak,
 *   Lagging = outlined weak. Same vocabulary as every other theme surface, so
 *   nothing new to learn here. The first stretch has nothing before it, so it
 *   carries tone only, at half strength — direction unknown is not direction
 *   flat.
 *
 * The window chosen up top is shaded across both, so "what you are ranking
 * on" and "how it got there" stay visibly the same stretch of time.
 */
import { SEGMENTS } from './segments'

const TONE = { strong: 'var(--color-took)', weak: 'var(--color-untested)' }

/** One stretch → the state grammar. Returns null when unmeasured. */
function cellState(v, prev) {
  if (v == null || !Number.isFinite(v)) return null
  const tone = v > 0 ? 'strong' : 'weak'
  if (prev == null || !Number.isFinite(prev)) return { tone, dir: null }
  return { tone, dir: v > prev ? 'widening' : 'narrowing' }
}

const STATE_NAME = {
  'strong widening': 'Leading', 'strong narrowing': 'Weakening',
  'weak widening': 'Improving', 'weak narrowing': 'Lagging',
}

function Heatstrip({ row }) {
  const vals = SEGMENTS.map((s) => row[s.key])
  return (
    <div className="grid grid-cols-4 gap-[3px]" role="img"
         aria-label={`${row.group} state by stretch`}>
      {vals.map((v, i) => {
        const st = cellState(v, i > 0 ? vals[i - 1] : null)
        if (!st) {
          return <span key={i} className="h-[12px] border border-dashed"
                       style={{ borderColor: 'var(--color-untested)' }}
                       title={`${SEGMENTS[i].label}: not measured`} />
        }
        const name = st.dir ? STATE_NAME[`${st.tone} ${st.dir}`]
          : (st.tone === 'strong' ? 'ahead' : 'behind')
        const style = st.dir === 'narrowing'
          ? { border: `1px solid ${TONE[st.tone]}`, background: 'transparent' }
          : { background: TONE[st.tone], opacity: st.dir ? 1 : 0.5 }
        return <span key={i} className="h-[12px]" style={style}
                     title={`${SEGMENTS[i].label}: ${name}${st.dir ? '' : ' — no prior stretch to compare'} (${(v * 100).toFixed(1)}%)`} />
      })}
    </div>
  )
}

export default function TrajectoryPanel({ picks, byName, highlight }) {
  const chosen = picks
    .map((p) => ({ ...p, row: byName.get(p.name) }))
    .filter((p) => p.row)

  if (!chosen.length) {
    return (
      <div className="border border-dashed border-[var(--color-border)] rounded px-4 py-5
                      text-[11.5px] leading-relaxed text-[var(--color-text-muted)]">
        <span className="font-mono text-[9px] uppercase tracking-[.2em] block mb-1.5">
          Trajectory — waiting for a selection
        </span>
        Pick up to three themes above (chips, dots, or ranking rows all select) and their
        four stretches draw here — the line for how much, the strip for what state. This
        is the layer that tells a trend from a bounce: the ranking cannot.
      </div>
    )
  }

  const W = 1000, H = 190, PADX = 46, PADY = 22
  const n = SEGMENTS.length
  const xs = (i) => PADX + (i / (n - 1)) * (W - PADX * 2)
  const all = chosen.flatMap((c) => SEGMENTS.map((s) => c.row[s.key]))
    .filter((v) => Number.isFinite(v))
  const span = Math.max(...all.map(Math.abs), 0.02)
  const ys = (v) => H / 2 - (v / span) * (H / 2 - PADY)

  return (
    <div>
      <div className="relative">
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-[180px] block"
             preserveAspectRatio="none">
          {/* the window being ranked on, shaded under everything */}
          {highlight?.length > 0 && (
            <rect x={xs(Math.min(...highlight)) - (W - PADX * 2) / (n - 1) / 2}
                  y={4}
                  width={(Math.max(...highlight) - Math.min(...highlight)
                          + 1) * (W - PADX * 2) / (n - 1) * 0.999}
                  height={H - 8}
                  fill="var(--color-hover-bg)" />
          )}
          <line x1={PADX} x2={W - PADX} y1={H / 2} y2={H / 2}
                stroke="var(--color-text-muted)" strokeWidth="1"
                vectorEffect="non-scaling-stroke" />
          {SEGMENTS.map((s, i) => (
            <line key={s.key} x1={xs(i)} x2={xs(i)} y1={8} y2={H - 8}
                  stroke="var(--color-border)" strokeWidth="1"
                  vectorEffect="non-scaling-stroke" />
          ))}
          {chosen.map((c, ci) => {
            // Per-series label side: when two lines converge (the usual case at
            // the newest stretch), labels on the same side collide into one
            // unreadable smudge. Series 0 labels above, 1 below, 2 further
            // above — deterministic, no measuring.
            const dy = [-8, 16, -19][ci] ?? -8
            const pts = SEGMENTS.map((s, i) => {
              const v = c.row[s.key]
              return Number.isFinite(v) ? `${xs(i)},${ys(v)}` : null
            })
            // straight segments between measured points; a gap stays a gap
            const runs = []
            let cur = []
            pts.forEach((p) => {
              if (p) cur.push(p)
              else { if (cur.length > 1) runs.push(cur); cur = [] }
            })
            if (cur.length > 1) runs.push(cur)
            return (
              <g key={c.name}>
                {runs.map((r, j) => (
                  <polyline key={j} points={r.join(' ')} fill="none"
                            stroke={c.colour} strokeWidth="2"
                            vectorEffect="non-scaling-stroke" strokeLinejoin="round" />
                ))}
                {SEGMENTS.map((s, i) => {
                  const v = c.row[s.key]
                  if (!Number.isFinite(v)) return null
                  return (
                    <g key={s.key}>
                      <circle cx={xs(i)} cy={ys(v)} r="3.4" fill={c.colour} />
                      <text x={xs(i)} y={ys(v) + dy} textAnchor="middle"
                            style={{ font: '10px var(--font-mono, monospace)',
                                     fill: c.colour }}>
                        {v > 0 ? '+' : ''}{(v * 100).toFixed(1)}
                      </text>
                    </g>
                  )
                })}
              </g>
            )
          })}
        </svg>
        <span className="absolute left-1 top-1/2 -translate-y-1/2 text-[9px] font-mono
                         text-[var(--color-text-muted)] pointer-events-none">SPY</span>
      </div>

      <div className="flex justify-between px-[3%] text-[9px] font-mono
                      text-[var(--color-text-muted)]">
        {SEGMENTS.map((s, i) => (
          <span key={s.key} title={s.note}
                className={highlight?.includes(i) ? 'text-[var(--color-text-secondary)] font-semibold' : ''}>
            {s.label}
          </span>
        ))}
      </div>

      {/* one strip per theme: the same four stretches as state instead of size */}
      <div className="mt-3 space-y-1.5">
        {chosen.map((c) => (
          <div key={c.name}
               className="grid grid-cols-[minmax(130px,200px)_1fr] gap-3 items-center">
            <span className="text-[11.5px] truncate font-medium" style={{ color: c.colour }}>
              {c.name}
            </span>
            <Heatstrip row={c.row} />
          </div>
        ))}
      </div>

      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2.5 text-[10px]
                      text-[var(--color-text-muted)]">
        <span className="flex items-center gap-1.5">
          <i className="inline-block w-3.5 h-[10px]" style={{ background: TONE.strong }} />Leading
        </span>
        <span className="flex items-center gap-1.5">
          <i className="inline-block w-3.5 h-[10px] border"
             style={{ borderColor: TONE.strong }} />Weakening
        </span>
        <span className="flex items-center gap-1.5">
          <i className="inline-block w-3.5 h-[10px]" style={{ background: TONE.weak }} />Improving
        </span>
        <span className="flex items-center gap-1.5">
          <i className="inline-block w-3.5 h-[10px] border"
             style={{ borderColor: TONE.weak }} />Lagging
        </span>
        <span>
          · same grammar as the ranking bars — tone is ahead/behind, solid is widening,
          outlined is narrowing. Lines are straight between measured points; nothing is
          smoothed.
        </span>
      </div>
    </div>
  )
}
