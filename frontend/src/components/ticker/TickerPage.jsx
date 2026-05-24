import { useMemo } from 'react'
import { usePortfolio } from '../portfolio/context/PortfolioContext'
import { useUniverse } from '../../hooks/useUniverse'
import { enrichTrades } from '../portfolio/lib/calculations'
import TickerHeader from './TickerHeader'
import TickerChart from './TickerChart'
import TickerStatusPanel from './TickerStatusPanel'
import TickerTrades from './TickerTrades'
import TickerStats from './TickerStats'

/**
 * Per-ticker tear-sheet page. Phase 3a: skeleton with chart + execution +
 * basic stats. Phase 3b/3c/3d add fundamentals, technicals, and AI narrative.
 */
export default function TickerPage({ symbol }) {
  const { state, dispatch } = usePortfolio()
  const { universe } = useUniverse()

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

      <div>
        <TickerStats universe={universeRow} />
      </div>
    </div>
  )
}
