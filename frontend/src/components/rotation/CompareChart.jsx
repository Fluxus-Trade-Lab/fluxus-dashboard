import { useRef } from 'react'
import { spreadLabels, questionOf } from './rotationLogic'
import { fmtPct } from './TipBody'

const W = 1000, H = 300, PAD = { l: 46, r: 170, t: 14, b: 26 }

/**
 * Compare: the shown groups' quarter excess over the archive, one line each,
 * the four-state history as a ribbon under every line, and the two checks
 * (verified / watch) beside each ribbon — F3's record lives here, on the
 * instrument you look at last before deciding.
 */
export default function CompareChart({ shown, picked, dates, historyOf, benchmark, onSelect, checks, onTip, offTip, colourOf, lists }) {
  const svgRef = useRef(null)
  const n = dates.length
  const series = shown.map((r) => ({ r, h: historyOf(r.group) })).filter((s) => s.h?.excess?.length)
  const lead = series.slice().sort((a, b) => (b.h.excess[n - 1] ?? -9) - (a.h.excess[n - 1] ?? -9))[0]
  const title = lead
    ? <>{lead.r.group} leads {series.length === 1 ? '' : `the ${series.length}`} on the quarter, {fmtPct(lead.h.excess[n - 1])} vs {benchmark}</>
    : 'Pick up to three'
  const vals = series.flatMap((s) => s.h.excess.filter((v) => v != null))
  const lo = Math.min(0, ...vals), hi = Math.max(0, ...vals)
  const x = (i) => PAD.l + (i * (W - PAD.l - PAD.r)) / Math.max(1, n - 1)
  const y = (v) => PAD.t + ((hi - v) / (hi - lo || 1)) * (H - PAD.t - PAD.b)
  const indexAt = (e) => {
    const svg = svgRef.current; const pt = svg.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY
    const p = pt.matrixTransform(svg.getScreenCTM().inverse())
    return Math.max(0, Math.min(n - 1, Math.round((p.x - PAD.l) / ((W - PAD.l - PAD.r) / Math.max(1, n - 1)))))
  }
  const ends = spreadLabels(series.filter((s) => s.h.excess[n - 1] != null), (s) => y(s.h.excess[n - 1]) + 3.5, 14)

  return (
    <div>
      <h2 className="m-0 text-[17px] font-bold" style={{ letterSpacing: '-.02em' }}>
        {title} · {picked ? 'your picks' : 'the top of each question'} · <b className="text-white">{checks.verified}</b> verified, <b className="text-white">{checks.watched}</b> on watch today
      </h2>
      <div className="text-[11px] mb-3" style={{ color: 'var(--rot-muted)' }}>quarter excess vs {benchmark} over the archive · under each line its four-state history · your checks live here</div>
      <div className="flex flex-wrap gap-[6px] mb-3">
        {shown.map((r) => (
          <button key={r.group} type="button" className="rot-chip" onClick={() => onSelect(r.group)} title={picked ? 'remove' : 'select'}>
            <i className="inline-block w-[8px] h-[8px] rounded-full" style={{ background: colourOf[r.state] }} />{r.group}{picked && <span style={{ color: 'var(--rot-muted)' }}>×</span>}
          </button>
        ))}
      </div>
      {n >= 2 && series.length ? (
        <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} className="block w-full h-auto" role="img" aria-label={`quarter excess vs ${benchmark}`}>
          {[lo, 0, hi].map((v) => (
            <g key={v}>
              <line x1={PAD.l} x2={W - PAD.r} y1={y(v).toFixed(1)} y2={y(v).toFixed(1)} stroke="var(--rot-grid)" strokeWidth={v === 0 ? 1 : 0.7} />
              <text x={PAD.l - 6} y={(y(v) + 3).toFixed(1)} textAnchor="end" style={{ fontWeight: 800 }}>{fmtPct(v)}</text>
            </g>
          ))}
          {[0, Math.floor((n - 1) / 2), n - 1].map((i, k) => (
            <text key={i} x={x(i)} y={H - 8} textAnchor={k === 0 ? 'start' : k === 2 ? 'end' : 'middle'}>{dates[i]}</text>
          ))}
          {series.map((s, j) => {
            const pts = s.h.excess.map((v, i) => (v == null ? null : `${x(i).toFixed(1)} ${y(v).toFixed(1)}`)).filter(Boolean)
            return (
              <g key={s.r.group}>
                <path className="rot-draw" pathLength="1" style={{ animationDelay: `${j * 150}ms` }} d={`M${pts.join(' L')}`} fill="none"
                      stroke={colourOf[s.r.state]} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
                {s.h.excess[n - 1] != null && <circle className="rot-pop" style={{ animationDelay: `${900 + j * 150}ms` }} cx={x(n - 1).toFixed(1)} cy={y(s.h.excess[n - 1]).toFixed(1)} r="4" fill={colourOf[s.r.state]} stroke="var(--rot-card)" strokeWidth="2" />}
              </g>
            )
          })}
          {ends.map(({ item: s, y: ly, y0 }) => (
            <g key={s.r.group}>
              <line x1={W - PAD.r + 4} x2={W - PAD.r + 12} y1={(y0 - 3.5).toFixed(1)} y2={(ly - 3.5).toFixed(1)} stroke="var(--rot-grid)" strokeWidth="0.7" />
              <text className="rot-ink" x={W - PAD.r + 14} y={ly.toFixed(1)} style={{ fontSize: 11 }}>{s.r.group} <tspan style={{ fill: 'var(--rot-muted)', fontWeight: 800 }}>{fmtPct(s.h.excess[n - 1])}</tspan></text>
            </g>
          ))}
          <rect x={PAD.l} y={PAD.t} width={W - PAD.l - PAD.r} height={H - PAD.t - PAD.b} fill="transparent" style={{ cursor: 'crosshair' }}
                onMouseMove={(e) => { const i = indexAt(e); onTip(e, <><b className="font-extrabold">{dates[i]}</b><br />{series.map((s) => <span key={s.r.group}>{s.r.group} <b>{fmtPct(s.h.excess[i])}</b><br /></span>)}</>) }}
                onMouseLeave={offTip} />
        </svg>
      ) : <div className="text-[13px] py-6" style={{ color: 'var(--rot-faint)' }}>{n < 2 ? 'The archive is too short to draw a path yet.' : 'Nothing selected has an archive row.'}</div>}
      {shown.map((r) => {
        const h = historyOf(r.group); const c = checks.checks[r.group] ?? {}
        const q = questionOf(r)
        return (
          <div key={r.group} className="grid grid-cols-[150px_1fr_190px] gap-3 items-center mt-2 text-[11px]">
            <span className="font-bold text-[13px]">{r.group}</span>
            <div className="flex gap-px h-[10px] rounded-full overflow-hidden" title={`four-state, ${dates[0] ?? '—'} → ${dates[n - 1] ?? '—'}`}>
              {(h?.state ?? []).map((st, i) => <i key={i} className="flex-1 block" style={{ background: colourOf[st] ?? 'var(--rot-grid)' }} title={`${dates[i]} · ${st ?? '—'}`} />)}
              {!h && <span style={{ color: 'var(--rot-faint)' }}>no archive row</span>}
            </div>
            <div className="flex gap-3" style={{ color: 'var(--rot-muted)' }}>
              <label className="flex items-center gap-[5px] cursor-pointer select-none"><input type="checkbox" className="rot-check" checked={!!c.verified} onChange={() => checks.toggle(r.group, 'verified', q ?? '')} /> verified</label>
              <label className="flex items-center gap-[5px] cursor-pointer select-none"><input type="checkbox" className="rot-check" checked={!!c.watch} onChange={() => checks.toggle(r.group, 'watch', q ?? '')} /> watch</label>
            </div>
          </div>
        )
      })}
      <div className="mt-3 flex items-center gap-3 text-[11px]" style={{ color: 'var(--rot-faint)' }}>
        <span>checks are kept in this browser per session date · {lists ? `${lists.q1.length + lists.q2.length + lists.q3.length} on the lists today` : ''}</span>
        <button type="button" className="rot-btn" onClick={() => { try { navigator.clipboard?.writeText(checks.exportJson()) } catch { /* clipboard may be unavailable */ } }}>copy checks as JSON</button>
      </div>
    </div>
  )
}
