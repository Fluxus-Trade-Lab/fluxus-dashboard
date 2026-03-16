import { formatTimestamp } from '../lib/format'

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
  return (
    <header className="flex items-center justify-between px-4 py-3 bg-white border-b border-stone-200">
      <div className="flex items-center gap-3">
        <h1 className="text-sm font-semibold tracking-tight text-stone-900">
          Fluxus Capital
        </h1>
        <div className="flex gap-1 ml-3">
          {NAV_ITEMS.map(({ key, label, hash }) => (
            <button
              key={key}
              onClick={() => onNavigate(hash)}
              className={`px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide rounded ${
                currentPage === key
                  ? 'bg-stone-800 text-stone-100'
                  : 'text-stone-500 hover:text-stone-800'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        {isOffline && (
          <span className="px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wider bg-stone-200 text-stone-600 rounded">
            Offline
          </span>
        )}
      </div>

      <div className="text-[10px] text-stone-400 font-mono">
        {formatTimestamp(lastUpdated)}
      </div>
    </header>
  )
}
