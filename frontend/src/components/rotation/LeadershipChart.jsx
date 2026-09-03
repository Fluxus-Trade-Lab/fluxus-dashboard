import { useRef } from 'react'
import { stateCounts, STATE_LADDER } from './rotationLogic'

const W = 640, H = 220, PAD = { l: 26, r: 12, t: 10, b: 22 }
const ORDER = ['Lagging', 'Improving', 'Weakening', 'Leading']

/** the four states over the archive as a stacked area, greys darkest = strongest; click a day to scrub the field there */
export default function LeadershipChart({ rows, historyOf, dates, at, onScrub, onTip, offTip }) {
  const svgRef = useRef(null)
  const n = dates.length
  if (n < 2) return <div className="text-[13px] py-6 text-[var(--color-text-muted)]">Two sessions of archive are needed before this can be drawn.</div>
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
                 fill={STATE_LADDER[k]} stroke="var(--color-surface)" strokeWidth="1.2"><title>{k}</title></path>
  })
  return (
    <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} className="block w-full h-auto" role="img" aria-label="state counts over time">
      {areas}
      <line x1={x(at)} x2={x(at)} y1={PAD.t} y2={H - PAD.b} stroke="var(--color-text)" strokeWidth="0.7" strokeDasharray="2 3" />
      <text x={PAD.l - 4} y={y(T) + 4} textAnchor="end">{T}</text>
      <text x={x(0)} y={H - 6}>{dates[0].slice(5)}</text>
      <text x={x(n - 1)} y={H - 6} textAnchor="end">{dates[n - 1].slice(5)}</text>
      <rect x={PAD.l} y={PAD.t} width={W - PAD.l - PAD.r} height={H - PAD.t - PAD.b} fill="transparent" style={{ cursor: 'crosshair' }}
            onMouseMove={(e) => { const i = indexAt(e); onTip(e, <><b>{dates[i]}</b><br />{ORDER.slice().reverse().map((k) => <span key={k}>{k} <b>{cnt[i][k]}</b> · </span>)}</>) }}
            onMouseLeave={offTip} onClick={(e) => onScrub(indexAt(e))} />
    </svg>
  )
}
