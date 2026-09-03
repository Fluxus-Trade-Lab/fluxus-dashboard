import { useMemo } from 'react'
import { fmtPct, TipBody } from './TipBody'

const W = 1000, H = 560, PAD = { l: 40, r: 30, t: 30, b: 36 }, TAIL = 8

/**
 * The field: quarter excess (→) against acceleration (↑), one dot per group,
 * sized by member count, coloured by its state on the scrubbed session, with
 * a tapered tail over the last eight sessions. Extents are fixed across the
 * whole archive so the scrubber does not rescale the picture under you.
 */
export default function FieldChart({ rows, historyOf, dates, at, selected, onSelect, onTip, offTip, colourOf }) {
  const { X, Y } = useMemo(() => {
    let mx = 0, my = 0
    rows.forEach((r) => {
      const h = historyOf(r.group)
      mx = Math.max(mx, Math.abs(r.excess_3m), ...(h?.excess ?? []).filter((v) => v != null).map(Math.abs))
      my = Math.max(my, Math.abs(r.rs_accel), ...(h?.rs_accel ?? []).filter((v) => v != null).map(Math.abs))
    })
    return { X: (mx || 0.1) * 1.05, Y: (my || 0.1) * 1.05 }
  }, [rows, historyOf])
  const x0 = (PAD.l + W - PAD.r) / 2, y0 = (PAD.t + H - PAD.b) / 2
  const sx = (W - PAD.l - PAD.r) / 2 / X, sy = (H - PAD.t - PAD.b) / 2 / Y
  const px = (v) => x0 + v * sx, py = (v) => y0 - v * sy
  const live = !dates.length
  const posOf = (r) => {
    if (live) return { x: r.excess_3m, y: r.rs_accel, state: r.state }
    const h = historyOf(r.group); if (!h) return null
    const x = h.excess?.[at], y = h.rs_accel?.[at]
    return x == null || y == null ? null : { x, y, state: h.state?.[at] }
  }
  const counts = { Leading: 0, Improving: 0, Weakening: 0, Lagging: 0 }
  const placed = rows.map((r) => ({ r, p: posOf(r) })).filter((o) => o.p)
  placed.forEach(({ p }) => { if (p.state in counts) counts[p.state] += 1 })
  const caps = [
    ['Leading', W - PAD.r, PAD.t + 14, 'end'], ['Weakening', W - PAD.r, H - PAD.b - 6, 'end'],
    ['Improving', PAD.l, PAD.t + 14, 'start'], ['Lagging', PAD.l, H - PAD.b - 6, 'start'],
  ]
  const isSel = (r) => selected.includes(r.group)
  const dim = selected.length > 0

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="block w-full h-auto" role="img"
         aria-label={`${placed.length} groups by quarter excess and acceleration`}>
      <line x1={x0} x2={x0} y1={PAD.t} y2={H - PAD.b} stroke="var(--rot-grid)" strokeWidth="0.7" />
      <line x1={PAD.l} x2={W - PAD.r} y1={y0} y2={y0} stroke="var(--rot-grid)" strokeWidth="0.7" />
      {caps.map(([s, x, y, anchor]) => (
        <text key={s} x={x} y={y} textAnchor={anchor} style={{ fontSize: 13, fontWeight: 800, fill: colourOf[s] }}>
          {s} <tspan style={{ fontWeight: 600, fill: 'var(--rot-muted)' }}>{counts[s]}</tspan>
        </text>
      ))}
      <text x={W - PAD.r} y={y0 - 6} textAnchor="end">quarter vs SPY → {fmtPct(X)}</text>
      <text x={x0 + 6} y={PAD.t + 4}>accel ↑ {fmtPct(Y)}</text>
      {/* tails */}
      {!live && placed.map(({ r, p }) => {
        const h = historyOf(r.group); const pts = []
        for (let k = Math.max(0, at - TAIL); k <= at; k++) {
          if (h.excess?.[k] != null && h.rs_accel?.[k] != null) pts.push([px(h.excess[k]), py(h.rs_accel[k])])
        }
        if (pts.length < 2) return null
        const on = !dim || isSel(r)
        return pts.slice(1).map((pt, k) => {
          const t = (k + 1) / (pts.length - 1)
          return <line key={`${r.group}-${k}`} x1={pts[k][0].toFixed(1)} y1={pts[k][1].toFixed(1)} x2={pt[0].toFixed(1)} y2={pt[1].toFixed(1)}
                       stroke={colourOf[p.state] ?? 'var(--rot-muted)'} strokeWidth={(0.5 + 1.8 * t).toFixed(1)}
                       strokeOpacity={(on ? 0.12 + 0.6 * t : 0.05).toFixed(2)} strokeLinecap="round" />
        })
      })}
      {/* dots */}
      {placed.map(({ r, p }, j) => {
        const sel = isSel(r), on = !dim || sel
        const rad = 2.6 + Math.sqrt(r.members ?? r.tickers?.length ?? 1) * 0.45
        const cx = px(p.x), cy = py(p.y)
        const label = sel || (!dim && (Math.abs(p.x) > X * 0.55 || Math.abs(p.y) > Y * 0.55))
        return (
          <g key={r.group}>
            <circle className="rot-pop" style={{ animationDelay: `${j * 12}ms`, cursor: 'pointer' }}
                    cx={cx.toFixed(1)} cy={cy.toFixed(1)} r={(sel ? rad + 2 : rad).toFixed(1)}
                    fill={colourOf[p.state] ?? 'var(--rot-muted)'} fillOpacity={on ? 0.95 : 0.18}
                    stroke={sel ? 'var(--rot-paper)' : 'var(--rot-card)'} strokeWidth={sel ? 2 : 1.2}
                    onClick={() => onSelect(r.group)}
                    onMouseMove={(e) => onTip(e, <TipBody r={r} state={p.state} x={p.x} y={p.y} colourOf={colourOf} />)}
                    onMouseLeave={offTip} />
            {label && <text className="rot-ink" x={(cx + rad + 5).toFixed(1)} y={(cy + 3.5).toFixed(1)}
                            style={{ fontSize: 11, fill: sel ? '#fff' : undefined }}>{r.group}</text>}
          </g>
        )
      })}
    </svg>
  )
}
