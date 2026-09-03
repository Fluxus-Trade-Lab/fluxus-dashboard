import { useMemo, useRef, useState } from 'react'
import { useLanguage } from '../../i18n/LanguageContext'
import { STATES, STATE_LADDER, WINDOWS, windowBounds, countsAt, namesByState } from './rotationLogic'

const W = 1000, H = 110, PAD = { l: 22, r: 6, t: 6, b: 16 }
const STACK = ['Lagging', 'Improving', 'Weakening', 'Leading']   // bottom → top, so Leading sits darkest on top

/**
 * TERRAIN · 地形 · 面 — the two-week board's four-state counts, stacked by
 * session. Hover reads a day; the window select lights a calendar fortnight
 * (TSF's "Last 2w / 2–4w ago / …" — the same board moved to an earlier end
 * date); expand lists who sat in each state on that window's last session.
 * Counts are over every group the ladder measures (themes, sectors,
 * factors), which is the range TSF's Current Leadership counts too.
 * Show, don't tell (Andy 2026-09-03): the expand is a "+", the names carry
 * no kind suffix, and nothing on the card says what it is.
 */
export default function TerrainCard({ ladder, loading, selected, onSelect }) {
  const { t } = useLanguage()
  const [wk, setWk] = useState(0)
  const [open, setOpen] = useState(false)
  const [hov, setHov] = useState(null)
  const svgRef = useRef(null)
  const h = ladder?.history?.['2w'] ?? null
  const dates = h?.dates ?? []
  const m = dates.length
  const names = useMemo(() => Object.keys(ladder?.themes ?? {}), [ladder])
  const total = Math.max(1, ...(h?.measurable ?? [names.length]))
  const seriesOf = (n) => ladder?.series?.[n] ?? null
  const todayOf = (n) => ladder?.themes?.[n]?.['2w'] ?? null
  const bounds = windowBounds(dates, wk)
  const end = bounds?.end ?? m - 1
  const x = (i) => PAD.l + (i * (W - PAD.l - PAD.r)) / Math.max(1, m - 1)
  const y = (v) => PAD.t + (1 - v / total) * (H - PAD.t - PAD.b)
  const stacks = []
  if (h) {
    let base = dates.map(() => 0)
    STACK.forEach((k) => {
      const top = base.map((b, i) => b + (h[k]?.[i] ?? 0))
      stacks.push({ k, d: `M${top.map((v, i) => `${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join(' L')} L${base.map((v, i) => `${x(i).toFixed(1)} ${y(v).toFixed(1)}`).reverse().join(' L')} Z` })
      base = top
    })
  }
  const counts = countsAt(h, end)
  const { byState, known } = namesByState(names, seriesOf, todayOf, end, m - 1)

  const indexAt = (e) => {
    const svg = svgRef.current; const pt = svg.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY
    const p = pt.matrixTransform(svg.getScreenCTM().inverse())
    return Math.max(0, Math.min(m - 1, Math.round((p.x - PAD.l) / ((W - PAD.l - PAD.r) / Math.max(1, m - 1)))))
  }
  const hc = hov == null ? null : countsAt(h, hov)
  const tipX = hov == null ? 0 : hov > m / 2 ? x(hov) - 134 : x(hov) + 8

  return (
    <div className="rot-card">
      <div className="rot-head">
        <h2 className="rot-title">{t('rot.terrain')}</h2>
        <div className="rot-tools">
          {m > 0 && <span className="rot-meta">{dates[end]} · Leading {counts.Leading} · Weakening {counts.Weakening} · Improving {counts.Improving} · Lagging {counts.Lagging}</span>}
          <select className="rot-sel" value={wk} onChange={(e) => setWk(+e.target.value)} aria-label="window" disabled={!m}>
            {WINDOWS.map((l, k) => <option key={k} value={k} disabled={!windowBounds(dates, k)}>{t(l)}{windowBounds(dates, k) ? '' : ` · ${t('rot.nodata')}`}</option>)}
          </select>
          <button type="button" className="rot-btn rot-plus" aria-expanded={open} aria-label={t('rot.expand')} onClick={() => setOpen((v) => !v)} disabled={!m}>{open ? '−' : '+'}</button>
        </div>
      </div>
      {m > 1 ? (
        <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} className="rot-chart" role="img" aria-label="four-state counts by session, two-week board"
             onPointerMove={(e) => setHov(indexAt(e))} onPointerLeave={() => setHov(null)} style={{ touchAction: 'none' }}>
          {stacks.map(({ k, d }) => <path key={k} d={d} fill={STATE_LADDER[k]} stroke="var(--color-surface)" strokeWidth="1" />)}
          {bounds && bounds.start > 0 && <rect x={PAD.l} y={PAD.t} width={(x(bounds.start) - PAD.l).toFixed(1)} height={H - PAD.t - PAD.b} fill="var(--color-surface)" opacity=".6" />}
          {bounds && bounds.end < m - 1 && <rect x={x(bounds.end).toFixed(1)} y={PAD.t} width={(x(m - 1) - x(bounds.end)).toFixed(1)} height={H - PAD.t - PAD.b} fill="var(--color-surface)" opacity=".6" />}
          <text className="rot-mono" x={x(0)} y={H - 4}>{dates[0].slice(5)}</text>
          <text className="rot-mono" x={x(m - 1)} y={H - 4} textAnchor="end">{dates[m - 1].slice(5)}</text>
          {hov != null && (
            <g style={{ pointerEvents: 'none' }}>
              <line x1={x(hov)} x2={x(hov)} y1={PAD.t} y2={H - PAD.b} stroke="var(--color-text)" strokeWidth=".8" />
              <rect x={tipX} y={PAD.t} rx="5" width="126" height="78" fill="var(--color-surface)" stroke="var(--color-border)" />
              <text className="rot-mono rot-ink" x={tipX + 8} y={PAD.t + 13}>{dates[hov]}</text>
              {STATES.map((k, r) => <text key={k} x={tipX + 8} y={PAD.t + 28 + 14 * r} style={{ fill: k === 'Lagging' ? 'var(--color-text-muted)' : STATE_LADDER[k] }}>{k} {hc[k]}</text>)}
            </g>
          )}
        </svg>
      ) : <div className="rot-empty" style={{ minHeight: 110 }}>{loading ? '' : t('rot.noHistory')}</div>}
      {open && m > 0 && (
        <div className="rot-band">
          {known ? STATES.map((st) => (
            <div key={st} className="rot-band-row">
              <div className="rot-st"><i style={{ background: STATE_LADDER[st] }} />{st} <span className="rot-meta">{byState[st].length}</span></div>
              <div className="rot-names">
                {byState[st].length ? byState[st].map((n) => (
                  <button key={n} type="button" className="rot-nmx" aria-pressed={selected.includes(n)} onClick={() => onSelect(n)}>{n}</button>
                )) : <span className="rot-meta">—</span>}
              </div>
            </div>
          )) : <div className="rot-empty">—</div>}
        </div>
      )}
    </div>
  )
}
