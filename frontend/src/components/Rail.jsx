import { useState, useEffect } from 'react'
import { useLanguage } from '../i18n/LanguageContext'

/**
 * The left rail — four layers, and inside MARKET, three functions.
 *
 * Design: Fluxus_Brand/visual/2026-08-09_WHAT_TO_SHOW.md
 *
 * The order is the operator's, not a taxonomy's: what the market is doing,
 * then what you did about it, then the two that teach. The daily loop is the
 * first two; Course and Library are where you go between sessions, so they sit
 * below the fold of attention rather than between the two halves of the loop.
 *
 *   MARKET   what the market is doing        open, no account
 *   MY BOOK  what you did about it           needs an account and your fills
 *   COURSE   the long-form version           open
 *   LIBRARY  how to read a market at all     open, not tied to today
 *
 * Until 2026-08-14 each of those four lines carried a sentence explaining it
 * ("Open. No account needed."), and MARKET carried three more naming its
 * clusters ("Read the environment"). Seven lines of prose in a 214px column,
 * every one of them read once and never again — the rail spent more ink
 * explaining itself than naming its destinations. The clusters survive as a
 * gap; the sentences are gone.
 *
 * Two levels, kept apart on three channels at once, because one was not enough
 * to feel: a group is a label + a RULE out to the edge (the site's own section
 * idiom, Tier.jsx) and its pages are INDENTED under it; a page is a row with a
 * left bar and a fill. Then the active marks: a group lifts its word and its
 * rule muted → bold when the page you are on lives inside it — it marks a
 * REGION; a page fills and bolds itself — it marks a ROW. Neither uses hue.
 *
 * Collapsed codes are declared, never derived. Slicing the label gave Portfolio
 * Management the same three letters as Portfolio, and did the same to every
 * RS-prefixed page — two destinations under one label is a broken rail.
 * Being declared makes them exact and unlearnable in equal measure, so each one
 * names itself on hover, beside the code, without the native tooltip's delay.
 *
 * The you-are-here bar is the one coloured thing on the rail, in `accent` — the
 * chrome colour, never an encoding one. It is what survives the collapse: the
 * group word goes, the page name goes, and the same coloured bar in the same
 * place is still under your eye. Collapsing should move the rail, not restart
 * the reader.
 *
 * Route hashes never change when a label does. Breadth still resolves at
 * #/breadth and Groups at #/groups; a rename that breaks a sent link costs more
 * than it is worth.
 */
export const NAV_GROUPS = [
  {
    // MARKET's eight pages were briefly split into three clusters — environment,
    // rotation, leaders — with a gap between them. They are one class: every one
    // of them reads the market. The gap claimed a distinction the operator does
    // not make, so it is gone and the group is flat like the other three.
    key: 'market',
    items: [
      { key: 'dashboard', short: 'DSH', hash: '#/dashboard' },
      // Market State and Correction Risk are off the rail on purpose.
      // Today already answers "what is the market doing"; the nine-cell
      // instrument is where you go when you want to know WHY, reached from
      // the link under the read. Two rail entries for one question made the
      // rail a table of contents instead of a set of destinations. The
      // routes still resolve — #/breadth and #/correction — so links that
      // were sent keep working.
      { key: 'groups', short: 'THM', hash: '#/groups' },         // shown as "Themes"
      { key: 'rs-live', short: 'LIV', hash: '#/rs-live' },
      // RS Rotation and RS Leaderboard both merged into Themes — the first
      // was one of its layers, the second is what the whole page became. Both
      // routes still resolve so sent links land on Themes.
      { key: 'screener', short: 'SCR', hash: '#/screener' },
      // Its own page, not a Screener tab: the Screener is a table you tune
      // and this is six questions already answered. Two postures, two pages.
      { key: 'watchlist', short: 'WCH', hash: '#/watchlist' },
    ],
  },
  {
    // The record. Second, because market → book is the daily loop.
    key: 'book',
    items: [
      { key: 'portfolio', short: 'PRT', hash: '#/portfolio' },
      // `key` IS the route's first segment — Layout derives `currentPage`
      // from the hash and the rail lights the row whose key equals it. Until
      // 2026-08-31 four entries carried a label-shaped key instead, and two of
      // them were each other's route: clicking Trade Journal went to #/journal
      // and lit Review. A key here is an identifier, never a name.
      { key: 'journal', short: 'LOG', hash: '#/journal' },
      { key: 'review', short: 'REV', hash: '#/review' },
    ],
  },
  {
    key: 'course',
    items: [{ key: 'masterclass', short: 'MCL', hash: '#/masterclass' }],
  },
  {
    // Not market, not record — how to read a market at all.
    key: 'library',
    items: [
      { key: 'modelbooks', short: 'MDL', hash: '#/modelbooks' },
      { key: 'defense', short: 'DEF', hash: '#/defense' },
      { key: 'offense', short: 'OFF', hash: '#/offense' },
      { key: 'psychology', short: 'PSY', hash: '#/psychology' },
      { key: 'portfolio-management', short: 'PMG', hash: '#/portfolio-management' },
      { key: 'news', short: 'NWS', hash: '#/news' },
    ],
  },
]

const ALL = NAV_GROUPS.flatMap((g) => g.items)
const KEY = 'rail-collapsed'

/** page key → the group that holds it, so a group can say "you are in here". */
const GROUP_OF = Object.fromEntries(
  NAV_GROUPS.flatMap((g) => g.items.map((i) => [i.key, g.key])),
)

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

        {NAV_GROUPS.map((g, gi) => {
          const here = GROUP_OF[currentPage] === g.key
          return (
            <div key={g.key} className={gi === 0 ? '' : (collapsed ? 'mt-2' : 'mt-5')}>
              {collapsed
                // no rule above the first group — there is nothing above it to
                // separate from, and the codes carry no group word to lift.
                ? (gi > 0 && <div className="mx-3 mb-2 h-px bg-[var(--color-border)]" />)
                : (
                  // The site's own section-label idiom (see Tier.jsx): the word,
                  // then a rule running out to the edge. Colour alone was not
                  // enough separation — a small grey word above a list still
                  // reads as another item in the list. The rule makes it a
                  // header, structurally, before any colour is applied.
                  <div className="flex items-center gap-2.5 px-4 pb-2">
                    <span className={`text-[10px] font-mono font-medium uppercase tracking-[.24em]
                                      ${here ? 'text-[var(--color-text-bold)]'
                                             : 'text-[var(--color-text-muted)]'}`}>
                      {t(`rail.${g.key}`)}
                    </span>
                    <i className={`flex-1 h-px ${here ? 'bg-[var(--color-text-muted)]'
                                                      : 'bg-[var(--color-border)]'}`} />
                  </div>
                )}

              {g.items.map(({ key, short, hash }) => {
                const on = currentPage === key
                return (
                  <button key={key} onClick={() => onNavigate(hash)}
                          aria-current={on ? 'page' : undefined}
                          aria-label={collapsed ? t(`nav.${key}`) : undefined}
                          className={`group relative w-full border-l-2 py-[7px]
                                      focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]
                                      ${collapsed
                                        ? 'text-[10px] font-mono font-medium text-center px-0'
                                        // indented past the header's word: the
                                        // second level sits under the first
                                        : 'text-[12.5px] text-left pl-6 pr-3'}
                                      ${on
                                        ? 'border-[var(--color-accent)] text-[var(--color-text-bold)] font-semibold bg-[var(--color-hover-bg)]'
                                        : 'border-transparent text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'}`}>
                    {collapsed ? short : t(`nav.${key}`)}
                    {collapsed && (
                      // The codes are declared, not derived, which makes them
                      // exact but unlearnable — nobody arrives knowing that THM
                      // is the Themes page. The name was already in `title`,
                      // but a native tooltip waits a second and appears under
                      // the cursor rather than beside the code it explains.
                      <span className="pointer-events-none absolute left-full top-1/2 z-40 ml-1
                                       hidden -translate-y-1/2 whitespace-nowrap rounded-lg
                                       border border-[var(--color-border)] bg-[var(--color-surface)]
                                       px-2 py-1 text-[11px] font-sans font-normal tracking-normal
                                       normal-case text-[var(--color-text)] shadow-lg
                                       group-hover:block group-focus-visible:block">
                        {t(`nav.${key}`)}
                      </span>
                    )}
                  </button>
                )
              })}
            </div>
          )
        })}
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
            <span className={`px-1.5 text-[10px] font-mono font-medium uppercase tracking-[.2em]
                              shrink-0 ${GROUP_OF[currentPage] === g.key
                                ? 'text-[var(--color-text-bold)]'
                                : 'text-[var(--color-text-muted)]'}`}>
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
