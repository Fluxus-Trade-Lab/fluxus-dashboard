/* The three tones are a severity ladder, not three categories: near the
 * 10EMA is a heads-up, a weekly T2 trigger is act, a fired STOP is act now.
 * The site already declares that ladder — caution / warning / riskoff — so
 * these stop being raw Tailwind and start being the same words the rest of
 * the product uses. */
const TONE = {
  amber:  'caution',
  orange: 'warning',
  red:    'riskoff',
}
const tone = (k) => {
  const v = `var(--color-signal-${TONE[k] ?? 'caution'})`
  return {
    background: `color-mix(in srgb, ${v} 15%, transparent)`,
    color: v,
    boxShadow: `inset 0 0 0 1px color-mix(in srgb, ${v} 30%, transparent)`,
  }
}

export default function ProximityChips({ chips }) {
  if (!chips || chips.length === 0) return null
  return (
    <span className="inline-flex gap-0.5">
      {chips.map((c, i) => (
        <span
          key={i}
          className="px-1 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider"
          style={tone(c.tone)}
        >
          {c.label}
        </span>
      ))}
    </span>
  )
}
