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
    // auto-fit + 1fr: the cards divide whatever width exists — ultrawide, laptop
    // or phone — and wrap instead of scrolling, so the row never ends in a blank
    <div className="grid gap-2"
         style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(128px, 1fr))' }}>
      {STRIP_TICKERS.map(({ key, source }) => (
        <TickerCard
          key={key}
          ticker={key}
          signal={source === 'signals' ? signals?.[key] : null}
          etf={etfMap[key] || null}
        />
      ))}
    </div>
  )
}
