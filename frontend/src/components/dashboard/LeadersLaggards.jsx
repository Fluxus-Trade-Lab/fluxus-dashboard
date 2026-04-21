import { fmtPct, pctColor } from '../../lib/format'

function TopList({ title, items }) {
  if (!items || items.length === 0) return null

  return (
    <div>
      <h4 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] mb-1.5">
        {title}
      </h4>
      <div className="flex flex-col gap-1">
        {items.map((etf) => (
          <div key={etf.ticker} className="flex items-center justify-between gap-2">
            <span className="font-mono text-xs font-medium text-[var(--color-text-bold)]">
              {etf.ticker}
            </span>
            <span className={`font-mono text-xs ${pctColor(etf.change)}`}>
              {fmtPct(etf.change)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function LeadersLaggards({ etfs }) {
  if (!etfs || etfs.length === 0) return null

  const sorted1d = [...etfs].sort((a, b) => (b.change_pct ?? 0) - (a.change_pct ?? 0))
  const sorted1w = [...etfs].sort((a, b) => (b.perf_1w ?? 0) - (a.perf_1w ?? 0))

  const dailyLeaders = sorted1d.slice(0, 3).map(e => ({ ticker: e.ticker, change: e.change_pct }))
  const dailyLaggards = sorted1d.slice(-3).reverse().map(e => ({ ticker: e.ticker, change: e.change_pct }))
  const weeklyLeaders = sorted1w.slice(0, 3).map(e => ({ ticker: e.ticker, change: e.perf_1w }))
  const weeklyLaggards = sorted1w.slice(-3).reverse().map(e => ({ ticker: e.ticker, change: e.perf_1w }))

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded overflow-hidden">
      <div className="px-3 py-1.5 border-b border-[var(--color-border)]">
        <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          Industries
        </span>
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-3 px-3 py-2.5">
        <TopList title="Daily Leaders" items={dailyLeaders} />
        <TopList title="Weekly Leaders" items={weeklyLeaders} />
        <TopList title="Daily Laggards" items={dailyLaggards} />
        <TopList title="Weekly Laggards" items={weeklyLaggards} />
      </div>
    </div>
  )
}
