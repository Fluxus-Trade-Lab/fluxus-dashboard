import { QUESTIONS, QUESTION_WORD, paces } from './rotationLogic'
import { fmtPct } from './TipBody'

/** the four stretches as a small bar shape, oldest first, this week in ink — each row's own scale */
export function Shape({ r, width = 64 }) {
  const p = paces(r); const m = Math.max(...p.map(Math.abs)) || 1
  const bw = (width - 3 * 3) / 4
  return (
    <svg viewBox={`0 0 ${width} 28`} width={width} height="28" role="img" aria-label={`four stretches: ${p.map((v) => fmtPct(v, 2)).join(', ')}`}>
      <line x1="0" x2={width} y1="14" y2="14" stroke="var(--color-border)" strokeWidth="0.6" />
      {p.map((v, k) => { const h = Math.max(1.5, (Math.abs(v) / m) * 12)
        return <rect key={k} x={k * (bw + 3)} y={v >= 0 ? 14 - h : 14} width={bw} height={h} rx="1" fill={k === 3 ? 'var(--color-text)' : 'var(--color-text-muted)'} /> })}
    </svg>
  )
}

/**
 * Three columns, three words, names and shapes — nothing else. Where a
 * question has nobody today the column says so in one line; an empty list is
 * a reading, not a gap.
 */
export default function ShapesCard({ lists, selected, onSelect }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {QUESTIONS.map((k) => (
        <div key={k}>
          <div className="rot-word mb-2">{QUESTION_WORD[k]}</div>
          {lists[k].length ? lists[k].map((r) => (
            <button key={r.group} type="button" aria-pressed={selected.includes(r.group)} onClick={() => onSelect(r.group)}
                    className="rot-row grid-cols-[1fr_64px] gap-3 items-center py-[5px]">
              <span className="text-[13px] font-medium truncate">{r.group}</span>
              <Shape r={r} />
            </button>
          )) : <div className="text-[13px] text-[var(--color-text-muted)] py-[5px]">—</div>}
        </div>
      ))}
    </div>
  )
}
