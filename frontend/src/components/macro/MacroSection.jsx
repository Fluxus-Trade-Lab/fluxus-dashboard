import SignalLights from './SignalLights'
import MarketConditions from './MarketConditions'
import TrendStatus from './TrendStatus'
import PowerTrend from './PowerTrend'

export default function MacroSection({ data }) {
  const signals = data?.signals

  if (!signals) return null

  return (
    <div>
      <div className="bg-[var(--color-surface)] border-b border-[var(--color-border)] px-3 py-3">
        <SignalLights signals={signals} />
      </div>
      <div className="bg-[var(--color-surface)] border-b border-[var(--color-border)] px-3 py-3">
        <MarketConditions signals={signals} />
      </div>
      <div className="bg-[var(--color-surface)] border-b border-[var(--color-border)] px-3 py-3">
        <TrendStatus signals={signals} />
      </div>
      <div className="bg-[var(--color-surface)] border-b border-[var(--color-border)] px-3 py-3">
        <PowerTrend signals={signals} />
      </div>
    </div>
  )
}
