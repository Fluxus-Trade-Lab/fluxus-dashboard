import { useLanguage } from '../../../i18n/LanguageContext'
import Squares from '../../Squares'

/**
 * How far a leg has been trimmed, counted rather than hued.
 *
 * It read as five unrelated colours — amber, blue, teal, green, grey — for
 * PRE-T1 through CLOSED. But those are not five categories: they are one
 * sequence, the trims that have executed. Five hues for an ordinal is rank
 * carried by hue alone, which the encoding rule forbids, and it left three of
 * the five in raw Tailwind, in no palette the brand declares.
 *
 * Counted instead, on the site's own isotype construction: one filled square
 * per trim taken, of the three the plan has. POST-T2 is two filled and one
 * empty — the same shape the vote marks and the top-quartile column use.
 */

const TAKEN = { PRE_TRIM: 0, POST_T1: 1, POST_T2: 2, POST_T3: 3 }
const OF = 3

export default function LegStateBadge({ state }) {
  const { t: tr } = useLanguage()
  if (!state || state === 'CLOSED') return null
  const n = TAKEN[state] ?? 0
  const label = tr(`pf.leg.${state}`)
  return (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap
                     text-[10px] font-mono font-medium uppercase tracking-[.1em]
                     text-[var(--color-text-secondary)]"
          title={`${label} — ${n} of ${OF} trims taken`}>
      <Squares n={n} of={OF} title={`${n} of ${OF} trims taken`} />
      {label}
    </span>
  )
}
