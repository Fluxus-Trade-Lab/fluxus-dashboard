import TickerGrid from './TickerGrid'

const BUCKETS = ['100', '99', '98', '97']

export default function Momentum97({ data }) {
  if (!data?.buckets) return null

  return (
    <div className="flex flex-col gap-3">
      {BUCKETS.map((key) => {
        const tickers = data.buckets[key]
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
