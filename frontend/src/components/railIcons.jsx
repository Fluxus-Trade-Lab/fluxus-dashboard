/**
 * One small line icon per rail destination — what the collapsed rail shows
 * instead of the three-letter codes (Andy 2026-10-04: 「左侧导航栏，折叠起来的
 * 时候能否用小图标来表示，而不是缩写」). The codes were exact but unlearnable;
 * nobody arrives knowing that THM is Themes. A funnel or an eye is read
 * before it is decoded.
 *
 * One weight for the whole set, so no row shouts: 24-unit grid, stroke only,
 * 1.6 wide, round caps and joins, `currentColor` so the row's own text colour
 * (muted, hover, active) drives the icon exactly as it drove the code. No
 * fills, no second colour — the accent bar stays the only coloured thing on
 * the rail. Drawn by hand: there is no icon library in this app and one set
 * of fifteen paths does not justify a dependency.
 */

const PATHS = {
  // gauge — the read on the whole market
  dashboard: (
    <>
      <path d="M3.5 16.5a8.5 8.5 0 1 1 17 0" />
      <path d="M12 16.5l4-4.5" />
      <path d="M3.5 19.5h17" />
    </>
  ),
  // layers — themes stacked on themes
  rotation: (
    <>
      <path d="M12 3.5l8.5 4.25L12 12 3.5 7.75z" />
      <path d="M3.5 12L12 16.25 20.5 12" />
      <path d="M3.5 16.25L12 20.5l8.5-4.25" />
    </>
  ),
  // pulse — relative strength, live
  'rs-live': <path d="M3 12h4l2.5-6.5 5 13 2.5-6.5H21" />,
  // funnel — the screener narrows the universe
  screener: <path d="M3.5 4.5h17l-6.5 8v6l-4 2v-8z" />,
  // eye — today's list, the names to watch
  watchlist: (
    <>
      <path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z" />
      <circle cx="12" cy="12" r="2.75" />
    </>
  ),
  // pie — the book, split by position
  portfolio: (
    <>
      <path d="M20.5 15.5A9 9 0 1 1 8.5 3.7" />
      <path d="M21 12a9 9 0 0 0-9-9v9z" />
    </>
  ),
  // notebook — the trade journal
  journal: (
    <>
      <rect x="5" y="3" width="14" height="18" rx="2" />
      <path d="M9 3v18" />
      <path d="M12.5 8h3.5" />
      <path d="M12.5 11.5h3.5" />
    </>
  ),
  // rewind clock — looking back at what you did
  review: (
    <>
      <path d="M3.5 12a8.5 8.5 0 1 0 2.5-6" />
      <path d="M3.5 3.5V8H8" />
      <path d="M12 7.5V12l3 2" />
    </>
  ),
  // graduation cap — the course
  masterclass: (
    <>
      <path d="M2.5 9.5L12 5l9.5 4.5L12 14z" />
      <path d="M6.5 11.6V16c0 1.4 2.5 2.75 5.5 2.75s5.5-1.35 5.5-2.75v-4.4" />
      <path d="M21.5 9.5v5" />
    </>
  ),
  // book with a rising line — model books, charts of past winners
  modelbooks: (
    <>
      <path d="M4.5 19V5a2 2 0 0 1 2-2h13v15h-13a2 2 0 0 0-2 2 2 2 0 0 0 2 2h13" />
      <path d="M8 13.5l3-3 2 2 3.5-4" />
    </>
  ),
  // shield — defense
  defense: <path d="M12 3l7.5 3v5.5c0 4.4-3.1 7.9-7.5 9.5-4.4-1.6-7.5-5.1-7.5-9.5V6z" />,
  // arrow up and out — offense
  offense: (
    <>
      <path d="M6.5 17.5l11-11" />
      <path d="M8.5 6.5h9v9" />
    </>
  ),
  // balance — psychology, keeping the scales level
  psychology: (
    <>
      <path d="M12 4v16" />
      <path d="M8 20h8" />
      <path d="M5 7.5h14" />
      <path d="M5 7.5l-2.75 6a2.75 2.75 0 0 0 5.5 0z" />
      <path d="M19 7.5l-2.75 6a2.75 2.75 0 0 0 5.5 0z" />
    </>
  ),
  // sliders — portfolio management, sizing and exposure
  'portfolio-management': (
    <>
      <path d="M4 6h9M17 6h3M15 4v4" />
      <path d="M4 12h3M11 12h9M9 10v4" />
      <path d="M4 18h11M19 18h1M17 16v4" />
    </>
  ),
  // newspaper — news
  news: (
    <>
      <path d="M4 5h12.5v13a2 2 0 0 0 2 2H6a2 2 0 0 1-2-2z" />
      <path d="M16.5 9h3.5v9a2 2 0 0 1-2 2" />
      <path d="M7.5 9h5.5M7.5 12.5h5.5M7.5 16h3.5" />
    </>
  ),
  // bars — market state / breadth (off the rail today; route still resolves)
  breadth: <path d="M5 20v-7M10 20V6M15 20v-9M20 20V9" />,
}

export const RAIL_ICON_KEYS = Object.keys(PATHS)

export function hasRailIcon(key) {
  return Object.prototype.hasOwnProperty.call(PATHS, key)
}

export default function RailIcon({ name, size = 18, className = '' }) {
  const body = PATHS[name]
  if (!body) return null
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"
         strokeLinejoin="round" aria-hidden="true" focusable="false"
         data-rail-icon={name} className={`shrink-0 ${className}`}>
      {body}
    </svg>
  )
}
