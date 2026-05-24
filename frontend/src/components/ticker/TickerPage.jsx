import { useMemo } from 'react'
import { PortfolioProvider, usePortfolio } from '../portfolio/context/PortfolioContext'
import { useUniverse } from '../../hooks/useUniverse'
import { useTickerData } from '../../hooks/useTickerData'
import { enrichTrades } from '../portfolio/lib/calculations'
import TickerHeader from './TickerHeader'
import TickerQuickStats from './TickerQuickStats'
import TickerChart from './TickerChart'
import TickerStatusPanel from './TickerStatusPanel'
import TickerTrades from './TickerTrades'
import TickerEarnings from './TickerEarnings'
import TickerValuation from './TickerValuation'
import TickerQuarterlyMetrics from './TickerQuarterlyMetrics'
import TickerAnalystSentiment from './TickerAnalystSentiment'
import TickerStats from './TickerStats'

/**
 * Per-ticker tear-sheet page. Phase 3a: skeleton with chart + execution +
 * basic stats. Phase 3b/3c/3d add fundamentals, technicals, and AI narrative.
 *
 * Wraps the body in PortfolioProvider so usePortfolio() works when the
 * tear-sheet is opened outside the Portfolio tab.
 */
export default function TickerPage({ symbol }) {
  return (
    <PortfolioProvider>
      <TickerPageBody symbol={symbol} />
    </PortfolioProvider>
  )
}

function TickerPageBody({ symbol }) {
  const { state, dispatch } = usePortfolio()
  const { universe } = useUniverse()
  const { data: tickerData } = useTickerData(symbol)

  const universeRow = useMemo(() => {
    if (!universe) return null
    return universe.find(r => r.ticker === symbol) || null
  }, [universe, symbol])

  // Enrich trades for this ticker so totals/PL are computed
  const enrichedAll = useMemo(() => {
    const px = state.startingCapital || 1
    return enrichTrades(state.trades, px, state.dailyPrices)
  }, [state.trades, state.startingCapital, state.dailyPrices])

  const tradesOnTicker = useMemo(
    () => enrichedAll.filter(t => t.ticker === symbol),
    [enrichedAll, symbol],
  )

  const openTrade = useMemo(() => {
    const open = tradesOnTicker.filter(t => !t.isClosed && t.currentQty > 0)
    if (!open.length) return null
    // Largest open layer as primary
    return open.reduce((best, t) => (t.currentQty > best.currentQty ? t : best), open[0])
  }, [tradesOnTicker])

  const lastClosed = useMemo(() => {
    const closed = tradesOnTicker.filter(t => t.isClosed)
    if (!closed.length) return null
    return closed.reduce((latest, t) =>
      (t.entryDate || '').localeCompare(latest.entryDate || '') > 0 ? t : latest, closed[0],
    )
  }, [tradesOnTicker])

  const handleAcceptStop = (id, newStop) => {
    dispatch({ type: 'UPDATE_TRADE', id, updates: { stopPrice: newStop } })
  }

  return (
    <div className="max-w-[1800px] mx-auto px-3 py-4">
      <TickerHeader symbol={symbol} universe={universeRow} />

      <TickerQuickStats tickerData={tickerData} universe={universeRow} />

      <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-4 mb-4">
        <TickerChart symbol={symbol} />
        <TickerStatusPanel
          symbol={symbol}
          openTrade={openTrade}
          lastClosed={lastClosed}
          universe={universeRow}
          onAcceptStop={handleAcceptStop}
        />
      </div>

      <div className="mb-4">
        <TickerTrades symbol={symbol} trades={enrichedAll} />
      </div>

      {/* Fundamentals row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <TickerEarnings tickerData={tickerData} />
        <TickerValuation tickerData={tickerData} />
      </div>

      <div className="mb-4">
        <TickerQuarterlyMetrics tickerData={tickerData} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>{/* placeholder for Phase 3c Catalysts section */}</div>
        <TickerAnalystSentiment tickerData={tickerData} />
      </div>

      <div>
        <TickerStats universe={universeRow} />
      </div>
    </div>
  )
}
