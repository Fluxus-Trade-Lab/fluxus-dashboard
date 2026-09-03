import { wkAccel, questionOf, swarmLevels } from './rotationLogic'
import { fmtPct, TipBody } from './TipBody'

const W = 640, H = 170, PAD = { l: 20, r: 20 }

/** every group by this week's pace minus the prior three weeks' pace; ringed when it sits on one of the three lists */
export default function SwarmChart({ rows, lists, selected, onSelect, onTip, offTip, colourOf }) {
  const on = new Set([...lists.q1, ...lists.q2, ...lists.q3].map((r) => r.group))
  const items = rows.map((r) => ({ r, v: wkAccel(r) })).sort((a, b) => a.v - b.v)
  if (!items.length) return null
  const lo = Math.min(...items.map((o) => o.v)), hi = Math.max(...items.map((o) => o.v))
  const x = (v) => PAD.l + ((v - lo) / (hi - lo || 1)) * (W - PAD.l - PAD.r)
  const levels = swarmLevels(items.map((o) => x(o.v)), 10)
  const dim = selected.length > 0
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="block w-full h-auto" role="img" aria-label="weekly acceleration swarm">
      <line x1={PAD.l} x2={W - PAD.r} y1={H / 2} y2={H / 2} stroke="var(--rot-grid)" strokeWidth="0.7" />
      <line x1={x(0)} x2={x(0)} y1={H / 2 - 44} y2={H / 2 + 44} stroke="var(--rot-grid)" strokeWidth="0.7" />
      {items.map(({ r, v }, j) => {
        const lvl = levels[j]; const cy = H / 2 + (lvl % 2 ? 1 : -1) * Math.ceil(lvl / 2) * 10
        const sel = selected.includes(r.group), listed = on.has(r.group)
        return (
          <circle key={r.group} className="rot-pop" style={{ animationDelay: `${j * 12}ms`, cursor: 'pointer' }}
                  cx={x(v).toFixed(1)} cy={cy} r={sel ? 6 : 4.5} fill={colourOf[r.state] ?? 'var(--rot-muted)'}
                  fillOpacity={!dim || sel ? 0.95 : 0.22} stroke={sel ? 'var(--rot-paper)' : listed ? 'var(--rot-paper)' : 'var(--rot-card)'}
                  strokeWidth={sel || listed ? 1.5 : 1} strokeOpacity={sel ? 1 : listed ? 0.7 : 1}
                  onClick={() => onSelect(r.group)}
                  onMouseMove={(e) => onTip(e, <><TipBody r={r} state={r.state} /><br />weekly acceleration <b>{fmtPct(v)}</b>{questionOf(r) ? ` · on list ${questionOf(r).replace('q', '')}` : ''}</>)}
                  onMouseLeave={offTip} />
        )
      })}
      <text x={PAD.l} y={H - 6} style={{ fontWeight: 800 }}>{fmtPct(lo)}</text>
      <text x={W - PAD.r} y={H - 6} textAnchor="end" style={{ fontWeight: 800 }}>{fmtPct(hi)}</text>
      <text x={x(0)} y={H / 2 - 50} textAnchor="middle">0</text>
    </svg>
  )
}
