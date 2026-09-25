/* Who can read which page — one table, three states.
 *
 * Andy set both halves of this on 2026-09-25:
 *
 *   "把其他的页面先锁上先不用注册 公开展示ModelBook。那一页是可以免费使用的
 *    其他的现在都出现一个锁住的这么一个图案 可以点击这个栏目但是出现的是一个
 *    模糊的界面"
 *   "我没有再完成确认审核的板块 那现在只是不对他们开放 只是写这是一个Beta"
 *
 * Those are two different things and he said so: a page can be FINISHED and
 * merely paid for, or it can be UNFINISHED and closed to everyone including
 * members. Two lock systems shipped the same day from the same lane — this
 * file's `LockedPane` and a separate `BetaLock` — and having both meant Model
 * Books, the one page he named as free, rendered locked in production. So the
 * three states live in one table now, and the page reads it once.
 *
 *   free     anyone, in full
 *   members  finished; membership is the only thing missing
 *   beta     not finished, nobody gets in yet — including members
 *
 * ⚠️ NONE OF THIS IS SECURITY. The blur is CSS over a page that has already
 * rendered, and every number behind it comes from JSON this site serves
 * publicly out of `data/output/`, from a repository that is also public.
 * Anyone who opens devtools reads all of it. It is a shop window: it shows a
 * buyer what they would get before there is any account system to enforce
 * anything. Nothing that must actually stay private may go behind it. Real
 * gating waits on the platform-integration work (fluxus-ops T-0925-73).
 *
 * WHY BLUR RATHER THAN HIDE. A hidden page teaches a visitor nothing — the
 * landing page's whole problem was that the product was invisible. A blurred
 * page is evidence: the shape of a real dashboard with today's date in it,
 * which no competitor's marketing screenshot can fake.
 */

export const FREE = 'free'
export const MEMBERS = 'members'
export const BETA = 'beta'

/**
 * Every page the rail can reach, and the state it is in. The `beta` rows each
 * carry the evidence that put them there, because "unfinished" is a claim that
 * goes stale — when a shelf gets its first article it should move to `members`
 * and the note is how the next person knows to check.
 */
export const PAGE_ACCESS = {
  // — free ——————————————————————————————————————————————————————————
  modelbooks: FREE,

  // — members: real pages, finished, behind the membership ——————————
  dashboard: MEMBERS,
  breadth: MEMBERS,
  correction: MEMBERS,
  rotation: MEMBERS,
  groups: MEMBERS,
  'rs-rotation': MEMBERS,
  'rs-leaders': MEMBERS,
  screener: MEMBERS,
  watchlist: MEMBERS,
  portfolio: MEMBERS,
  journal: MEMBERS,
  briefing: MEMBERS,
  // 1 article on 2026-09-25 (data/output/library/index.json) — the only shelf
  // that is not empty, which is why it is not beta with the other four.
  offense: MEMBERS,

  // — beta: not finished, closed to everyone ————————————————————————
  // Renders <Placeholder>, not a page.
  'rs-live': BETA,
  masterclass: BETA,
  // ops ruling T-0925-77 called Portfolio Review 未定稿 and T-0925-75 wrapped
  // it; kept here rather than re-litigated.
  review: BETA,
  // 0 articles each on 2026-09-25. Move to MEMBERS the day one lands.
  defense: BETA,
  psychology: BETA,
  'portfolio-management': BETA,
  news: BETA,
}

/**
 * One line per closed page saying WHAT IT IS — never "subscribe to continue".
 * A lock that names the thing behind it is an advertisement; a lock that says
 * "members only" is just a door. Values are i18n ids, so this file holds no
 * prose of its own.
 */
export const BLURB = {
  dashboard: 'locked.blurb.dashboard',
  breadth: 'locked.blurb.breadth',
  correction: 'locked.blurb.correction',
  rotation: 'locked.blurb.rotation',
  groups: 'locked.blurb.rotation',
  'rs-rotation': 'locked.blurb.rotation',
  'rs-leaders': 'locked.blurb.rotation',
  'rs-live': 'locked.blurb.rsLive',
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
 * The state of one page.
 *
 * A route this table has never heard of comes back FREE. That is deliberate:
 * an unknown route is far more likely to be a page someone just added than a
 * secret, and hiding a colleague's work on the day they ship it is the worse
 * of the two failures.
 */
export function accessOf(pageKey) {
  if (!pageKey) return FREE
  return PAGE_ACCESS[pageKey] ?? FREE
}

/** True when the page should render behind the blur — members OR beta. */
export function isLocked(pageKey) {
  return accessOf(pageKey) !== FREE
}
