import { useLanguage } from '../../../i18n/LanguageContext'

const COLORS = {
  PRE_TRIM:  { bg: 'bg-[color-mix(in_srgb,var(--color-signal-caution)_15%,transparent)]',  text: 'text-[var(--color-signal-caution)]',  ring: 'ring-amber-500/30' },
  POST_T1:   { bg: 'bg-blue-500/15',   text: 'text-blue-600',   ring: 'ring-blue-500/30' },
  POST_T2:   { bg: 'bg-teal-500/15',   text: 'text-teal-600',   ring: 'ring-teal-500/30' },
  POST_T3:   { bg: 'bg-[color-mix(in_srgb,var(--color-profit)_15%,transparent)]',  text: 'text-[var(--color-profit)]',  ring: 'ring-green-500/30' },
  CLOSED:    { bg: 'bg-gray-500/10',   text: 'text-gray-500',   ring: 'ring-gray-500/20' },
}

export default function LegStateBadge({ state }) {
  const { t: tr } = useLanguage()
  if (!state || state === 'CLOSED') return null
  const c = COLORS[state] || COLORS.PRE_TRIM
  const label = tr(`pf.leg.${state}`)
  return (
    <span
      className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide ring-1 ${c.bg} ${c.text} ${c.ring}`}
      title={label}
    >
      {label}
    </span>
  )
}
