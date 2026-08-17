import { useEffect, useRef, useState } from 'react'
import { loadEntries, mergeRemote, onWrite, todayKey, weekKey } from '../lib/writingStore'
import { credentials, pullAll, pushMonths } from '../lib/writingSync'

const KINDS = ['trading-recap', 'founders-daily', 'founders-weekly', 'premarket-checklist']

/**
 * Mirror the handwritten entries to the Sheet.
 *
 * Mounted once, at the layout, because the slots are on three different pages
 * and a per-slot sync would pull four times on every navigation.
 *
 * The push is debounced hard — 3 seconds — because the caller is a textarea
 * and each Apps Script round trip is seconds long. Pending months are batched
 * by (kind, month), so a paragraph typed straight through is one write.
 */
export default function useWritingSync() {
  const [status, setStatus] = useState('idle')   // idle | syncing | success | error
  const pending = useRef(new Map())              // kind -> Set(month)
  const timer = useRef(null)

  useEffect(() => {
    if (!credentials()) return                   // nothing configured; stay local

    let dead = false

    // Pull once. `current` differs per kind: the weekly note's "now" is a week.
    setStatus('syncing')
    pullAll().then((res) => {
      if (dead) return
      if (!res.ok) { setStatus('error'); return }
      for (const kind of KINDS) {
        if (!res.byKind[kind]) continue
        mergeRemote(kind, res.byKind[kind],
                    kind === 'founders-weekly' ? weekKey() : todayKey())
      }
      setStatus('success')
      // The merge itself writes, and those writes must not bounce straight
      // back out as pushes — nothing changed that the Sheet does not have.
      pending.current.clear()
    })

    onWrite((kind, _entries, month) => {
      if (!pending.current.has(kind)) pending.current.set(kind, new Set())
      pending.current.get(kind).add(month)
      clearTimeout(timer.current)
      timer.current = setTimeout(flush, 3000)
    })

    async function flush() {
      const batch = [...pending.current.entries()]
      pending.current.clear()
      if (!batch.length) return
      setStatus('syncing')
      let ok = true
      for (const [kind, months] of batch) {
        const res = await pushMonths(kind, loadEntries(kind), [...months])
        if (!res.ok) ok = false
      }
      if (!dead) setStatus(ok ? 'success' : 'error')
    }

    return () => {
      dead = true
      clearTimeout(timer.current)
      onWrite(null)
      // A paragraph typed and the tab closed inside the debounce window would
      // otherwise never reach the Sheet.
      const batch = [...pending.current.entries()]
      for (const [kind, months] of batch) {
        pushMonths(kind, loadEntries(kind), [...months])
      }
    }
  }, [])

  return status
}
