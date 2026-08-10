/**
 * The field: every theme as one dot on one axis, zero = SPY.
 *
 * Answers the question the ranking cannot — is picking worth anything today?
 * Dots bunched on the rule mean the choice barely matters; long tails mean
 * being right pays. The reading is the SHAPE; names live one layer down.
 *
 * TEXT LIVES IN HTML, MARKS LIVE IN SVG. The svg stretches to full width with
 * preserveAspectRatio="none", which is fine for geometry and fatal for glyphs
 * — the first version put its tick numbers inside the svg and they rendered
 * stretched. Labels are absolutely-positioned HTML at percentage offsets, so
 * they stay crisp at any width.
 *
 * The box is quartile-to-quartile: data-derived, nothing to tune. Dot lanes
 * hash the theme's NAME, not its index — index lanes gave adjacent themes
 * adjacent lanes and drew diagonal streaks through the pile that read as a
 * pattern in the data. A name hash is just as deterministic and has no order
 * to leak.
 */

function tickStep(scale) {
  const raw = scale / 2.5
  const mag = 10 ** Math.floor(Math.log10(raw))
  const n = raw / mag
  return (n < 1.5 ? 1 : n < 3.5 ? 2 : n < 7.5 ? 5 : 10) * mag
}

/** Small stable string hash for lane assignment. */
function laneHash(name) {
  let h = 0
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0
  return h
}

const H = 96          // svg height = rendered height, so vertical scale is 1:1

export default function DistributionStrip({ rows, scale, colourOf, onToggle, atLimit }) {
  const scored = rows.filter((r) => Number.isFinite(r._value))
  if (scored.length < 4) return null

  // 0.8% padding either side keeps the extreme dot's full circle on canvas —
  // the strongest theme is the one reading that must not be half-cropped.
  const pct = (v) => 0.8 + ((v + scale) / (2 * scale)) * 98.4

  const sorted = [...scored].sort((a, b) => a._value - b._value)
  const q = (p) => sorted[Math.round(p * (sorted.length - 1))]._value
  const [q25, mid, q75] = [q(0.25), q(0.5), q(0.75)]

  const step = tickStep(scale)
  const ticks = [0]
  for (let t = step; t <= scale + 1e-9; t += step) ticks.push(t, -t)

  return (
    <div>
      {/* the median, said where it sits rather than in a caption */}
      <div className="relative h-[15px] text-[10px] font-mono
                      text-[var(--color-text-secondary)]">
        <span className="absolute -translate-x-1/2 whitespace-nowrap"
              style={{ left: `${pct(mid)}%` }}>
          median {(mid * 100).toFixed(1)}%
        </span>
      </div>

      <svg viewBox={`0 0 1000 ${H}`} className="w-full h-[96px] block"
           preserveAspectRatio="none" role="img"
           aria-label={`${scored.length} themes; median ${(mid * 100).toFixed(1)}%; middle half ${(q25 * 100).toFixed(1)} to ${(q75 * 100).toFixed(1)}%`}>
        {/* the middle half — where "just the market" lives today */}
        <rect x={pct(q25) * 10} y={0} width={Math.max(4, (pct(q75) - pct(q25)) * 10)}
              height={H - 1} fill="var(--color-hover-bg)" />
        <line x1={0} x2={1000} y1={H - 1} y2={H - 1}
              stroke="var(--color-border)" strokeWidth="1" vectorEffect="non-scaling-stroke" />
        {ticks.map((t) => (
          <line key={t} x1={pct(t) * 10} x2={pct(t) * 10} y1={H - 6} y2={H - 1}
                stroke="var(--color-text-muted)" strokeWidth="1"
                vectorEffect="non-scaling-stroke" />
        ))}
        <line x1={pct(0) * 10} x2={pct(0) * 10} y1={2} y2={H - 1}
              stroke="var(--color-text-muted)" strokeWidth="1"
              vectorEffect="non-scaling-stroke" />
        <line x1={pct(mid) * 10} x2={pct(mid) * 10} y1={0} y2={7}
              stroke="var(--color-text-secondary)" strokeWidth="1"
              vectorEffect="non-scaling-stroke" />

        {scored.map((r) => {
          const colour = colourOf(r.group)
          const cy = 14 + (laneHash(r.group) % (H - 34))
          return (
            <circle key={r.group} cx={pct(r._value) * 10} cy={cy}
                    r={colour ? 6 : 3.2}
                    fill={colour ?? 'var(--color-text-muted)'}
                    stroke={colour ? 'var(--color-bg)' : 'none'}
                    strokeWidth={colour ? 1.5 : 0}
                    opacity={colour ? 1 : 0.42}
                    style={{ cursor: atLimit && !colour ? 'not-allowed' : 'pointer' }}
                    onClick={() => onToggle(r.group)}>
              <title>{r.group} {(r._value * 100).toFixed(1)}% — click to compare</title>
            </circle>
          )
        })}
      </svg>

      {/* the axis's own numbers, crisp in HTML */}
      <div className="relative h-[15px] text-[10px] font-mono
                      text-[var(--color-text-muted)]">
        {ticks.map((t) => (
          <span key={t} className="absolute -translate-x-1/2 whitespace-nowrap"
                style={{ left: `${pct(t)}%` }}>
            {t === 0 ? 'SPY' : `${t > 0 ? '+' : ''}${Math.round(t * 100)}%`}
          </span>
        ))}
      </div>
    </div>
  )
}
