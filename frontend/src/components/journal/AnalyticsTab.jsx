import { useState, useMemo } from 'react'
import { usePortfolio, PortfolioProvider } from '../portfolio/context/PortfolioContext'
import { enrichTrades, computeMonthlyStats, computeSectorData } from '../portfolio/lib/calculations'
import { buildEquityCurve } from '../portfolio/lib/equityCurve'
import { computeTrimAnalysis, computeStopAnalysis, computePortfolioHeat, computeVolContribution, computePortfolioVol, computeSpyVol, computeInsights } from '../portfolio/lib/diagnostics'
import SummarySection from './analytics/SummarySection'
import RiskSection from './analytics/RiskSection'
import VolatilitySection from './analytics/VolatilitySection'
import TrimStopsSection from './analytics/TrimStopsSection'
import MonthlyReviewSection from './analytics/MonthlyReviewSection'
import DemonFinderSection from './analytics/DemonFinderSection'

const SUB_TABS = [
  { key: 'summary', label: 'Summary' },
  { key: 'demon-finder', label: 'Demon Finder' },
  { key: 'risk', label: 'Risk' },
  { key: 'volatility', label: 'Volatility' },
  { key: 'trim-stops', label: 'Trim & Stops' },
  { key: 'monthly-review', label: 'Monthly Review' },
]

export default function AnalyticsTab() {
  return (
    <PortfolioProvider>
      <AnalyticsTabInner />
    </PortfolioProvider>
  )
}

function AnalyticsTabInner() {
  const { state } = usePortfolio()
  const [activeTab, setActiveTab] = useState('summary')

  const { trades, dailyPrices, benchmarkHistories, startingCapital } = state
  const spyHistory = benchmarkHistories?.SPY || []

  // Core enriched data
  const performanceData = useMemo(
    () => buildEquityCurve(trades, startingCapital, dailyPrices, benchmarkHistories),
    [trades, startingCapital, dailyPrices, benchmarkHistories]
  )

  const portfolioValue = useMemo(() => {
    if (performanceData.length === 0) return startingCapital
    return performanceData[performanceData.length - 1].value
  }, [performanceData, startingCapital])

  const enriched = useMemo(
    () => enrichTrades(trades, portfolioValue, dailyPrices),
    [trades, portfolioValue, dailyPrices]
  )

  const openTrades = useMemo(() => enriched.filter(t => !t.isClosed), [enriched])
  const closedTrades = useMemo(() => enriched.filter(t => t.isClosed), [enriched])

  const monthlyStats = useMemo(
    () => computeMonthlyStats(enriched, performanceData),
    [enriched, performanceData]
  )

  // Diagnostics computations
  const trimAnalysis = useMemo(
    () => computeTrimAnalysis(closedTrades, dailyPrices),
    [closedTrades, dailyPrices]
  )

  const stopAnalysis = useMemo(
    () => computeStopAnalysis(closedTrades, dailyPrices),
    [closedTrades, dailyPrices]
  )

  const heatData = useMemo(
    () => computePortfolioHeat(openTrades, dailyPrices, portfolioValue),
    [openTrades, dailyPrices, portfolioValue]
  )

  const volContrib = useMemo(
    () => computeVolContribution(openTrades, dailyPrices, spyHistory, portfolioValue),
    [openTrades, dailyPrices, spyHistory, portfolioValue]
  )

  const portfolioVol = useMemo(
    () => computePortfolioVol(performanceData),
    [performanceData]
  )

  const spyVol = useMemo(
    () => computeSpyVol(spyHistory),
    [spyHistory]
  )

  const sectorData = useMemo(() => computeSectorData(openTrades), [openTrades])

  const insights = useMemo(
    () => computeInsights(enriched, monthlyStats, trimAnalysis, stopAnalysis),
    [enriched, monthlyStats, trimAnalysis, stopAnalysis]
  )

  if (!trades.length) {
    return (
      <div className="text-center py-16 text-[var(--color-text-muted)]">
        No portfolio data. Import trades in the Portfolio tab first.
      </div>
    )
  }

  return (
    <div>
      {/* Sub-tab switcher */}
      <div className="flex gap-1 mb-5 border-b border-[var(--color-border)] pb-2">
        {SUB_TABS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`px-3 py-1.5 text-[11px] font-medium rounded-t cursor-pointer transition-colors ${
              activeTab === key
                ? 'text-[var(--color-text)] border-b-2 border-[var(--color-accent)]'
                : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {activeTab === 'demon-finder' && (
        <DemonFinderSection
          enriched={enriched}
          dailyPrices={dailyPrices}
        />
      )}
      {activeTab === 'summary' && (
        <SummarySection
          enriched={enriched}
          closedTrades={closedTrades}
          monthlyStats={monthlyStats}
          performanceData={performanceData}
          insights={insights}
          startingCapital={startingCapital}
        />
      )}
      {activeTab === 'risk' && (
        <RiskSection
          openTrades={openTrades}
          enriched={enriched}
          heatData={heatData}
          sectorData={sectorData}
          dailyPrices={dailyPrices}
          spyHistory={spyHistory}
          portfolioValue={portfolioValue}
        />
      )}
      {activeTab === 'volatility' && (
        <VolatilitySection
          volContrib={volContrib}
          portfolioVol={portfolioVol}
          spyVol={spyVol}
          dailyPrices={dailyPrices}
          spyHistory={spyHistory}
        />
      )}
      {activeTab === 'trim-stops' && (
        <TrimStopsSection
          trimAnalysis={trimAnalysis}
          stopAnalysis={stopAnalysis}
        />
      )}
      {activeTab === 'monthly-review' && (
        <MonthlyReviewSection
          enriched={enriched}
          monthlyStats={monthlyStats}
          performanceData={performanceData}
        />
      )}
    </div>
  )
}
