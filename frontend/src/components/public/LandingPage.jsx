import { useState, useEffect } from 'react'
import HeroField from './HeroField'
import { PUBLIC_STATS } from './publicStats'

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
            <button
              onClick={() => onNavigate('#/results')}
              className="public-cta"
            >
              See the results
            </button>
          </div>

          <div className="grid grid-cols-3 gap-4 sm:gap-8 max-w-[540px] mt-12">
            <div>
              <div className="public-stat-number" style={{ color: 'var(--color-poster-blue)' }}>+{stats.h1Return}%</div>
              <div className="public-label mt-1">H1 2026 Return</div>
            </div>
            <div>
              <div className="public-stat-number" style={{ color: 'var(--color-poster-blue)' }}>{stats.payoff}&times;</div>
              <div className="public-label mt-1">Payoff Ratio</div>
            </div>
            <div>
              <div className="public-stat-number" style={{ color: 'var(--color-poster-blue)' }}>{stats.profitFactor}</div>
              <div className="public-label mt-1">Profit Factor</div>
            </div>
          </div>
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
