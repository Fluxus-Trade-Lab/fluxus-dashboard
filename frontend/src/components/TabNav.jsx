const TABS = [
  { id: 'macro', label: 'Macro' },
  { id: 'equities', label: 'Equities' },
  { id: 'screeners', label: 'Scan' },
]

export default function TabNav({ activeTab, onTabChange }) {
  return (
    <nav className="flex border-b border-[var(--color-border)] bg-[var(--color-surface)] sm:hidden">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`flex-1 py-2.5 text-xs font-medium uppercase tracking-wide transition-colors
            ${activeTab === tab.id
              ? 'text-[var(--color-text)] border-b-2 border-[var(--color-text)]'
              : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'
            }`}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  )
}
