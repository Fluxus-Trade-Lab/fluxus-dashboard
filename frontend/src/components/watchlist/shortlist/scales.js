/**
 * One quantity, two scales, in one file.
 *
 * Measured against the series in shortlist.json on 2026-08-20, PSNL's 08-19:
 *
 *   readings.change_pct   0.1366   a FRACTION
 *   panels[].chg_pct      13.7     a PERCENT
 *   marks[].chg           13.7     a PERCENT
 *
 * All three describe the same day's move. This is the shape that has already
 * cost us once — the same quantity wearing different names, where reading one
 * with the other's converter prints 0.14% for a 14% day and nothing about the
 * page looks broken. So the conversion happens HERE, once, named after the
 * SOURCE rather than after the quantity, and `scales.test.js` recomputes every
 * one of them from `series.c` so a silent normalisation on the data side makes
 * a test fail instead of a card lie.
 *
 * Neither is "right". The ask is in DATA_CONTRACTS §七; until it is answered
 * the frontend's job is to be correct about both.
 */

/** readings.change_pct — a fraction. 0.1366 -> 13.66 */
export const pctFromReading = (v) => (v == null ? null : v * 100)

/** marks[].chg and panels[].chg_pct — already percent. 13.7 -> 13.7 */
export const pctFromMark = (v) => (v == null ? null : v)

/** Signed percent, two ways of being absent kept apart from zero. */
export function fmtPct(pct, digits = 2) {
  if (pct == null) return null
  const s = pct >= 0 ? '+' : ''
  return `${s}${pct.toFixed(digits)}%`
}

/** ATR distance from the 50-day. Signed — below the line is a real reading,
 *  not a missing one, and HIMS printed -0.33 on the day this was written. */
export function fmtAtr(v) {
  if (v == null) return null
  return `${v >= 0 ? '+' : ''}${v.toFixed(1)}`
}

/** A percentile that may be an integer rank or a float. One decimal, never
 *  more: rs_line_pctl_21 arrives as 76.19047619047619 and 14 of those digits
 *  are the division, not the measurement. */
export function fmtPctl(v) {
  if (v == null) return null
  return Number.isInteger(v) ? String(v) : v.toFixed(1)
}
