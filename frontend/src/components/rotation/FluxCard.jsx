import { useId, useRef, useState } from 'react'
import { LINE, STATE_LADDER, Y_MAX, R2W_LAG, fmtPct, r2wSeries, spreadLabels, smoothPath } from './rotationLogic'

const W = 1040, H = 340, PAD = { l: 44, r: 150, t: 14, b: 24 }

/**
 * FLUX · 轨迹 · 线 — up to three themes' two-week relative strength against
 * the benchmark, every session, over the ladder's ten-week calendar. The
 * y-axis is fixed at ±15% so a line added never moves the others; what
 * overflows is clipped and the hover still reads the true value. The lines
 * are blue, red, ink; the benchmark's zero line carries its name in the same
 * column as theirs. Under each line, its two-week state per session in the
 * grey ladder. No markers — a sudden week is read from the hover (Andy
 * 2026-09-03: 突变记号不要了).
 */
export default function FluxCard({ shown, dates, stateDates, benchmark, picked, onSelect, note }) {
  const clip = useId()
  const svgRef = useRef(null)
  const [hov, setHov] = useState(null)
  const lag = R2W_LAG
  const n = dates.length
  const drawn = Math.max(0, n - lag)            // sessions with a whole two-week window behind them
  const x = (i) => PAD.l + ((i - lag) * (W - PAD.l - PAD.r)) / Math.max(1, drawn - 1)
  const y = (v) => PAD.t + ((Y_MAX - v) / (2 * Y_MAX)) * (H - PAD.t - PAD.b)
  const lines = shown.map((o, j) => ({ ...o, j, r2w: r2wSeries(o.rel) })).filter((o) => o.rel?.length)
  const ends = spreadLabels(
    [{ name: benchmark, j: -1, v: 0 }, ...lines.map((o) => { const last = [...o.r2w].reverse().find((v) => v != null); return { name: o.name, j: o.j, v: last ?? null } }).filter((e) => e.v != null)],
    (e) => y(e.v) + 3.5, 14,
  )
  const indexAt = (e) => {
    const svg = svgRef.current; const pt = svg.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY
    const p = pt.matrixTransform(svg.getScreenCTM().inverse())
    return Math.max(lag, Math.min(n - 1, lag + Math.round((p.x - PAD.l) / ((W - PAD.l - PAD.r) / Math.max(1, drawn - 1)))))
  }
  const stateIndex = (d) => (stateDates ? stateDates.indexOf(d) : -1)
  const tipX = hov == null ? 0 : hov - lag > drawn / 2 ? x(hov) - 178 : x(hov) + 8
  const rows = hov == null ? [] : [...lines].sort((a, b) => (b.r2w[hov] ?? -9) - (a.r2w[hov] ?? -9))

  return (
    <div className="rot-card">
      <div className="rot-head"><h2 className="rot-title">Flux<span className="rot-cn">轨迹 · 线</span></h2></div>
      <div className="rot-chips">
        {shown.map((o, j) => (
          <button key={o.name} type="button" className="rot-chip" onClick={() => onSelect(o.name)} title={picked ? 'remove' : 'select'}>
            <i style={{ background: LINE[j] }} />{o.name}{o.rel?.length ? '' : <span className="rot-meta">(no series yet)</span>} <span className="rot-meta">×</span>
          </button>
        ))}
      </div>
      {drawn >= 2 && lines.length ? (
        <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} className="rot-chart" role="img" aria-label={`two-week relative strength vs ${benchmark}`}
             onPointerMove={(e) => setHov(indexAt(e))} onPointerLeave={() => setHov(null)} style={{ touchAction: 'none' }}>
          <defs><clipPath id={clip}><rect x={PAD.l - 4} y={PAD.t - 4} width={W - PAD.l - PAD.r + 8} height={H - PAD.t - PAD.b + 8} /></clipPath></defs>
          {[-Y_MAX, -Y_MAX / 2, 0, Y_MAX / 2, Y_MAX].map((v) => (
            <g key={v}>
              <line x1={PAD.l} x2={W - PAD.r} y1={y(v).toFixed(1)} y2={y(v).toFixed(1)} stroke={v === 0 ? 'var(--color-border)' : 'var(--color-border-light)'} strokeWidth={v === 0 ? 1 : 0.6} />
              <text className="rot-mono" x={PAD.l - 6} y={(y(v) + 3.5).toFixed(1)} textAnchor="end">{fmtPct(v, 0)}</text>
            </g>
          ))}
          {dates.map((d, i) => (i >= lag && (i - lag) % 10 === 0 ? <text key={d} className="rot-mono" x={x(i).toFixed(1)} y={H - 8} textAnchor="middle">{d.slice(5)}</text> : null))}
          <g clipPath={`url(#${clip})`}>
            {lines.map((o) => {
              const pts = o.r2w.map((v, i) => (v == null || i < lag ? null : [x(i), y(v)])).filter(Boolean)
              return pts.length >= 2 ? <path key={o.name} d={smoothPath(pts)} fill="none" stroke={LINE[o.j]} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" /> : null
            })}
          </g>
          {ends.map(({ item: e, y: ly }) => (e.j < 0
            ? <text key="bench" x={W - PAD.r + 8} y={ly.toFixed(1)}>{benchmark}</text>
            : <text key={e.name} className="rot-ink" x={W - PAD.r + 8} y={ly.toFixed(1)} style={{ fill: LINE[e.j] }}>{e.name} <tspan className="rot-mono" style={{ fill: 'var(--color-text-muted)', fontWeight: 500 }}>{fmtPct(e.v)}</tspan></text>))}
          {hov != null && (
            <g style={{ pointerEvents: 'none' }}>
              <line x1={x(hov).toFixed(1)} x2={x(hov).toFixed(1)} y1={PAD.t} y2={H - PAD.b} stroke="var(--color-text-secondary)" strokeWidth=".8" strokeDasharray="3 3" />
              {lines.map((o) => (o.r2w[hov] != null && Math.abs(o.r2w[hov]) <= Y_MAX
                ? <circle key={o.name} cx={x(hov).toFixed(1)} cy={y(o.r2w[hov]).toFixed(1)} r="4" fill="var(--color-surface)" stroke={LINE[o.j]} strokeWidth="2" /> : null))}
              <rect x={tipX} y={PAD.t + 4} rx="6" width="170" height={18 + 15 * (lines.length + 1)} fill="var(--color-surface)" stroke="var(--color-border)" />
              <text className="rot-mono rot-ink" x={tipX + 8} y={PAD.t + 18}>{dates[hov]}</text>
              {rows.map((o, r) => (
                <g key={o.name}>
                  <text x={tipX + 8} y={PAD.t + 34 + 15 * r} style={{ fill: LINE[o.j] }}>{o.name}</text>
                  <text className="rot-mono" x={tipX + 162} y={PAD.t + 34 + 15 * r} textAnchor="end">{fmtPct(o.r2w[hov])}</text>
                </g>
              ))}
              <text x={tipX + 8} y={PAD.t + 34 + 15 * lines.length}>{benchmark}</text>
              <text className="rot-mono" x={tipX + 162} y={PAD.t + 34 + 15 * lines.length} textAnchor="end">0.0%</text>
            </g>
          )}
        </svg>
      ) : <div className="rot-empty">{n ? 'Nothing selected has a series yet.' : 'The ten-week series arrives with the next nightly run of the ladder.'}</div>}
      {lines.map((o) => (
        <div key={o.name} className="rot-rib">
          <span style={{ color: LINE[o.j] }}>{o.name}</span>
          <div className="rot-rib-bar">
            {dates.slice(lag).map((d) => { const st = o.states?.[stateIndex(d)] ?? null; return <i key={d} style={{ background: STATE_LADDER[st] ?? 'var(--color-border-light)' }} title={`${d} · ${st ?? '—'}`} /> })}
          </div>
        </div>
      ))}
      {note && <div className="rot-note">{note}</div>}
    </div>
  )
}
