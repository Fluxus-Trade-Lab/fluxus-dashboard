/**
 * The stage pin from the URL, or null when there is none.
 *
 * Exported for its test, which exists because of how this went wrong: the
 * original inline version was `Number(params.get('stage'))`, and .get()
 * returns null when the parameter is absent — and Number(null) is 0, which is
 * a valid stage. Every visitor without ?stage was pinned to stage 0, the hero
 * froze on its first panel in production for days, and no error said so.
 * Found by counting the app's requestAnimationFrame calls over CDP in Andy's
 * own Chrome: canvas present, zero schedules — the loop was never entered.
 */
export function parsePinnedStage(search, stageCount) {
  const raw = new URLSearchParams(search).get('stage')
  if (raw == null || raw.trim() === '') return null
  const n = Number(raw)
  return Number.isInteger(n) && n >= 0 && n < stageCount ? n : null
}
