/**
 * What a writing slot can truthfully say about its own saving.
 *
 * Debounced autosave is invisible, which is fine until it matters — and this
 * is the one place on the site holding words that cannot be regenerated. Andy:
 * "我在书写的时候不确定已经同步完成". A Save button is half the answer; the other
 * half is that saving here is TWO events, and a control that reports one of
 * them as if it were both is worse than none.
 *
 *   local  — in this browser. Immediate, and enough not to lose a sentence to
 *            a closed tab.
 *   sheet  — in the Meta tab. Seconds away through Apps Script, and the only
 *            copy that survives this machine.
 *
 * `sheet` stays 'off' when no credentials are configured, so a slot never
 * promises a sync that was never going to happen.
 */

const listeners = new Set()
let state = { local: 'idle', sheet: 'off', at: null }

export function getStatus() { return state }

export function subscribe(fn) {
  listeners.add(fn)
  fn(state)
  return () => listeners.delete(fn)
}

export function setStatus(patch) {
  state = { ...state, ...patch }
  for (const fn of listeners) {
    try { fn(state) } catch { /* a bad listener must not stop the others */ }
  }
}

/** Local write landed. */
export function markLocal() {
  setStatus({ local: 'saved', at: Date.now() })
}

/** Sheet round trip. 'syncing' | 'saved' | 'error' | 'off'. */
export function markSheet(value) {
  setStatus({ sheet: value })
}
