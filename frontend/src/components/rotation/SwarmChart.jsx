import { changeOf, changeColour } from '../groups/stateChange'
import { wkAccel, questionOf, swarmLevels, CHANGE_WINDOW } from './rotationLogic'
import { fmtPct, TipBody } from './TipBody'

const W = 1000, H = 280, PAD = { l: 24, r: 24 }

/**
 * Every group by this week's pace against the prior three weeks'. Right is
 * speeding up. The fastest on each end are named — the names are the point,
 * not the count (Andy 2026-09-03). Ink dots; the pair only where a group
 * changed sides over the last five sessions; a ring where it sits on a list.
 */
export default function SwarmChart({ rows, lists, historyOf, dates, selected, onSelect, onTip, offTip, named }) {
  const listed = new Set([...lists.q1, ...lists.q2, ...lists.q3].map((r) => r.group))
  const items = rows.map((r) => ({ r, v: wkAccel(r) })).sort((a, b) => a.v - b.v)
  if (!items.length) return null
  const lo = Math.min(...items.map((o) => o.v)), hi = Math.max(...items.map((o) => o.v))
  const x = (v) => PAD.l + ((v - lo) / (hi - lo || 1)) * (W - PAD.l - PAD.r)
  const levels = swarmLevels(items.map((o) => x(o.v)), 13)
  const dim = selected.length > 0
  const last = dates.length - 1
  const nameSet = new Set(named)
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="block w-full h-auto" role="img" aria-label="weekly acceleration swarm">
      <line x1={PAD.l} x2={W - PAD.r} y1={H / 2} y2={H / 2} stroke="var(--color-border)" strokeWidth="0.6" />
      <line x1={x(0)} x2={x(0)} y1={H / 2 - 70} y2={H / 2 + 70} stroke="var(--color-border)" strokeWidth="0.6" />
      <text x={PAD.l} y={H - 8}>slowing</text>
      <text x={W - PAD.r} y={H - 8} textAnchor="end">speeding up</text>
      {items.map(({ r, v }, j) => {
        const lvl = levels[j]; const cy = H / 2 + (lvl % 2 ? 1 : -1) * Math.ceil(lvl / 2) * 13
        const sel = selected.includes(r.group), on = !dim || sel
        const h = historyOf(r.group)
        const dir = h ? changeOf((h.state ?? []).slice(Math.max(0, last - CHANGE_WINDOW), last + 1)) : null
        const colour = changeColour(dir) ?? 'var(--color-text)'
        const cx = x(v)
        return (
          <g key={r.group}>
            <circle className="rot-pop" style={{ animationDelay: `${j * 10}ms`, cursor: 'pointer' }} cx={cx.toFixed(1)} cy={cy} r={sel ? 6.5 : 5}
                    fill={colour} fillOpacity={on ? 1 : 0.15} stroke={listed.has(r.group) ? 'var(--color-text)' : 'var(--color-surface)'} strokeWidth={listed.has(r.group) ? 1.6 : 1}
                    onClick={() => onSelect(r.group)}
                    onMouseMove={(e) => onTip(e, <><TipBody r={r} state={r.state} /><br />weekly acceleration <b>{fmtPct(v)}</b>{questionOf(r) ? ` · ${questionOf(r) === 'q1' ? 'building' : questionOf(r) === 'q2' ? 'igniting' : 'fading'}` : ''}</>)}
                    onMouseLeave={offTip} />
            {(sel || (nameSet.has(r.group) && on)) && (
              <text className="rot-ink" x={cx.toFixed(1)} y={(cy + (lvl % 2 ? 1 : -1) * -14 + (lvl % 2 ? 4 : 0)).toFixed(1)} textAnchor="middle">{r.group}</text>
            )}
          </g>
        )
      })}
    </svg>
  )
}
