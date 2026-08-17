/**
 * Dated entries for the things Andy writes himself.
 *
 * Three surfaces on this site are his words rather than the pipeline's — the
 * pre-market checklist, the trading recap, the founder's note — and each had
 * invented its own storage or none at all. The checklist's was the instructive
 * one: a single slot, overwritten by `if (parsed.date !== todayKey()) return
 * {}`, so every morning silently destroyed the previous day's reflection. A
 * journal that cannot be re-read is a habit, not a record.
 *
 * One store, keyed by (kind, date). Nothing is ever overwritten by the passage
 * of time; a new day writes a new key.
 *
 * DURABILITY, stated rather than assumed: this is localStorage. It lives in
 * one browser on one machine and a cleared cache takes it with it — unlike the
 * trade log, which survives because it also lives in the Sheet. `exportAll`
 * exists so the record can leave; wiring these into the Sheet's Meta tab is a
 * separate decision, not something to assume.
 */

const PREFIX = 'fluxus-writing'

/** Local calendar date, not UTC — a journal entry belongs to the day you had. */
export function todayKey(d = new Date()) {
  return d.toLocaleDateString('en-CA')          // YYYY-MM-DD
}

/**
 * The Monday of the week a date falls in, as that week's key.
 *
 * Weekly notes need a stable identity or Monday's and Thursday's entries become
 * two different weeks. ISO weeks start Monday; getDay() calls Sunday 0, so
 * Sunday folds back six days rather than forward one.
 */
export function weekKey(d = new Date()) {
  const x = new Date(d)
  const shift = (x.getDay() + 6) % 7
  x.setDate(x.getDate() - shift)
  return todayKey(x)
}

const storageKey = (kind) => `${PREFIX}:${kind}`

function readAll(kind) {
  try {
    return JSON.parse(localStorage.getItem(storageKey(kind)) || '{}') || {}
  } catch {
    return {}
  }
}

/** Every entry for a kind, as { date: text }. */
export function loadEntries(kind) {
  return readAll(kind)
}

/** One entry, '' when never written. */
export function loadEntry(kind, date) {
  const v = readAll(kind)[date]
  return typeof v === 'string' ? v : ''
}

/**
 * Write one entry. Empty text DELETES the key rather than storing '' — an
 * entry that exists but says nothing would show up in the history list as a
 * day with something to read.
 */
export function saveEntry(kind, date, text) {
  const all = readAll(kind)
  if (text && text.trim()) all[date] = text
  else delete all[date]
  try {
    localStorage.setItem(storageKey(kind), JSON.stringify(all))
  } catch {
    // Quota, or storage disabled. The caller keeps its in-memory value; losing
    // the write is bad, but throwing here would lose the keystroke too.
  }
  return all
}

/** Dates that actually carry text, newest first. */
export function datesWithEntries(kind) {
  return Object.keys(readAll(kind)).sort().reverse()
}

/** Everything, for getting the record out of one browser. */
export function exportAll() {
  const out = {}
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i)
    if (k && k.startsWith(`${PREFIX}:`)) out[k.slice(PREFIX.length + 1)] = readAll(k.slice(PREFIX.length + 1))
  }
  return out
}
