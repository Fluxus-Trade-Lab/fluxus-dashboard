import { useCallback } from 'react'
import { usePortfolio } from '../context/PortfolioContext'
import { fetchQuotes, fetchBatchHistory, fetchHistory } from '../services/priceService'
import { todayStr } from '../lib/portfolioFormat'
import { prevWeekday } from '../../../lib/tradingDate'

export function usePrices() {
  const { state, dispatch } = usePortfolio()

  /** Fetch current quotes for all open tickers */
  const refreshOpenPositions = useCallback(async () => {
    if (!state.gasUrl) {
      dispatch({ type: 'SET_LOADING', loading: false, status: 'Set your GAS proxy URL in Settings first.' })
      return
    }

    const openTickers = [...new Set(state.trades.filter(t => !t.isClosed).map(t => t.ticker))]
    if (!openTickers.length) return

    dispatch({ type: 'SET_LOADING', loading: true, status: `Fetching ${openTickers.length} quotes...` })

    try {
      const quotes = await fetchQuotes(openTickers, state.gasUrl)
      const today = todayStr()
      const newPrices = {}

      Object.entries(quotes).forEach(([ticker, q]) => {
        if (q.error) return
        if (q.price != null) newPrices[`${ticker}:${today}`] = q.price
        if (q.prevClose != null) {
          // Store prev close for 1D change calculation. Keyed off the ET
          // session, because `calculations.js` reads this key off the ET
          // session — writer and reader must share one calendar.
          newPrices[`${ticker}:${prevWeekday(today)}`] = q.prevClose
        }
      })

      dispatch({ type: 'SET_DAILY_PRICES', prices: newPrices })
      dispatch({ type: 'SET_LOADING', loading: false, status: `Updated ${Object.keys(quotes).length} tickers.` })
    } catch (e) {
      dispatch({ type: 'SET_LOADING', loading: false, status: `Refresh failed: ${e.message}` })
    }
  }, [state.gasUrl, state.trades, dispatch])

  /** Fetch full candle history for all tickers + SPY benchmark. Powers the equity curve. */
  const fetchFullHistory = useCallback(async () => {
    if (!state.gasUrl) {
      dispatch({ type: 'SET_LOADING', loading: false, status: 'Set your GAS proxy URL in Settings first.' })
      return
    }

    // Find the earliest entry date across all trades
    const allTickers = [...new Set(state.trades.map(t => t.ticker))]
    const earliestDate = state.trades.reduce(
      (min, t) => (t.entryDate < min ? t.entryDate : min),
      todayStr()
    )
    const today = todayStr()

    dispatch({ type: 'SET_LOADING', loading: true, status: `Loading history for ${allTickers.length} tickers...` })

    try {
      // Batch fetch all tickers + SPY in one GAS call
      const tickersWithBenchmark = [...new Set([...allTickers, 'SPY'])]
      const batchData = await fetchBatchHistory(tickersWithBenchmark, earliestDate, today, state.gasUrl)

      const newPrices = {}
      Object.entries(batchData).forEach(([ticker, candles]) => {
        if (!Array.isArray(candles)) return
        candles.forEach(c => {
          newPrices[`${ticker}:${c.date}`] = c.close
        })
      })

      // REPLACE (not merge): a full-range refetch is self-consistent, so this
      // purges any stale pre-split bars left over from earlier fetches — the
      // mixed-scale cache that caused the SOXS/TZA split phantom.
      dispatch({ type: 'REPLACE_DAILY_PRICES', prices: newPrices })

      // Store SPY as benchmark history
      if (batchData.SPY && Array.isArray(batchData.SPY)) {
        dispatch({ type: 'SET_BENCHMARK', ticker: 'SPY', history: batchData.SPY })
      }

      const priceCount = Object.keys(newPrices).length
      dispatch({ type: 'SET_LOADING', loading: false, status: `Loaded ${priceCount} price points for ${tickersWithBenchmark.length} tickers.` })
    } catch (e) {
      dispatch({ type: 'SET_LOADING', loading: false, status: `History fetch failed: ${e.message}` })
    }
  }, [state.gasUrl, state.trades, dispatch])

  /** Ensure prices exist for weight-based position sizing */
  const getPriceForSizing = useCallback(async (tickers, date) => {
    // Check which tickers are missing from cache
    const missing = tickers.filter(tk => {
      for (let d = 0; d < 5; d++) {
        const checkDate = new Date(date)
        checkDate.setDate(checkDate.getDate() - d)
        if (state.dailyPrices[`${tk}:${checkDate.toISOString().split('T')[0]}`]) return false
      }
      return true
    })

    if (missing.length === 0) return // All cached

    if (!state.gasUrl) return

    dispatch({ type: 'SET_LOADING', loading: true, status: `Fetching prices for sizing...` })

    try {
      // Fetch a 7-day window around the target date
      const fromDate = new Date(date)
      fromDate.setDate(fromDate.getDate() - 7)
      const fromStr = fromDate.toISOString().split('T')[0]

      const batchData = await fetchBatchHistory(missing, fromStr, date, state.gasUrl)
      const newPrices = {}
      Object.entries(batchData).forEach(([ticker, candles]) => {
        if (!Array.isArray(candles)) return
        candles.forEach(c => { newPrices[`${ticker}:${c.date}`] = c.close })
      })

      dispatch({ type: 'SET_DAILY_PRICES', prices: newPrices })
      dispatch({ type: 'SET_LOADING', loading: false, status: '' })
    } catch (e) {
      dispatch({ type: 'SET_LOADING', loading: false, status: `Sizing fetch failed: ${e.message}` })
    }
  }, [state.gasUrl, state.dailyPrices, dispatch])

  return { refreshOpenPositions, fetchFullHistory, getPriceForSizing }
}
