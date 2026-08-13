const TONE = {
  amber:  'bg-[color-mix(in_srgb,var(--color-signal-caution)_15%,transparent)] text-[var(--color-signal-caution)] ring-amber-500/30',
  red:    'bg-[color-mix(in_srgb,var(--color-loss)_15%,transparent)] text-[var(--color-loss)] ring-red-500/30',
  orange: 'bg-orange-500/15 text-orange-600 ring-orange-500/30',
}

export default function ProximityChips({ chips }) {
  if (!chips || chips.length === 0) return null
  return (
    <span className="inline-flex gap-0.5">
      {chips.map((c, i) => (
        <span
          key={i}
          className={`px-1 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ring-1 ${TONE[c.tone] || TONE.amber}`}
        >
          {c.label}
        </span>
      ))}
    </span>
  )
}
