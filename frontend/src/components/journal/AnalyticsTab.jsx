import { useState, useMemo } from 'react'
import { usePortfolio, PortfolioProvider } from '../portfolio/context/PortfolioContext'
import { enrichTrades, computeMonthlyStats, computeSectorData, computeRiskMetrics } from '../portfolio/lib/calculations'
import { buildEquityCurve } from '../portfolio/lib/equityCurve'
import { computeTrimAnalysis, computeStopAnalysis, computePortfolioHeat, computeVolContribution, computePortfolioVol, computeSpyVol, computeInsights } from '../portfolio/lib/diagnostics'
import SummarySection from './analytics/SummarySection'
import VolatilitySection from './analytics/VolatilitySection'
import TrimStopsSection from './analytics/TrimStopsSection'
import MonthlyReviewSection from './analytics/MonthlyReviewSection'
import DemonFinderSection from './analytics/DemonFinderSection'
import BehaviorSection from './analytics/BehaviorSection'
import BehaviorDiagnosisSection from './analytics/BehaviorDiagnosisSection'
import RiskAdjustedSection from './analytics/RiskAdjustedSection'
import PositionSizeChart from '../portfolio/PositionSizeChart'

const SUB_TABS = [
  { key: 'summary', label: 'Summary' },
  { key: 'size-vs-r', label: 'Size vs R' },
  { key: 'risk-adjusted', label: 'Risk-adjusted' },
  { key: 'diagnosis', label: 'Diagnosis' },
  { key: 'demon-finder', label: 'Demon Finder' },
  { key: 'behavior', label: 'Behavior' },
  { key: 'risk', label: 'Risk' },
  { key: 'volatility', label: 'Volatility' },
  { key: 'trim-stops', label: 'Trim & Stops' },
  { key: 'monthly-review', label: 'Monthly Review' },
]

export default function AnalyticsTab({ initialSection }) {
  return (
    <PortfolioProvider>
      <AnalyticsTabInner initialSection={initialSection} />
    </PortfolioProvider>
  )
}

function AnalyticsTabInner({ initialSection }) {
  const { state } = usePortfolio()
  // Review addresses one of these sections directly, so the opening tab is the
  // caller's to choose. Its own tab strip still works from there.
  const [activeTab, setActiveTab] = useState(initialSection || 'summary')

  const { trades, dailyPrices, benchmarkHistories, startingCapital } = state
  const spyHistory = benchmarkHistories?.SPY || []

  // Core enriched data
  const performanceData = useMemo(
    () => buildEquityCurve(trades, startingCapital, dailyPrices, benchmarkHistories),
    [trades, startingCapital, dailyPrices, benchmarkHistories]
  )

  // Arrived with RiskAdjustedSection from the Portfolio page, where it was
  // computed off the same equity curve this page already builds.
  const benchmarkTicker = state.benchmarkTicker
  const riskMetrics = useMemo(
    () => computeRiskMetrics(performanceData, benchmarkTicker),
    [performanceData, benchmarkTicker]
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
      {/* Sub-tab switcher — hidden when Review is driving, which addresses one
          section directly and already shows its own. Two tab strips stacked is
          the eighteen-tab problem rebuilt one level down. */}
      <div className={`flex gap-1 flex-wrap mb-5 border-b border-[var(--color-border)] pb-2 ${
        initialSection ? 'hidden' : ''}`}>
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
      {activeTab === 'diagnosis' && (
        <BehaviorDiagnosisSection enriched={enriched} performanceData={performanceData} startingCapital={startingCapital} />
      )}
      {activeTab === 'behavior' && (
        <BehaviorSection enriched={enriched} />
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
      {/* The beta-weighted exposure that used to sit here reads openTrades —
          it was the only section on this page that did. It answers "how much
          am I carrying right now", which is the Portfolio page's question, and
          it moved there. What arrived in its place is the equity curve's
          risk-adjusted statistics, which are about a long past. */}
      {/* The sizing stage's question, and it was already answered here — this
          chart computes the size-to-R correlation. It lived inside Summary,
          which the restructure retired, so it was unreachable until now. */}
      {activeTab === 'size-vs-r' && (
        <PositionSizeChart enrichedTrades={enriched} performanceData={performanceData}
                           startingCapital={startingCapital} />
      )}
      {activeTab === 'risk-adjusted' && (
        <RiskAdjustedSection riskMetrics={riskMetrics} benchmarkTicker={benchmarkTicker} />
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
