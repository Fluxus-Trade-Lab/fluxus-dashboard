/**
 * The trading day, in the market's timezone — never the reader's, never UTC.
 *
 * WHY THIS EXISTS. Every "today" in this app used to be
 * `new Date().toISOString().split('T')[0]`, which is today in UTC. The host
 * clock here is JST (UTC+9), so between 09:00 and 18:00 JST the UTC date has
 * already rolled over while New York is still on the previous session —
 * 09:00 JST is 20:00 ET the day before. For those nine hours every UTC "today"
 * named a session that had not happened yet.
 *
 * WHAT IT BROKE. The portfolio's 1D column keys its prices by date. A position
 * opened during the New York evening (JST morning) was compared against a
 * "today" one day ahead of its own entry date, so the entry-date test in
 * `calculations.js` — the one that stops us charging you for the gap you were
 * not in (see the MRNA case there) — read false exactly during the hours Andy
 * actually looks at the page.
 *
 * This is the browser-side companion to `pipeline.marketcal`, which is the
 * authority on the server. It deliberately does NOT know about holidays or
 * half-days: a second, wrong market calendar living in the frontend is worse
 * than a calendar-free date. It answers one question — what calendar day is it
 * in New York right now — and stops.
 */

/** Today in New York as an ISO date (YYYY-MM-DD). The market's day. */
export function todayET(now = new Date()) {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit',
  }).format(now)
}

/**
 * `n` calendar days before an ISO date. Calendar, not trading — callers that
 * need the previous SESSION walk back from here until a price exists, which is
 * what `lookupPriceAt` already does.
 */
export function isoDaysAgo(iso, n) {
  const d = new Date(`${iso}T00:00:00Z`)
  if (Number.isNaN(d.getTime())) return iso
  d.setUTCDate(d.getUTCDate() - n)
  return d.toISOString().split('T')[0]
}

/** The previous WEEKDAY before an ISO date. Saturday and Sunday are skipped. */
export function prevWeekday(iso) {
  let d = isoDaysAgo(iso, 1)
  // 0 = Sunday, 6 = Saturday, read in UTC because the string is UTC midnight.
  while ([0, 6].includes(new Date(`${d}T00:00:00Z`).getUTCDay())) d = isoDaysAgo(d, 1)
  return d
}
