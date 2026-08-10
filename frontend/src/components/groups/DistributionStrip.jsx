/**
 * The distribution: every theme as one dot on one axis, zero = SPY.
 *
 * This strip answers the question the ranking cannot: is today's spread worth
 * picking through at all? Dots bunched on the rule mean the choice barely
 * matters; long tails mean it is worth being right. The reading is the SHAPE —
 * names deliberately do not appear here, they live one layer down.
 *
 * The shaded box is the middle half of the field (quartile to quartile).
 * Data-derived, no threshold to tune: an earlier sketch shaded a fixed ±5%
 * band, which was one more invented parameter — the IQR moves with the field
 * and needs no defending.
 *
 * Vertical position is deterministic jitter (i·47 mod n), so overlapping dots
 * separate without implying a second dimension, and the same theme lands on
 * the same spot every render.
 *
 * Shares its scale with the ranking below by contract — the caller computes
 * one scale for both. Two objects on one axis are one instrument; on two
 * axes they are two charts that happen to be adjacent.
 */
export default function DistributionStrip({ rows, scale, colourOf, onToggle, atLimit }) {
  const scored = rows.filter((r) => Number.isFinite(r._value))
  if (scored.length < 4) return null

  const W = 1000, H = 74, PAD = 8
  const x = (v) => PAD + ((v + scale) / (2 * scale)) * (W - PAD * 2)

  const sorted = [...scored].sort((a, b) => a._value - b._value)
  const q = (p) => sorted[Math.round(p * (sorted.length - 1))]._value
  const [q25, mid, q75] = [q(0.25), q(0.5), q(0.75)]

  return (
    <div>
      <div className="relative">
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-[64px] block"
             preserveAspectRatio="none" role="img"
             aria-label={`${scored.length} themes; median ${(mid * 100).toFixed(1)}%; middle half ${(q25 * 100).toFixed(1)} to ${(q75 * 100).toFixed(1)}%`}>
          <rect x={x(q25)} y={6} width={Math.max(1, x(q75) - x(q25))} height={H - 12}
                fill="var(--color-hover-bg)" />
          <line x1={x(0)} x2={x(0)} y1={2} y2={H - 2}
                stroke="var(--color-text-muted)" strokeWidth="1"
                vectorEffect="non-scaling-stroke" />
          {scored.map((r, i) => {
            const colour = colourOf(r.group)
            const cy = H / 2 + (((i * 47) % (H - 26)) - (H - 26) / 2) * 0.9
            return (
              <circle key={r.group} cx={x(r._value)} cy={cy}
                      r={colour ? 5.5 : 3}
                      fill={colour ?? 'var(--color-text-muted)'}
                      opacity={colour ? 1 : 0.4}
                      style={{ cursor: atLimit && !colour ? 'not-allowed' : 'pointer' }}
                      onClick={() => onToggle(r.group)}>
                <title>{r.group} {(r._value * 100).toFixed(1)}% — click to compare</title>
              </circle>
            )
          })}
        </svg>
        <span className="absolute left-1/2 -translate-x-1/2 -top-1 text-[9px] font-mono
                         text-[var(--color-text-muted)] pointer-events-none">SPY</span>
      </div>
      <p className="m-0 mt-1 text-[10.5px] leading-snug text-[var(--color-text-muted)]">
        One dot per theme. The box is the middle half: median{' '}
        <span className="font-mono tabular-nums">{(mid * 100).toFixed(1)}%</span>, half the
        field inside{' '}
        <span className="font-mono tabular-nums">
          {(q25 * 100).toFixed(1)}…{(q75 * 100).toFixed(1)}%
        </span>
        {' '}— a narrow box says picking barely matters today; long tails say it does.
      </p>
    </div>
  )
}
