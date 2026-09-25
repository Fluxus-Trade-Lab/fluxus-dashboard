import { useState, useEffect } from 'react'
import HeroField from './HeroField'
import { PUBLIC_STATS } from './publicStats'

/* The four parts of the tool, named by Andy on 2026-09-25:
   "dashboard是工具，这个工具分几个部分，一个是市场观察 market state, themes,
   screener. 二是portfolio管理和review 三是education，其中modelbook免费。
   四是每日复盘pdf". Kept in that order and that grouping so the page and the
   product cannot drift apart. */
const PILLARS = [
  {
    title: 'Read the market',
    what: 'Is today tradable, and where is the money going.',
    pages: [
      { name: 'Market State', hash: '#/breadth', line: 'The morning read, six steps.' },
      { name: 'Themes', hash: '#/rotation', line: 'What is leading, and what just turned.' },
      { name: 'Screener', hash: '#/screener', line: 'Eight thousand tickers down to a handful.' },
    ],
  },
  {
    title: 'Your own book',
    what: 'The account as one object, and where its money actually goes.',
    pages: [
      { name: 'Portfolio', hash: '#/portfolio', line: 'Open risk and exposure, every position in R.' },
      { name: 'Review', hash: '#/review', line: 'Your leaks, measured rather than remembered.' },
    ],
  },
  {
    title: 'Learn the pattern',
    what: 'The part that makes you not need the signal.',
    pages: [
      { name: 'Model Books', hash: '#/modelbooks', free: true,
        line: '1,400 past leaders, replayed one bar at a time.' },
      { name: 'Masterclass', hash: '#/masterclass', line: 'The whole method, start to finish.' },
    ],
  },
  {
    title: 'The daily recap',
    what: 'The session written up, every trading day.',
    pages: [
      { name: 'Daily Recap', hash: '#/briefing', line: 'English and Chinese, the same evening.' },
    ],
  },
]

export default function LandingPage({ onNavigate }) {
  // Same source as ResultsPage, so the two can never disagree again. Until
  // 2026-08-31 this page showed 72% / 2.1R / 340+ — invented placeholders that
  // survived the 2026-08-16 cleanup of ResultsPage; a visitor who clicked "See
  // the results" watched the win rate drop 32 points.
  //
  // Which three to headline is an editorial call, and Andy made it on 08-31:
  // H1 return, payoff, profit factor. All three are true and all three describe
  // this system better than its win rate does — a 39.9% win rate with a 3.40x
  // payoff is the system working as designed, but the number alone reads as
  // failure to anyone who has not read the method.
  const [stats, setStats] = useState(PUBLIC_STATS)
  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/output/performance.json`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { if (d?.stats) setStats({ ...PUBLIC_STATS, ...d.stats }) })
    // Merge, do not replace: performance.json carries winRate/avgReturn/
    // totalTrades/profitFactor but not h1Return/payoff, and a bare replace
    // renders "+undefined%" on the headline the moment the fetch succeeds.
      .catch(() => {})
  }, [])
  return (
    <div>
      {/*
        The first viewport belongs to the field, whole. Three layouts fought
        for this screen and lost: a square beside the headline read as an
        ornament; a square behind the copy needed a scrim, and the scrim
        needed every stage's layout compressed away from the poster's own
        proportions; and still the words sat ON the picture — Andy's screenshot
        had the triangle inside "compounds." The reference he pointed at gets
        its impact from one thing: the graphic owns the frame, uncontested.

        So the copy is not IN the hero any more. It is the next thing — scroll
        once and the pitch begins. 100svh, not 100vh, so the mobile address bar
        cannot push the field's bottom edge off screen.
      */}
      <section className="public-hero-dark h-[100svh] relative">
        <HeroField />
      </section>

      <section className="public-hero-dark">
        <div className="public-section public-section-wide pt-14 sm:pt-20 pb-16 sm:pb-20 relative z-10">
          <h1 className="public-h1 max-w-[600px]">
            No 10-baggers. No YOLO plays.
            <br />
            <span style={{ color: 'var(--color-poster-red)' }}>Just systematic trading</span> that compounds.
          </h1>
          <p className="public-body mt-6 max-w-[540px]" style={{ color: '#a8a29e' }}>
            Fluxus is a trading community for traders who want to get better, not just get lucky.
          </p>
          <div className="mt-9">
            {/* The primary action is now INTO the product, not at the track
                record. Both TSF and PrimeTrading put "Launch app" / "Join" here;
                "See the results" sends a visitor to a page of numbers about a
                person, which is the pitch a personal brand makes, not a
                platform. Model Books is the one section open to everyone, so
                it is what the button can honestly promise. */}
            <button
              onClick={() => onNavigate('#/modelbooks')}
              className="public-cta"
            >
              Open Model Books — free
            </button>
          </div>

          {/* The record, one line instead of three billboards. Andy,
              2026-09-25: "业绩这个卖点不会持久。持久的是平台和每日的更新."
              A number that headlines a page has to be re-earned every quarter;
              this one is dated, cited and one click from its own page. */}
          <p className="text-[13px] mt-10 mb-0" style={{ color: '#8a8580' }}>
            <span style={{ color: 'var(--color-poster-blue)' }}>+{stats.h1Return}%</span>
            {' '}H1 2026 · {stats.payoff}&times; payoff · {stats.profitFactor} profit factor ·{' '}
            <button onClick={() => onNavigate('#/results')}
                    className="underline cursor-pointer bg-transparent border-0 p-0 text-[13px]"
                    style={{ color: 'inherit', font: 'inherit' }}>
              every trade
            </button>
          </p>
        </div>
      </section>

      {/* What a member actually gets, in the four parts Andy named on
          2026-09-25: market read / your own book / education / the daily recap.
          Every row links to the real page. The locked ones render for real and
          then blur, so clicking is the proof — a visitor sees this site's own
          dashboard with today's date in it, which is the one thing a
          competitor's marketing screenshot cannot fake. */}
      <section className="border-t border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="public-section public-section-wide py-16">
          <h2 className="public-h2">What you get</h2>
          <p className="public-body mt-3 max-w-[560px]" style={{ color: 'var(--color-text-secondary)' }}>
            A tool you open every morning, not a signal you wait for.
            Everything below is live — click any of it and you will see the real
            page, today's data included.
          </p>

          <div className="grid gap-4 mt-9"
               style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))' }}>
            {PILLARS.map((pillar) => (
              <div key={pillar.title}
                   className="rounded-2xl p-5"
                   style={{ background: 'var(--color-bg)',
                            border: '1px solid var(--color-border)' }}>
                <h3 className="text-[17px] font-semibold m-0"
                    style={{ color: 'var(--color-text-bold)' }}>{pillar.title}</h3>
                <p className="text-[13px] mt-1.5 mb-4"
                   style={{ color: 'var(--color-text-muted)' }}>{pillar.what}</p>
                <ul className="list-none p-0 m-0 flex flex-col gap-2.5">
                  {pillar.pages.map((pg) => (
                    <li key={pg.hash}>
                      <button onClick={() => onNavigate(pg.hash)}
                              className="text-left bg-transparent border-0 p-0 cursor-pointer w-full">
                        <span className="text-[13px] font-medium inline-flex items-center gap-1.5"
                              style={{ color: 'var(--color-text)' }}>
                          {pg.name}
                          {/* The same drawn lock the rail uses. The emoji
                              version rendered as a colour illustration next to
                              a page of outline type — one visual language per
                              page. */}
                          {pg.free
                            ? <span className="text-[11px] px-1.5 py-0.5 rounded"
                                    style={{ background: 'var(--color-poster-blue)', color: '#fff' }}>FREE</span>
                            : <svg width="11" height="11" viewBox="0 0 24 24" fill="none"
                                   aria-label="members only" role="img"
                                   className="shrink-0 opacity-55"
                                   style={{ color: 'var(--color-text-muted)' }}>
                                <rect x="4.5" y="10.5" width="15" height="10" rx="2.5"
                                      stroke="currentColor" strokeWidth="2.2" />
                                <path d="M8 10.5V7.5a4 4 0 0 1 8 0v3" stroke="currentColor"
                                      strokeWidth="2.2" strokeLinecap="round" />
                              </svg>}
                        </span>
                        <span className="block text-[13px] mt-0.5"
                              style={{ color: 'var(--color-text-muted)' }}>{pg.line}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <p className="text-[13px] mt-8 mb-0" style={{ color: 'var(--color-text-muted)' }}>
            Sections still being finished are closed rather than shown half-built.
            Model Books is open to everyone, in full.
          </p>
        </div>
      </section>

      {/* Testimonial */}
      <section className="border-t border-[var(--color-border)]">
        <div className="public-section public-section-prose py-12">
          <blockquote className="public-body text-[var(--color-text-secondary)] italic">
            "Half of this year's profits came under the guidance of Fluxus."
          </blockquote>
          <p className="text-xs text-[var(--color-text-muted)] mt-3 tracking-wide uppercase">
            Community member
          </p>
        </div>
      </section>

      {/* The method teaser */}
      <section className="border-t border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="public-section public-section-prose py-16">
          <h2 className="public-h2">The Fluxus Method</h2>
          <p className="public-body mt-4 text-[var(--color-text-secondary)]">
            Three pillars. One system. No shortcuts.
            We teach you to select strong stocks in strong themes,
            read the market in real time, and size your positions
            so no single trade can hurt you.
          </p>
          <div className="mt-6">
            <button
              onClick={() => onNavigate('#/method')}
              className="public-cta-secondary"
            >
              Read the method
            </button>
          </div>
        </div>
      </section>

      {/* Who is Fluxus */}
      <section className="border-t border-[var(--color-border)]">
        <div className="public-section public-section-prose py-16">
          <h2 className="public-h2">Who is Fluxus?</h2>
          <p className="public-body mt-4 text-[var(--color-text-secondary)]">
            A seasoned trader — once a fierce day trader, now a sharp discretionary
            swing strategist. Trained under a hedge fund manager who navigated every
            major bear market since the 1980s. He approaches the market as a game of
            numbers and probability — always an apprentice of mathematics and an ally
            of volatility.
          </p>
          <p className="public-body mt-4 text-[var(--color-text-muted)] text-sm italic">
            The name pays tribute to the 60s-70s Fluxus art movement — a radical
            attitude and desire for continuous change.
          </p>
        </div>
      </section>
    </div>
  )
}
