import { useMemo } from 'react'
import { changeOf, changeColour } from '../groups/stateChange'
import { positionAt, CHANGE_WINDOW } from './rotationLogic'
import { TipBody } from './TipBody'

const W = 1000, H = 600, PAD = { l: 36, r: 36, t: 34, b: 34 }

/**
 * The field as an ink painting (Andy 2026-09-03: 吴冠中). Thin lines are the
 * whole archive of each group's path; a small dot is where it is at the
 * scrubbed moment; the pair colours only the dots that changed sides over the
 * last five sessions — blue stronger, red weaker — and those get their names.
 * Nothing else is written on it. `t` is fractional, so play glides.
 */
export default function FieldChart({ rows, historyOf, dates, t, selected, onSelect, onTip, offTip }) {
  const { X, Y } = useMemo(() => {
    let mx = 0, my = 0
    rows.forEach((r) => {
      const h = historyOf(r.group)
      mx = Math.max(mx, Math.abs(r.excess_3m), ...(h?.excess ?? []).filter((v) => v != null).map(Math.abs))
      my = Math.max(my, Math.abs(r.rs_accel), ...(h?.rs_accel ?? []).filter((v) => v != null).map(Math.abs))
    })
    return { X: (mx || 0.1) * 1.08, Y: (my || 0.1) * 1.08 }
  }, [rows, historyOf])
  const x0 = (PAD.l + W - PAD.r) / 2, y0 = (PAD.t + H - PAD.b) / 2
  const sx = (W - PAD.l - PAD.r) / 2 / X, sy = (H - PAD.t - PAD.b) / 2 / Y
  const px = (v) => x0 + v * sx, py = (v) => y0 - v * sy
  const live = !dates.length
  const i = Math.round(t)
  const items = rows.map((r) => {
    const h = historyOf(r.group)
    const p = live ? { x: r.excess_3m, y: r.rs_accel, state: r.state } : positionAt(h, t)
    if (!p) return null
    const dir = live ? null : changeOf((h.state ?? []).slice(Math.max(0, i - CHANGE_WINDOW), i + 1))
    return { r, h, p, dir }
  }).filter(Boolean)
  const dim = selected.length > 0
  const isSel = (r) => selected.includes(r.group)

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="block w-full h-auto" role="img" aria-label={`${items.length} groups by quarter excess and acceleration`}>
      <line x1={x0} x2={x0} y1={PAD.t} y2={H - PAD.b} stroke="var(--color-border)" strokeWidth="0.6" />
      <line x1={PAD.l} x2={W - PAD.r} y1={y0} y2={y0} stroke="var(--color-border)" strokeWidth="0.6" />
      <text x={W - PAD.r} y={PAD.t - 12} textAnchor="end">Leading</text>
      <text x={W - PAD.r} y={H - PAD.b + 22} textAnchor="end">Weakening</text>
      <text x={PAD.l} y={PAD.t - 12}>Improving</text>
      <text x={PAD.l} y={H - PAD.b + 22}>Lagging</text>
      {/* the lines: each group's whole path up to now, one thin ink stroke */}
      {!live && items.map(({ r, h }) => {
        const pts = []
        for (let k = 0; k <= Math.floor(t); k++) if (h.excess?.[k] != null && h.rs_accel?.[k] != null) pts.push(`${px(h.excess[k]).toFixed(1)} ${py(h.rs_accel[k]).toFixed(1)}`)
        const head = positionAt(h, t); if (head) pts.push(`${px(head.x).toFixed(1)} ${py(head.y).toFixed(1)}`)
        if (pts.length < 2) return null
        const on = !dim || isSel(r)
        return <path key={r.group} d={`M${pts.join(' L')}`} fill="none" stroke="var(--color-text)" strokeWidth={isSel(r) ? 1.4 : 0.7}
                     strokeOpacity={on ? (isSel(r) ? 0.75 : 0.32) : 0.06} strokeLinejoin="round" strokeLinecap="round" />
      })}
      {/* the dots, and the names of the ones that changed sides */}
      {items.map(({ r, p, dir }) => {
        const sel = isSel(r), on = !dim || sel
        const colour = changeColour(dir) ?? 'var(--color-text)'
        const rad = sel ? 5 : dir ? 4 : 2.6
        const cx = px(p.x), cy = py(p.y)
        return (
          <g key={r.group}>
            <circle className="rot-pop" style={{ cursor: 'pointer' }} cx={cx.toFixed(1)} cy={cy.toFixed(1)} r={rad}
                    fill={colour} fillOpacity={on ? 1 : 0.15} stroke="var(--color-surface)" strokeWidth={sel ? 2 : 1}
                    onClick={() => onSelect(r.group)} onMouseMove={(e) => onTip(e, <TipBody r={r} state={p.state} x={p.x} y={p.y} />)} onMouseLeave={offTip} />
            {(sel || (dir && on)) && (
              <text className="rot-ink" x={(cx + rad + 4).toFixed(1)} y={(cy + 3.5).toFixed(1)} style={{ fill: sel ? 'var(--color-text)' : colour }}>{r.group}</text>
            )}
          </g>
        )
      })}
    </svg>
  )
}
