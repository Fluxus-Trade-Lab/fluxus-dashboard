import { useRef } from 'react'
import { stateCounts } from './rotationLogic'

const W = 640, H = 230, PAD = { l: 30, r: 14, t: 12, b: 24 }
const ORDER = ['Lagging', 'Weakening', 'Improving', 'Leading']

/**
 * Four-state counts over the archive as a stacked area. Leaders growing is a
 * healthy tape; laggards growing is a tape going soft — Andy's reading of the
 * same panel on TSF, with the history that panel never had.
 */
export default function LeadershipChart({ rows, historyOf, dates, at, onScrub, onTip, offTip, colourOf }) {
  const svgRef = useRef(null)
  const n = dates.length
  if (n < 2) return <div className="text-[13px] py-6" style={{ color: 'var(--rot-faint)' }}>The archive has {n} session{n === 1 ? '' : 's'} — the count over time starts at two.</div>
  const cnt = dates.map((_, i) => stateCounts(rows, historyOf, i))
  const T = Math.max(1, ...cnt.map((c) => ORDER.reduce((a, k) => a + c[k], 0)))
  const x = (i) => PAD.l + (i * (W - PAD.l - PAD.r)) / (n - 1)
  const y = (v) => PAD.t + (1 - v / T) * (H - PAD.t - PAD.b)
  const indexAt = (e) => {
    const svg = svgRef.current; const pt = svg.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY
    const p = pt.matrixTransform(svg.getScreenCTM().inverse())
    return Math.max(0, Math.min(n - 1, Math.round((p.x - PAD.l) / ((W - PAD.l - PAD.r) / (n - 1)))))
  }
  let base = dates.map(() => 0)
  const areas = ORDER.map((k, j) => {
    const top = base.map((b, i) => b + cnt[i][k])
    const up = top.map((v, i) => `${x(i).toFixed(1)} ${y(v).toFixed(1)}`)
    const dn = base.map((v, i) => `${x(i).toFixed(1)} ${y(v).toFixed(1)}`).reverse()
    base = top
    return <path key={k} className="rot-fade" style={{ animationDelay: `${j * 120}ms` }} d={`M${up.join(' L')} L${dn.join(' L')} Z`}
                 fill={colourOf[k]} fillOpacity="0.8" stroke="var(--rot-card)" strokeWidth="1.5"><title>{k}</title></path>
  })
  return (
    <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} className="block w-full h-auto" role="img" aria-label="state counts over time">
      {[0.5, 1].map((f) => (
        <g key={f}>
          <line x1={PAD.l} x2={W - PAD.r} y1={y(T * f)} y2={y(T * f)} stroke="var(--rot-grid)" strokeWidth="0.7" />
          <text x={PAD.l - 5} y={y(T * f) + 3} textAnchor="end" style={{ fontWeight: 800 }}>{Math.round(T * f)}</text>
        </g>
      ))}
      {areas}
      <line x1={x(at)} x2={x(at)} y1={PAD.t} y2={H - PAD.b} stroke="var(--rot-paper)" strokeWidth="0.7" strokeDasharray="2 3" />
      {dates.map((d, i) => (i === 0 || i === n - 1 || i % 6 === 0) && (
        <text key={d} x={x(i)} y={H - 6} textAnchor={i === 0 ? 'start' : i === n - 1 ? 'end' : 'middle'}>{d.slice(5)}</text>
      ))}
      <rect x={PAD.l} y={PAD.t} width={W - PAD.l - PAD.r} height={H - PAD.t - PAD.b} fill="transparent" style={{ cursor: 'crosshair' }}
            onMouseMove={(e) => { const i = indexAt(e); onTip(e, <><b className="font-extrabold">{dates[i]}</b><br />{ORDER.slice().reverse().map((k) => <span key={k}>{k} <b>{cnt[i][k]}</b> · </span>)}</>) }}
            onMouseLeave={offTip} onClick={(e) => onScrub(indexAt(e))} />
    </svg>
  )
}
