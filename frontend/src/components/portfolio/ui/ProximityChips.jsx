const TONE = {
  amber:  'bg-amber-500/15 text-amber-600 ring-amber-500/30',
  red:    'bg-red-500/15 text-red-600 ring-red-500/30',
  orange: 'bg-orange-500/15 text-orange-600 ring-orange-500/30',
}

export default function ProximityChips({ chips }) {
  if (!chips || chips.length === 0) return null
  return (
    <span className="inline-flex gap-0.5">
      {chips.map((c, i) => (
        <span
          key={i}
          className={`px-1 py-0.5 rounded text-[8.5px] font-bold uppercase tracking-wider ring-1 ${TONE[c.tone] || TONE.amber}`}
        >
          {c.label}
        </span>
      ))}
    </span>
  )
}
