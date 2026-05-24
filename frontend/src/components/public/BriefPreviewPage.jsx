import { useState, useEffect } from 'react'

const SAMPLE_BRIEFS = [
  {
    date: '2026-03-21',
    title: 'Rotation into defensives accelerating',
    summary: 'Breadth narrowing as leaders consolidate. Utilities and healthcare seeing inflows while tech names rest. SPX holding above 5-day EMA but internals softer than price suggests. Watching NVDA, PLTR for continuation setups if they hold yesterday\'s lows.',
    watchlist: ['NVDA', 'PLTR', 'UNH', 'XLU'],
  },
  {
    date: '2026-03-20',
    title: 'FOMC digestion — vol crush confirmed',
    summary: 'As expected, IV crush across the board post-FOMC. Put/call ratio normalizing. Key level on SPX is 5,820 support. Above that, we stay constructive. Two new names added to watchlist on relative strength breakouts.',
    watchlist: ['ANET', 'CRWD', 'META'],
  },
  {
    date: '2026-03-19',
    title: 'Pre-FOMC positioning: light and nimble',
    summary: 'Reduced exposure ahead of the announcement. No new entries today. Existing positions have stops tightened. Options flow showing hedging activity in QQQ and SPY. Expect a move — direction less certain than magnitude.',
    watchlist: ['SPY', 'QQQ'],
  },
  {
    date: '2026-03-18',
    title: 'Semis leading again — SMH breakout watch',
    summary: 'Semiconductor names showing strength across the board. SMH testing resistance with volume. NVDA earnings runup in play. Watching for a clean breakout above $248 for a swing entry. Risk is well-defined at $240 support.',
    watchlist: ['SMH', 'NVDA', 'AMD', 'AVGO'],
  },
  {
    date: '2026-03-17',
    title: 'Quiet open expected — scanning for setups',
    summary: 'Futures flat after last week\'s rally. Market needs time to digest gains. Focus today is on scanning for new base breakouts in mid-cap growth names. Two positions from Friday hit first targets — trailing stops moved to breakeven.',
    watchlist: ['CELH', 'DUOL', 'TOST'],
  },
]

export default function BriefPreviewPage({ onNavigate }) {
  const [briefs, setBriefs] = useState(null)

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/output/briefs.json`)
      .then(r => r.ok ? r.json() : null)
      .then(setBriefs)
      .catch(() => setBriefs(null))
  }, [])

  const data = briefs || SAMPLE_BRIEFS

  return (
    <div>
      {/* Header */}
      <section className="public-section public-section-prose pt-16 sm:pt-24 pb-8">
        <h1 className="public-h1">The Daily Brief</h1>
        <p className="public-body mt-4 text-[var(--color-text-secondary)]">
          Every morning before the open, members get a concise market read —
          what happened, what to watch, and where the setups are. Here's a
          preview of recent briefs.
        </p>
      </section>

      {/* Briefs list */}
      <section className="public-section public-section-prose pb-16">
        <div className="space-y-0">
          {data.map((brief, i) => (
            <article
              key={brief.date}
              className={`py-8 ${i > 0 ? 'border-t border-[var(--color-border-light)]' : ''}`}
            >
              <time className="text-xs font-mono text-[var(--color-text-muted)] tracking-wide">
                {brief.date}
              </time>
              <h2 className="text-lg font-semibold text-[var(--color-text)] mt-2">
                {brief.title}
              </h2>
              <p className="text-sm text-[var(--color-text-secondary)] mt-3 leading-relaxed">
                {brief.summary}
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {brief.watchlist.map(ticker => (
                  <span
                    key={ticker}
                    className="text-xs font-mono px-2 py-0.5 rounded bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)]"
                  >
                    {ticker}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="public-section public-section-prose py-12 text-center">
          <p className="public-body text-[var(--color-text-secondary)]">
            Members receive the full brief with entry levels, stop placements,
            and position sizing guidance.
          </p>
          <div className="mt-6">
            <button
              onClick={() => onNavigate('#/pricing')}
              className="public-cta"
            >
              Get full access
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}
