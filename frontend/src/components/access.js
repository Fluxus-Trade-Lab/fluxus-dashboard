/* Which pages a visitor can read, and which ones they can only look at.
 *
 * Andy, 2026-09-25: "把其他的页面先锁上先不用注册 公开展示ModelBook。那一页是
 * 可以免费使用的 其他的现在都出现一个锁住的这么一个图案 可以点击这个栏目但是
 * 出现的是一个模糊的界面."
 *
 * ⚠️ THIS IS A SHOP WINDOW, NOT A LOCK. The blur is a CSS filter over a page
 * that has already rendered, and every number behind it comes from JSON this
 * site serves publicly out of `data/output/` — from a repository that is also
 * public. Anyone who opens devtools reads it all. That is fine for what this
 * is for: showing a buyer what they would get, before there is any account
 * system to enforce anything. It is NOT access control, and nothing that must
 * actually stay private may be put behind it. Real gating waits on the
 * platform-integration decision (fluxus-ops T-0925-73).
 *
 * WHY BLUR RATHER THAN HIDE. A hidden page teaches a visitor nothing; the
 * landing page's whole problem was that the product was invisible. A blurred
 * page is evidence — the shape of a real dashboard with today's date on it,
 * which no screenshot of a competitor's marketing site can fake.
 */

/** Pages any visitor may use in full. */
export const FREE_PAGES = new Set([
  // The library of historical leaders, with the bar-by-bar replay. Free by
  // Andy's decision the same day: it is the education module, and education
  // is what brings people in — both TSF and PrimeTrading's own numbers say
  // the teaching outdraws the picks by 5-8x.
  'modelbooks',
])

/**
 * One line per locked page saying WHAT IT DOES — not "subscribe to continue".
 * A lock that names the thing behind it is an advertisement; a lock that says
 * "members only" is a door. Keys are i18n ids so the card speaks the reader's
 * language; `access.js` holds no prose of its own.
 */
export const LOCKED_BLURB = {
  dashboard: 'locked.blurb.dashboard',
  breadth: 'locked.blurb.breadth',
  correction: 'locked.blurb.correction',
  rotation: 'locked.blurb.rotation',
  groups: 'locked.blurb.rotation',
  'rs-live': 'locked.blurb.rsLive',
  'rs-rotation': 'locked.blurb.rotation',
  'rs-leaders': 'locked.blurb.rotation',
  screener: 'locked.blurb.screener',
  watchlist: 'locked.blurb.watchlist',
  portfolio: 'locked.blurb.portfolio',
  journal: 'locked.blurb.journal',
  review: 'locked.blurb.review',
  briefing: 'locked.blurb.briefing',
  masterclass: 'locked.blurb.masterclass',
  defense: 'locked.blurb.defense',
  offense: 'locked.blurb.offense',
  psychology: 'locked.blurb.psychology',
  'portfolio-management': 'locked.blurb.portfolioManagement',
  news: 'locked.blurb.news',
}

/**
 * True when this page should render behind the blur.
 *
 * Unknown pages are NOT locked. A route this table has never heard of is more
 * likely a new page someone just added than a secret — and a wrong lock is
 * worse than a missing one here, because the missing one shows a page that was
 * already public anyway while the wrong one hides work from the person who
 * just shipped it.
 */
export function isLocked(pageKey) {
  if (!pageKey) return false
  if (FREE_PAGES.has(pageKey)) return false
  return Object.prototype.hasOwnProperty.call(LOCKED_BLURB, pageKey)
}
