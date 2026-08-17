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
 * DURABILITY. localStorage is the working copy; the Sheet is the record. Every
 * write pushes the month it touched (see writingSync), and a pull at load
 * brings back anything written elsewhere. localStorage alone is one browser on
 * one machine, and these are the only things on the site that cannot be
 * regenerated — they were written by hand.
 *
 * MERGE, stated rather than fudged: on pull, the Sheet wins for PAST dates and
 * the local copy wins for the CURRENT one. Andy writes today and reads the
 * past, so this propagates an entry written on another machine without ever
 * clobbering the sentence being typed right now. Two machines editing the same
 * past day is still last-write-wins; no merge protocol fits in a sheet cell.
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
 * One structured entry — the checklist keeps six answers and a note, not a
 * string. Same store, same keying; only the shape of the value differs.
 */
export function loadRecord(kind, date, fallback = null) {
  const v = readAll(kind)[date]
  return v && typeof v === 'object' ? v : fallback
}

/** Write a structured entry. Pass null, or let `isEmpty` say so, to delete. */
export function saveRecord(kind, date, value, isEmpty = (v) => !v) {
  const all = readAll(kind)
  if (value && !isEmpty(value)) all[date] = value
  else delete all[date]
  try {
    localStorage.setItem(storageKey(kind), JSON.stringify(all))
  } catch { /* see saveEntry */ }
  notify(kind, date)
  return all
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
  notify(kind, date)
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


/* ── Sheet mirror ──────────────────────────────────────────────────────── */

let pushHook = null

/**
 * Register the pusher. Injected rather than imported so the store stays a
 * plain module — the test suite, and any page that never syncs, load it
 * without pulling a network client in behind them.
 */
export function onWrite(fn) { pushHook = fn }

function notify(kind, date) {
  if (pushHook) {
    try { pushHook(kind, readAll(kind), String(date).slice(0, 7)) } catch { /* never block a save */ }
  }
}

/**
 * Fold entries pulled from the Sheet into the local copy.
 * Past dates take the remote value; `current` keeps whatever is local.
 */
export function mergeRemote(kind, remote, current) {
  if (!remote || typeof remote !== 'object') return readAll(kind)
  const local = readAll(kind)
  const merged = { ...local }
  for (const [date, value] of Object.entries(remote)) {
    if (date === current && Object.prototype.hasOwnProperty.call(local, date)) continue
    merged[date] = value
  }
  try {
    localStorage.setItem(storageKey(kind), JSON.stringify(merged))
  } catch { /* see saveEntry */ }
  return merged
}
