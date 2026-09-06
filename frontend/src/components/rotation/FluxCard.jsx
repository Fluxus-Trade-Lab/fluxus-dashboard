import { useId, useRef, useState } from 'react'
import { useLanguage } from '../../i18n/LanguageContext'
import { LINE, STATE_LADDER, Y_MAX, Y_TAIL, R2W_LAG, FLUX_STEP, sampleIndices, yFrac, fmtPct, r2wSeries, spreadLabels, smoothPath } from './rotationLogic'

const W = 640, H = 380, PAD = { l: 44, r: 140, t: 14, b: 24 }

/**
 * FLUX · 轨迹 · 线 — up to three themes' two-week relative strength against
 * the benchmark over the ladder's ten-week calendar, one point a week. The
 * y-axis is fixed at ±20% so a line added never moves the others; past that
 * the scale saturates instead of clipping — a line off the scale rides just
 * inside the frame and the hover still reads the true value. The lines
 * are blue, red, ink; the benchmark's zero line carries its name in the same
 * column as theirs. Under each line, its two-week state per session in the
 * grey ladder. No markers — a sudden week is read from the hover (Andy
 * 2026-09-03: 突变记号不要了). One point a week rather than one a day: the
 * daily line was true and unreadable three at a time (brief §18.25), and the
 * hover snaps to a plotted week so the number never disagrees with the line.
 */
export default function FluxCard({ shown, dates, stateDates, benchmark, picked, loading, onSelect }) {
  const { t } = useLanguage()
  const clip = useId()
  const svgRef = useRef(null)
  const [hov, setHov] = useState(null)
  const lag = R2W_LAG
  const n = dates.length
  const drawn = Math.max(0, n - lag)            // sessions with a whole two-week window behind them
  const x = (i) => PAD.l + ((i - lag) * (W - PAD.l - PAD.r)) / Math.max(1, drawn - 1)
  const midY = PAD.t + (H - PAD.t - PAD.b) / 2, halfH = (H - PAD.t - PAD.b) / 2
  const y = (v) => midY - yFrac(v) * halfH
  const at = sampleIndices(n, lag, FLUX_STEP)
  const lines = shown.map((o, j) => ({ ...o, j, r2w: r2wSeries(o.rel) })).filter((o) => o.rel?.length)
  const ends = spreadLabels(
    [{ name: benchmark, j: -1, v: 0 }, ...lines.map((o) => ({ name: o.name, j: o.j, v: [...at].reverse().map((i) => o.r2w[i]).find((v) => v != null) ?? null })).filter((e) => e.v != null)],
    (e) => y(e.v) + 3.5, 14,
  )
  const indexAt = (e) => {
    const svg = svgRef.current; const pt = svg.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY
    const p = pt.matrixTransform(svg.getScreenCTM().inverse())
    const raw = lag + Math.round((p.x - PAD.l) / ((W - PAD.l - PAD.r) / Math.max(1, drawn - 1)))
    // snap to a plotted week, so the readout never names a day the line does not pass through
    return at.reduce((best, i) => (Math.abs(i - raw) < Math.abs(best - raw) ? i : best), at[0] ?? lag)
  }
  const stateIndex = (d) => (stateDates ? stateDates.indexOf(d) : -1)
  const tipX = hov == null ? 0 : hov - lag > drawn / 2 ? x(hov) - 178 : x(hov) + 8
  const rows = hov == null ? [] : [...lines].sort((a, b) => (b.r2w[hov] ?? -9) - (a.r2w[hov] ?? -9))

  return (
    <div className="rot-card">
      <div className="rot-head"><h2 className="rot-title">{t('rot.flux')}</h2></div>
      <div className="rot-chips">
        {shown.map((o, j) => (
          <button key={o.name} type="button" className="rot-chip" onClick={() => onSelect(o.name)} title={picked ? 'remove' : 'select'}>
            <i style={{ background: LINE[j] }} />{o.name}{o.rel?.length ? '' : <span className="rot-meta">·</span>} <span className="rot-meta">×</span>
          </button>
        ))}
      </div>
      {drawn >= 2 && lines.length ? (
        <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} className="rot-chart" role="img" aria-label={`two-week relative strength vs ${benchmark}`}
             onPointerMove={(e) => setHov(indexAt(e))} onPointerLeave={() => setHov(null)} style={{ touchAction: 'none' }}>
          <defs><clipPath id={clip}><rect x={PAD.l - 4} y={PAD.t - 4} width={W - PAD.l - PAD.r + 8} height={H - PAD.t - PAD.b + 8} /></clipPath></defs>
          {/* the saturating band, tinted so the bend past ±20% is visible without a sentence */}
          <rect x={PAD.l} y={PAD.t} width={W - PAD.l - PAD.r} height={(halfH * Y_TAIL).toFixed(1)} fill="var(--color-text)" opacity=".045" />
          <rect x={PAD.l} y={(midY + halfH * (1 - Y_TAIL)).toFixed(1)} width={W - PAD.l - PAD.r} height={(halfH * Y_TAIL).toFixed(1)} fill="var(--color-text)" opacity=".045" />
          {[-Y_MAX, -Y_MAX / 2, 0, Y_MAX / 2, Y_MAX].map((v) => (
            <g key={v}>
              <line x1={PAD.l} x2={W - PAD.r} y1={y(v).toFixed(1)} y2={y(v).toFixed(1)} stroke={v === 0 ? 'var(--color-border)' : 'var(--color-border-light)'} strokeWidth={v === 0 ? 1 : 0.6} />
              <text className="rot-mono" x={PAD.l - 6} y={(y(v) + 3.5).toFixed(1)} textAnchor="end">{fmtPct(v, 0)}</text>
            </g>
          ))}
          {dates.map((d, i) => (i >= lag && (i - lag) % 10 === 0 ? <text key={d} className="rot-mono" x={x(i).toFixed(1)} y={H - 8} textAnchor="middle">{d.slice(5)}</text> : null))}
          <g clipPath={`url(#${clip})`}>
            {lines.map((o) => {
              const pts = at.filter((i) => o.r2w[i] != null).map((i) => [x(i), y(o.r2w[i])])
              return pts.length >= 2 ? (
                <g key={o.name}>
                  <path d={smoothPath(pts)} fill="none" stroke={LINE[o.j]} strokeWidth={o.j === 0 ? 2.6 : 2} strokeLinejoin="round" strokeLinecap="round" />
                  {pts.map(([cx, cy], k) => <circle key={k} cx={cx.toFixed(1)} cy={cy.toFixed(1)} r="2.5" fill={LINE[o.j]} stroke="var(--color-surface)" strokeWidth="1.2" />)}
                </g>
              ) : null
            })}
          </g>
          {ends.map(({ item: e, y: ly }) => (e.j < 0
            ? <text key="bench" x={W - PAD.r + 8} y={ly.toFixed(1)}>{benchmark}</text>
            : <text key={e.name} className="rot-ink" x={W - PAD.r + 8} y={ly.toFixed(1)} style={{ fill: LINE[e.j] }}>{e.name} <tspan className="rot-mono" style={{ fill: 'var(--color-text-muted)', fontWeight: 500 }}>{fmtPct(e.v)}</tspan></text>))}
          {hov != null && (
            <g style={{ pointerEvents: 'none' }}>
              <line x1={x(hov).toFixed(1)} x2={x(hov).toFixed(1)} y1={PAD.t} y2={H - PAD.b} stroke="var(--color-text-secondary)" strokeWidth=".8" strokeDasharray="3 3" />
              {lines.map((o) => (o.r2w[hov] != null
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
      ) : <div className="rot-empty" style={{ minHeight: 120 }}>{loading ? '' : n ? t('rot.nothingSelected') : t('rot.noSeries')}</div>}
      {lines.map((o) => (
        <div key={o.name} className="rot-rib">
          <span style={{ color: LINE[o.j] }}>{o.name}</span>
          <div className="rot-rib-bar">
            {dates.slice(lag).map((d) => { const st = o.states?.[stateIndex(d)] ?? null; return <i key={d} style={{ background: STATE_LADDER[st] ?? 'var(--color-border-light)' }} title={`${d} · ${st ?? '—'}`} /> })}
          </div>
        </div>
      ))}
    </div>
  )
}
