import { useState, useRef, useMemo, useEffect, useCallback } from 'react'
import { usePortfolio } from './context/PortfolioContext'
import { computePortfolioHeat } from './lib/diagnostics'
import { computeCashUsed, enrichTrades, computeMonthlyStats, computeYtdStats, computeRiskMetrics, computeSectorData, computeHoldingsData, computeMergedHoldingsData } from './lib/calculations'
import { buildEquityCurve } from './lib/equityCurve'
import { computeReturnOnDeployed } from './lib/capitalEfficiency'
import { adjustTradesForSplits } from './lib/splits'
import { suggestSplits, buildFrozenSnapshot } from './lib/snapshot'
import { SPLIT_TABLE } from './lib/splitTable'
import { parseCSV, generateCSV, downloadFile } from './lib/csv'
import { TABS, todayStr } from './lib/portfolioFormat'
import { useLanguage } from '../../i18n/LanguageContext'
import PortfolioHeader from './PortfolioHeader'
import TradeForm from './TradeForm'
import TrimModal from './TrimModal'
import SettingsPanel from './SettingsPanel'
import OverviewTab from './tabs/OverviewTab'
import ExposureTab from './tabs/ExposureTab'
// OptionsTab is off the tab bar (Andy, 2026-08-17: "可以暂时下线"). The file
// and its route back are intact — this is an unwiring, not a deletion.
// import OptionsTab from './tabs/OptionsTab'
import InputField from './ui/InputField'
import Button from './ui/Button'
import PageHeader from '../PageHeader'

// Two tabs. "Risk" held Sharpe/Sortino/max-drawdown — statistics about a long
// past, which is Review's question, not this page's; they moved there. What
// came back is the beta-weighted exposure of the OPEN book, and that is the
// same subject as Exposure seen from a second angle, so they are one tab.
const TAB_KEYS = ['pf.tab.overview', 'pf.tab.exposure']

export default function Layout() {
  const { state, dispatch } = usePortfolio()
  // Options Port came off the bar, so a reader parked on its index has a
  // persisted activeTab that no longer resolves. Clamped at read time rather
  // than dispatched during render (a side effect in render) or migrated in
  // storage — the tab may come back, and a migration would forget where they
  // were.
  const tabIx = Math.min(state.activeTab ?? 0, TAB_KEYS.length - 1)
  const { t: tr } = useLanguage()
  const [showForm, setShowForm] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [showResetConfirm, setShowResetConfirm] = useState(false)
  const [trimModal, setTrimModal] = useState(null)
  const [exportData, setExportData] = useState(null)
  const [showSplitNotices, setShowSplitNotices] = useState(false)
  const [capitalInput, setCapitalInput] = useState(String(state.startingCapital))
  const fileInputRef = useRef(null)

  // Escape key to close modals
  const handleEscape = useCallback((e) => {
    if (e.key === 'Escape') {
      if (exportData) setExportData(null)
      else if (showResetConfirm) setShowResetConfirm(false)
    }
  }, [exportData, showResetConfirm])

  useEffect(() => {
    if (showResetConfirm || exportData) {
      document.addEventListener('keydown', handleEscape)
      return () => document.removeEventListener('keydown', handleEscape)
    }
  }, [showResetConfirm, exportData, handleEscape])

  // Auto-dismiss status bar
  useEffect(() => {
    if (!state.fetchStatus) return
    const t = setTimeout(() => dispatch({ type: 'SET_FETCH_STATUS', status: '' }), 8000)
    return () => clearTimeout(t)
  }, [state.fetchStatus, dispatch])

  // Correct for retroactive stock splits before any valuation. The price feed is
  // split-adjusted across its whole history, so a position held/closed before a
  // later split (e.g. SNXX's 8:1 on 2026-06-03) would otherwise be valued as
  // qty(as-traded) × close(adjusted). adjustTradesForSplits auto-detects the
  // per-trade scale mismatch and rescales qty/prices onto the feed's scale.
  const { trades: adjTrades, detected: detectedSplits } = useMemo(
    () => adjustTradesForSplits(state.trades, state.dailyPrices),
    [state.trades, state.dailyPrices]
  )

  // Core calculations
  const cashUsed = useMemo(() => computeCashUsed(adjTrades), [adjTrades])
  const cashAvailable = state.startingCapital - cashUsed

  const openMarketValue = useMemo(() =>
    adjTrades.filter(t => !t.isClosed).reduce((s, t) => {
      const dir = t.direction === 'long' ? 1 : -1
      // Look up current price
      const today = todayStr()
      let price = t.entryPrice
      for (let d = 0; d < 5; d++) {
        const checkDate = new Date(today)
        checkDate.setDate(checkDate.getDate() - d)
        const key = `${t.ticker}:${checkDate.toISOString().split('T')[0]}`
        if (state.dailyPrices[key] != null) { price = state.dailyPrices[key]; break }
      }
      return s + t.currentQty * price * dir
    }, 0),
    [adjTrades, state.dailyPrices]
  )

  const totalPortfolioValue = cashAvailable + openMarketValue
  const totalPL = totalPortfolioValue - state.startingCapital
  const totalReturnPct = state.startingCapital > 0 ? (totalPL / state.startingCapital) * 100 : 0

  const enrichedTrades = useMemo(
    () => enrichTrades(adjTrades, totalPortfolioValue, state.dailyPrices),
    [adjTrades, totalPortfolioValue, state.dailyPrices]
  )
  const openTrades = useMemo(() => enrichedTrades.filter(t => !t.isClosed), [enrichedTrades])

  // Curve values RAW trades (never mutated) — buildEquityCurve applies a robust
  // fill-anchored split correction internally, so it needs the as-traded fills.
  // (adjTrades still drives the split banner + live header valuation above.)
  const performanceData = useMemo(
    () => buildEquityCurve(state.trades, state.startingCapital, state.dailyPrices, state.benchmarkHistories),
    [state.trades, state.startingCapital, state.dailyPrices, state.benchmarkHistories]
  )

  const capitalEfficiency = useMemo(
    () => computeReturnOnDeployed(state.trades, state.startingCapital),
    [state.trades, state.startingCapital]
  )

  const monthlyStats = useMemo(
    () => computeMonthlyStats(enrichedTrades, performanceData),
    [enrichedTrades, performanceData]
  )
  const ytdStats = useMemo(
    () => computeYtdStats(enrichedTrades, totalReturnPct),
    [enrichedTrades, totalReturnPct]
  )
  // Arrived with the beta-weighted exposure section from Review, which reads
  // both. Computed here rather than inside ExposureTab so the tab stays a view.
  const heatData = useMemo(
    () => computePortfolioHeat(openTrades, state.dailyPrices, totalPortfolioValue),
    [openTrades, state.dailyPrices, totalPortfolioValue]
  )

  const sectorData = useMemo(() => computeSectorData(openTrades), [openTrades])
  const holdingsData = useMemo(() => computeHoldingsData(openTrades), [openTrades])
  const mergedHoldingsData = useMemo(() => computeMergedHoldingsData(openTrades), [openTrades])

  const cashPct = totalPortfolioValue > 0 ? (cashAvailable / totalPortfolioValue) * 100 : 0

  // Split-truth tooling (see lib/splitTable.js + lib/snapshot.js):
  //  • Suggest split-table entries — auto-detects splits INCLUDING repeated /
  //    composite leveraged-ETF splits (the SOXS case that mis-valued history).
  //  • Freeze snapshot — un-adjusts the live feed onto the as-traded scale and
  //    downloads it as immutable truth so history is immune to FUTURE splits.
  const handleSuggestSplits = useCallback(() => {
    const { suggestions, straddles } = suggestSplits(state.trades, state.dailyPrices)
    const payload = {
      generatedAt: new Date().toISOString(),
      note: 'Confirm exDate for each entry, then paste into lib/splitTable.js → SPLIT_TABLE.',
      suggestions,
      straddles,
    }
    downloadFile(JSON.stringify(payload, null, 2),
      `split_table_suggestions_${new Date().toISOString().slice(0, 10)}.json`, 'application/json')
  }, [state.trades, state.dailyPrices])

  const handleFreezeSnapshot = useCallback(() => {
    const { prices, meta } = buildFrozenSnapshot(state.trades, state.dailyPrices, SPLIT_TABLE)
    downloadFile(JSON.stringify({ meta, prices }, null, 2),
      `frozen_prices_${new Date().toISOString().slice(0, 10)}.json`, 'application/json')
  }, [state.trades, state.dailyPrices])

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
          <div className="text-[26px] font-bold mb-2">{tr('pf.title')}</div>
          <div className="text-[var(--color-text-muted)] mb-6 text-[14px]">{tr('pf.intro.subtitle')}</div>
          <InputField
            label={tr('pf.intro.capitalLabel')}
            type="number"
            value={capitalInput}
            onChange={e => setCapitalInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter') {
                const v = parseFloat(capitalInput)
                if (v > 0) dispatch({ type: 'SET_CAPITAL', capital: v })
              }
            }}
            className="text-[17px] text-center w-[220px] mx-auto"
          />
          <div className="mt-4 flex gap-2 justify-center">
            <Button onClick={() => {
              const v = parseFloat(capitalInput)
              if (v > 0) dispatch({ type: 'SET_CAPITAL', capital: v })
            }}>
              {tr('pf.intro.startTracking')}
            </Button>
            <Button variant="ghost" onClick={() => fileInputRef.current?.click()}>
              {tr('pf.intro.uploadCsv')}
            </Button>
            <Button variant="ghost" onClick={handleLoadSample}>
              {tr('pf.intro.trySample')}
            </Button>
          </div>
          {state.fetchStatus && (
            <div className="mt-3 text-[12.5px] text-[var(--color-accent)]">{state.fetchStatus}</div>
          )}
        </div>
      </div>
    )
  }

  // Main app
  return (
    <div>
      {fileInput}

      {/* The page frame goes above the working header, not instead of it —
          PortfolioHeader carries the account switcher, the privacy mask and
          the sync state, all of which have to keep working. */}
      <PageHeader group="book" title="Portfolio" />

      <PortfolioHeader
        portfolioValue={totalPortfolioValue}
        totalPL={totalPL}
        totalReturnPct={totalReturnPct}
        cashAvailable={cashAvailable}
        cashPct={cashPct}
        openCount={new Set(openTrades.map(t => t.ticker)).size}
        onShowForm={() => setShowForm(!showForm)}
        showForm={showForm}
        onExport={handleExport}
        onImport={() => fileInputRef.current?.click()}
        onShowSettings={() => setShowSettings(!showSettings)}
        onReset={() => setShowResetConfirm(true)}
      />

      {/* Status bar — PortfolioHeader end */}
      {state.fetchStatus && (
        <div className="px-6 py-1.5 bg-[var(--color-bg)] text-[12.5px] text-[var(--color-text-secondary)] border-b border-[var(--color-border)]">
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
              <div className="text-[14px] text-[var(--color-text-secondary)] mb-4">This deletes everything. Export first if needed.</div>
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
                <button onClick={() => setExportData(null)} className="text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] cursor-pointer text-[17px]">&times;</button>
              </div>
              <div className="text-[12.5px] text-[var(--color-text-secondary)] mb-2">Copy the CSV below, or save as .csv to open in Excel.</div>
              <div className="flex gap-2 mb-2">
                <Button onClick={() => {
                  navigator.clipboard.writeText(exportData)
                  dispatch({ type: 'SET_FETCH_STATUS', status: 'Copied to clipboard!' })
                }}>Copy</Button>
                <Button variant="ghost" onClick={() => downloadFile(exportData, `portfolio_${new Date().toISOString().split('T')[0]}.csv`, 'text/csv')}>Download Again</Button>
              </div>
              <textarea readOnly value={exportData} className="flex-1 min-h-[300px] p-2.5 rounded-3xl text-[11px] font-mono resize-y whitespace-pre overflow-auto" />
            </div>
          </div>
        )}

        {/* Trim modal */}
        {trimModal && <TrimModal trade={trimModal} onClose={() => setTrimModal(null)} />}

        {/* Tabs */}
        {/* The one tab row on the site that was its own shape: 14px semibold
            with an underline, where every other page uses an 11px pill. Same
            job, so it wears the same clothes now. */}
        <div className="flex gap-1 flex-wrap mt-4 mb-5">
          {TABS.map((tab, i) => (
            <button
              key={tab}
              onClick={() => dispatch({ type: 'SET_ACTIVE_TAB', tab: i })}
              className={`px-3 py-1.5 text-[11px] font-medium rounded cursor-pointer border-none transition-colors ${
                tabIx === i
                  ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)]'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] bg-[var(--color-surface-raised)]'
              }`}
            >
              {tr(TAB_KEYS[i])}
            </button>
          ))}
        </div>

        {/* Tab content */}
        {/* Options Port came off the bar, so a reader parked on its index has a
            persisted activeTab that no longer resolves. Clamped at read time
            rather than dispatched during render (a side effect in render) or
            migrated in storage (the tab may come back, and a migration would
            forget where they were). */}
        {tabIx === 0 && <OverviewTab performanceData={performanceData} totalReturnPct={totalReturnPct} monthlyStats={monthlyStats} ytdStats={ytdStats} enrichedTrades={enrichedTrades} onTrim={setTrimModal} />}
        {tabIx === 1 && <ExposureTab openTrades={openTrades} enriched={enrichedTrades} sectorData={sectorData} holdingsData={holdingsData} mergedHoldingsData={mergedHoldingsData} performanceData={performanceData} capitalEfficiency={capitalEfficiency} dailyPrices={state.dailyPrices} spyHistory={state.benchmarkHistories?.SPY || []} portfolioValue={totalPortfolioValue} heatData={heatData} />}

        {/* Split-adjustment notices — collapsed by default at the bottom of the
            Overview to keep the visual noise down. */}
        {tabIx === 0 && detectedSplits.length > 0 && (() => {
          const uniq = [...new Map(detectedSplits.map(s => [
            s.straddle ? `straddle:${s.ticker}` : `${s.ticker}:${s.ratioLabel}`, s,
          ])).values()]
          const straddles = uniq.filter(s => s.straddle).length
          const adjusts = uniq.length - straddles
          return (
            <div className="mt-4 text-[12.5px] text-[var(--color-text-muted)]">
              <button
                onClick={() => setShowSplitNotices(v => !v)}
                className="inline-flex items-center gap-1.5 hover:text-[var(--color-text-secondary)]"
              >
                <span>{showSplitNotices ? '▾' : '▸'}</span>
                <span>Split adjustments · {adjusts} auto-applied{straddles ? ` · ⚠ ${straddles} to verify` : ''}</span>
              </button>
              {showSplitNotices && (
                <div className="mt-2 px-3 py-2 bg-[var(--color-surface-raised)] rounded-3xl leading-6">
                  {uniq.map((s, i) => (
                    <span key={i} className="mr-3">
                      {s.straddle
                        ? `⚠ ${s.ticker}: split straddles a trade — verify manually`
                        : `↔ ${s.ticker} ${s.ratioLabel} split auto-adjusted`}
                    </span>
                  ))}
                  <div className="mt-2">
                    <button onClick={handleSuggestSplits} className="text-[var(--color-accent)] hover:underline mr-3">⤓ split-table suggestions</button>
                    <button onClick={handleFreezeSnapshot} className="text-[var(--color-accent)] hover:underline">📌 freeze snapshot</button>
                  </div>
                </div>
              )}
            </div>
          )
        })()}
      </div>
    </div>
  )
}
