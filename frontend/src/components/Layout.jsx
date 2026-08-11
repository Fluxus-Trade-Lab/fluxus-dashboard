import { useHash } from '../hooks/useHash'
import Header from './Header'
import Rail from './Rail'
import PageHeader from './PageHeader'
import Placeholder from './Placeholder'
import HowToRead from './HowToRead'
import Reference from './Reference'
import Tier from './Tier'

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
import RegimeBand from './dashboard/RegimeBand'
import LeadersLaggards from './dashboard/LeadersLaggards'
import { VoteMarks } from './breadth/VoteGlyphs'
import { ETF_GROUPS } from '../lib/etfGroups'
import ScreenerPage from './screener/ScreenerPage'
import PortfolioPage from './portfolio/PortfolioPage'
import JournalPage from './journal/JournalPage'
import BriefingPage from './briefing/BriefingPage'
import BreadthPage from './breadth/BreadthPage'
import CorrectionRiskPage from './breadth/CorrectionRiskPage'
import GroupsPage from './groups/GroupsPage'
import ThemeLeaderboard from './groups/ThemeLeaderboard'
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
        /* Today, in the three tiers of 2026-08-09_WHAT_TO_SHOW.md §4.

           SUBJECT    the read and the twelve votes that produced it. This used
                      to be a one-line chip and eight prices; eight prices
                      answer "what happened", which is not the page's question.
           EVIDENCE   regime band · best/worst industries · the five checks per
                      benchmark · what is stacking.
           REFERENCE  the price strip, the trend table, the full cross-section.

           The Founders-note slot is deliberately an empty frame: Andy writes
           it, the layout only reserves the space. */
        <main className="max-w-[1800px] mx-auto px-3 py-4 space-y-4">
          <PageHeader group="market" title="Today"
            blurb="What the market is doing, before you decide what to do about it."
            meta={['the read, then the evidence, then reference',
                   'sizing is not on this page — it needs an R and a ceiling, and those are yours']} />

          {/* SUBJECT — the read on the left, its own history on the right.
              Side by side because they answer one question in two tenses:
              what the market is today, and whether today is unusual for it.
              Stacked, the chart read as a second object; beside the votes it
              reads as their denominator. */}
          <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,7fr)_minmax(0,9fr)] gap-4 items-stretch">
            {data?.breadth?.verdict && (
              <section className="border border-[var(--color-border)] rounded-lg px-4 py-3
                                  bg-[var(--color-surface)]">
                <div className="flex flex-wrap items-baseline gap-x-5 gap-y-1 mb-4">
                  <h2 className="text-[34px] leading-none font-semibold m-0"
                      style={{ fontFamily: 'var(--font-cond)',
                               color: /BULL/i.test(data.breadth.verdict.env)
                                 ? 'var(--color-took)' : 'var(--color-refused)' }}>
                    {data.breadth.verdict.env}
                  </h2>
                  <span className="text-[19px] font-mono tabular-nums">
                    {data.breadth.verdict.score > 0 ? '+' : ''}{data.breadth.verdict.score}
                    <span className="text-[var(--color-text-muted)]"> / 12</span>
                  </span>
                  <button type="button" onClick={() => navigate('#/breadth')}
                          className="text-[11px] bg-transparent border-0 p-0 cursor-pointer underline
                                     text-[var(--color-text-muted)] hover:text-[var(--color-text)]">
                    the nine conditions behind it →
                  </button>
                </div>
                <VoteMarks votes={data.breadth.verdict.votes} />
              </section>
            )}

            <RegimeBand verdict={data?.breadth?.verdict} signals={data?.signals}
                        conditions={data?.breadth?.conditions} onNavigate={navigate} />
          </div>

          {/* Reserved for the founder's own words — written, never generated.
              An empty frame, because a slot that appears only once it is full
              was never reserved. */}
          <section className="border border-dashed border-[var(--color-border)] rounded-lg
                              px-4 py-3">
            <span className="text-[10px] font-mono uppercase tracking-[.24em]
                             text-[var(--color-text-muted)]">Founders note</span>
            <p className="text-[11px] text-[var(--color-text-muted)] m-0 mt-1">
              Reserved. Written by hand on the days there is something to say — an
              empty slot on the other days is the honest state.
            </p>
          </section>

          <Tier label="Evidence" supports="what the read leans on">
            <div className="space-y-3">
              {/* Benchmarks first, unfolded: where the four indices sit is the
                  context every row under it is measured against, and it was
                  behind a click. */}
              <TickerStrip signals={data?.signals} etfData={data?.etf_data} />

              {/* Equal width, equal row height, so neither card decides the
                  other's layout. items-stretch is the default and is what makes
                  them end level regardless of how many rows each holds. */}
              <div className="grid grid-cols-1 xl:grid-cols-2
                              gap-3 items-stretch">
                {/* One component, two cohorts (Andy 2026-08-11: Sectors learns
                    the Industries grammar, not the reverse) — the symmetry is
                    structural, not imitated. Each window column shows that
                    window's leaders and laggards WITH that window's move. */}
                <LeadersLaggards title="Industries"
                  etfs={(ETF_GROUPS.Industries || [])
                    .map((t) => (data?.etf_data || []).find((e) => e.ticker === t))
                    .filter(Boolean)}
                  windows={['1D', '1W', '1M']} limit={3} />
                <LeadersLaggards title="Sectors"
                  etfs={(ETF_GROUPS['Sel Sectors'] || [])
                    .map((t) => (data?.etf_data || []).find((e) => e.ticker === t))
                    .filter(Boolean)}
                  windows={['1D', '1W', '1M']} limit={3} />
              </div>
            </div>
          </Tier>

          <HowToRead>
            <p>
              Read this page top to bottom — the order is the argument. The read
              and its twelve votes come first, then the regime band, then the
              evidence — where the money went this week and this month, at two
              grains — then reference.
            </p>
            <p>
              The score is a <b>count of conditions, not a confidence level</b> —
              count the marks rather than trusting the number. The regime band is
              the <b>weakest of three voters, never their average</b>: averaging
              dilutes one danger into a caution, and that danger is the most
              expensive information on the page. The line under it names exactly
              which voter is holding the reading down, and on what condition.
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

          {/* RS Rotation lives inside Themes now (the trajectory layer);
              the route survives so sent links keep working. */}
          {current === 'rs-rotation' && <GroupsPage />}

          {current === 'rs-leaders' && <ThemeLeaderboard />}

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
