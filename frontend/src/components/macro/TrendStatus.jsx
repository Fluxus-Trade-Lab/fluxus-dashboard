import { pctColor } from '../../lib/format'

const TICKERS = ['SPY', 'QQQ', 'IWM', 'RSP']

const COLUMNS = [
  { key: '9ema_dist', label: '9EMA' },
  { key: '21ema_dist', label: '21EMA' },
  { key: '50sma_dist', label: '50SMA' },
  { key: '200sma_dist', label: '200SMA' },
  { key: '52w_high_dist', label: '52W High' },
]

function formatDist(val) {
  if (val == null || isNaN(val)) return '--'
  const sign = val > 0 ? '+' : ''
  return `${sign}${val.toFixed(2)}%`
}

export default function TrendStatus({ signals }) {
  if (!signals) return null

  return (
    <div>
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-2">
        Trend Status
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr>
              <th className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] pb-1.5 pr-2">
                Ticker
              </th>
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] pb-1.5 pr-2 text-right"
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {TICKERS.map((ticker) => {
              const s = signals[ticker]
              if (!s) return null
              const ts = s.trend_status || {}
              return (
                <tr key={ticker}>
                  <td className="font-mono text-sm text-[var(--color-text-bold)] py-0.5 pr-2">
                    {ticker}
                  </td>
                  {COLUMNS.map((col) => {
                    const val = ts[col.key]
                    return (
                      <td
                        key={col.key}
                        className={`font-mono text-xs py-0.5 pr-2 text-right ${pctColor(val)}`}
                      >
                        {formatDist(val)}
                      </td>
                    )
                  })}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
