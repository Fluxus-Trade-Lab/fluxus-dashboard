/**
 * The comparison: the chosen themes' four stretches, as lines and as state.
 *
 * The LINES answer "by how much" — excess vs SPY per disjoint stretch, drawn
 * straight between measured points. Never splined: a curve through four
 * samples manufactures readings between them, which is the exact sin the rest
 * of this dashboard exists to avoid.
 *
 * Lines are labelled AT THEIR ENDS — name and latest value in the line's own
 * colour — instead of through a legend. Direct labelling is the difference
 * between reading a chart and decoding one: the eye never leaves the line to
 * look up what it was. Intermediate values live in hover titles; printing
 * every point was the old version's clutter.
 *
 * The HEATSTRIPS below are the same four stretches as state, in the site's
 * one grammar: tone = ahead/behind SPY, solid = widening, outlined =
 * narrowing — which IS Leading/Weakening/Improving/Lagging. The first stretch
 * has no predecessor, so it carries tone only at half strength: direction
 * unknown is not direction flat.
 *
 * The window chosen up top is shaded across the chart, so "what you are
 * ranking on" and "how it got there" stay visibly the same stretch of time.
 */
import { SEGMENTS } from './segments'

const TONE = { strong: 'var(--color-took)', weak: 'var(--color-untested)' }

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
      <div className="h-[52px] rounded border border-dashed border-[var(--color-border)]
                      flex items-center px-4 text-[11.5px] text-[var(--color-text-muted)]">
        Pick up to three themes — search above, or click a dot or a row.
      </div>
    )
  }

  // Geometry in svg, text in HTML: the svg stretches non-uniformly to fill
  // its column, which distorts glyphs — the first version's end labels came
  // out widened and clipped. HTML overlays position by percentage and stay
  // crisp at any width.
  const H = 190, PADY = 24
  const LEFT = 5, RIGHT = 20            // % of width reserved either side
  const n = SEGMENTS.length
  const xsPct = (i) => LEFT + (i / (n - 1)) * (100 - LEFT - RIGHT)
  const all = chosen.flatMap((c) => SEGMENTS.map((s) => c.row[s.key]))
    .filter((v) => Number.isFinite(v))
  const span = Math.max(...all.map(Math.abs), 0.02)
  const ys = (v) => H / 2 - (v / span) * (H / 2 - PADY)

  // End labels in HTML, nudged apart so converging lines cannot smear them.
  const ends = chosen.map((c) => {
    let last = null
    SEGMENTS.forEach((s) => {
      if (Number.isFinite(c.row[s.key])) last = c.row[s.key]
    })
    return last != null && { c, y: ys(last), v: last }
  }).filter(Boolean).sort((a, b) => a.y - b.y)
  for (let i = 1; i < ends.length; i++) {
    if (ends[i].y - ends[i - 1].y < 16) ends[i].y = ends[i - 1].y + 16
  }

  return (
    <div>
      <div className="relative">
        <svg viewBox={`0 0 1000 ${H}`} className="w-full h-[190px] block"
             preserveAspectRatio="none">
          {highlight?.length > 0 && (
            <rect x={(xsPct(Math.min(...highlight)) - (100 - LEFT - RIGHT) / (n - 1) / 2) * 10}
                  y={4}
                  width={(Math.max(...highlight) - Math.min(...highlight) + 1)
                         * (100 - LEFT - RIGHT) / (n - 1) * 10 * 0.999}
                  height={H - 8}
                  fill="var(--color-hover-bg)" opacity="0.45" />
          )}
          <line x1={LEFT * 10} x2={(100 - RIGHT) * 10 + 30} y1={H / 2} y2={H / 2}
                stroke="var(--color-text-muted)" strokeWidth="1"
                vectorEffect="non-scaling-stroke" />
          {SEGMENTS.map((s, i) => (
            <line key={s.key} x1={xsPct(i) * 10} x2={xsPct(i) * 10} y1={10} y2={H - 10}
                  stroke="var(--color-border)" strokeWidth="1"
                  vectorEffect="non-scaling-stroke" />
          ))}

          {chosen.map((c) => {
            const pts = SEGMENTS.map((s, i) => {
              const v = c.row[s.key]
              return Number.isFinite(v) ? `${xsPct(i) * 10},${ys(v)}` : null
            })
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
                    <circle key={s.key} cx={xsPct(i) * 10} cy={ys(v)} r="3.4" fill={c.colour}>
                      <title>{c.name} · {s.label}: {v > 0 ? '+' : ''}{(v * 100).toFixed(1)}%</title>
                    </circle>
                  )
                })}
              </g>
            )
          })}
        </svg>

        <span className="absolute text-[10px] font-mono text-[var(--color-text-muted)]
                         pointer-events-none"
              style={{ left: `${LEFT}%`, top: H / 2, transform: 'translate(-110%, -50%)' }}>
          SPY
        </span>
        {/* the chart's own extent — an axis without numbers is not an axis,
            which was this page's first finding and applies to itself */}
        <span className="absolute text-[9px] font-mono text-[var(--color-text-muted)]
                         pointer-events-none" style={{ left: `${LEFT + 0.5}%`, top: 2 }}>
          +{(span * 100).toFixed(0)}%
        </span>
        <span className="absolute text-[9px] font-mono text-[var(--color-text-muted)]
                         pointer-events-none" style={{ left: `${LEFT + 0.5}%`, bottom: 2 }}>
          −{(span * 100).toFixed(0)}%
        </span>
        {ends.map(({ c, y, v }) => (
          <span key={c.name}
                className="absolute text-[11px] font-mono whitespace-nowrap
                           pointer-events-none -translate-y-1/2"
                style={{ left: `${100 - RIGHT + 1.2}%`, top: y, color: c.colour }}>
            {c.name.length > 18 ? `${c.name.slice(0, 17)}…` : c.name}
            {' '}{v > 0 ? '+' : ''}{(v * 100).toFixed(1)}%
          </span>
        ))}
      </div>

      <div className="flex justify-between text-[9px] font-mono
                      text-[var(--color-text-muted)]"
           style={{ paddingLeft: `${LEFT - 1}%`, paddingRight: `${RIGHT - 1}%` }}>
        {SEGMENTS.map((s, i) => (
          <span key={s.key} title={s.note}
                className={highlight?.includes(i)
                  ? 'text-[var(--color-text-secondary)] font-semibold' : ''}>
            {s.label}
          </span>
        ))}
      </div>

      {/* Strips share the chart's plot edges — two objects on two coordinate
          systems read as two charts that happen to be stacked. The name lives
          at the line's end already; a colour dot is identity enough here. */}
      <div className="mt-2.5 space-y-[5px]">
        {chosen.map((c) => (
          <div key={c.name} className="relative"
               style={{ paddingLeft: `${LEFT}%`, paddingRight: `${RIGHT}%` }}>
            <span className="absolute top-1/2 -translate-y-1/2 w-2 h-2 rounded-full"
                  style={{ left: `calc(${LEFT}% - 17px)`, background: c.colour }}
                  title={c.name} />
            <Heatstrip row={c.row} />
          </div>
        ))}
      </div>
    </div>
  )
}
