import { useRef } from 'react'
import { spreadLabels, STATE_LADDER } from './rotationLogic'
import { fmtPct } from './TipBody'

const W = 1000, H = 300, PAD = { l: 44, r: 160, t: 12, b: 24 }
const LINE = ['var(--color-slot-1)', 'var(--color-slot-2)', 'var(--color-slot-3)']
const DASH = ['', '6 4', '2 3']

/**
 * Compare: the shown groups' quarter excess over the archive — identity by
 * dash and label, as the Themes page does — the four-state ribbon under each
 * line in the grey ladder, and one small tick per chip: the verified mark
 * (F3), kept per session date. No sentences.
 */
export default function CompareChart({ shown, picked, dates, historyOf, onSelect, checks, onTip, offTip }) {
  const svgRef = useRef(null)
  const n = dates.length
  const series = shown.map((r, j) => ({ r, j, h: historyOf(r.group) })).filter((s) => s.h?.excess?.length)
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
      <div className="flex flex-wrap gap-2 mb-3 items-center">
        {shown.map((r, j) => {
          const c = checks.checks[r.group]
          return (
            <span key={r.group} className="rot-chip">
              <button type="button" className="rot-tick" aria-pressed={!!c?.verified} aria-label={`verified ${r.group}`} title="verified"
                      onClick={() => checks.toggle(r.group, 'verified')}>{c?.verified ? '✓' : ''}</button>
              <svg width="18" height="8" aria-hidden="true"><line x1="0" x2="18" y1="4" y2="4" stroke={LINE[j % 3]} strokeWidth="2" strokeDasharray={DASH[j % 3]} /></svg>
              <button type="button" className="bg-transparent border-0 p-0 cursor-pointer text-[13px] text-[var(--color-text)]" onClick={() => onSelect(r.group)} title={picked ? 'remove' : 'select'}>{r.group}</button>
            </span>
          )
        })}
        {!picked && <span className="text-[11px] text-[var(--color-text-muted)]">default — the top of each question</span>}
      </div>
      {n >= 2 && series.length ? (
        <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} className="block w-full h-auto" role="img" aria-label="quarter excess over the archive">
          {[lo, 0, hi].map((v) => (
            <g key={v}>
              <line x1={PAD.l} x2={W - PAD.r} y1={y(v).toFixed(1)} y2={y(v).toFixed(1)} stroke="var(--color-border)" strokeWidth={v === 0 ? 0.9 : 0.6} />
              <text x={PAD.l - 6} y={(y(v) + 3).toFixed(1)} textAnchor="end">{fmtPct(v)}</text>
            </g>
          ))}
          <text x={x(0)} y={H - 6}>{dates[0]}</text>
          <text x={x(n - 1)} y={H - 6} textAnchor="end">{dates[n - 1]}</text>
          {series.map((s) => {
            const pts = s.h.excess.map((v, i) => (v == null ? null : `${x(i).toFixed(1)} ${y(v).toFixed(1)}`)).filter(Boolean)
            return <path key={s.r.group} className="rot-draw" pathLength="1" style={{ animationDelay: `${s.j * 150}ms` }} d={`M${pts.join(' L')}`} fill="none"
                         stroke={LINE[s.j % 3]} strokeDasharray={DASH[s.j % 3]} strokeWidth="1.8" strokeLinejoin="round" strokeLinecap="round" />
          })}
          {ends.map(({ item: s, y: ly, y0 }) => (
            <g key={s.r.group}>
              <line x1={W - PAD.r + 4} x2={W - PAD.r + 12} y1={(y0 - 3.5).toFixed(1)} y2={(ly - 3.5).toFixed(1)} stroke="var(--color-border)" strokeWidth="0.6" />
              <text className="rot-ink" x={W - PAD.r + 14} y={ly.toFixed(1)}>{s.r.group} <tspan style={{ fill: 'var(--color-text-muted)', fontWeight: 500 }}>{fmtPct(s.h.excess[n - 1])}</tspan></text>
            </g>
          ))}
          <rect x={PAD.l} y={PAD.t} width={W - PAD.l - PAD.r} height={H - PAD.t - PAD.b} fill="transparent" style={{ cursor: 'crosshair' }}
                onMouseMove={(e) => { const i = indexAt(e); onTip(e, <><b>{dates[i]}</b><br />{series.map((s) => <span key={s.r.group}>{s.r.group} <b>{fmtPct(s.h.excess[i])}</b><br /></span>)}</>) }}
                onMouseLeave={offTip} />
        </svg>
      ) : <div className="text-[13px] py-6 text-[var(--color-text-muted)]">{n < 2 ? 'Two sessions of archive are needed before a path can be drawn.' : 'Nothing selected has an archive row.'}</div>}
      {series.map((s) => (
        <div key={s.r.group} className="grid grid-cols-[150px_1fr] gap-3 items-center mt-2">
          <span className="text-[13px] font-medium truncate">{s.r.group}</span>
          <div className="flex gap-px h-[8px] rounded-full overflow-hidden">
            {(s.h.state ?? []).map((st, i) => <i key={i} className="flex-1 block" style={{ background: STATE_LADDER[st] ?? 'var(--color-border)' }} title={`${dates[i]} · ${st ?? '—'}`} />)}
          </div>
        </div>
      ))}
    </div>
  )
}
