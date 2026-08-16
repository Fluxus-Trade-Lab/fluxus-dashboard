/**
 * The comparison: the chosen themes' four stretches, as a curve and a ribbon.
 *
 * BOTH prettier forms are allowed by the encoding rules, each under one law:
 *
 * The CURVE is monotone cubic (Fritsch–Carlson), not a free spline. A straight
 * segment and a curve are both assumptions about the unmeasured space between
 * two samples; what a free spline adds — and what stays forbidden — is
 * OVERSHOOT: highs and lows that were never measured. Monotone interpolation
 * cannot leave the range of its neighbouring samples, so the curve is exactly
 * as honest as the polyline it replaces, and the measured points stay drawn
 * on top of it.
 *
 * The RIBBON is the heatstrip rebuilt as a value gradient. A gradient between
 * two measured colours is linear interpolation in colour space — the same
 * assumption as the line segment between two measured points. The anchors are
 * the four measurements; between anchors, linear; nothing else. Tone still
 * carries the one grammar: blue for ahead of SPY, grey for behind, intensity
 * for how far. Discrete four-state cells threw away magnitude that the data
 * had; the gradient keeps it.
 *
 * The window chosen up top is shaded across the chart, so "what you are
 * ranking on" and "how it got there" stay visibly the same stretch of time.
 *
 * 2026-08-16 — the y-axis is excess PER SESSION, not the stretch's total, and
 * the chart covers the quarter only. Both changes are Andy's call and the
 * first one is not cosmetic.
 *
 * The stretches are 42, 16 and 5 sessions long. Plotted raw, a shorter stretch
 * yields a smaller number for purely mechanical reasons, so almost every theme
 * appears to fade toward the right edge — including ones whose pace has not
 * changed at all. High Octane read +34.7% → +12.9% → +3.8%, which looks like a
 * collapse; per session it is 0.83% → 0.81% → 0.76%, which is a straight line.
 * Cybersecurity runs the other way: +35.7% → +1.8% → −0.3% reads as a slowdown
 * while per session it is 0.85% → 0.11% → −0.06%, already negative.
 *
 * Dividing by the stretch's length is the whole fix, and it lands the axis on
 * the same quantity the field quadrant plots vertically (acceleration), so the
 * two layers of this page now corroborate instead of each saying its own thing.
 * The stretch's own total is not lost — it is in every dot's tooltip.
 */
import { SEGMENTS, QUARTER_SEGMENTS, ratePerSession } from './segments'
import { slotDash } from './useThemeCompare'
import { barStyle } from './ThemeBars'

/**
 * The real fortnight ribbon, when the archive carries it: five segments of
 * {state, level, accel}, drawn in THIS page's grammar (tone + fill via
 * barStyle) — not StateRibbon's four-hue palette. One page, one grammar; the
 * same four words must not wear two palettes on one screen.
 *
 * Its time axis is five fortnights, which is NOT the curve's four stretches —
 * so the caller only uses it when EVERY chosen theme has one, and labels the
 * axis once. Mixing real-fortnight rows with synthetic-stretch rows in one
 * stack would put two time axes in one object.
 */
function FortnightRibbon({ ribbon, group }) {
  return (
    <div className="grid grid-cols-5 gap-[3px]" role="img"
         aria-label={`${group} state by fortnight`}>
      {ribbon.map((seg, i) => (
        seg?.state ? (
          <span key={i} className="h-[10px]" style={barStyle(seg.state)}
                title={`${seg.state} · level ${(seg.level * 100).toFixed(1)}% · accel ${(seg.accel * 100).toFixed(1)}pp — state computed on month-scale windows; each block is a fortnight of drawing`} />
        ) : (
          <span key={i} className="h-[10px] border border-dashed"
                style={{ borderColor: 'var(--color-untested)' }} title="not measured" />
        )
      ))}
    </div>
  )
}

/** Excess value → colour. Anchors only; the gradient does the interpolation. */
function valueColour(v, span) {
  if (v == null || !Number.isFinite(v)) return 'transparent'
  const tone = v > 0 ? 'var(--color-took)' : 'var(--color-refused)'
  const strength = Math.round(12 + 78 * Math.min(1, Math.abs(v) / span))
  return `color-mix(in srgb, ${tone} ${strength}%, transparent)`
}

/**
 * One theme's four stretches as a continuous ribbon. Gradient stops sit at
 * the same x as the chart's sample columns, so ribbon and curve are one
 * coordinate system. Hover splits into the four measured stretches, each
 * titled with its own number — the beauty is continuous, the measurements
 * stay countable.
 */
function Ribbon({ row, span, xsPct }) {
  const vals = QUARTER_SEGMENTS.map((s) => ratePerSession(row, s))
  const stops = vals.map((v, i) => `${valueColour(v, span)} ${xsPct(i)}%`)
  return (
    <div className="relative h-[10px]"
         style={{ background: `linear-gradient(90deg, ${stops.join(', ')})` }}
         role="img" aria-label={`${row.group} excess by stretch`}>
      {QUARTER_SEGMENTS.map((seg, i) => {
        const v = vals[i]
        const lo = i === 0 ? 0 : (xsPct(i - 1) + xsPct(i)) / 2
        const hi = i === QUARTER_SEGMENTS.length - 1 ? 100 : (xsPct(i) + xsPct(i + 1)) / 2
        const dead = v == null || !Number.isFinite(v)
        return (
          <span key={seg.key} className="absolute inset-y-0"
                style={{ left: `${lo}%`, width: `${hi - lo}%`,
                         /* an unmeasured stretch must not fade elegantly into
                            its neighbours — it wears the dashed outline */
                         border: dead ? '1px dashed var(--color-untested)' : undefined }}
                title={`${seg.label}: ${dead ? 'not measured'
                  : `${v > 0 ? '+' : ''}${(v * 100).toFixed(2)}%/session`
                    + ` · ${seg.sessions} sessions · stretch total `
                    + `${row[seg.key] > 0 ? '+' : ''}${(row[seg.key] * 100).toFixed(1)}%`}`} />
        )
      })}
    </div>
  )
}

/**
 * Monotone cubic (Fritsch–Carlson) through the measured points, emitted as
 * cubic Béziers. Tangents are clamped so the curve never leaves the range of
 * its neighbouring samples — smooth, but incapable of inventing an extreme.
 */
function monotonePath(pts) {
  if (pts.length < 2) return ''
  if (pts.length === 2) {
    return `M${pts[0][0]},${pts[0][1]} L${pts[1][0]},${pts[1][1]}`
  }
  const n = pts.length
  const dx = [], dy = [], slope = []
  for (let i = 0; i < n - 1; i++) {
    dx.push(pts[i + 1][0] - pts[i][0])
    dy.push(pts[i + 1][1] - pts[i][1])
    slope.push(dy[i] / dx[i])
  }
  const m = [slope[0]]
  for (let i = 1; i < n - 1; i++) {
    if (slope[i - 1] * slope[i] <= 0) m.push(0)
    else {
      const w1 = 2 * dx[i] + dx[i - 1], w2 = dx[i] + 2 * dx[i - 1]
      m.push((w1 + w2) / (w1 / slope[i - 1] + w2 / slope[i]))
    }
  }
  m.push(slope[n - 2])
  let path = `M${pts[0][0]},${pts[0][1]}`
  for (let i = 0; i < n - 1; i++) {
    const c1x = pts[i][0] + dx[i] / 3
    const c1y = pts[i][1] + (m[i] * dx[i]) / 3
    const c2x = pts[i + 1][0] - dx[i] / 3
    const c2y = pts[i + 1][1] - (m[i + 1] * dx[i]) / 3
    path += ` C${c1x.toFixed(1)},${c1y.toFixed(1)} ${c2x.toFixed(1)},${c2y.toFixed(1)} ${pts[i + 1][0]},${pts[i + 1][1]}`
  }
  return path
}

export default function TrajectoryPanel({ picks, byName, highlight }) {
  const chosen = picks
    .map((p) => ({ ...p, row: byName.get(p.name) }))
    .filter((p) => p.row)

  if (!chosen.length) {
    // This ran to 189ch on a wide screen — one line of prose stretched across
    // the whole card. A measure keeps it readable at any width.
    return (
      <div className="min-h-[52px] rounded-2xl border border-dashed border-[var(--color-border)]
                      flex items-center px-4 py-3">
        <p className="m-0 max-w-[62ch] text-[11px] leading-relaxed
                      text-[var(--color-text-muted)]">
          Pick up to three themes — search above, or click a dot or a row.
        </p>
      </div>
    )
  }

  // Geometry in svg, text in HTML: the svg stretches non-uniformly to fill
  // its column, which distorts glyphs — the first version's end labels came
  // out widened and clipped. HTML overlays position by percentage and stay
  // crisp at any width.
  const H = 190, PADY = 24
  const LEFT = 5, RIGHT = 20            // % of width reserved either side
  const SEG = QUARTER_SEGMENTS
  const n = SEG.length
  const xsPct = (i) => LEFT + (i / (n - 1)) * (100 - LEFT - RIGHT)
  const all = chosen.flatMap((c) => SEG.map((s) => ratePerSession(c.row, s)))
    .filter((v) => Number.isFinite(v))
  // 0.001 = a tenth of a percent per session; below that the axis is noise
  const span = Math.max(...all.map(Math.abs), 0.001)
  const ys = (v) => H / 2 - (v / span) * (H / 2 - PADY)

  // The window buttons index into SEGMENTS, which still has four entries; this
  // chart draws three. Remapping rather than subtracting one keeps the shade on
  // the right stretch if the segment list ever changes shape again.
  const hl = (highlight || [])
    .map((i) => SEG.indexOf(SEGMENTS[i]))
    .filter((i) => i >= 0)
  // Shading all three says nothing — 3M IS the chart.
  const shade = hl.length > 0 && hl.length < n ? hl : []

  // End labels in HTML, nudged apart so converging lines cannot smear them.
  const ends = chosen.map((c) => {
    let last = null
    SEG.forEach((s) => {
      const r = ratePerSession(c.row, s)
      if (Number.isFinite(r)) last = r
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
          {shade.length > 0 && (
            <rect x={(xsPct(Math.min(...shade)) - (100 - LEFT - RIGHT) / (n - 1) / 2) * 10}
                  y={4}
                  width={(Math.max(...shade) - Math.min(...shade) + 1)
                         * (100 - LEFT - RIGHT) / (n - 1) * 10 * 0.999}
                  height={H - 8}
                  /* same shade, same reason — see DistributionStrip */
                  fill="var(--color-text)" opacity="0.07" />
          )}
          <line x1={LEFT * 10} x2={(100 - RIGHT) * 10 + 30} y1={H / 2} y2={H / 2}
                stroke="var(--color-text-muted)" strokeWidth="1"
                vectorEffect="non-scaling-stroke" />
          {SEG.map((s, i) => (
            <line key={s.key} x1={xsPct(i) * 10} x2={xsPct(i) * 10} y1={10} y2={H - 10}
                  stroke="var(--color-border)" strokeWidth="1"
                  vectorEffect="non-scaling-stroke" />
          ))}

          {chosen.map((c) => {
            const pts = SEG.map((s, i) => {
              const v = ratePerSession(c.row, s)
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
                  <path key={j}
                        d={monotonePath(r.map((pt) => pt.split(',').map(Number)))}
                        fill="none" stroke={c.colour} strokeWidth="2"
                        strokeDasharray={slotDash(c.colour) ?? undefined}
                        vectorEffect="non-scaling-stroke" strokeLinecap="round" />
                ))}
                {SEG.map((s, i) => {
                  const v = ratePerSession(c.row, s)
                  if (!Number.isFinite(v)) return null
                  return (
                    <circle key={s.key} cx={xsPct(i) * 10} cy={ys(v)} r="3.4" fill={c.colour}>
                      {/* both readings: the pace, and the total it came from */}
                      <title>{c.name} · {s.label}: {v > 0 ? '+' : ''}{(v * 100).toFixed(2)}% per session
                        {' · '}{s.sessions} sessions, {c.row[s.key] > 0 ? '+' : ''}
                        {(c.row[s.key] * 100).toFixed(1)}% over the stretch</title>
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
        <span className="absolute text-[10px] font-mono text-[var(--color-text-muted)]
                         pointer-events-none" style={{ left: `${LEFT + 0.5}%`, top: 2 }}>
          +{(span * 100).toFixed(2)}%/session
        </span>
        <span className="absolute text-[10px] font-mono text-[var(--color-text-muted)]
                         pointer-events-none" style={{ left: `${LEFT + 0.5}%`, bottom: 2 }}>
          −{(span * 100).toFixed(2)}%/session
        </span>
        {ends.map(({ c, y, v }) => (
          <span key={c.name}
                className="absolute text-[11px] font-mono whitespace-nowrap
                           pointer-events-none -translate-y-1/2"
                style={{ left: `${100 - RIGHT + 1.2}%`, top: y, color: c.colour }}>
            {c.name.length > 18 ? `${c.name.slice(0, 17)}…` : c.name}
            {' '}{v > 0 ? '+' : ''}{(v * 100).toFixed(2)}%
          </span>
        ))}
      </div>

      <div className="flex justify-between text-[10px] font-mono
                      text-[var(--color-text-muted)]"
           style={{ paddingLeft: `${LEFT - 1}%`, paddingRight: `${RIGHT - 1}%` }}>
        {SEG.map((s, i) => (
          <span key={s.key} title={`${s.note} · ${s.sessions} sessions`}
                className={hl.includes(i)
                  ? 'text-[var(--color-text-secondary)] font-semibold' : ''}>
            {s.label}
            {/* the length is the reason the axis is a rate; printing it here
                means the reader never has to take that on trust — so it has to
                be legible. --color-border is a hairline, not an ink: 1.29:1. */}
            <span className="text-[var(--color-text-muted)] font-normal"> · {s.sessions}</span>
          </span>
        ))}
      </div>
      <p className="m-0 mt-1 text-[10px] font-mono text-[var(--color-text-muted)]"
         style={{ paddingLeft: `${LEFT - 1}%` }}>
        excess per session — each stretch divided by its own length, so a
        five-session week and a forty-two-session run read on one scale
      </p>

      {/* Ribbons share the chart's plot edges and its sample columns — one
          coordinate system, two readings: the curve is the path, the ribbon is
          the temperature along it. Identity is the dot; the name lives at the
          line's end. */}
      {(() => {
        // Real fortnight ribbons only when every pick has one — otherwise the
        // stack would carry two different time axes.
        const real = chosen.every((c) => Array.isArray(c.row.ribbon) && c.row.ribbon.length > 0)
        return (
          <div className="mt-2.5 space-y-[5px]">
            {chosen.map((c) => (
              <div key={c.name} className="relative"
                   style={{ paddingLeft: `${LEFT}%`, paddingRight: `${RIGHT}%` }}>
                <span className="absolute top-1/2 -translate-y-1/2 w-2 h-2 rounded-full"
                      style={{ left: `calc(${LEFT}% - 17px)`, background: c.colour }}
                      title={c.name} />
                {real
                  ? <FortnightRibbon ribbon={c.row.ribbon} group={c.name} />
                  : <Ribbon row={c.row} span={span}
                            xsPct={(i) => ((xsPct(i) - LEFT) / (100 - LEFT - RIGHT)) * 100} />}
              </div>
            ))}
            {real && (
              <p className="m-0 text-[10px] font-mono text-[var(--color-text-muted)]"
                 style={{ paddingLeft: `${LEFT}%` }}>
                fortnights, oldest first — 10w ago → last 2w
              </p>
            )}
          </div>
        )
      })()}
    </div>
  )
}
