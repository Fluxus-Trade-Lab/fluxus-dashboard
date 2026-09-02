import { compute, isHit } from '../lib/trimTargets'

export default function TrimTargetsLine({ trade }) {
  const targets = compute(trade)
  if (!targets) return null
  const hit4 = isHit(trade.trims, targets.targetR4, trade.direction)
  const hit8 = isHit(trade.trims, targets.targetR8, trade.direction)
  return (
    <div className="text-[11px] text-[var(--color-text-muted)] mt-0.5">
      <span className={hit4 ? 'line-through text-[var(--color-text-muted)]' : ''}>
        +4R ${targets.targetR4.toFixed(2)}
      </span>
      {' · '}
      <span className={hit8 ? 'line-through text-[var(--color-text-muted)]' : ''}>
        +8R ${targets.targetR8.toFixed(2)}
      </span>
    </div>
  )
}
