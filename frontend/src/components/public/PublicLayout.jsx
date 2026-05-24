import PublicHeader from './PublicHeader'

export default function PublicLayout({ currentPage, onNavigate, children }) {
  return (
    <div className="min-h-screen bg-[var(--color-bg)]">
      <PublicHeader currentPage={currentPage} onNavigate={onNavigate} />

      <main>
        {children}
      </main>

      <footer className="border-t border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="max-w-[720px] mx-auto px-4 sm:px-12 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-xs text-[var(--color-text-muted)]">
            Fluxus Capital
          </div>
          <div className="flex items-center gap-4 text-xs text-[var(--color-text-muted)]">
            <a
              href="https://x.com/Fluxus_Z"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-[var(--color-text-secondary)] transition-colors"
            >
              X / Twitter
            </a>
            <a
              href="https://youtube.com/@FluxusCapital"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-[var(--color-text-secondary)] transition-colors"
            >
              YouTube
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}
