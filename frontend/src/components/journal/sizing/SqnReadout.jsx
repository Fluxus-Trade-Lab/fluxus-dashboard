import { useMemo } from 'react'
import { expectancyStats, sqn, sqnBand } from '../lib/sizingStats'

const TONE_CLASS = {
  bad: 'text-red-600 dark:text-red-400',
  warn: 'text-amber-600 dark:text-amber-400',
  neutral: 'text-[var(--color-text)]',
  good: 'text-green-700 dark:text-green-400',
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
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-2">
          System Quality — SQN &amp; Expectancy
        </h3>
        <p className="text-xs text-[var(--color-text-muted)]">No closed trades with a defined stop yet.</p>
      </div>
    )
  }

  const meanKnown = Number.isFinite(stats.meanR)

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          System Quality — SQN &amp; Expectancy
        </h3>
        <code className="text-[9px] font-mono text-[var(--color-text-muted)]">SQN = √N × (mean R ÷ stdev R)</code>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div>
          <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">Closed Trades</span>
          <span className="text-sm font-semibold font-mono text-[var(--color-text)]">{stats.n}</span>
        </div>
        <div>
          <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">Expectancy</span>
          <span
            className={`text-sm font-semibold font-mono ${
              !meanKnown
                ? 'text-[var(--color-text-muted)]'
                : stats.meanR >= 0
                  ? 'text-green-700 dark:text-green-400'
                  : 'text-red-600 dark:text-red-400'
            }`}
          >
            {meanKnown ? `${stats.meanR >= 0 ? '+' : ''}${fmt(stats.meanR)}R` : '—'}
          </span>
        </div>
        <div>
          <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">Stdev R</span>
          <span className="text-sm font-medium font-mono text-[var(--color-text)]">{fmt(stats.stdevR)}</span>
        </div>
        <div>
          <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">SQN</span>
          <span className="text-sm font-semibold font-mono text-[var(--color-text)]">{fmt(sqnValue)}</span>
        </div>
        <div>
          <span className="text-[9px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">Tharp Band</span>
          <span className={`text-sm font-semibold ${TONE_CLASS[band.tone]}`}>{band.label}</span>
        </div>
      </div>

      <p className="text-[10px] text-[var(--color-text-secondary)] leading-relaxed border-t border-[var(--color-border-light)] pt-2">
        Tharp grades systems by SQN, not by return: it rewards a consistent R-stream, and the grade sets how much sizing freedom you&rsquo;ve earned.
        Raising it means tightening the loss tail and letting the payoff work — not betting bigger. Bands: &lt;1.6 poor · 1.6–1.9 below avg · 2.0–2.4 average · 2.5–2.9 good · 3.0–5.0 excellent · 5.1–6.9 superb.
        {stats.n < 20 && ' ⚠ Fewer than 20 closed trades — SQN is noisy at this sample size.'}
      </p>
    </div>
  )
}
