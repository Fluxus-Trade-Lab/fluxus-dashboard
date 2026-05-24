/* Abstract data-art compositions — inspired by the Masterclass poster.
   Each pillar gets a unique cluster of dots in red/blue,
   like the poster's market-data-as-art visual language. */

function SelectArt() {
  // Cluster of dots rising in a pattern — "selecting" the strong from the weak
  return (
    <div className="pillar-art">
      {/* Strong (blue) dots rising */}
      <div className="pillar-dot pillar-dot-blue" style={{ width: 44, height: 44, left: '8%', bottom: 10 }} />
      <div className="pillar-dot pillar-dot-blue" style={{ width: 36, height: 36, left: '18%', bottom: 30 }} />
      <div className="pillar-dot pillar-dot-blue" style={{ width: 52, height: 52, left: '30%', bottom: 50 }} />
      <div className="pillar-dot pillar-dot-blue" style={{ width: 28, height: 28, left: '44%', bottom: 70 }} />
      <div className="pillar-dot pillar-dot-blue" style={{ width: 40, height: 40, left: '56%', bottom: 85 }} />
      {/* Weak (red) dots scattered lower */}
      <div className="pillar-dot pillar-dot-red" style={{ width: 18, height: 18, left: '14%', bottom: 5 }} />
      <div className="pillar-dot pillar-dot-red" style={{ width: 14, height: 14, left: '38%', bottom: 15 }} />
      <div className="pillar-dot pillar-dot-red" style={{ width: 22, height: 22, left: '50%', bottom: 8 }} />
      <div className="pillar-dot pillar-dot-red" style={{ width: 12, height: 12, left: '64%', bottom: 20 }} />
      <div className="pillar-dot pillar-dot-red" style={{ width: 16, height: 16, left: '72%', bottom: 12 }} />
      {/* Muted noise */}
      <div className="pillar-dot pillar-dot-muted" style={{ width: 10, height: 10, left: '25%', bottom: 2 }} />
      <div className="pillar-dot pillar-dot-muted" style={{ width: 8, height: 8, left: '60%', bottom: 35 }} />
      <div className="pillar-dot pillar-dot-muted" style={{ width: 6, height: 6, left: '80%', bottom: 45 }} />
    </div>
  )
}

function ReadArt() {
  // Flowing dots in two streams — reading the tape, two forces in tension
  return (
    <div className="pillar-art">
      {/* Blue flow — bullish signal */}
      <div className="pillar-dot pillar-dot-blue" style={{ width: 20, height: 20, left: '5%', top: 30 }} />
      <div className="pillar-dot pillar-dot-blue" style={{ width: 24, height: 24, left: '15%', top: 40 }} />
      <div className="pillar-dot pillar-dot-blue" style={{ width: 32, height: 32, left: '28%', top: 35 }} />
      <div className="pillar-dot pillar-dot-blue" style={{ width: 28, height: 28, left: '42%', top: 28 }} />
      <div className="pillar-dot pillar-dot-blue" style={{ width: 38, height: 38, left: '55%', top: 22 }} />
      <div className="pillar-dot pillar-dot-blue" style={{ width: 22, height: 22, left: '70%', top: 30 }} />
      {/* Red flow — bearish signal */}
      <div className="pillar-dot pillar-dot-red" style={{ width: 22, height: 22, left: '10%', bottom: 25 }} />
      <div className="pillar-dot pillar-dot-red" style={{ width: 30, height: 30, left: '22%', bottom: 30 }} />
      <div className="pillar-dot pillar-dot-red" style={{ width: 26, height: 26, left: '38%', bottom: 38 }} />
      <div className="pillar-dot pillar-dot-red" style={{ width: 18, height: 18, left: '52%', bottom: 42 }} />
      <div className="pillar-dot pillar-dot-red" style={{ width: 34, height: 34, left: '64%', bottom: 35 }} />
      <div className="pillar-dot pillar-dot-red" style={{ width: 16, height: 16, left: '78%', bottom: 28 }} />
      {/* Intersection points */}
      <div className="pillar-dot pillar-dot-muted" style={{ width: 12, height: 12, left: '35%', top: '50%' }} />
      <div className="pillar-dot pillar-dot-muted" style={{ width: 8, height: 8, left: '48%', top: '48%' }} />
    </div>
  )
}

function SizeArt() {
  // Yin-yang inspired — balance, like the poster's Day 5 illustration
  // Dots arranged in a circular cluster, red and blue in equilibrium
  return (
    <div className="pillar-art">
      {/* Central balance — large opposing dots */}
      <div className="pillar-dot pillar-dot-blue" style={{ width: 56, height: 56, left: '30%', top: 20 }} />
      <div className="pillar-dot pillar-dot-red" style={{ width: 56, height: 56, left: '46%', top: 50 }} />
      {/* Orbiting smaller dots */}
      <div className="pillar-dot pillar-dot-blue" style={{ width: 16, height: 16, left: '25%', top: 70 }} />
      <div className="pillar-dot pillar-dot-blue" style={{ width: 12, height: 12, left: '50%', top: 10 }} />
      <div className="pillar-dot pillar-dot-red" style={{ width: 14, height: 14, left: '62%', top: 30 }} />
      <div className="pillar-dot pillar-dot-red" style={{ width: 10, height: 10, left: '38%', bottom: 15 }} />
      {/* Tiny balance particles */}
      <div className="pillar-dot pillar-dot-muted" style={{ width: 8, height: 8, left: '20%', top: 45 }} />
      <div className="pillar-dot pillar-dot-muted" style={{ width: 6, height: 6, left: '70%', top: 65 }} />
      <div className="pillar-dot pillar-dot-muted" style={{ width: 10, height: 10, left: '55%', bottom: 20 }} />
      <div className="pillar-dot pillar-dot-muted" style={{ width: 7, height: 7, left: '28%', top: 15 }} />
    </div>
  )
}

export default function MethodPage({ onNavigate }) {
  return (
    <div>
      {/* Intro */}
      <section className="public-section public-section-prose pt-16 sm:pt-24 pb-12">
        <h1 className="public-h1">The Fluxus Method</h1>
        <p className="public-body mt-6 text-[var(--color-text-secondary)]">
          Three pillars. One system. No shortcuts.
        </p>
        <p className="public-body mt-4 text-[var(--color-text-secondary)]">
          Most traders chase signals. They hop from strategy to strategy,
          looking for the one that finally "works." We don't teach signals —
          we teach a process. A repeatable, systematic approach that compounds
          over months and years, not days.
        </p>
      </section>

      {/* Pillar 1: Select */}
      <section className="border-t border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="public-section public-section-prose py-16">
          <SelectArt />
          <p className="public-label" style={{ color: 'var(--color-poster-blue)' }}>Pillar 1</p>
          <h2 className="public-h2 mt-2">Select</h2>
          <p className="public-body mt-4 text-[var(--color-text-secondary)]">
            Strong stocks in strong themes. Not hot tips — systematic screening.
          </p>
          <p className="public-body mt-4 text-[var(--color-text-secondary)]">
            We scan for relative strength, institutional accumulation, and
            sector momentum. Every trade starts with the same question: is this
            stock moving because the market is moving, or because something
            specific to this name is happening? Only the latter earns a spot
            on our watchlist.
          </p>
          <p className="public-body mt-4 text-[var(--color-text-secondary)]">
            You'll learn to read sector rotation, identify emerging themes
            before they hit mainstream, and filter 8,000 tickers down to the
            5-10 that matter today.
          </p>
        </div>
      </section>

      {/* Pillar 2: Read */}
      <section className="border-t border-[var(--color-border)]">
        <div className="public-section public-section-prose py-16">
          <ReadArt />
          <p className="public-label" style={{ color: 'var(--color-poster-red)' }}>Pillar 2</p>
          <h2 className="public-h2 mt-2">Read</h2>
          <p className="public-body mt-4 text-[var(--color-text-secondary)]">
            Interpret risk in real time. Not predict — read.
          </p>
          <p className="public-body mt-4 text-[var(--color-text-secondary)]">
            Options flow, volume profile, breadth internals, volatility
            structure — we read the tape the way a pilot reads instruments.
            Not to predict turbulence, but to know when we're in it and what
            to do.
          </p>
          <p className="public-body mt-4 text-[var(--color-text-secondary)]">
            Fluxus was trained under a hedge fund manager who navigated every
            major bear market since the 1980s. That mentorship instilled one
            principle above all: know where risk is, always. You can't avoid
            every drawdown, but you can avoid the ones that end careers.
          </p>
        </div>
      </section>

      {/* Pillar 3: Size */}
      <section className="border-t border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="public-section public-section-prose py-16">
          <SizeArt />
          <p className="public-label" style={{ color: 'var(--color-poster-blue)' }}>Pillar 3</p>
          <h2 className="public-h2 mt-2">Size</h2>
          <p className="public-body mt-4 text-[var(--color-text-secondary)]">
            Position sizing is the only edge that doesn't decay.
          </p>
          <p className="public-body mt-4 text-[var(--color-text-secondary)]">
            No single trade should have the power to hurt you. Our tools
            enforce this mathematically — calculating position size based on
            your account, your stop, and the stock's volatility. Not gut feel.
            Not "I'll risk 2%." Actual, calibrated sizing for every entry.
          </p>
          <p className="public-body mt-4 text-[var(--color-text-secondary)]">
            This is what separates traders who survive from traders who thrive.
            It's also the pillar most people skip — and the reason most
            accounts blow up even with a winning strategy.
          </p>
        </div>
      </section>

      {/* Philosophy */}
      <section className="border-t border-[var(--color-border)]">
        <div className="public-section public-section-prose py-16">
          <h2 className="public-h2">Philosophy</h2>
          <p className="public-body mt-4 text-[var(--color-text-secondary)]">
            We don't promise overnight riches. We promise a disciplined,
            systematic approach to trading. Our methods are tested and proven,
            focusing on long-term success, relentless consistency, and 2%
            improvement every month.
          </p>
          <p className="public-body mt-4 text-[var(--color-text-secondary)]">
            Data guides insight. Discipline shapes execution. Decision turns
            strategy into consistent performance. This isn't education for
            knowledge's sake — it's training to trade professionally, with
            process and accountability.
          </p>
          <p className="public-body mt-4 text-[var(--color-text-muted)] text-sm italic">
            The name 'Fluxus' pays tribute to the 60s-70s international art
            movement — a radical attitude and desire for continuous change.
          </p>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="public-section public-section-prose py-16 text-center">
          <h2 className="public-h2">Ready to see what this looks like in practice?</h2>
          <div className="mt-6 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={() => onNavigate('#/results')}
              className="public-cta"
            >
              See the results
            </button>
            <button
              onClick={() => onNavigate('#/pricing')}
              className="public-cta-secondary"
            >
              View pricing
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}
