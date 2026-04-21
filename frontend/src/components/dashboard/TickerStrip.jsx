import { useMemo } from 'react'
import TickerCard from './TickerCard'

// Display order for the ticker strip
const STRIP_TICKERS = [
  { key: 'SPY', source: 'signals' },
  { key: 'QQQ', source: 'signals' },
  { key: 'IWM', source: 'signals' },
  { key: 'DIA', source: 'etf' },
  { key: 'RSP', source: 'signals' },
  { key: 'QQQE', source: 'etf' },
  { key: 'BTC-USD', source: 'signals' },
  { key: 'GLD', source: 'etf' },
  { key: 'TLT', source: 'etf' },
  { key: '^VIX', source: 'signals' },
]

export default function TickerStrip({ signals, etfData }) {
  const etfMap = useMemo(() => {
    if (!etfData) return {}
    const map = {}
    for (const etf of etfData) {
      map[etf.ticker] = etf
    }
    return map
  }, [etfData])

  return (
    <div className="overflow-x-auto pb-2 -mx-2 px-2">
      <div className="flex gap-2">
        {STRIP_TICKERS.map(({ key, source }) => (
          <TickerCard
            key={key}
            ticker={key}
            signal={source === 'signals' ? signals?.[key] : null}
            etf={etfMap[key] || null}
          />
        ))}
      </div>
    </div>
  )
}
