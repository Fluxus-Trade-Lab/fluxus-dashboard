import { useState, useRef, useMemo, useEffect } from 'react'
import { usePortfolio } from './context/PortfolioContext'
import { computeCashUsed, enrichTrades, computeMonthlyStats, computeYtdStats, computeRiskMetrics, computeSectorData, computeHoldingsData, computeMergedHoldingsData } from './lib/calculations'
import { buildEquityCurve } from './lib/equityCurve'
import { parseCSV, generateCSV, downloadFile } from './lib/csv'
import { fmtCur, TABS } from './lib/portfolioFormat'
import { computeThreeStopSim } from './lib/threeStopSim'
import PortfolioHeader from './PortfolioHeader'
import TradeForm from './TradeForm'
import TrimModal from './TrimModal'
import SettingsPanel from './SettingsPanel'
import PLTab from './tabs/PLTab'
import ExposureTab from './tabs/ExposureTab'
import PerformanceTab from './tabs/PerformanceTab'
import MonthlyTab from './tabs/MonthlyTab'
import RiskTab from './tabs/RiskTab'
import ThreeStopTab from './tabs/ThreeStopTab'
import OptionsTab from './tabs/OptionsTab'
import InputField from './ui/InputField'
import Button from './ui/Button'

export default function Layout() {
  const { state, dispatch } = usePortfolio()
  const [showForm, setShowForm] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [showResetConfirm, setShowResetConfirm] = useState(false)
  const [trimModal, setTrimModal] = useState(null)
  const [exportData, setExportData] = useState(null)
  const [capitalInput, setCapitalInput] = useState(String(state.startingCapital))
  const fileInputRef = useRef(null)

  // Auto-dismiss status bar
  useEffect(() => {
    if (!state.fetchStatus) return
    const t = setTimeout(() => dispatch({ type: 'SET_FETCH_STATUS', status: '' }), 8000)
    return () => clearTimeout(t)
  }, [state.fetchStatus, dispatch])

  // Core calculations
  const cashUsed = useMemo(() => computeCashUsed(state.trades), [state.trades])
  const cashAvailable = state.startingCapital - cashUsed

  const openMarketValue = useMemo(() =>
    state.trades.filter(t => !t.isClosed).reduce((s, t) => {
      const dir = t.direction === 'long' ? 1 : -1
      // Look up current price
      const today = new Date().toISOString().split('T')[0]
      let price = t.entryPrice
      for (let d = 0; d < 5; d++) {
        const checkDate = new Date(today)
        checkDate.setDate(checkDate.getDate() - d)
        const key = `${t.ticker}:${checkDate.toISOString().split('T')[0]}`
        if (state.dailyPrices[key] != null) { price = state.dailyPrices[key]; break }
      }
      return s + t.currentQty * price * dir
    }, 0),
    [state.trades, state.dailyPrices]
  )

  const totalPortfolioValue = cashAvailable + openMarketValue
  const totalPL = totalPortfolioValue - state.startingCapital
  const totalReturnPct = state.startingCapital > 0 ? (totalPL / state.startingCapital) * 100 : 0

  const enrichedTrades = useMemo(
    () => enrichTrades(state.trades, totalPortfolioValue, state.dailyPrices),
    [state.trades, totalPortfolioValue, state.dailyPrices]
  )
  const openTrades = useMemo(() => enrichedTrades.filter(t => !t.isClosed), [enrichedTrades])

  const performanceData = useMemo(
    () => buildEquityCurve(state.trades, state.startingCapital, state.dailyPrices, state.benchmarkHistories),
    [state.trades, state.startingCapital, state.dailyPrices, state.benchmarkHistories]
  )

  const monthlyStats = useMemo(
    () => computeMonthlyStats(enrichedTrades, performanceData),
    [enrichedTrades, performanceData]
  )
  const ytdStats = useMemo(
    () => computeYtdStats(enrichedTrades, totalReturnPct),
    [enrichedTrades, totalReturnPct]
  )
  const riskMetrics = useMemo(
    () => computeRiskMetrics(performanceData, state.benchmarkTicker),
    [performanceData, state.benchmarkTicker]
  )
  const sectorData = useMemo(() => computeSectorData(openTrades), [openTrades])
  const holdingsData = useMemo(() => computeHoldingsData(openTrades), [openTrades])
  const mergedHoldingsData = useMemo(() => computeMergedHoldingsData(openTrades), [openTrades])

  const threeStopSimData = useMemo(
    () => computeThreeStopSim(state.trades, state.dailyPrices),
    [state.trades, state.dailyPrices]
  )

  const cashPct = totalPortfolioValue > 0 ? (cashAvailable / totalPortfolioValue) * 100 : 0

  // Import handler
  const handleImport = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => {
      try {
        const text = ev.target.result
        const result = parseCSV(text)
        dispatch({
          type: 'IMPORT_DATA',
          trades: result.trades,
          capital: result.startingCapital,
          dailyPrices: result.dailyPrices,
        })
        dispatch({ type: 'SET_FETCH_STATUS', status: `Imported ${result.trades?.length || 0} trades.` })
      } catch (err) {
        dispatch({ type: 'SET_FETCH_STATUS', status: 'Import failed: ' + err.message })
      }
    }
    reader.readAsText(file)
    e.target.value = ''
  }

  // Export handler
  const handleExport = () => {
    const csv = generateCSV(state.trades, state.startingCapital)
    setExportData(csv)
    downloadFile(csv, `portfolio_${new Date().toISOString().split('T')[0]}.csv`, 'text/csv')
  }

  // Load sample data
  const handleLoadSample = async () => {
    try {
      const res = await fetch(import.meta.env.BASE_URL + 'sample/portfolio_2026-03-14.csv')
      const text = await res.text()
      const result = parseCSV(text)
      dispatch({
        type: 'IMPORT_DATA',
        trades: result.trades,
        capital: result.startingCapital,
        dailyPrices: result.dailyPrices,
      })
      dispatch({ type: 'SET_FETCH_STATUS', status: `Loaded sample: ${result.trades?.length || 0} trades.` })
    } catch (err) {
      dispatch({ type: 'SET_FETCH_STATUS', status: 'Failed to load sample: ' + err.message })
    }
  }

  // Hidden file input
  const fileInput = (
    <input ref={fileInputRef} type="file" accept=".csv" className="hidden" onChange={handleImport} />
  )

  // Setup screen
  if (!state.capitalSet) {
    return (
      <div className="flex items-center justify-center py-20">
        {fileInput}
        <div className="text-center max-w-md">
          <div className="text-3xl font-bold mb-2">Portfolio Tracker</div>
          <div className="text-[var(--color-text-muted)] mb-6 text-sm">Enter starting capital, or upload an existing trade log</div>
          <InputField
            label="Starting Capital ($)"
            type="number"
            value={capitalInput}
            onChange={e => setCapitalInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter') {
                const v = parseFloat(capitalInput)
                if (v > 0) dispatch({ type: 'SET_CAPITAL', capital: v })
              }
            }}
            className="text-lg text-center w-[220px] mx-auto"
          />
          <div className="mt-4 flex gap-2 justify-center">
            <Button onClick={() => {
              const v = parseFloat(capitalInput)
              if (v > 0) dispatch({ type: 'SET_CAPITAL', capital: v })
            }}>
              Start Tracking
            </Button>
            <Button variant="ghost" onClick={() => fileInputRef.current?.click()}>
              Upload CSV
            </Button>
            <Button variant="ghost" onClick={handleLoadSample}>
              Try Sample
            </Button>
          </div>
          {state.fetchStatus && (
            <div className="mt-3 text-xs text-[var(--color-accent)]">{state.fetchStatus}</div>
          )}
        </div>
      </div>
    )
  }

  // Main app
  return (
    <div>
      {fileInput}

      <PortfolioHeader
        portfolioValue={totalPortfolioValue}
        totalPL={totalPL}
        totalReturnPct={totalReturnPct}
        cashAvailable={cashAvailable}
        cashPct={cashPct}
        openCount={openTrades.length}
        onShowForm={() => setShowForm(!showForm)}
        showForm={showForm}
        onExport={handleExport}
        onImport={() => fileInputRef.current?.click()}
        onShowSettings={() => setShowSettings(!showSettings)}
        onReset={() => setShowResetConfirm(true)}
      />

      {/* Status bar — PortfolioHeader end */}
      {state.fetchStatus && (
        <div className="px-6 py-1.5 bg-blue-50 text-xs text-[var(--color-accent)] border-b border-blue-100">
          {state.fetchStatus}
        </div>
      )}

      <div className="px-6 pb-10">
        {showSettings && <SettingsPanel onClose={() => setShowSettings(false)} />}
        {showForm && <TradeForm onClose={() => setShowForm(false)} />}

        {/* Reset confirm modal */}
        {showResetConfirm && (
          <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
            <div className="bg-[var(--color-surface)] rounded-lg p-6 w-80 shadow-xl">
              <div className="font-bold mb-2">Reset All Data?</div>
              <div className="text-sm text-[var(--color-text-secondary)] mb-4">This deletes everything. Export first if needed.</div>
              <div className="flex gap-2">
                <Button variant="danger" onClick={() => { dispatch({ type: 'RESET_ALL' }); setShowResetConfirm(false) }}>Yes, Reset</Button>
                <Button variant="ghost" onClick={() => setShowResetConfirm(false)}>Cancel</Button>
              </div>
            </div>
          </div>
        )}

        {/* Export modal */}
        {exportData && (
          <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
            <div className="bg-[var(--color-surface)] rounded-lg p-6 w-[600px] max-h-[80vh] shadow-xl flex flex-col">
              <div className="font-bold mb-2 flex justify-between">
                <span>Export Data</span>
                <button onClick={() => setExportData(null)} className="text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] cursor-pointer text-lg">&times;</button>
              </div>
              <div className="text-xs text-[var(--color-text-secondary)] mb-2">Copy the CSV below, or save as .csv to open in Excel.</div>
              <div className="flex gap-2 mb-2">
                <Button onClick={() => {
                  navigator.clipboard.writeText(exportData)
                  dispatch({ type: 'SET_FETCH_STATUS', status: 'Copied to clipboard!' })
                }}>Copy</Button>
                <Button variant="ghost" onClick={() => downloadFile(exportData, `portfolio_${new Date().toISOString().split('T')[0]}.csv`, 'text/csv')}>Download Again</Button>
              </div>
              <textarea readOnly value={exportData} className="flex-1 min-h-[300px] p-2.5 border border-[var(--color-border)] rounded text-[11px] font-mono resize-y whitespace-pre overflow-auto" />
            </div>
          </div>
        )}

        {/* Trim modal */}
        {trimModal && <TrimModal trade={trimModal} onClose={() => setTrimModal(null)} />}

        {/* Tabs */}
        <div className="flex gap-0 border-b border-[var(--color-border)] mt-4 mb-5">
          {TABS.map((tab, i) => (
            <button
              key={tab}
              onClick={() => dispatch({ type: 'SET_ACTIVE_TAB', tab: i })}
              className={`px-5 py-2.5 font-semibold text-sm cursor-pointer bg-transparent border-none border-b-2 transition-colors ${
                state.activeTab === i
                  ? 'border-[var(--color-accent)] text-[var(--color-accent)]'
                  : 'border-transparent text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Tab content */}
        {state.activeTab === 0 && <PLTab enrichedTrades={enrichedTrades} onTrim={setTrimModal} />}
        {state.activeTab === 1 && <ExposureTab openTrades={openTrades} sectorData={sectorData} holdingsData={holdingsData} mergedHoldingsData={mergedHoldingsData} />}
        {state.activeTab === 2 && <PerformanceTab performanceData={performanceData} totalReturnPct={totalReturnPct} riskMetrics={riskMetrics} />}
        {state.activeTab === 3 && <MonthlyTab monthlyStats={monthlyStats} ytdStats={ytdStats} totalReturnPct={totalReturnPct} />}
        {state.activeTab === 4 && <RiskTab riskMetrics={riskMetrics} benchmarkTicker={state.benchmarkTicker} />}
        {state.activeTab === 5 && <ThreeStopTab simData={threeStopSimData} />}
        {state.activeTab === 6 && <OptionsTab />}
      </div>
    </div>
  )
}
