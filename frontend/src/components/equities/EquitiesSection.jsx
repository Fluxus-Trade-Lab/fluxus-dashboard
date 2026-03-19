import { useMemo } from 'react'
import EtfSection from './EtfSection'
import { ETF_GROUPS } from '../../lib/etfGroups'

const GROUP_ORDER = [
  'Indices',
  'S&P Style',
  'Sel Sectors',
  'Industries',
]

export default function EquitiesSection({ data }) {
  const etfData = data?.etf_data

  const groupedEtfs = useMemo(() => {
    if (!etfData) return {}

    const tickerMap = {}
    for (const etf of etfData) {
      tickerMap[etf.ticker] = etf
    }

    const groups = {}
    for (const groupName of GROUP_ORDER) {
      const tickers = ETF_GROUPS[groupName]
      if (!tickers) continue
      groups[groupName] = tickers
        .map((t) => tickerMap[t])
        .filter(Boolean)
    }
    return groups
  }, [etfData])

  if (!etfData) return null

  return (
    <div className="flex flex-col gap-3">
      {GROUP_ORDER.map((groupName) => {
        const etfs = groupedEtfs[groupName]
        if (!etfs || etfs.length === 0) return null
        return (
          <EtfSection
            key={groupName}
            title={groupName}
            etfs={etfs}
          />
        )
      })}
    </div>
  )
}
