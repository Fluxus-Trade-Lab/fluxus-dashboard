/**
 * A trend glyph, not a chart. No axis, no gridline, no hover — the row it sits
 * in already prints the exact reading in words (StateBoard's evidence text),
 * so this exists only to answer "getting better or worse", which a number by
 * itself does not.
 *
 * Scaled to its OWN min/max, same as every other per-row glyph on this site —
 * comparing two sparklines' heights against each other would be exactly the
 * mistake VoteGlyphs' own doc warns against (a McClellan of 3.2 and 1.3 points
 * of breadth are not the same distance). This is shape only.
 */
export default function Spark({ values, width = 130, height = 22, title }) {
  const v = (values ?? []).filter(Number.isFinite)
  if (v.length < 2) {
    return (
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
        <line x1="0" x2={width} y1={height / 2} y2={height / 2}
              stroke="var(--color-untested)" strokeDasharray="2 2" />
      </svg>
    )
  }
  const lo = Math.min(...v), hi = Math.max(...v)
  const x = (i) => (i * width) / (v.length - 1)
  const y = (val) => height - 2 - ((val - lo) / (hi - lo || 1)) * (height - 4)
  const d = v.map((val, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)} ${y(val).toFixed(1)}`).join('')

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} role="img" aria-label={title}>
      {title && <title>{title}</title>}
      <path d={d} fill="none" stroke="var(--color-text-secondary)" strokeWidth="1.2"
            strokeLinejoin="round" />
      <circle cx={x(v.length - 1)} cy={y(v.at(-1))} r="2.4" fill="var(--color-accent)" />
    </svg>
  )
}
