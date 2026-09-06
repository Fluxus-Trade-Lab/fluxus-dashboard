import { useId, useRef, useState } from 'react'
import { useLanguage } from '../../i18n/LanguageContext'
import { STATES, STATE_LADDER, WINDOWS, windowBounds, visibleFrom, countsAt, namesByState } from './rotationLogic'

// short and wide: the names live under the chart in the same card now, so the
// terrain gives up height to them and the card stays level with Flux beside it
const W = 640, H = 230, PAD = { l: 6, r: 6, t: 6, b: 16 }
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
export default function TerrainCard({ ladder, loading, wk, setWk, open, onToggle, selected, onSelect }) {
  const { t } = useLanguage()
  const win = useId()
  const [hov, setHov] = useState(null)
  const svgRef = useRef(null)
  const h = ladder?.history?.['2w'] ?? null
  const dates = h?.dates ?? []
  const m = dates.length
  const total = Math.max(1, ...(h?.measurable ?? [Object.keys(ladder?.themes ?? {}).length]))
  const bounds = windowBounds(dates, wk)
  const end = bounds?.end ?? m - 1
  // draw only as far back as the oldest window the select can reach
  const from = visibleFrom(dates)
  const idx = Array.from({ length: Math.max(0, m - from) }, (_, i) => i + from)
  const x = (i) => PAD.l + ((i - from) * (W - PAD.l - PAD.r)) / Math.max(1, m - 1 - from)
  const y = (v) => PAD.t + (1 - v / total) * (H - PAD.t - PAD.b)
  const stacks = []
  if (h) {
    let base = idx.map(() => 0)
    STACK.forEach((k) => {
      const top = base.map((b, j) => b + (h[k]?.[idx[j]] ?? 0))
      stacks.push({ k, d: `M${top.map((v, j) => `${x(idx[j]).toFixed(1)} ${y(v).toFixed(1)}`).join(' L')} L${base.map((v, j) => `${x(idx[j]).toFixed(1)} ${y(v).toFixed(1)}`).reverse().join(' L')} Z` })
      base = top
    })
  }
  const counts = countsAt(h, end)

  const indexAt = (e) => {
    const svg = svgRef.current; const pt = svg.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY
    const p = pt.matrixTransform(svg.getScreenCTM().inverse())
    return Math.max(from, Math.min(m - 1, from + Math.round((p.x - PAD.l) / ((W - PAD.l - PAD.r) / Math.max(1, m - 1 - from)))))
  }
  const hc = hov == null ? null : countsAt(h, hov)
  const tipX = hov == null ? 0 : hov - from > (m - from) / 2 ? x(hov) - 134 : x(hov) + 8

  return (
    <div className="rot-card">
      <div className="rot-head">
        <h2 className="rot-title">{t('rot.terrain')}</h2>
        <div className="rot-tools">
          {m > 0 && <span className="rot-meta rot-counts">{dates[end]}{STATES.map((s) => <span key={s} title={s}><i style={{ background: STATE_LADDER[s] }} />{counts[s]}</span>)}</span>}
          <select className="rot-sel" value={wk} onChange={(e) => setWk(+e.target.value)} aria-label="window" disabled={!m}>
            {WINDOWS.map((l, k) => <option key={k} value={k} disabled={!windowBounds(dates, k)}>{t(l)}{windowBounds(dates, k) ? '' : ` · ${t('rot.nodata')}`}</option>)}
          </select>
          <button type="button" className="rot-btn rot-plus" aria-expanded={open} aria-label={t('rot.expand')} onClick={onToggle} disabled={!m}>{open ? '−' : '+'}</button>
        </div>
      </div>
      {m - from > 1 ? (
        <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} className="rot-chart" role="img" aria-label="four-state counts by session, two-week board"
             onPointerMove={(e) => setHov(indexAt(e))} onPointerLeave={() => setHov(null)} style={{ touchAction: 'none' }}>
          {/* A lightbox, not a tinted block: the whole terrain is drawn faint, the
              picked fortnight is drawn again over it at full strength. Opacity
              carries it, so it reads the same on paper and on ink — the old
              version washed the outside toward the surface colour, which made
              the window look like a dark slab in the light theme and something
              else again in the dark one (Andy 2026-09-06). */}
          <defs><clipPath id={win}><rect x={bounds ? x(bounds.start) : PAD.l} y={PAD.t - 2}
                width={bounds ? Math.max(0, x(bounds.end) - x(bounds.start)) : W - PAD.l - PAD.r} height={H - PAD.t - PAD.b + 4} /></clipPath></defs>
          <g opacity=".3">{stacks.map(({ k, d }) => <path key={k} d={d} fill={STATE_LADDER[k]} stroke="var(--color-surface)" strokeWidth="1" />)}</g>
          <g clipPath={`url(#${win})`}>{stacks.map(({ k, d }) => <path key={k} d={d} fill={STATE_LADDER[k]} stroke="var(--color-surface)" strokeWidth="1" />)}</g>
          {bounds && [bounds.start, bounds.end].map((i, k) => (
            <line key={k} x1={x(i).toFixed(1)} x2={x(i).toFixed(1)} y1={PAD.t - 2} y2={H - PAD.b + 2} stroke="var(--color-border)" strokeWidth=".8" />
          ))}
          <text className="rot-mono" x={x(from)} y={H - 4}>{dates[from].slice(5)}</text>
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
      {open && <StateBand ladder={ladder} wk={wk} selected={selected} onSelect={onSelect} />}
    </div>
  )
}

/** the names under the terrain — who sat in each state on the picked window's last session */
function StateBand({ ladder, wk, selected, onSelect }) {
  const h = ladder?.history?.['2w'] ?? null
  const dates = h?.dates ?? []
  const m = dates.length
  if (!m) return null
  const names = Object.keys(ladder?.themes ?? {})
  const end = windowBounds(dates, wk)?.end ?? m - 1
  const { byState, known } = namesByState(names, (n) => ladder?.series?.[n] ?? null, (n) => ladder?.themes?.[n]?.['2w'] ?? null, end, m - 1)
  return (
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
  )
}
