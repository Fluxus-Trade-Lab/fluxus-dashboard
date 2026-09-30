/**
 * The Screener funnel — pure reads over one file, no market arithmetic.
 *
 * Andy approved the funnel on 2026-09-30 (「合」, artifact TTVDd4Jd8n2e6bRgrMxb1N)
 * and the one-sentence notes on 2026-10-01 (「那 27 句候选，写法ok」). The daily
 * `focus-notes` job (.claude/skills/focus-notes) writes everything this panel
 * shows into one file: the fact cards, which names passed which gate, the
 * market readings, and a zh/en sentence per Focus name.
 *
 * WHY THE PAGE DOES NOT RECOMPUTE THE CARDS. The gate and the §11.1 checks
 * already live in `build_cards.py`, and that is the copy the sentences were
 * gated against. A second copy here would be the "same rule in two places"
 * that this repo has had drift twice; the page renders the file's verdicts.
 */

/** the three setups that have a pipeline today, in the order the funnel shows them */
export const LIVE_SETUPS = ['pullback', 'ep', 'vcp']

/**
 * The other twelve scanners of course §5.5. They are drawn greyed so the page
 * says which named setups exist and which have no pipeline yet, instead of
 * pretending the three are the whole list. i18n keys, not prose.
 */
export const PENDING_SETUPS = [
  'growth', 'sectorEtf', 'liquidLeader', 'newHigh52', 'highAdrInside', 'longBase',
  'bullRun', 'topToday', 'premarket', 'recentIpo', 'boxLeader', 'rescreen',
]

/** How many Focus names the course allows on the list (§5.6: ≤ 15, five in play). */
export const FOCUS_CAP = 15

/** The group a sentence talks about: the theme when the name has one, else its industry. */
export function groupOf(card) {
  if (!card) return null
  if (card.theme) return { ...card.theme, kind: 'theme' }
  if (card.ind) return { ...card.ind, kind: 'industry' }
  return null
}

/** accel is rs_accel × 100 with its sign; zero or missing reads as flat. */
export function accelDir(accel) {
  if (accel == null || accel === 0) return 'flat'
  return accel > 0 ? 'up' : 'down'
}

/** Where a non-Focus name stopped: the universe gate (①) or §11.1 (③) with its score. */
export function blockedAt(card) {
  if (!card.tight) return { layer: 'gate' }
  return { layer: 's111', passed: card.qn ?? 0 }
}

const byRs = (a, b) => (b.rs ?? -1) - (a.rs ?? -1) || a.t.localeCompare(b.t)

/**
 * Split one setup's rows into Focus and the rest.
 * Focus = the file's own `focus` flag; RS descending is the page's only ordering
 * (the preview Andy approved), ties broken by ticker so the list is stable.
 */
export function splitSetup(doc, key) {
  const rows = doc?.setups?.[key]?.rows ?? []
  const focus = rows.filter((r) => r.focus).sort(byRs)
  const other = rows.filter((r) => !r.focus).sort(byRs)
  return { focus, other, total: rows.length }
}

/** One sentence in the reader's language, or null. Never falls back to the other language. */
export function noteFor(doc, ticker, lang) {
  const n = doc?.notes?.[ticker]
  if (!n) return null
  const s = n[lang === 'zh' ? 'zh' : 'en']
  return typeof s === 'string' && s.trim() ? s : null
}

/** True when the sentence begins with the data-contradiction marker the skill prescribes. */
export function isFlagged(sentence) {
  return typeof sentence === 'string' && sentence.trimStart().startsWith('⚠')
}

/**
 * Is the file behind the latest session the rest of the site is showing?
 * Compared as ISO dates; a missing side is "unknown", never "fresh".
 */
export function freshness(docAsof, marketDate) {
  if (!docAsof || !marketDate) return 'unknown'
  return docAsof === marketDate ? 'fresh' : docAsof < marketDate ? 'stale' : 'ahead'
}

/** §1.7 question 4: net 52-week new highs, with its sign as the answer. */
export function netHighs(market) {
  if (market?.nh == null || market?.nl == null) return null
  return market.nh - market.nl
}
