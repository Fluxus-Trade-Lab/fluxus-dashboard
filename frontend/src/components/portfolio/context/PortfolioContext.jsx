import { createContext, useContext, useReducer, useEffect, useRef } from 'react'
import { pullFromSheets, pushToSheets } from '../services/sheetsSync'

const STORAGE_KEY = 'portfolio-v4'

const initialState = {
  startingCapital: 100000,
  trades: [],
  dailyPrices: {},
  benchmarkHistories: {},
  gasUrl: '',
  benchmarkTicker: 'SPY',
  capitalSet: false,
  activeTab: 0,
  showClosed: false,
  privacyMode: false,
  loading: false,
  fetchStatus: '',
  optionsCapital: 25000,
  optionsTrades: [],
  optionsCapitalSet: false,
  syncToken: '',
  syncStatus: 'idle',
  lastSyncTime: null,
  monthlyReviews: {},
}

function loadFromStorage() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (!stored) return initialState
    const parsed = JSON.parse(stored)
    return {
      ...initialState,
      startingCapital: parsed.startingCapital ?? initialState.startingCapital,
      trades: parsed.trades ?? [],
      dailyPrices: parsed.dailyPrices ?? {},
      benchmarkHistories: parsed.benchmarkHistories ?? {},
      gasUrl: parsed.gasUrl ?? '',
      benchmarkTicker: parsed.benchmarkTicker ?? 'SPY',
      capitalSet: !!(parsed.startingCapital && parsed.trades?.length > 0),
      privacyMode: parsed.privacyMode ?? false,
      loading: false,
      fetchStatus: '',
      optionsCapital: parsed.optionsCapital ?? 25000,
      optionsTrades: (parsed.optionsTrades ?? []).map(t =>
        t.id?.startsWith('s') && t.entryDate?.startsWith('2025-')
          ? { ...t, entryDate: t.entryDate.replace('2025-', '2026-'), exitDate: t.exitDate?.replace('2025-', '2026-') }
          : t
      ),
      optionsCapitalSet: parsed.optionsCapitalSet ?? false,
      syncToken: parsed.syncToken ?? '',
      monthlyReviews: parsed.monthlyReviews ?? {},
    }
  } catch {
    return initialState
  }
}

function reducer(state, action) {
  switch (action.type) {
    case 'SET_CAPITAL':
      return { ...state, startingCapital: action.capital, capitalSet: true }

    case 'IMPORT_DATA': {
      const next = {
        ...state,
        trades: action.trades ?? state.trades,
        capitalSet: true,
      }
      if (action.capital != null) next.startingCapital = action.capital
      if (action.dailyPrices) {
        next.dailyPrices = { ...state.dailyPrices, ...action.dailyPrices }
      }
      return next
    }

    case 'ADD_TRADE':
      return { ...state, trades: [...state.trades, action.trade] }

    case 'UPDATE_TRADE':
      return {
        ...state,
        trades: state.trades.map(t =>
          t.id === action.id ? { ...t, ...action.updates } : t
        ),
      }

    case 'TRIM_TRADE':
      return {
        ...state,
        trades: state.trades.map(t => {
          if (t.id !== action.id) return t
          const { trimType, trimPrice, trimDate } = action
          let tq
          if (trimType === 'trim_1_3') tq = Math.floor(t.originalQty / 3)
          else if (trimType === 'trim_1_2') tq = Math.floor(t.originalQty / 2)
          else if (trimType === 'trim_1_5') tq = Math.floor(t.originalQty / 5)
          else tq = t.currentQty
          tq = Math.min(tq, t.currentQty)
          if (tq <= 0) return t
          const nq = t.currentQty - tq
          return {
            ...t,
            currentQty: nq,
            trims: [...(t.trims || []), { date: trimDate, price: trimPrice, qty: tq, type: trimType }],
            isClosed: nq <= 0,
          }
        }),
      }

    case 'DELETE_TRADE':
      return { ...state, trades: state.trades.filter(t => t.id !== action.id) }

    case 'SET_DAILY_PRICES':
      return { ...state, dailyPrices: { ...state.dailyPrices, ...action.prices } }

    case 'SET_BENCHMARK':
      return {
        ...state,
        benchmarkHistories: {
          ...state.benchmarkHistories,
          [action.ticker]: action.history,
        },
      }

    case 'SET_GAS_URL':
      return { ...state, gasUrl: action.url }

    case 'SET_SYNC_TOKEN':
      return { ...state, syncToken: action.token }

    case 'SET_SYNC_STATUS':
      return {
        ...state,
        syncStatus: action.status,
        lastSyncTime: action.status === 'success' ? new Date().toISOString() : state.lastSyncTime,
      }

    case 'HYDRATE_FROM_SHEETS': {
      let reviews = state.monthlyReviews
      if (action.meta?.monthlyReviews) {
        try { reviews = JSON.parse(action.meta.monthlyReviews) } catch {}
      }
      return {
        ...state,
        trades: action.stockTrades ?? state.trades,
        optionsTrades: action.optionsTrades ?? state.optionsTrades,
        startingCapital: action.meta?.startingCapital ?? state.startingCapital,
        optionsCapital: action.meta?.optionsCapital ?? state.optionsCapital,
        benchmarkTicker: action.meta?.benchmarkTicker ?? state.benchmarkTicker,
        monthlyReviews: reviews,
        capitalSet: true,
        optionsCapitalSet: !!(action.meta?.optionsCapital),
        syncStatus: 'success',
        lastSyncTime: new Date().toISOString(),
      }
    }

    case 'SET_ACTIVE_TAB':
      return { ...state, activeTab: action.tab }

    case 'SET_LOADING':
      return {
        ...state,
        loading: action.loading,
        fetchStatus: action.status ?? state.fetchStatus,
      }

    case 'SET_FETCH_STATUS':
      return { ...state, fetchStatus: action.status }

    case 'TOGGLE_SHOW_CLOSED':
      return { ...state, showClosed: !state.showClosed }

    case 'TOGGLE_PRIVACY':
      return { ...state, privacyMode: !state.privacyMode }

    case 'SET_OPTIONS_CAPITAL':
      return { ...state, optionsCapital: action.capital, optionsCapitalSet: true }

    case 'ADD_OPTIONS_TRADE':
      return { ...state, optionsTrades: [...state.optionsTrades, action.trade] }

    case 'CLOSE_OPTIONS_TRADE':
      return {
        ...state,
        optionsTrades: state.optionsTrades.map(t =>
          t.id === action.id ? { ...t, exitDate: action.exitDate, exitPrice: action.exitPrice } : t
        ),
      }

    case 'UPDATE_OPTIONS_TRADE':
      return {
        ...state,
        optionsTrades: state.optionsTrades.map(t =>
          t.id === action.id ? { ...t, ...action.updates } : t
        ),
      }

    case 'DELETE_OPTIONS_TRADE':
      return { ...state, optionsTrades: state.optionsTrades.filter(t => t.id !== action.id) }

    case 'IMPORT_OPTIONS_DATA':
      return { ...state, optionsTrades: action.trades, optionsCapital: action.capital ?? state.optionsCapital, optionsCapitalSet: true }

    case 'SET_MONTHLY_REVIEWS':
      return { ...state, monthlyReviews: action.reviews }

    case 'RESET_ALL':
      localStorage.removeItem(STORAGE_KEY)
      return { ...initialState }

    default:
      return state
  }
}

export const PortfolioContext = createContext(null)

export function usePortfolio() {
  const ctx = useContext(PortfolioContext)
  if (!ctx) throw new Error('usePortfolio must be used within PortfolioProvider')
  return ctx
}

export function PortfolioProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, null, loadFromStorage)
  const isHydrating = useRef(true)

  // Pull from Sheets on init
  useEffect(() => {
    if (!state.gasUrl || !state.syncToken) return
    let cancelled = false
    isHydrating.current = true
    dispatch({ type: 'SET_SYNC_STATUS', status: 'syncing' })
    pullFromSheets(state.gasUrl, state.syncToken).then(result => {
      if (cancelled) return
      if (result.ok) {
        dispatch({ type: 'HYDRATE_FROM_SHEETS', ...result })
      } else {
        console.warn('Sheets pull failed, using localStorage:', result.error)
        dispatch({ type: 'SET_SYNC_STATUS', status: 'error' })
      }
      // Allow push effects to fire after hydration settles
      setTimeout(() => { isHydrating.current = false }, 3000)
    })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Persist to localStorage (debounced)
  useEffect(() => {
    if (!state.capitalSet && state.trades.length === 0 && state.optionsTrades.length === 0) return
    const t = setTimeout(() => {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          startingCapital: state.startingCapital,
          trades: state.trades,
          dailyPrices: state.dailyPrices,
          benchmarkHistories: state.benchmarkHistories,
          gasUrl: state.gasUrl,
          benchmarkTicker: state.benchmarkTicker,
          privacyMode: state.privacyMode,
          optionsCapital: state.optionsCapital,
          optionsTrades: state.optionsTrades,
          optionsCapitalSet: state.optionsCapitalSet,
          syncToken: state.syncToken,
          monthlyReviews: state.monthlyReviews,
        })
      )
    }, 500)
    return () => clearTimeout(t)
  }, [state.startingCapital, state.trades, state.dailyPrices, state.benchmarkHistories, state.gasUrl, state.benchmarkTicker, state.capitalSet, state.optionsCapital, state.optionsTrades, state.optionsCapitalSet, state.monthlyReviews, state.privacyMode])

  // Auto-push to Sheets (debounced 2s, skip during hydration)
  useEffect(() => {
    if (!state.gasUrl || !state.syncToken) return
    if (!state.capitalSet && state.trades.length === 0) return
    if (isHydrating.current) return
    const t = setTimeout(() => {
      dispatch({ type: 'SET_SYNC_STATUS', status: 'syncing' })
      pushToSheets(state.gasUrl, state.syncToken, {
        stockTrades: state.trades,
        optionsTrades: state.optionsTrades,
        meta: {
          startingCapital: state.startingCapital,
          optionsCapital: state.optionsCapital,
          benchmarkTicker: state.benchmarkTicker,
          monthlyReviews: JSON.stringify(state.monthlyReviews),
        },
      }).then(result => {
        dispatch({ type: 'SET_SYNC_STATUS', status: result.ok ? 'success' : 'error' })
      })
    }, 2000)
    return () => clearTimeout(t)
  }, [state.trades, state.optionsTrades, state.startingCapital, state.optionsCapital, state.benchmarkTicker, state.gasUrl, state.syncToken, state.capitalSet, dispatch])

  return (
    <PortfolioContext.Provider value={{ state, dispatch }}>
      {children}
    </PortfolioContext.Provider>
  )
}
