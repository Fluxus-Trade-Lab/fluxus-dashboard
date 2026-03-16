import { formatTimestamp } from '../lib/format'

export default function Footer({ lastUpdated, isOffline }) {
  return (
    <footer className="flex items-center justify-center gap-2 py-4 text-[10px] text-[var(--color-text-muted)] font-mono">
      <span>Last updated: {formatTimestamp(lastUpdated)}</span>
      {isOffline && (
        <span className="px-1.5 py-0.5 bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)] rounded uppercase tracking-wider text-[9px] font-medium">
          Cached
        </span>
      )}
    </footer>
  )
}
