import HeroField from './HeroField'

export default function LandingPage({ onNavigate }) {
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
      {/* The studio: the reference's light room, not the poster's black. The
          spheres carry the poster's red and blue; the ground carries the
          light that makes them material. Everything below the fold returns
          to poster black — the cut IS the design. */}
      <section className="h-[100svh] relative"
               style={{ backgroundColor: 'var(--color-poster-paper)' }}>
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
