import { useHash } from '../hooks/useHash'
import Header from './Header'
import Rail from './Rail'
import PageHeader from './PageHeader'

/** A tier marker. The dashboard's problem was rank, not content — seven blocks
 *  at equal weight read as seven equally important things. */
function Band({ label, note }) {
  return (
    <div className="flex items-baseline gap-3 pt-4">
      <span className="text-[9px] font-mono uppercase tracking-[.24em] text-[var(--color-text-muted)]">
        {label}
      </span>
      {note && <span className="text-[11px] text-[var(--color-text-muted)]">{note}</span>}
      <i className="flex-1 h-px bg-[var(--color-border)]" />
    </div>
  )
}
import TickerStrip from './dashboard/TickerStrip'
import MarketPosture from './dashboard/MarketPosture'
import BreadthChip from './breadth/BreadthChip'
import PreMarketChecklist from './dashboard/PreMarketChecklist'
import MacroGrid from './dashboard/MacroGrid'
import HeatingUp from './screener/HeatingUp'
import EquitiesSection from './equities/EquitiesSection'
import ScreenerPage from './screener/ScreenerPage'
import PortfolioPage from './portfolio/PortfolioPage'
import JournalPage from './journal/JournalPage'
import BriefingPage from './briefing/BriefingPage'
import BreadthPage from './breadth/BreadthPage'
import CorrectionRiskPage from './breadth/CorrectionRiskPage'
import GroupsPage from './groups/GroupsPage'
import ModelBooksPage from './modelbooks/ModelBooksPage'
import PublicLayout from './public/PublicLayout'
import LandingPage from './public/LandingPage'
import MethodPage from './public/MethodPage'
import ResultsPage from './public/ResultsPage'
import PricingPage from './public/PricingPage'
import BriefPreviewPage from './public/BriefPreviewPage'
import TickerPage from './ticker/TickerPage'
import TradeJournalPage from './journal/TradeJournalPage'
import TradeDetailPage from './journal/TradeDetailPage'
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
  const tradeIdMatch = (page || '').match(/^#\/trade\/([A-Za-z0-9._\-]+)$/)
  const tradeId = tradeIdMatch ? tradeIdMatch[1] : null

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

  // Dashboard pages: rail on the left, status bar across the content
  return (
    <div className="min-h-screen lg:flex"
         style={{ background: 'var(--ground), var(--color-bg)' }}>
      <Rail currentPage={current} onNavigate={navigate} />
      <div className="flex-1 min-w-0">
      <Header
        lastUpdated={lastUpdated}
        isOffline={isOffline}
        currentPage={current}
        onNavigate={navigate}
      />

      {current === 'dashboard' ? (
        /* Seven blocks at equal weight, so none of them was first. Ordered now:
           the read, then what is stacking, then reference, then the two personal
           objects — which belong to MY BOOK and are only still here because that
           half has not been rebuilt and he uses them at 06:30. */
        <main className="max-w-[1800px] mx-auto px-3 py-4 space-y-4">
          <PageHeader group="market" title="Today"
            blurb="What the market is doing, before you decide what to do about it."
            meta={['the read, then what is stacking, then reference',
                   'sizing is not on this page — it needs an R and a ceiling, and those are yours']} />

          <BreadthChip verdict={data?.breadth?.verdict} onNavigate={navigate} />
          <TickerStrip signals={data?.signals} etfData={data?.etf_data} />

          <Band label="What is stacking" />
          <HeatingUp compact limit={5} />

          <Band label="Reference" note="answers where, never so what" />
          <MacroGrid signals={data?.signals} />
          <EquitiesSection data={data} />

          <Band label="Yours" note="belongs to My Book — parked here until that half is rebuilt" />
          <div className="grid grid-cols-1 sm:grid-cols-[auto_1fr] gap-3">
            <MarketPosture signals={data?.signals} />
            <PreMarketChecklist />
          </div>
        </main>
      ) : tickerSymbol ? (
        <TickerPage symbol={tickerSymbol} />
      ) : tradeId ? (
        <TradeDetailPage tradeId={tradeId} />
      ) : (
        <main className="max-w-[1800px] mx-auto px-3 py-4">
          {current === 'screener' && <ScreenerPage />}
          {current === 'portfolio' && <PortfolioPage />}
          {current === 'journal' && <JournalPage />}
          {current === 'trades' && <TradeJournalPage />}
          {current === 'briefing' && <BriefingPage />}
          {current === 'breadth' && <BreadthPage data={data} />}
          {current === 'correction' && <CorrectionRiskPage />}
          {current === 'groups' && <GroupsPage />}
          {current === 'modelbooks' && <ModelBooksPage />}
        </main>
      )}

      <Footer lastUpdated={lastUpdated} isOffline={isOffline} />
      </div>
    </div>
  )
}
