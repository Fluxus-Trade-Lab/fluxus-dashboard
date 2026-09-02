const ENV_DOT = {
  BULLISH: 'bg-[var(--color-took)]',
  BEARISH: 'bg-[var(--color-refused)]',
  MIXED: 'bg-[var(--color-signal-caution)]',
  OVERSOLD: 'bg-[var(--color-signal-caution)]',
  OVERBOUGHT: 'bg-[var(--color-signal-caution)]',
}

export default function BreadthChip({ verdict, onNavigate }) {
  if (!verdict) return null
  const summary = verdict.notes?.[0] ?? verdict.confirmation
  return (
    <button
      onClick={() => onNavigate('#/breadth')}
      className="w-full flex items-center gap-2 bg-[var(--color-surface)] rounded-3xl px-3 py-1.5 hover:bg-[var(--color-hover-bg)] text-left"
    >
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${ENV_DOT[verdict.env] ?? ''}`} />
      <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] shrink-0">
        Breadth
      </span>
      <span className="text-[11px] font-mono text-[var(--color-text)] shrink-0">{verdict.env}</span>
      <span className="text-[11px] text-[var(--color-text-secondary)] truncate">
        · {verdict.exposure} · {summary}
      </span>
    </button>
  )
}
