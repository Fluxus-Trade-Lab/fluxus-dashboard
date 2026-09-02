import { useMemo } from 'react'
import { expectancyStats, sqn, sqnBand } from '../lib/sizingStats'

const TONE_CLASS = {
  bad: 'text-[var(--color-loss)]',
  warn: 'text-[var(--color-signal-caution)]',
  neutral: 'text-[var(--color-text)]',
  good: 'text-[var(--color-profit)]',
  muted: 'text-[var(--color-text-muted)]',
}

/**
 * Format a stat for display. sqn() returns null when undefined (n < 2 or zero
 * stdev) and NaN when the R series carries a non-finite value — .toFixed() on
 * NaN prints the literal string "NaN", so every number is finite-checked before
 * it reaches the DOM. Unknown renders as the same em-dash sqnBand() shows.
 */
function fmt(value, digits = 2) {
  return Number.isFinite(value) ? value.toFixed(digits) : '—'
}

export default function SqnReadout({ rs }) {
  const stats = useMemo(() => expectancyStats(rs), [rs])
  const sqnValue = useMemo(() => sqn(rs), [rs])
  const band = sqnBand(sqnValue)

  if (!stats.n) {
    return (
      <div className="bg-[var(--color-surface)] rounded-3xl p-4">
        <h3 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-2">
          System Quality — SQN &amp; Expectancy
        </h3>
        <p className="text-[13px] text-[var(--color-text-muted)]">No closed trades with a defined stop yet.</p>
      </div>
    )
  }

  const meanKnown = Number.isFinite(stats.meanR)

  return (
    <div className="bg-[var(--color-surface)] rounded-3xl p-4 space-y-3">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          <h3 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
            System Quality — SQN &amp; Expectancy
          </h3>
          <span className="text-[11px] font-mono uppercase tracking-wide px-1.5 py-0.5 rounded bg-[var(--color-bg)] border border-[var(--color-border-light)] text-[var(--color-text-muted)]">
            Live · your synced book
          </span>
        </div>
        <code className="text-[11px] font-mono text-[var(--color-text-muted)]">SQN = √min(N,100) × (mean R ÷ stdev R)</code>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div>
          <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">Closed Trades</span>
          <span className="text-[13px] font-semibold font-mono text-[var(--color-text)]">{stats.n}</span>
        </div>
        <div>
          <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">Expectancy</span>
          <span
            className={`text-[13px] font-semibold font-mono ${
              !meanKnown
                ? 'text-[var(--color-text-muted)]'
                : stats.meanR >= 0
                  ? 'text-[var(--color-profit)]'
                  : 'text-[var(--color-loss)]'
            }`}
          >
            {meanKnown ? `${stats.meanR >= 0 ? '+' : ''}${fmt(stats.meanR)}R` : '—'}
          </span>
        </div>
        <div>
          <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">Win Rate</span>
          <span className="text-[13px] font-medium font-mono text-[var(--color-text)]">{fmt(stats.winRate * 100, 1)}%</span>
        </div>
        <div>
          <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">Payoff</span>
          <span className="text-[13px] font-medium font-mono text-[var(--color-text)]">{fmt(stats.payoff)}×</span>
        </div>
        <div>
          <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">Stdev R</span>
          <span className="text-[13px] font-medium font-mono text-[var(--color-text)]">{fmt(stats.stdevR)}</span>
        </div>
        <div>
          <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">SQN</span>
          <span className="text-[13px] font-semibold font-mono text-[var(--color-text)]">{fmt(sqnValue)}</span>
        </div>
        <div>
          <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">Tharp Band</span>
          <span className={`text-[13px] font-semibold ${TONE_CLASS[band.tone]}`}>{band.label}</span>
        </div>
      </div>

      <p className="text-[11px] text-[var(--color-text-secondary)] leading-relaxed border-t border-[var(--color-border-light)] pt-2">
        Tharp grades systems by SQN, not by return: it rewards a consistent R-stream, and the grade sets how much sizing freedom you&rsquo;ve earned.
        Raising it means tightening the loss tail and letting the payoff work — not betting bigger. Bands: &lt;1.6 poor · 1.6 to &lt;2.0 below avg · 2.0 to &lt;2.5 average · 2.5 to &lt;3.0 good · 3.0–5.0 excellent · &gt;5.0 to &lt;7.0 superb · &ge;7.0 holy grail.
        {stats.n < 20 && ' ⚠ Fewer than 20 closed trades — SQN is noisy at this sample size.'}
      </p>
    </div>
  )
}
