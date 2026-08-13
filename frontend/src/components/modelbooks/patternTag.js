/**
 * How a chart-pattern tag looks — defined once.
 *
 * It was defined three times, identically, in StudyMode / BrowseView /
 * TagStats: twelve patterns × twelve hues, each copy free to drift from the
 * others. Two copies is how two tags start meaning slightly different things.
 *
 * And the twelve hues were doing no work. Every chip prints the pattern's
 * NAME — "Cup With Handle", "Flat Base" — so the colour was a second identity
 * channel for something already identified, in raw Tailwind, in no palette
 * this brand declares. Twelve hues is also past the point anyone learns them:
 * a reader cannot recall that cyan means pocket pivot, so they read the word,
 * which was there all along.
 *
 * One exception earns its ink. `faulty_base` is not a twelfth pattern, it is
 * the negative case — the base that failed — and in a wall of tags that is
 * the one a reader scans for. It keeps `refused`, the encoding's own colour
 * for the chance that was offered and not taken.
 */

const FAILED = 'faulty_base'

const NEUTRAL = 'bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)]'
const MARKED =
  'bg-[color-mix(in_srgb,var(--color-refused)_18%,transparent)] text-[var(--color-refused)]'

/** Chip classes for a pattern key. Unknown keys read neutral, like the rest. */
export function patternTag(pattern) {
  return pattern === FAILED ? MARKED : NEUTRAL
}

/** `cup_with_handle` → `Cup With Handle`. */
export function formatPattern(key) {
  return String(key ?? '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}
