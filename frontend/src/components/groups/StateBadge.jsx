
import { barStyle } from './ThemeBars'

/**
 * The four-state label is deliberately descriptive, not a signal.
 *
 * Backtested over 10 years and 112 non-overlapping periods, filtering an
 * already momentum-ranked list by "accelerating" was a *negative* contribution
 * (-0.18pp, consistent across half-samples) and Weakening actually beat
 * Leading by +0.37pp. So this reads the state of a group; it does not tell you
 * what to buy. The title text says so on hover rather than leaving a green
 * badge to imply an endorsement it has not earned.
 *
 * It said that in a FOURTH palette — emerald / amber / sky / rose — while the
 * same four states are drawn everywhere else as tone × fill through barStyle.
 * Two encodings of one thing is one encoding too many, and the raw-Tailwind
 * one was in no palette the brand declares. Same glyph as the rest now, and
 * the word beside it stays neutral.
 */
export default function StateBadge({ state, title }) {
  if (!state) return <span className="text-[var(--color-text-muted)]">—</span>
  return (
    <span
      title={title ?? 'Descriptive state, not a buy signal'}
      className="inline-flex items-center gap-[5px] text-[11px] whitespace-nowrap
                 text-[var(--color-text-secondary)]"
    >
      <i className="block w-[7px] h-[7px] rounded-[1px]" style={barStyle(state)} />
      {state}
    </span>
  )
}
