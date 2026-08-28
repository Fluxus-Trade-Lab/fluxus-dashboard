/**
 * How far behind is what you are looking at?
 *
 * WHY THIS EXISTS. On 2026-08-24 the nightly job started failing and the page
 * went on showing Monday's date, calmly, for three days. Nothing lied — the
 * title prints whatever session the file carries — but nothing said "this is
 * old" either, and Andy found the gap himself rather than being told. That is
 * the same defect this site has a rule against everywhere else: absent must
 * not render as nothing. A stale reading rendered as a current one is the same
 * failure wearing a date.
 *
 * WHAT IT REFUSES TO CLAIM. It counts WEEKDAYS, not trading sessions. The
 * browser has no holiday calendar, and inventing one here would put a second,
 * wrong market calendar in the app next to `pipeline.marketcal` — which is the
 * "same quantity, two definitions" trap this repo keeps falling into. So the
 * badge says "weekdays", which stays true on the four or five days a year a
 * holiday makes it read one high. Being coarse and honest beats being precise
 * and wrong, and the number only has to be good enough to make you look.
 *
 * THE ONE-WEEKDAY GRACE. Through most of any given day the newest session on
 * file IS yesterday's — today's close has not been published yet. Firing on a
 * gap of one would mean the badge is lit almost always, and a warning that is
 * always on is furniture.
 */

/** Weekdays strictly after `from`, up to and including `to`. Both ISO dates. */
export function weekdaysBetween(from, to) {
  const a = new Date(`${from}T00:00:00Z`)
  const b = new Date(`${to}T00:00:00Z`)
  if (Number.isNaN(a.getTime()) || Number.isNaN(b.getTime()) || b <= a) return 0
  let n = 0
  const d = new Date(a)
  while (d < b) {
    d.setUTCDate(d.getUTCDate() + 1)
    const wd = d.getUTCDay()
    if (wd !== 0 && wd !== 6) n += 1
  }
  return n
}

/** Today in New York, as an ISO date. The market's day, not the reader's. */
export function todayET(now = new Date()) {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit',
  }).format(now)
}

export const WARN_AT = 2   // badge appears
export const ALARM_AT = 4  // badge turns red

/**
 * @returns {null|{behind:number, level:'warn'|'alarm', date:string}}
 *   null when the data is current enough to say nothing.
 */
export function freshness(sessionDate, now = new Date()) {
  if (!sessionDate) return null
  const behind = weekdaysBetween(sessionDate, todayET(now))
  if (behind < WARN_AT) return null
  return { behind, level: behind >= ALARM_AT ? 'alarm' : 'warn', date: sessionDate }
}
