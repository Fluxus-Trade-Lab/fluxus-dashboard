import { useHash } from '../hooks/useHash'
import Header from './Header'
import Rail from './Rail'
import PageHeader from './PageHeader'
import WritingSlot from './WritingSlot'
import useWritingSync from '../hooks/useWritingSync'
import Placeholder from './Placeholder'
import HowToRead from './HowToRead'
import Reference from './Reference'

/** A tier marker. The dashboard's problem was rank, not content — seven blocks
 *  at equal weight read as seven equally important things. */
function Band({ label, note }) {
  return (
    <div className="flex items-baseline gap-3 pt-4">
      <span className="text-[10px] font-mono uppercase tracking-[.24em] text-[var(--color-text-muted)]">
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
import VerdictCard from './dashboard/VerdictCard'
import ThemeMovers from './dashboard/ThemeMovers'
import { ETF_GROUPS } from '../lib/etfGroups'
import ScreenerPage from './screener/ScreenerPage'
import WatchlistPage from './watchlist/WatchlistPage'
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

/**
 * `#/review/hold` → { key: 'review', sub: 'hold' }.
 *
 * Sub-routes so a stage is a place: linkable, back-button-able, and reachable
 * from outside. The whole point of the overview pointing at one stage is lost
 * if that stage cannot be addressed.
 */
function pageKey(hash) {
  const path = hash.replace('#/', '') || ''
  const [key, sub] = path.split('/')
  return { key: key || '', sub: sub || null }
}

export default function Layout({ data, lastUpdated, isOffline }) {
  // Mirror the handwritten slots to the Sheet. Mounted here, once, because
  // they live on three different pages and a per-slot sync would pull on
  // every navigation.
  useWritingSync()
  const [page, navigate] = useHash()
  const { key: current, sub: subRoute } = pageKey(page)
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
        /* Page 1 of the morning's three, and the three share one skeleton:
           a matrix of cards whose inside always reads change → strength →
           names. What differs between the pages is WHO is changing (market,
           theme, name) and — Andy's amendment on 2026-08-18 — WHICH CARD IS
           BIGGEST. Size is the fourth channel: it says what this page is for,
           and each page spends it differently.

           On this page it goes to the verdict, because §5.1 asks the top of
           every page to survive as a standalone screenshot and that is how
           this one is actually distributed.

             LARGE   the verdict and the condition that ends it
             MID     market cycle · the founder's own words
             SMALL   what moved, at four grains: benchmarks, sectors,
                     industries, themes

           The founder's notes keep a middle card, not a large one. They are
           the only thing here that is not computed, which earns them the tier;
           they are also empty on most days, and a large empty card reads as a
           broken page rather than as the honest state an empty day is. */
        <main className="max-w-[1800px] mx-auto px-3 py-4 space-y-4">
          <PageHeader group="market" title="Today" meta={[]} />

          {/* ── LARGE ─────────────────────────────────────────────────── */}
          <VerdictCard verdict={data?.breadth?.verdict}
                       conditions={data?.breadth?.conditions}
                       onNavigate={navigate} />

          {/* ── MID ───────────────────────────────────────────────────────
              Where the cycle sits, and what he makes of it. Side by side
              because they are the same reading twice — one measured, one
              written — and stacking them would put the writing among the
              evidence, where it is not evidence.

              Two cadences, because they are two different readings and were
              sharing one box. The daily note is what the tape did today; the
              weekly is what the month is turning into, and a week's worth of
              daily notes is not the same thing as having written the weekly
              one. Both keep their back-catalogue — the second reading is the
              point of writing them. (Andy, 2026-08-17.) */}
          <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]
                          gap-4 items-stretch">
            <RegimeBand verdict={data?.breadth?.verdict} signals={data?.signals}
                        conditions={data?.breadth?.conditions} onNavigate={navigate} />
            <div className="flex flex-col gap-3">
              <WritingSlot
                label="Founders note · daily"
                kind="founders-daily"
                rows={4}
                className="flex-1"
                placeholder="What the session actually did, in your words."
                reserved="Written by hand on the days there is something to say — an
                          empty slot on the other days is the honest state."
              />
              <WritingSlot
                label="Founders note · weekly"
                kind="founders-weekly"
                cadence="weekly"
                rows={4}
                className="flex-1"
                placeholder="What the week is turning into."
                reserved="The longer read. Not a summary of the dailies — the thing
                          that only shows up at a week's distance."
              />
            </div>
          </div>

          {/* ── SMALL ─────────────────────────────────────────────────────
              What moved. The tier word went (Andy 2026-08-16); the rule alone
              now marks the seam between the read and its evidence. */}
          <div className="pt-5">
            <i className="block h-px bg-[var(--color-border)] mb-4" />
            <div className="space-y-3">
              {/* Benchmarks first, unfolded: where the four indices sit is the
                  context every row under it is measured against, and it was
                  behind a click. */}
              <TickerStrip signals={data?.signals} etfData={data?.etf_data} />

              {/* Three grains of the same question, equal width and equal row
                  height so none of them decides another's layout. Themes join
                  the two ETF cohorts here for the first time: the brief asks
                  this page for the one-day and one-week change in sectors AND
                  themes, and only the sector half was ever built. */}
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3
                              gap-3 items-stretch">
                {/* One component, two cohorts (Andy 2026-08-11: Sectors learns
                    the Industries grammar, not the reverse) — the symmetry is
                    structural, not imitated. Each window column shows that
                    window's leaders and laggards WITH that window's move. */}
                <LeadersLaggards title="Industry Leaders and Laggards"
                  etfs={(ETF_GROUPS.Industries || [])
                    .map((t) => (data?.etf_data || []).find((e) => e.ticker === t))
                    .filter(Boolean)}
                  windows={['1D', '1W']} limit={3} />
                <LeadersLaggards title="Sector Leaders and Laggards"
                  etfs={(ETF_GROUPS['Sel Sectors'] || [])
                    .map((t) => (data?.etf_data || []).find((e) => e.ticker === t))
                    .filter(Boolean)}
                  windows={['1D', '1W']} limit={3} />
                <ThemeMovers limit={3} />
              </div>
            </div>
          </div>

          <HowToRead>
            <p>
              Read this page by size. The largest card is today&rsquo;s read and the
              condition that would end it; the middle pair is where the cycle sits and
              what Andy makes of it; the small band underneath is what actually moved,
              at four grains &mdash; benchmarks, industries, sectors, themes. Every card
              is built the same way inside: what changed, then how strong, then which
              names.
            </p>
            <p>
              <b>The verdict card carries two different counts on purpose.</b> The line
              above the word counts <b>conditions</b> (15 of them, and the only daily
              series this pipeline stores with a date on it, which is why the change
              line can exist at all). The number beside the word counts <b>votes</b>
              (12 of them). They are separate instruments and the pipeline has always
              kept them apart. The score is a <b>count of votes, not a confidence
              level</b> &mdash; count the marks rather than trusting the number.
            </p>
            <p>
              The twelve marks are drawn <b>each inside its own range</b>: height is how
              far that vote sits from its own flip line, in its own unit, and two marks
              are never comparable to each other. A ringed mark is a vote sitting on its
              line. That is also why the sentence under them says how many votes have to
              turn but never which ones &mdash; ranking a ratio against a count of names
              would be a number this data cannot carry.
            </p>
            <p>
              The regime band is the <b>weakest of three voters, never their average</b>:
              averaging dilutes one danger into a caution, and that danger is the most
              expensive information on the page. The line under it names exactly which
              voter is holding the reading down, and on what condition.
            </p>
            <p>
              Nothing here sizes a trade. Sizing needs an R and a ceiling, and both
              of those are yours &mdash; the market half of this app deliberately stops at
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
          {current === 'watchlist' && <WatchlistPage zone={subRoute} />}
          {current === 'portfolio' && <PortfolioPage />}
          {/* Renamed 2026-08-17 (Andy): two routes, each named for what it is.
              #/review is the review; #/journal is the trade journal. The old
              #/trades fallback is gone at his call — this repo's habit is to
              keep a retired route resolving so sent links still land, and that
              habit is worth breaking when the reader is the only sender and
              says so. */}
          {current === 'review' && <JournalPage stage={subRoute} />}
          {current === 'journal' && <TradeJournalPage />}
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

          {/* RS Leaderboard deleted. Its content — themes ranked, members
              underneath — is what the Themes page now IS, from the Rank layer
              down through the top-10 tables. Same treatment as RS Rotation
              above: the route resolves so sent links land somewhere true. */}
          {current === 'rs-leaders' && <GroupsPage />}

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
