export default function LandingPage({ onNavigate }) {
  return (
    <div>
      {/* Dark hero — poster-inspired */}
      <section className="public-hero-dark">
        {/* Abstract background dots — like the poster's bubble clusters */}
        <div className="hero-dot hero-dot-blue" style={{ width: 280, height: 280, top: -60, right: -40 }} />
        <div className="hero-dot hero-dot-red" style={{ width: 180, height: 180, top: 80, right: 120 }} />
        <div className="hero-dot hero-dot-blue" style={{ width: 100, height: 100, bottom: 20, left: '15%' }} />
        <div className="hero-dot hero-dot-red" style={{ width: 60, height: 60, top: 40, left: '10%' }} />
        <div className="hero-dot hero-dot-blue" style={{ width: 40, height: 40, bottom: 60, right: '30%' }} />
        <div className="hero-dot hero-dot-red" style={{ width: 140, height: 140, bottom: -40, left: '40%' }} />

        <div className="public-section public-section-wide pt-20 sm:pt-32 pb-16 sm:pb-24 relative z-10">
          <h1 className="public-h1 max-w-[600px]">
            No 10-baggers. No YOLO plays.
            <br />
            <span style={{ color: 'var(--color-poster-red)' }}>Just systematic trading</span> that compounds.
          </h1>
          <p className="public-body mt-6 max-w-[540px]" style={{ color: '#a8a29e' }}>
            Fluxus is a trading community for traders who want to get better, not just get lucky.
          </p>
          <div className="mt-10">
            <button
              onClick={() => onNavigate('#/results')}
              className="public-cta"
            >
              See the results
            </button>
          </div>
        </div>

        {/* Stats row — still inside dark section */}
        <div className="public-section public-section-wide pb-20 sm:pb-28 relative z-10">
          <div className="grid grid-cols-3 gap-4 sm:gap-8 max-w-[540px]">
            <div>
              <div className="public-stat-number" style={{ color: 'var(--color-poster-blue)' }}>72%</div>
              <div className="public-label mt-1">Win Rate</div>
            </div>
            <div>
              <div className="public-stat-number" style={{ color: 'var(--color-poster-blue)' }}>2.1R</div>
              <div className="public-label mt-1">Avg Return</div>
            </div>
            <div>
              <div className="public-stat-number" style={{ color: 'var(--color-poster-blue)' }}>340+</div>
              <div className="public-label mt-1">Trades</div>
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
