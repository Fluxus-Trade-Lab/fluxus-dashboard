/**
 * Explicit, hand-maintained split table — the source of truth for known splits.
 *
 * Why this exists: the price feed (Yahoo via GAS) is split-adjusted RETROACTIVELY
 * across its whole history. Every time a ticker splits, the feed rescales every
 * historical bar, which silently corrupts historical MTM. Auto-detecting the
 * factor per trade (see splits.js) is fragile — it fails on repeated leveraged-ETF
 * splits (cumulative gaps like 1/90 that match no clean ratio) and on straddles.
 *
 * Instead we record splits explicitly here and UN-ADJUST the feed back onto the
 * as-traded scale, then freeze the result (see snapshot.js). `splits.js` is kept
 * only as a *suggester* that proposes new entries for this table.
 *
 * Convention:
 *   factor = post-split SHARE multiplier.
 *     forward  N:1  (e.g. 8:1)  → shares ×N,  price ÷N   → factor = N
 *     reverse  1:N  (e.g. 1:10) → shares ×1/N, price ×N  → factor = 1/N
 *   exDate = first session the NEW (post-split) price is in effect, 'YYYY-MM-DD'.
 *
 * Un-adjust identity (holds for forward AND reverse):
 *   asTradedClose(date) = adjustedFeedClose(date) × Π(factor of splits with exDate > date)
 *
 * Entries with a null exDate are placeholders (ratio known, date not yet
 * confirmed) — they are IGNORED by the math until you fill the real ex-date,
 * so the table is always safe to import. Use the in-app "Freeze History"
 * suggester (suggestSplits) to get precise ex-dates, confirm, then paste here.
 */

// Reverse-split helper for readability: rev(10) === 1/10.
const rev = n => 1 / n

export const SPLIT_TABLE = {
  // Forward splits (share count grows)
  SNXX: [{ exDate: '2026-06-03', factor: 8, confirmed: true, note: '2x SNDK, 8:1 fwd' }],
  NVDL: [{ exDate: null, factor: 3, confirmed: false, note: '3:1 fwd — confirm ex-date' }],
  NEBX: [{ exDate: null, factor: 3, confirmed: false, note: '2x NBIS, 3:1 fwd — confirm ex-date' }],

  // Reverse splits — leveraged ETFs, can happen repeatedly (list each separately)
  SOXS: [
    { exDate: null, factor: rev(10), confirmed: false, note: '3x inverse semis, 1:10 rev — confirm ex-date' },
    { exDate: null, factor: rev(9), confirmed: false, note: 'second reverse split (~1:9) — confirm ex-date' },
  ],
  TZA: [
    { exDate: null, factor: rev(10), confirmed: false, note: '3x inverse small-cap, 1:10 rev — confirm ex-date; one trade straddles' },
  ],
}

/**
 * Cumulative un-adjust factor for a ticker on a given date: the product of the
 * share multipliers of every split whose ex-date is AFTER `date`. Placeholder
 * entries (null exDate) are skipped. Returns 1 when nothing applies.
 *
 * @param {string} ticker
 * @param {string} date   'YYYY-MM-DD' (lexical compare is valid for ISO dates)
 * @param {object} table  defaults to SPLIT_TABLE
 */
export function cumFactorAfter(ticker, date, table = SPLIT_TABLE) {
  const entries = table?.[ticker]
  if (!entries?.length) return 1
  const d = (date || '').slice(0, 10)
  let f = 1
  for (const e of entries) {
    if (!e.exDate) continue // unconfirmed placeholder — ignore
    if (e.exDate > d) f *= e.factor
  }
  return f
}

/**
 * Convert an adjusted feed close back to the as-traded scale for `date`.
 * @returns {number|null} null if adjustedClose is null/undefined.
 */
export function unadjustClose(adjustedClose, ticker, date, table = SPLIT_TABLE) {
  if (adjustedClose == null) return null
  return adjustedClose * cumFactorAfter(ticker, date, table)
}
