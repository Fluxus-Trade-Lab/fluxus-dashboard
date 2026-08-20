/**
 * The other half of the veto loop — the client side of it.
 *
 * A ✗ has to reach the sheet or it is not learning material. What it must NOT
 * do is ride the existing push: `pushToSheets` sends `action: 'sync_all'` with
 * the whole portfolio attached, so one veto would carry a possibly-stale copy
 * of every trade and two open tabs would clobber each other. This sends ONE
 * record and touches nothing else (DATA_CONTRACTS §七).
 *
 * LOCAL IS THE TRUTH, THE PUSH IS A MIRROR. Every mark is written to
 * localStorage first and stays there whether or not it reaches the sheet, with
 * a `syncedAt` stamp recording that it did. Unsent records are retried when the
 * page opens or the next mark is made — never on a timer, because an endpoint
 * that does not exist yet should not be hammered. A judgement Andy made is not
 * allowed to disappear because a network was down.
 *
 * The GAS action does not exist yet. Until it does, every push fails, the marks
 * stay local, and `state()` says so — which is what the page prints. That is
 * the honest arrangement: a button that looks saved and feeds nothing is worse
 * than no button.
 */

/** Credentials live in the portfolio's store; this page is outside its
 *  provider, so it reads the same key rather than duplicating a settings UI.
 *  Named loudly because a silent reach into another feature's storage is the
 *  kind of coupling that rots. */
const PORTFOLIO_STORE = 'portfolio-v4'

export function credentials() {
  try {
    const p = JSON.parse(localStorage.getItem(PORTFOLIO_STORE) || 'null')
    const url = p?.gasUrl || ''
    const token = p?.syncToken || ''
    return url && token ? { url, token } : null
  } catch { return null }
}

/** One record, in the shape the sheet's Shortlist tab takes.
 *  Idempotency is the server's, on (ticker, added_date) — the client's job is
 *  to always send those two so it CAN be idempotent. */
export function record(date, ticker, entry, seat, readings) {
  return {
    ticker,
    added_date: date,
    status: entry?.mark ?? 'noted',      // vetoed | starred | noted
    note: entry?.note ?? '',
    seat: seat ?? null,
    readings: readings ?? null,
  }
}

const TIMEOUT_MS = 12000

/** POST one record. Resolves {ok} or {ok:false, error} — never throws. */
export async function pushOne(rec, creds = credentials()) {
  if (!creds) return { ok: false, error: 'no-credentials' }
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
  try {
    const res = await fetch(`${creds.url}?token=${encodeURIComponent(creds.token)}`, {
      method: 'POST',
      // text/plain avoids the CORS preflight GAS cannot answer — same reason
      // the portfolio's own push does it
      headers: { 'Content-Type': 'text/plain' },
      body: JSON.stringify({ action: 'shortlist_upsert', token: creds.token, ...rec }),
      signal: controller.signal,
    })
    clearTimeout(timer)
    if (!res.ok) return { ok: false, error: `HTTP ${res.status}` }
    const data = await res.json().catch(() => null)
    // An unknown action must not read as success. GAS answers a request it does
    // not recognise with a 200 and its own shape, so "no explicit ok" is a
    // failure here rather than a shrug.
    if (data?.ok === true) return { ok: true }
    return { ok: false, error: data?.error || 'action-not-implemented' }
  } catch (err) {
    clearTimeout(timer)
    return { ok: false, error: err.name === 'AbortError' ? 'timeout' : err.message }
  }
}

/**
 * What the page says about the loop.
 * Three states, and they are three different sentences:
 *   off       no GAS credentials — nothing was ever going to send
 *   pending   credentials exist, records are waiting (the action is missing, or it failed)
 *   synced    everything made today has reached the sheet
 */
export function state({ hasCreds, unsent, lastError }) {
  if (!hasCreds) return { kind: 'off', unsent, lastError: null }
  if (unsent > 0) return { kind: 'pending', unsent, lastError }
  return { kind: 'synced', unsent: 0, lastError: null }
}
