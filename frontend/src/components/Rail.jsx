import { useState, useEffect } from 'react'
import { useLanguage } from '../i18n/LanguageContext'

/**
 * The left rail — four layers, and inside MARKET, three functions.
 *
 * Design: Fluxus_Brand/visual/2026-08-09_WHAT_TO_SHOW.md
 *
 *   MARKET   what the market is doing        open, no account
 *   LIBRARY  how to read a market at all     open, not tied to today
 *   COURSE   the long-form version           open
 *   MY BOOK  what you did about it           needs an account and your fills
 *
 * MARKET carries sub-labels because it holds three different jobs — read the
 * environment, follow where money is rotating, find the leaders early — and a
 * flat list of eight could not say which page does which. One page, one job.
 *
 * Collapsed codes are declared, never derived. Slicing the label gave RS Live
 * Tracker and RS Leaderboard the same three letters, and Portfolio Management
 * the same as Portfolio — two destinations under one label is a broken rail.
 *
 * Route hashes never change when a label does. Breadth still resolves at
 * #/breadth and Groups at #/groups; a rename that breaks a sent link costs more
 * than it is worth.
 */
export const NAV_GROUPS = [
  {
    key: 'market',
    sections: [
      {
        key: 'env',
        items: [
          { key: 'dashboard', short: 'DSH', hash: '#/dashboard' },
          // Market State and Correction Risk are off the rail on purpose.
          // Today already answers "what is the market doing"; the nine-cell
          // instrument is where you go when you want to know WHY, reached from
          // the link under the read. Two rail entries for one question made the
          // rail a table of contents instead of a set of destinations. The
          // routes still resolve — #/breadth and #/correction — so links that
          // were sent keep working.
        ],
      },
      {
        key: 'rotation',
        items: [
          { key: 'groups', short: 'THM', hash: '#/groups' },         // shown as "Themes"
          { key: 'rslive', short: 'LIV', hash: '#/rs-live' },
          // RS Rotation merged into Themes (the trajectory layer). The rail
          // entry promised a page whose whole content was one layer of another
          // page; the route still resolves so sent links land on Themes.
          { key: 'rsleaders', short: 'LDR', hash: '#/rs-leaders' },
        ],
      },
      {
        key: 'leaders',
        items: [
          { key: 'screener', short: 'SCR', hash: '#/screener' },
        ],
      },
    ],
  },
  {
    // Not market, not record — how to read a market at all.
    key: 'library',
    sections: [{
      key: null,
      items: [
        { key: 'modelbooks', short: 'MDL', hash: '#/modelbooks' },
        { key: 'defense', short: 'DEF', hash: '#/defense' },
        { key: 'offense', short: 'OFF', hash: '#/offense' },
        { key: 'psychology', short: 'PSY', hash: '#/psychology' },
        { key: 'pfmgmt', short: 'PMG', hash: '#/portfolio-management' },
        { key: 'news', short: 'NWS', hash: '#/news' },
      ],
    }],
  },
  {
    key: 'course',
    sections: [{
      key: null,
      items: [{ key: 'masterclass', short: 'MCL', hash: '#/masterclass' }],
    }],
  },
  {
    key: 'book',
    sections: [{
      key: null,
      items: [
        { key: 'portfolio', short: 'PRT', hash: '#/portfolio' },
        { key: 'trades', short: 'LOG', hash: '#/trades' },
        { key: 'journal', short: 'COA', hash: '#/journal' },
      ],
    }],
  },
]

const ALL = NAV_GROUPS.flatMap((g) => g.sections.flatMap((s) => s.items))
const KEY = 'rail-collapsed'

export default function Rail({ currentPage, onNavigate }) {
  const { t } = useLanguage()
  const [collapsed, setCollapsed] = useState(
    () => (typeof localStorage !== 'undefined' && localStorage.getItem(KEY) === '1'),
  )
  useEffect(() => { localStorage.setItem(KEY, collapsed ? '1' : '0') }, [collapsed])

  const glass = {
    background: 'var(--glass)',
    backdropFilter: 'var(--glass-blur)',
    WebkitBackdropFilter: 'var(--glass-blur)',
  }

  return (
    <>
      {/* wide: the rail itself */}
      <nav aria-label="Sections" style={glass}
           className={`hidden lg:flex lg:flex-col shrink-0 min-h-screen pt-4 pb-6
                       border-r border-[var(--glass-edge)] transition-[width] duration-200
                       ${collapsed ? 'w-[62px]' : 'w-[214px]'}`}>
        <div className="flex items-center px-4 pb-4 h-[36px]">
          {!collapsed && (
            <span className="text-[14px] font-semibold tracking-[.16em] flex-1"
                  style={{ fontFamily: 'var(--font-cond)' }}>FLUXUS</span>
          )}
        </div>

        {NAV_GROUPS.map((g) => (
          <div key={g.key} className="pb-1">
            {collapsed
              ? <div className="mx-3 my-2 h-px bg-[var(--color-border)]" />
              : <div className="px-4 pt-3 pb-1 text-[10px] font-mono font-medium uppercase
                                tracking-[.24em] text-[var(--color-text-muted)]">{t(`rail.${g.key}`)}</div>}

            {g.sections.map((sec, si) => (
              <div key={sec.key ?? si}>
                {!collapsed && sec.key && (
                  <div className="px-4 pt-2 pb-0.5 text-[11px] leading-snug
                                  text-[var(--color-text-muted)]">
                    {t(`rail.sec.${sec.key}`)}
                  </div>
                )}
                {sec.items.map(({ key, short, hash }) => {
                  const on = currentPage === key
                  return (
                    <button key={key} onClick={() => onNavigate(hash)}
                            aria-current={on ? 'page' : undefined}
                            title={collapsed ? t(`nav.${key}`) : undefined}
                            className={`w-full border-l-2 py-[7px]
                                        focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]
                                        ${collapsed
                                          ? 'text-[10px] font-mono font-medium text-center px-0'
                                          : 'text-[12.5px] text-left px-4'}
                                        ${on
                                          ? 'border-[var(--color-text)] text-[var(--color-text)] font-semibold bg-[var(--color-hover-bg)]'
                                          : 'border-transparent text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'}`}>
                      {collapsed ? short : t(`nav.${key}`)}
                    </button>
                  )
                })}
              </div>
            ))}

            {!collapsed && (
              <p className="px-4 pt-2 text-[11px] leading-snug text-[var(--color-text-muted)] m-0">
                {t(`rail.${g.key}.note`)}
              </p>
            )}
          </div>
        ))}
      </nav>

      {/* The collapse handle rides the rail's edge at the viewport's vertical
          middle — fixed, so it is under the hand at any scroll depth instead
          of back at the top of the page. */}
      <button type="button" onClick={() => setCollapsed((v) => !v)}
              title={collapsed ? 'Expand' : 'Collapse'}
              aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              style={{ left: collapsed ? 62 : 214 }}
              className="hidden lg:flex fixed top-1/2 -translate-y-1/2 -ml-[11px] z-30
                         w-[22px] h-11 items-center justify-center rounded-full
                         border border-[var(--color-border)] bg-[var(--color-surface)]
                         text-[var(--color-text-muted)] hover:text-[var(--color-text)]
                         cursor-pointer text-[12.5px] transition-[left] duration-200"
              >
        {collapsed ? '»' : '«'}
      </button>

      {/* narrow: one scrollable strip, group labels kept. A rail that becomes a
          hamburger hides the split it exists to show. */}
      <nav aria-label="Sections" style={glass}
           className="lg:hidden flex gap-1 overflow-x-auto px-3 py-2
                      border-b border-[var(--glass-edge)]">
        {NAV_GROUPS.map((g) => (
          <div key={g.key} className="flex items-center gap-1 shrink-0">
            <span className="px-1.5 text-[10px] font-mono font-medium uppercase tracking-[.2em]
                             text-[var(--color-text-muted)] shrink-0">
              {t(`rail.${g.key}`)}
            </span>
            {g.sections.flatMap((s) => s.items).map(({ key, hash }) => (
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
