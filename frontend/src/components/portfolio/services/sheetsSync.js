/**
 * Google Sheets sync service.
 * Reads/writes portfolio data via the Google Apps Script web app.
 */

const TIMEOUT_MS = 15000 // GAS cold start can take 6s

/**
 * Pull all data from Google Sheets.
 * Returns { ok, stockTrades, optionsTrades, meta } or { ok: false, error }
 */
export async function pullFromSheets(gasUrl, token) {
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
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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
