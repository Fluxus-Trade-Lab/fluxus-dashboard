import { useHash } from '../hooks/useHash'
import Header from './Header'
import Rail from './Rail'
import PageHeader from './PageHeader'
import Placeholder from './Placeholder'
import HowToRead from './HowToRead'

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

          <HowToRead>
            <p>
              Read this page top to bottom — the order is the argument. The reading
              comes first, then <b>what is stacking</b> (names clearing more than one
              screen, and recently), then reference, then the two objects that are
              yours rather than the market's.
            </p>
            <p>
              The score at the top is a <b>count of conditions, not a confidence
              level</b>. Nine votes plus their weights make twelve; +8 means the
              balance of measured conditions leans one way, and the line beside it
              says how many would have to cross before the reading changes. That
              number is the useful one, because it tells you how close this is.
            </p>
            <p>
              Nothing here sizes a trade. Sizing needs an R and a ceiling, and both
              of those are yours — the market half of this app deliberately stops at
              what the market is doing.
            </p>
          </HowToRead>
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

          {/* Reserved. The rail entry, the title and the frame are real from day
              one; a slot that appears only once it is full was never reserved.
              Each says what it will hold and which file it will read. */}
          {current === 'rs-live' && <Placeholder group="market" title="RS Live Tracker"
            blurb="Every theme against SPY, one bar each, sorted, refreshed through the session. One object on the page and nothing else."
            willHold={['One horizontal bar per theme, ranked by relative strength',
                       'Intraday refresh, with the time of the last one printed',
                       'Member count beside each name — a theme of one stock is one stock']}
            source="data/output/groups.json" />}

          {current === 'rs-rotation' && <Placeholder group="market" title="RS Rotation"
            blurb="Where the money left and where it arrived — level against acceleration, over time rather than as a snapshot."
            willHold={['Each theme\'s path across the four states, session by session',
                       'The crossings that matter: lagging into improving, leading into weakening',
                       'How long a theme has held its state, drawn as countable marks']}
            source="data/output/groups.json · breadth archive" />}

          {current === 'rs-leaders' && <Placeholder group="market" title="RS Leaderboard"
            blurb="The strongest themes right now, by level and by acceleration — two rankings, because a board that ranks only what has already won cannot show a turn."
            willHold={['Top themes by 3-month relative strength',
                       'Top themes by acceleration, which is usually a different list',
                       'The denominator on every list — how many themes were ranked']}
            source="data/output/groups.json" />}

          {current === 'defense' && <Placeholder group="library" title="Defense"
            blurb="What to do when you are wrong, and what cash is for."
            willHold={['Stops, and why the one you set at entry is the only honest one',
                       'Cash as a position, not as the absence of one',
                       'Drawdown rules: what to cut, in what order, before deciding anything']} />}

          {current === 'offense' && <Placeholder group="library" title="Offense"
            blurb="How much, when to add, and how to tell a good setup from one that merely looks familiar."
            willHold={['Sizing: fixed R, and why the number is small',
                       'Pyramiding — adding to a position that has already paid',
                       'Leverage, and the conditions under which it is not a mistake',
                       'Grading setups: what separates an A from a B before the outcome']} />}

          {current === 'psychology' && <Placeholder group="library" title="Psychology"
            blurb="Patience, and what to do on the day after a loss."
            willHold={['Waiting as a position — the cost of trading a mediocre setup',
                       'Tilt: recognising it in your own log rather than in the moment',
                       'The re-attack, which the H1 audit named as the single largest leak']} />}

          {current === 'portfolio-management' && <Placeholder group="library" title="Portfolio Management"
            blurb="The book as one object rather than a list of trades."
            willHold={['Open heat — total risk across every position at once',
                       'Correlation: several positions that are secretly one position',
                       'Sharpe, expectancy, SQN — what each measures and what none of them do']} />}

          {current === 'news' && <Placeholder group="library" title="News"
            blurb="Reading the tape's reaction rather than the headline."
            willHold={['News trading: the setup is the reaction, not the announcement',
                       'News failure — when a good headline cannot lift a name, that is the signal',
                       'Using news flow to track where momentum is arriving and leaving']} />}

          {current === 'masterclass' && <Placeholder group="course" title="Swing Trading Masterclass"
            blurb="Sixteen lessons, beginner first, English with Chinese subtitles. Already written; not yet wired into this app."
            willHold={['16 lessons plus a four-part epilogue',
                       'Two gears throughout — foundational and advanced',
                       'Drafted in full 2026-07-12; lives in ~/Documents/SwingMasterclass']} />}
        </main>
      )}

      <Footer lastUpdated={lastUpdated} isOffline={isOffline} />
      </div>
    </div>
  )
}
