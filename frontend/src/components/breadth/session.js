/**
 * Weekends only — the browser has no NYSE holiday calendar and this deliberately
 * does not pretend otherwise. A row stamped on a Saturday is the case that has
 * actually occurred; a row stamped on Thanksgiving would still slip through, and
 * the fix for that belongs in the pipeline, where the row should not be written
 * at all.
 *
 * Shared because two objects need it: the state board, and the verdict banner —
 * which travels on its own as a screenshot, so it cannot rely on a caveat
 * printed somewhere further down the page.
 */
export function isWeekend(iso) {
  if (!iso) return false
  const d = new Date(`${iso}T12:00:00Z`).getUTCDay()
  return d === 0 || d === 6
}
