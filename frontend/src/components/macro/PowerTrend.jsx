const CHECKS = [
  { key: '3d_gt_20sma', label: 'Close > 20 SMA (3d)' },
  { key: '3d_gt_50sma', label: 'Close > 50 SMA (3d)' },
  { key: '3d_gt_200sma', label: 'Close > 200 SMA (3d)' },
  { key: '20sma_gt_50sma', label: '20 SMA > 50 SMA' },
  { key: '50sma_gt_200sma', label: '50 SMA > 200 SMA' },
]

const TICKERS = ['SPY', 'QQQ', 'IWM', 'RSP']

export default function PowerTrend({ signals }) {
  if (!signals) return null

  return (
    <div>
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-2">
        Power Trend
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr>
              <th className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] pb-1.5 pr-2">
                Check
              </th>
              {TICKERS.map((t) => (
                <th
                  key={t}
                  className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] pb-1.5 text-center"
                >
                  {t}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {CHECKS.map((check) => (
              <tr key={check.key}>
                <td className="text-xs text-[var(--color-text-secondary)] py-0.5 pr-2">
                  {check.label}
                </td>
                {TICKERS.map((ticker) => {
                  const pt = signals[ticker]?.power_trend
                  const passed = pt?.[check.key]
                  return (
                    <td
                      key={ticker}
                      className={`font-mono text-xs py-0.5 text-center ${
                        passed ? 'text-green-600' : 'text-red-500'
                      }`}
                    >
                      {passed ? 'Yes' : 'No'}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
