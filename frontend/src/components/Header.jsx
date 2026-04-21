import { formatTimestamp } from '../lib/format'
import { useTheme } from '../hooks/useTheme'

const NAV_ITEMS = [
  { key: 'dashboard', label: 'Dashboard', hash: '#/dashboard' },
  { key: 'screener', label: 'Screener', hash: '#/screener' },
  { key: 'portfolio', label: 'Portfolio', hash: '#/portfolio' },
  { key: 'journal', label: 'AI Coach', hash: '#/journal' },
  { key: 'briefing', label: 'Briefing', hash: '#/briefing' },
  { key: 'breadth', label: 'Breadth', hash: '#/breadth' },
  { key: 'modelbooks', label: 'Model Books', hash: '#/modelbooks' },
]

export default function Header({ lastUpdated, isOffline, currentPage, onNavigate }) {
  const { theme, toggle } = useTheme()

  return (
    <header className="flex items-center justify-between px-4 py-3 bg-[var(--color-surface)] border-b border-[var(--color-border)]">
      <div className="flex items-center gap-3">
        <h1 className="text-sm font-semibold tracking-tight text-[var(--color-text)]">
          Fluxus Capital
        </h1>
        <div className="flex gap-1 ml-3 overflow-x-auto">
          {NAV_ITEMS.map(({ key, label, hash }) => (
            <button
              key={key}
              onClick={() => onNavigate(hash)}
              className={`px-2.5 py-1 text-[10px] font-medium uppercase tracking-wide rounded flex-shrink-0 focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] focus-visible:ring-offset-1 ${
                currentPage === key
                  ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)]'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        {isOffline && (
          <span className="px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wider bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)] rounded">
            Offline
          </span>
        )}
      </div>

      <div className="flex items-center gap-3">
        <div className="text-[10px] text-[var(--color-text-muted)] font-mono hidden sm:block">
          {formatTimestamp(lastUpdated)}
        </div>
        <button
          onClick={toggle}
          className="w-7 h-7 flex items-center justify-center rounded-full bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors cursor-pointer border-none text-sm"
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? '\u2600' : '\u263E'}
        </button>
      </div>
    </header>
  )
}
