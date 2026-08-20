import { useCallback, useMemo, useSyncExternalStore } from 'react'
import { useWatchlist } from './useWatchlist'

const KEY = 'page3-shortlist'

/**
 * The names taken off page 3 this morning.
 *
 * PRODUCT.md names the morning's ACTION in one line — "就地做今天的短名单 …
 * 页面需要选中 / 标记 / 带走的机制，并且要记住选了谁" — and until now no part
 * of this app had it. You could read three pages of evidence and leave with
 * nothing in your hand.
 *
 * ONE STORE, NOT ONE PER CALLER. This began as a plain useState hook and was
 * wrong the first time it was used twice: the chart card added a name, its own
 * copy updated, and the tray beside it went on saying the list was empty. Two
 * components holding two states over one fact is the same defect this codebase
 * chases out of its colour encodings, and it has the same cure — a single
 * source everyone subscribes to. localStorage is the persistence, never the
 * channel between two live components.
 *
 * A SHORTLIST BELONGS TO A DATE. It is not a watchlist and not a portfolio; it
 * is what you decided to look at on one session's data. So it is stored with
 * the date of the file it was made against, and when a newer file lands the
 * list does NOT silently carry over wearing today's clothes — it says which
 * close it was made on and offers to clear. A stale list presented as current
 * is the same failure as a stale price: right numbers, wrong clock.
 *
 * WHY EACH ENTRY KEEPS ITS REASON. A bare ticker is unreviewable a week later:
 * the whole value of writing the list down is being able to ask "was that a
 * good call" — which needs what the name looked like when it was taken, not
 * what it looks like now. So the readings are frozen at the moment of adding,
 * and the tray says so rather than refreshing them.
 *
 * STORAGE IS LOCAL, FOR NOW. PRODUCT.md leaves the location undecided
 * (localStorage vs the Google Sheet the portfolio already syncs to). This is
 * localStorage, which needs nothing from anybody and works today; the shape
 * below is a plain array of records, so a Sheet writer is an addition rather
 * than a rewrite. It does mean the list does not follow you to another
 * machine, and the tray says that out loud rather than letting you find out.
 */

function read() {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) ?? 'null')
    if (!raw || !Array.isArray(raw.names)) return null
    return { date: raw.date ?? null, names: raw.names.filter((n) => n && n.ticker) }
  } catch {
    return null
  }
}

let snapshot = read()
const subs = new Set()

function commit(next) {
  snapshot = next
  try {
    if (next?.names?.length) localStorage.setItem(KEY, JSON.stringify(next))
    else localStorage.removeItem(KEY)
  } catch { /* private mode — the list just does not survive the reload */ }
  subs.forEach((fn) => fn())
}

const subscribe = (fn) => { subs.add(fn); return () => subs.delete(fn) }
const getSnapshot = () => snapshot
/** the same object on the server, so the snapshot is stable there too */
const getServerSnapshot = () => null

export function useShortlist() {
  const { data } = useWatchlist()
  const fileDate = data?.date ?? null
  const store = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)

  const names = store?.names ?? []
  const madeOn = store?.date ?? null
  /** made against an older close than the one on screen */
  const stale = Boolean(madeOn && fileDate && madeOn !== fileDate && names.length)

  const has = useCallback((t) => (snapshot?.names ?? []).some((n) => n.ticker === t), [store])

  /**
   * `row` is whatever the caller was looking at — the panel row, so the entry
   * carries the same readings the page showed. Adding a name the file no
   * longer describes is still allowed; the missing fields stay missing rather
   * than being filled with zeroes.
   */
  const add = useCallback((ticker, row = {}, from = null) => {
    if (!ticker) return
    const prev = snapshot?.names ?? []
    if (prev.some((n) => n.ticker === ticker)) return
    commit({
      date: fileDate ?? snapshot?.date ?? null,
      names: [...prev, {
        ticker,
        from,
        group: row.group ?? null,
        group_state: row.group_state ?? null,
        rs_1m: row.rs_1m ?? null,
      }],
    })
  }, [fileDate])

  const remove = useCallback((ticker) => {
    const kept = (snapshot?.names ?? []).filter((n) => n.ticker !== ticker)
    commit(kept.length ? { ...snapshot, names: kept } : null)
  }, [])

  const clear = useCallback(() => commit(null), [])

  /** Every name on today's file, with its readings — what the picker searches. */
  const universe = useMemo(() => {
    const out = new Map()
    for (const z of data?.zones ?? []) {
      for (const p of z.panels ?? []) {
        if (!p.measured) continue
        for (const r of p.tickers ?? []) {
          if (!out.has(r.ticker)) out.set(r.ticker, { ...r, from: p.label })
        }
      }
    }
    return [...out.values()]
  }, [data])

  return { names, madeOn, fileDate, stale, has, add, remove, clear, universe }
}
