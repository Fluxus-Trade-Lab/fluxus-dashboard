const STYLES = {
  Leading: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  Weakening: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  Improving: 'bg-sky-500/15 text-sky-400 border-sky-500/30',
  Lagging: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
}

/**
 * The four-state label is deliberately descriptive, not a signal.
 *
 * Backtested over 10 years and 112 non-overlapping periods, filtering an
 * already momentum-ranked list by "accelerating" was a *negative* contribution
 * (-0.18pp, consistent across half-samples) and Weakening actually beat
 * Leading by +0.37pp. So this reads the state of a group; it does not tell you
 * what to buy. The title text says so on hover rather than leaving a green
 * badge to imply an endorsement it has not earned.
 */
export default function StateBadge({ state, title }) {
  if (!state) return <span className="text-[var(--color-text-muted)]">—</span>
  return (
    <span
      title={title ?? 'Descriptive state, not a buy signal'}
      className={`inline-block px-1.5 py-0.5 rounded border text-[11px] font-medium
                  whitespace-nowrap ${STYLES[state] ?? ''}`}
    >
      {state}
    </span>
  )
}
