const COLORS = {
  PRE_TRIM:  { bg: 'bg-amber-500/15',  text: 'text-amber-600',  ring: 'ring-amber-500/30' },
  POST_T1:   { bg: 'bg-blue-500/15',   text: 'text-blue-600',   ring: 'ring-blue-500/30' },
  POST_T2:   { bg: 'bg-teal-500/15',   text: 'text-teal-600',   ring: 'ring-teal-500/30' },
  POST_T3:   { bg: 'bg-green-500/15',  text: 'text-green-600',  ring: 'ring-green-500/30' },
  CLOSED:    { bg: 'bg-gray-500/10',   text: 'text-gray-500',   ring: 'ring-gray-500/20' },
}

const LABELS = {
  PRE_TRIM: 'PRE-T1',
  POST_T1: 'POST-T1',
  POST_T2: 'POST-T2',
  POST_T3: 'POST-T3',
  CLOSED: '—',
}

export default function LegStateBadge({ state }) {
  if (!state || state === 'CLOSED') return null
  const c = COLORS[state] || COLORS.PRE_TRIM
  return (
    <span
      className={`inline-block px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wide ring-1 ${c.bg} ${c.text} ${c.ring}`}
      title={`Leg state: ${LABELS[state]}`}
    >
      {LABELS[state]}
    </span>
  )
}
