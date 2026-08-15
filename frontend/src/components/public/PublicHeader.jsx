import { useState } from 'react'
import { useTheme } from '../../hooks/useTheme'

const NAV_ITEMS = [
  { key: 'method', label: 'Method', hash: '#/method' },
  { key: 'results', label: 'Results', hash: '#/results' },
  { key: 'pricing', label: 'Pricing', hash: '#/pricing' },
  { key: 'brief', label: 'Brief', hash: '#/brief' },
]

export default function PublicHeader({ currentPage, onNavigate }) {
  const { theme, toggle } = useTheme()
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <header className="border-b border-[var(--color-border)] bg-[var(--color-surface)]">
      <div className="max-w-[1200px] mx-auto px-4 sm:px-12 flex items-center justify-between h-14">
        {/* Logo */}
        <button
          onClick={() => onNavigate('#/')}
          className="text-sm font-semibold tracking-tight text-[var(--color-text)] cursor-pointer bg-transparent border-none p-0"
        >
          Fluxus Capital
        </button>

        {/* Desktop nav */}
        <nav className="hidden sm:flex items-center gap-6">
          {NAV_ITEMS.map(({ key, label, hash }) => (
            <button
              key={key}
              onClick={() => onNavigate(hash)}
              className={`text-sm bg-transparent border-none cursor-pointer transition-colors ${
                currentPage === key
                  ? 'text-[var(--color-text)] font-medium'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
              }`}
            >
              {label}
            </button>
          ))}
          <button
            onClick={() => onNavigate('#/pricing')}
            className="bg-[var(--color-accent-solid)] text-white px-4 py-2 rounded text-sm font-semibold uppercase tracking-wide cursor-pointer border-none"
          >
            Join
          </button>
          <button
            onClick={toggle}
            className="w-7 h-7 flex items-center justify-center rounded-full bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors cursor-pointer border-none text-sm"
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {theme === 'dark' ? '\u2600' : '\u263E'}
          </button>
        </nav>

        {/* Mobile: Join + hamburger */}
        <div className="flex sm:hidden items-center gap-2">
          <button
            onClick={() => onNavigate('#/pricing')}
            className="bg-[var(--color-accent-solid)] text-white px-3 py-1.5 rounded text-xs font-semibold uppercase tracking-wide cursor-pointer border-none"
          >
            Join
          </button>
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="w-8 h-8 flex items-center justify-center text-[var(--color-text-secondary)] cursor-pointer bg-transparent border-none text-lg"
            aria-label="Toggle menu"
          >
            {menuOpen ? '\u2715' : '\u2630'}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <nav className="sm:hidden border-t border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 flex flex-col gap-3">
          {NAV_ITEMS.map(({ key, label, hash }) => (
            <button
              key={key}
              onClick={() => { onNavigate(hash); setMenuOpen(false) }}
              className={`text-sm text-left bg-transparent border-none cursor-pointer py-1 ${
                currentPage === key
                  ? 'text-[var(--color-text)] font-medium'
                  : 'text-[var(--color-text-secondary)]'
              }`}
            >
              {label}
            </button>
          ))}
          <button
            onClick={toggle}
            className="text-sm text-left text-[var(--color-text-secondary)] bg-transparent border-none cursor-pointer py-1"
          >
            {theme === 'dark' ? 'Light mode' : 'Dark mode'}
          </button>
        </nav>
      )}
    </header>
  )
}
