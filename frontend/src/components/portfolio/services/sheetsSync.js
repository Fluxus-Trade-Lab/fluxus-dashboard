/**
 * Google Sheets sync service.
 * Reads/writes portfolio data via the Google Apps Script web app.
 */

const TIMEOUT_MS = 15000 // GAS cold start can take 6s

/**
 * Pull all data from Google Sheets.
 * Returns { ok, stockTrades, optionsTrades, meta } or { ok: false, error }
 *
 * `retryOnTimeout` exists for ONE caller: the pull that runs when the page
 * opens. The data side traced Andy's red ✕ to a cold start (2026-08-24,
 * DATA_CONTRACTS §七) — the first request of the day boots the Apps Script
 * container, overruns 15s, and the page has worn an error mark ever since
 * while nothing was actually broken. A second attempt lands on the container
 * the first one just warmed, so it is not a hopeful retry: the first request
 * did the expensive part.
 *
 * ONLY on Timeout. An HTTP error or a bad token is a real answer and repeating
 * it just doubles the wait before the page tells the truth.
 */
export async function pullFromSheets(gasUrl, token, { retryOnTimeout = false } = {}) {
  const first = await pullOnce(gasUrl, token)
  if (first.ok || !retryOnTimeout || first.error !== 'Timeout') return first
  return pullOnce(gasUrl, token)
}

async function pullOnce(gasUrl, token) {
  const url = `${gasUrl}?action=pull&token=${encodeURIComponent(token)}`
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)

  try {
    const res = await fetch(url, { signal: controller.signal })
    clearTimeout(timer)
    if (!res.ok) return { ok: false, error: `HTTP ${res.status}` }
    const data = await res.json()
    if (!data.ok) return { ok: false, error: data.error || 'Pull failed' }
    return data
  } catch (err) {
    clearTimeout(timer)
    if (err.name === 'AbortError') return { ok: false, error: 'Timeout' }
    return { ok: false, error: err.message }
  }
}

/**
 * Push all data to Google Sheets (full replace).
 * Returns { ok } or { ok: false, error }
 */
export async function pushToSheets(gasUrl, token, { stockTrades, optionsTrades, meta }) {
  const url = `${gasUrl}?token=${encodeURIComponent(token)}`
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)

  try {
    // Use text/plain to avoid CORS preflight (GAS doesn't support OPTIONS)
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' },
      body: JSON.stringify({ action: 'sync_all', token, stockTrades, optionsTrades, meta }),
      signal: controller.signal,
    })
    clearTimeout(timer)
    if (!res.ok) return { ok: false, error: `HTTP ${res.status}` }
    const data = await res.json()
    return data
  } catch (err) {
    clearTimeout(timer)
    if (err.name === 'AbortError') return { ok: false, error: 'Timeout' }
    return { ok: false, error: err.message }
  }
}

/**
 * Test connection -- pull and check response.
 */
export async function testConnection(gasUrl, token) {
  const result = await pullFromSheets(gasUrl, token)
  if (result.ok) {
    return {
      ok: true,
      stockTradeCount: result.stockTrades?.length ?? 0,
      optionsTradeCount: result.optionsTrades?.length ?? 0,
    }
  }
  return result
}
