import { useLanguage } from '../i18n/LanguageContext'

/**
 * The left rail — two modes, labelled.
 *
 * Design: Fluxus_Brand/visual/explorations/2026-08-08/market_today.html
 *
 * The split is the product's shape, not a tidier menu. MARKET is the state of
 * the market, identical for everyone, and needs no account. MY BOOK is a
 * framework and a record, different per person, and cannot exist without one.
 * Nine flat items could not say that; two labelled groups say it without a
 * sentence.
 *
 * Route hashes are unchanged. Breadth and Groups are renamed on screen only —
 * #/breadth and #/groups still resolve, so anything already sent out keeps
 * working. A rename that breaks old links is a rename that costs more than it
 * is worth.
 */
export const NAV_GROUPS = [
  {
    key: 'market',
    items: [
      { key: 'dashboard', hash: '#/dashboard' },
      { key: 'screener', hash: '#/screener' },
      { key: 'breadth', hash: '#/breadth' },     // shown as "Market State"
      { key: 'groups', hash: '#/groups' },       // shown as "Themes"
      { key: 'modelbooks', hash: '#/modelbooks' },
    ],
  },
  {
    key: 'book',
    items: [
      { key: 'portfolio', hash: '#/portfolio' },
      { key: 'trades', hash: '#/trades' },
      { key: 'journal', hash: '#/journal' },
    ],
  },
]

const ALL = NAV_GROUPS.flatMap((g) => g.items)

export default function Rail({ currentPage, onNavigate }) {
  const { t } = useLanguage()

  return (
    <>
      {/* wide: the rail itself */}
      <nav aria-label="Sections"
           className="hidden lg:flex lg:flex-col w-[212px] shrink-0 min-h-screen pt-4
                      border-r border-[var(--glass-edge)]"
           style={{ background: 'var(--glass)', backdropFilter: 'var(--glass-blur)',
                    WebkitBackdropFilter: 'var(--glass-blur)' }}>
        <div className="px-5 pb-5 text-[15px] font-semibold tracking-[.16em]"
             style={{ fontFamily: 'var(--font-cond)' }}>FLUXUS</div>

        {NAV_GROUPS.map((g) => (
          <div key={g.key} className="pb-1">
            <div className="px-5 pt-3 pb-1.5 text-[9px] font-mono uppercase tracking-[.24em]
                            text-[var(--color-text-muted)]">
              {t(`rail.${g.key}`)}
            </div>
            {g.items.map(({ key, hash }) => (
              <button key={key} onClick={() => onNavigate(hash)}
                      aria-current={currentPage === key ? 'page' : undefined}
                      className={`w-full text-left px-5 py-[7px] text-[13px] border-l-2
                                  focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] ${
                        currentPage === key
                          ? 'border-[var(--color-text)] text-[var(--color-text)] font-semibold bg-[var(--color-hover-bg)]'
                          : 'border-transparent text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
                      }`}>
                {t(`nav.${key}`)}
              </button>
            ))}
            <p className="px-5 pt-2 text-[10px] leading-snug text-[var(--color-text-muted)] m-0">
              {t(`rail.${g.key}.note`)}
            </p>
          </div>
        ))}
      </nav>

      {/* narrow: the same items as one scrollable strip. A rail that becomes a
          hamburger hides the split it exists to show, so the groups stay visible
          as labels in the strip. */}
      <nav aria-label="Sections"
           className="lg:hidden flex gap-1 overflow-x-auto px-3 py-2
                      border-b border-[var(--glass-edge)]"
           style={{ background: 'var(--glass)', backdropFilter: 'var(--glass-blur)',
                    WebkitBackdropFilter: 'var(--glass-blur)' }}>
        {NAV_GROUPS.map((g) => (
          <div key={g.key} className="flex items-center gap-1 shrink-0">
            <span className="px-1.5 text-[8px] font-mono uppercase tracking-[.2em]
                             text-[var(--color-text-muted)] shrink-0">
              {t(`rail.${g.key}`)}
            </span>
            {g.items.map(({ key, hash }) => (
              <button key={key} onClick={() => onNavigate(hash)}
                      aria-current={currentPage === key ? 'page' : undefined}
                      className={`px-2.5 py-1 text-[10px] font-medium uppercase tracking-wide
                                  rounded shrink-0 ${
                        currentPage === key
                          ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)]'
                          : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
                      }`}>
                {t(`nav.${key}`)}
              </button>
            ))}
          </div>
        ))}
      </nav>
    </>
  )
}

export { ALL as NAV_ITEMS }
