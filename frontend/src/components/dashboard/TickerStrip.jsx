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

  // One scale across the ten, so the bars are comparable card to card: today's
  // widest move among the benchmarks that carry one. Naming a fixed ±X% would
  // be a constant nobody measured.
  const scale = useMemo(() => {
    const vals = STRIP_TICKERS
      .map(({ key }) => etfMap[key]?.change_pct)
      .filter((v) => Number.isFinite(v))
      .map(Math.abs)
    return vals.length ? Math.max(...vals) : 0
  }, [etfMap])

  return (
    // 2 / 5 / 10 — every count divides the ten cards, so each row is always
    // full: 2-up on a phone, 5+5 on a laptop, one row on wide screens. auto-fit
    // packed 7+3 at laptop width. The 10-across step needs ~150px per card
    // after the 214px rail, so it starts at 1720px, not at Tailwind's xl=1280
    // (which squeezed ten cards to 101px and clipped their text).
    <div className="ticker-strip-10 grid gap-2 grid-cols-2 sm:grid-cols-5">
      {STRIP_TICKERS.map(({ key, source }) => (
        <TickerCard
          key={key}
          ticker={key}
          signal={source === 'signals' ? signals?.[key] : null}
          etf={etfMap[key] || null}
          scale={scale}
        />
      ))}
    </div>
  )
}
