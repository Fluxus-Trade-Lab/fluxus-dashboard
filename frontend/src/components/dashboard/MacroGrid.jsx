import TrendStatus from '../macro/TrendStatus'
import PowerTrend from '../macro/PowerTrend'

export default function MacroGrid({ signals }) {
  if (!signals) return null

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-4 py-3">
        <TrendStatus signals={signals} />
      </div>
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-4 py-3">
        <PowerTrend signals={signals} />
      </div>
    </div>
  )
}
