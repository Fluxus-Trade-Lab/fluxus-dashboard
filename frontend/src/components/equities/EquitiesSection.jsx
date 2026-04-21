import { useMemo } from 'react'
import EtfSection from './EtfSection'
import LeadersLaggards from '../dashboard/LeadersLaggards'
import { ETF_GROUPS } from '../../lib/etfGroups'

const TABLE_GROUPS = ['Indices', 'S&P Style', 'Sel Sectors']

export default function EquitiesSection({ data }) {
  const etfData = data?.etf_data

  const { grouped, industryEtfs } = useMemo(() => {
    if (!etfData) return { grouped: {}, industryEtfs: [] }

    const tickerMap = {}
    for (const etf of etfData) {
      tickerMap[etf.ticker] = etf
    }

    const groups = {}
    for (const groupName of TABLE_GROUPS) {
      const tickers = ETF_GROUPS[groupName]
      if (!tickers) continue
      groups[groupName] = tickers.map((t) => tickerMap[t]).filter(Boolean)
    }

    const industries = (ETF_GROUPS.Industries || [])
      .map((t) => tickerMap[t])
      .filter(Boolean)

    return { grouped: groups, industryEtfs: industries }
  }, [etfData])

  if (!etfData) return null

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      {TABLE_GROUPS.map((groupName) => {
        const etfs = grouped[groupName]
        if (!etfs || etfs.length === 0) return null
        return (
          <EtfSection key={groupName} title={groupName} etfs={etfs} />
        )
      })}
      <LeadersLaggards etfs={industryEtfs} />
    </div>
  )
}
