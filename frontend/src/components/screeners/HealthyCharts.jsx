import TickerGrid from './TickerGrid'

export default function HealthyCharts({ data }) {
  if (!data?.rs_groups) return null

  const sortedKeys = Object.keys(data.rs_groups)
    .sort((a, b) => Number(b) - Number(a))

  return (
    <div className="flex flex-col gap-3">
      {sortedKeys.map((key) => {
        const tickers = data.rs_groups[key]
        if (!tickers || tickers.length === 0) return null
        return (
          <div key={key}>
            <h4 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-1.5">
              RS {key}
            </h4>
            <TickerGrid tickers={tickers} />
          </div>
        )
      })}
    </div>
  )
}
