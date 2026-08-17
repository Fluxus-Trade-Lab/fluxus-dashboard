/**
 * Put the handwritten entries in the Sheet, so they survive this browser.
 *
 * The trade log is safe because it lives in two places; the journal did not.
 * localStorage is one machine, one browser, one cleared cache — and these are
 * the only things on the site Andy wrote himself, so they are the only things
 * that cannot be regenerated.
 *
 * NO APPS SCRIPT CHANGE. `update_meta` is already a generic upsert into the
 * Meta tab and `pull` already returns the whole meta object, so this rides the
 * deployment that is live today. Nothing here needs a redeploy.
 *
 * ONE ROW PER MONTH, not per entry. A sheet cell holds 50,000 characters, and
 * a year of daily notes in one cell would eventually hit that ceiling silently
 * — the write just fails and the tail of the year goes missing. Keys are
 * `writing:<kind>:<YYYY-MM>`, about twenty entries each, which also keeps the
 * Meta tab readable by a human.
 *
 * LAST WRITE WINS, per month, and that is a real limitation: two browsers
 * editing the same month can lose the older edit. Stated rather than papered
 * over — the alternative is a merge protocol the Apps Script cannot express.
 */

const PORTFOLIO_KEY = 'portfolio-v4'
const PREFIX = 'writing'
const TIMEOUT_MS = 20000        // the script cold-starts

/** Credentials, from wherever the portfolio put them. Never stored twice. */
export function credentials() {
  try {
    const p = JSON.parse(localStorage.getItem(PORTFOLIO_KEY) || '{}')
    const gasUrl = (p.gasUrl || '').trim()
    const token = (p.syncToken || '').trim()
    return gasUrl && token ? { gasUrl, token } : null
  } catch {
    return null
  }
}

export const monthOf = (date) => String(date).slice(0, 7)     // YYYY-MM
export const metaKey = (kind, month) => `${PREFIX}:${kind}:${month}`

/** Split a { date: value } map into { 'writing:kind:YYYY-MM': {date: value} }. */
export function toMetaRows(kind, entries) {
  const byMonth = {}
  for (const [date, value] of Object.entries(entries || {})) {
    const m = monthOf(date)
    ;(byMonth[m] ||= {})[date] = value
  }
  const out = {}
  for (const [m, v] of Object.entries(byMonth)) out[metaKey(kind, m)] = v
  return out
}

/** The inverse: pull a meta object apart into { kind: { date: value } }. */
export function fromMeta(meta) {
  const out = {}
  for (const [k, raw] of Object.entries(meta || {})) {
    if (!k.startsWith(`${PREFIX}:`)) continue
    const [, kind] = k.split(':')
    if (!kind) continue
    let parsed = raw
    if (typeof raw === 'string') {
      try { parsed = JSON.parse(raw) } catch { continue }
    }
    if (!parsed || typeof parsed !== 'object') continue
    Object.assign(out[kind] ||= {}, parsed)
  }
  return out
}

async function post(gasUrl, body) {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS)
  try {
    // text/plain dodges the CORS preflight Apps Script cannot answer — the
    // same content type the portfolio's own push uses.
    const res = await fetch(gasUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    })
    if (!res.ok) return { ok: false, error: `HTTP ${res.status}` }
    const data = await res.json()
    return data?.ok ? { ok: true } : { ok: false, error: data?.error || 'rejected' }
  } catch (e) {
    return { ok: false, error: e.name === 'AbortError' ? 'timeout' : e.message }
  } finally {
    clearTimeout(timer)
  }
}

/**
 * Push the months an edit actually touched — not the whole history, which
 * would be one write per month per keystroke-batch for the rest of the year.
 */
export async function pushMonths(kind, entries, months) {
  const cred = credentials()
  if (!cred) return { ok: false, error: 'not configured' }
  const rows = toMetaRows(kind, entries)
  const wanted = [...new Set(months)]
  const results = await Promise.all(wanted.map((m) => {
    const key = metaKey(kind, m)
    // A month emptied of every entry still needs a write, to clear the cell.
    const value = JSON.stringify(rows[key] || {})
    return post(cred.gasUrl, { action: 'update_meta', token: cred.token, key, value })
  }))
  const bad = results.find((r) => !r.ok)
  return bad || { ok: true }
}

/** Read every writing key back out of the Sheet. */
export async function pullAll() {
  const cred = credentials()
  if (!cred) return { ok: false, error: 'not configured' }
  const url = `${cred.gasUrl}?action=pull&token=${encodeURIComponent(cred.token)}`
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS)
  try {
    const res = await fetch(url, { signal: ctrl.signal })
    if (!res.ok) return { ok: false, error: `HTTP ${res.status}` }
    const data = await res.json()
    if (!data?.ok) return { ok: false, error: data?.error || 'pull rejected' }
    return { ok: true, byKind: fromMeta(data.meta) }
  } catch (e) {
    return { ok: false, error: e.name === 'AbortError' ? 'timeout' : e.message }
  } finally {
    clearTimeout(timer)
  }
}
