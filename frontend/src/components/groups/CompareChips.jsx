import { MAX_COMPARE } from './useThemeCompare'

/**
 * The theme picker: every theme as a chip, pick up to three.
 *
 * All of them are visible, on purpose. TSF's wall of chips is the one place
 * their page quietly brags — it shows the size of the universe you may pick
 * from. Ours is larger (79 published against their 58), and hiding it behind
 * a search box would hide exactly that. Alphabetical, because chips are found
 * by name; the ranking below is where themes are found by strength, and
 * clicking a row there selects too.
 *
 * At the cap the whole wall says so at once: unselected chips drop to
 * half-strength and the pointer turns to not-allowed. The refusal happens
 * BEFORE the click, in the hand, not after it in a toast nobody reads.
 *
 * A chip wears its slot colour only while selected — colour identifies a line
 * in the chart below, it does not rate the theme.
 */
export default function CompareChips({ rows, picks, atLimit, onToggle, onClear }) {
  const names = [...rows.map((r) => r.group)].sort((a, b) => a.localeCompare(b))
  const picked = new Map(picks.map((p) => [p.name, p.colour]))

  return (
    <section>
      <div className="flex items-baseline gap-3 pb-1.5">
        <span className="text-[10px] font-mono uppercase tracking-[.2em]
                         text-[var(--color-text-muted)]">
          Compare
        </span>
        <span className="text-[11px] text-[var(--color-text-muted)]">
          pick up to {MAX_COMPARE} — {picks.length} of {MAX_COMPARE} chosen
          {atLimit && ' · full — unselect one to swap'}
        </span>
        {picks.length > 0 && (
          <button type="button" onClick={onClear}
                  className="ml-auto text-[10px] bg-transparent border-0 p-0 cursor-pointer
                             underline text-[var(--color-text-muted)]
                             hover:text-[var(--color-text)]">
            clear
          </button>
        )}
      </div>

      <div className="flex flex-wrap gap-1">
        {names.map((name) => {
          const colour = picked.get(name)
          const blocked = atLimit && !colour
          return (
            <button key={name} type="button"
                    onClick={() => onToggle(name)}
                    aria-pressed={!!colour}
                    aria-disabled={blocked || undefined}
                    title={blocked
                      ? `${picks.length} of ${MAX_COMPARE} selected — unselect one first`
                      : undefined}
                    style={colour
                      ? { borderColor: colour, color: colour,
                          background: `color-mix(in srgb, ${colour} 14%, transparent)` }
                      : undefined}
                    className={`px-2 py-[3px] text-[10.5px] leading-tight rounded-full border
                                bg-transparent transition-opacity duration-150
                                ${colour
                                  ? 'font-semibold cursor-pointer'
                                  : blocked
                                    ? 'border-[var(--color-border)] text-[var(--color-text-muted)] opacity-45 cursor-not-allowed'
                                    : 'border-[var(--color-border)] text-[var(--color-text-secondary)] cursor-pointer hover:border-[var(--color-text-muted)] hover:text-[var(--color-text)]'}`}>
              {colour && <span aria-hidden className="mr-1">✓</span>}
              {name}
            </button>
          )
        })}
      </div>
    </section>
  )
}
