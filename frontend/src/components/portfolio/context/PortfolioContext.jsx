import { createContext, useContext, useReducer, useEffect } from 'react'

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

    case 'DELETE_OPTIONS_TRADE':
      return { ...state, optionsTrades: state.optionsTrades.filter(t => t.id !== action.id) }

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
        })
      )
    }, 500)
    return () => clearTimeout(t)
  }, [state.startingCapital, state.trades, state.dailyPrices, state.benchmarkHistories, state.gasUrl, state.benchmarkTicker, state.capitalSet, state.optionsCapital, state.optionsTrades, state.optionsCapitalSet])

  return (
    <PortfolioContext.Provider value={{ state, dispatch }}>
      {children}
    </PortfolioContext.Provider>
  )
}
