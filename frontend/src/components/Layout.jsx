import { useHash } from '../hooks/useHash'
import Header from './Header'
import TickerStrip from './dashboard/TickerStrip'
import MarketPosture from './dashboard/MarketPosture'
import PreMarketChecklist from './dashboard/PreMarketChecklist'
import MacroGrid from './dashboard/MacroGrid'
import EquitiesSection from './equities/EquitiesSection'
import ScreenerPage from './screener/ScreenerPage'
import PortfolioPage from './portfolio/PortfolioPage'
import JournalPage from './journal/JournalPage'
import BriefingPage from './briefing/BriefingPage'
import BreadthPage from './breadth/BreadthPage'
import ModelBooksPage from './modelbooks/ModelBooksPage'
import PublicLayout from './public/PublicLayout'
import LandingPage from './public/LandingPage'
import MethodPage from './public/MethodPage'
import ResultsPage from './public/ResultsPage'
import PricingPage from './public/PricingPage'
import BriefPreviewPage from './public/BriefPreviewPage'
import TickerPage from './ticker/TickerPage'
import { parseTickerHash } from './portfolio/lib/tickerUrl'
import Footer from './Footer'

const PUBLIC_PAGES = ['', 'method', 'results', 'pricing', 'brief']

function pageKey(hash) {
  const key = hash.replace('#/', '') || ''
  return key
}

export default function Layout({ data, lastUpdated, isOffline }) {
  const [page, navigate] = useHash()
  const current = pageKey(page)
  const tickerSymbol = parseTickerHash(page)

  // Public pages use PublicLayout
  if (PUBLIC_PAGES.includes(current)) {
    return (
      <PublicLayout currentPage={current} onNavigate={navigate}>
        {current === '' && <LandingPage onNavigate={navigate} />}
        {current === 'method' && <MethodPage onNavigate={navigate} />}
        {current === 'results' && <ResultsPage />}
        {current === 'pricing' && <PricingPage />}
        {current === 'brief' && <BriefPreviewPage onNavigate={navigate} />}
      </PublicLayout>
    )
  }

  // Dashboard pages use existing layout
  return (
    <div className="min-h-screen bg-[var(--color-bg)]">
      <Header
        lastUpdated={lastUpdated}
        isOffline={isOffline}
        currentPage={current}
        onNavigate={navigate}
      />

      {current === 'dashboard' ? (
        <main className="max-w-[1800px] mx-auto px-3 py-4 space-y-4">
          {/* Hero: Ticker Strip */}
          <TickerStrip signals={data?.signals} etfData={data?.etf_data} />

          {/* Decision Panel: Market Posture + Pre-Market Checklist */}
          <div className="grid grid-cols-1 sm:grid-cols-[auto_1fr] gap-3">
            <MarketPosture signals={data?.signals} />
            <PreMarketChecklist />
          </div>

          {/* Macro: Trend Status + Power Trend */}
          <MacroGrid signals={data?.signals} />

          {/* ETF Performance */}
          <EquitiesSection data={data} />
        </main>
      ) : tickerSymbol ? (
        <TickerPage symbol={tickerSymbol} />
      ) : (
        <main className="max-w-[1800px] mx-auto px-3 py-4">
          {current === 'screener' && <ScreenerPage />}
          {current === 'portfolio' && <PortfolioPage />}
          {current === 'journal' && <JournalPage />}
          {current === 'briefing' && <BriefingPage />}
          {current === 'breadth' && <BreadthPage data={data} />}
          {current === 'modelbooks' && <ModelBooksPage />}
        </main>
      )}

      <Footer lastUpdated={lastUpdated} isOffline={isOffline} />
    </div>
  )
}
