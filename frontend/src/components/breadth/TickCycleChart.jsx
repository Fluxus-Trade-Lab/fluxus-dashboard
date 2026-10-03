import { useState } from 'react'
import { useTickCycle } from '../../hooks/useTickCycle'
import { tickSeries } from './tickCycleMath'

/**
 * The TICK cycle as a chart — Linda Raschke's read: the 10-day averages of
 * the NYSE TICK's daily high, close and low. When the high and low averages
 * pull together the band is contracted (a grind); when they spread it is open.
 *
 * Andy 2026-10-03: 「linda raschke的tick chart也应该在advanced里面」. The chart
 * came off on 08-24 because tick_cycle.json carried one day only; RND Linda
 * added the `history` array the same day (T-1003-81).
 *
 * Neutral tints, not red/green: entering the contracted band lowers 5%
 * drawdown odds (components/dashboard/TickBand.jsx has the numbers), so it is not an alarm.
 */
const W = 1100, H = 240, L = 8, R = 56, T = 22, B = 22
const INK = { high: 'var(--color-text)', close: 'var(--color-accent)', low: 'var(--color-text)' }
const BAND = { grind: { fill: 'var(--color-text)', opacity: 0.08, label: 'Contracted' }, washout: { fill: 'var(--color-accent)', opacity: 0.12, label: 'Open' } }

export default function TickCycleChart() {
  const { data } = useTickCycle()
  const [hover, setHover] = useState(null)
  const s = tickSeries(data)
  if (!s) return null
  const { rows, lo, hi, runs } = s
  const n = rows.length
  const x = (i) => L + (i * (W - L - R)) / (n - 1)
  const y = (v) => T + (1 - (v - lo) / (hi - lo)) * (H - T - B)
  const path = (k) => rows.map((r, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(r[k]).toFixed(1)}`).join('')
  const last = rows[n - 1]
  const h = hover == null ? null : rows[hover]
  const months = rows.map((r, i) => [r.date.slice(0, 7), i]).filter(([m], i, a) => i === 0 || m !== a[i - 1][0])

  const onMove = (e) => {
    const box = e.currentTarget.getBoundingClientRect()
    const px = ((e.clientX - box.left) / box.width) * W
    setHover(Math.max(0, Math.min(n - 1, Math.round(((px - L) / (W - L - R)) * (n - 1)))))
  }

  return (
    <div className="bg-[var(--color-bg)] rounded-2xl p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2 mb-1.5">
        <h3 className="m-0 text-[13px] font-semibold text-[var(--color-text-bold)]">TICK cycle</h3>
        <span className="font-mono tabular-nums text-[11px] text-[var(--color-text-muted)]" data-testid="tick-readout">
          {(h ?? last).date} · high {Math.round((h ?? last).ma_high)} · close {Math.round((h ?? last).ma_close)} · low {Math.round((h ?? last).ma_low)}
          {(h ?? last).band !== 'neutral' && ` · ${BAND[(h ?? last).band]?.label ?? (h ?? last).band}`}
        </span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img"
           aria-label={`TICK 10-day averages of high, close and low, ${n} sessions`}
           onMouseMove={onMove} onMouseLeave={() => setHover(null)}>
        {runs.map(([a, b, band]) => (
          <rect key={`${a}-${band}`} x={x(a) - 1} y={T} width={Math.max(2, x(b) - x(a) + 2)} height={H - T - B}
                fill={BAND[band].fill} opacity={BAND[band].opacity} />
        ))}
        <line x1={L} x2={W - R} y1={y(0)} y2={y(0)} stroke="var(--color-border)" />
        {['high', 'low'].map((k) => <path key={k} d={path(`ma_${k}`)} fill="none" stroke={INK[k]} strokeWidth="1.4" />)}
        <path d={path('ma_close')} fill="none" stroke={INK.close} strokeWidth="1.4" />
        {['high', 'close', 'low'].map((k) => (
          <text key={k} x={W - R + 6} y={y(last[`ma_${k}`]) + 4} fontSize="11" className="font-mono" style={{ fill: INK[k] }}>{Math.round(last[`ma_${k}`])}</text>
        ))}
        {months.map(([m, i]) => (
          <text key={m} x={x(i)} y={H - 6} fontSize="10" style={{ fill: 'var(--color-text-muted)' }}>{m.slice(5) === '01' ? m.slice(0, 4) : m.slice(5)}</text>
        ))}
        <text x={L + 4} y={T - 8} fontSize="11">
          <tspan style={{ fill: 'var(--color-text)' }}>High / low</tspan>
          <tspan dx="10" style={{ fill: 'var(--color-accent)' }}>Close</tspan>
          <tspan dx="10" style={{ fill: 'var(--color-text-muted)' }}>shaded: contracted (grey) · open (accent)</tspan>
        </text>
        {hover != null && <line x1={x(hover)} x2={x(hover)} y1={T} y2={H - B} stroke="var(--color-text-muted)" strokeDasharray="3 3" />}
      </svg>
    </div>
  )
}
