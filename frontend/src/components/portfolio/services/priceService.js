/**
 * Price service — calls the Google Apps Script proxy.
 * The GAS script forwards requests to Yahoo Finance (server-side, no CORS issues).
 */

/**
 * Fetch current quotes for multiple tickers in one call.
 * Returns { AAPL: { price, prevClose, change, changePercent }, ... }
 */
export async function fetchQuotes(symbols, gasUrl) {
  if (!gasUrl || !symbols.length) return {}
  const url = `${gasUrl}?action=quotes&symbols=${symbols.join(',')}`
  const res = await fetch(url)
  if (!res.ok) throw new Error(`GAS quotes failed: ${res.status}`)
  return res.json()
}

/**
 * Fetch daily candle history for a single ticker.
 * Returns [{ date, close }, ...]
 */
export async function fetchHistory(symbol, from, to, gasUrl) {
  if (!gasUrl) return []
  const url = `${gasUrl}?action=history&symbol=${symbol}&from=${from}&to=${to}`
  const res = await fetch(url)
  if (!res.ok) throw new Error(`GAS history failed: ${res.status}`)
  return res.json()
}

/**
 * Fetch daily candle history for multiple tickers in one GAS call.
 * Returns { AAPL: [{date, close}, ...], MSFT: [...] }
 */
export async function fetchBatchHistory(symbols, from, to, gasUrl) {
  if (!gasUrl || !symbols.length) return {}
  const url = `${gasUrl}?action=batch_history&symbols=${symbols.join(',')}&from=${from}&to=${to}`
  const res = await fetch(url)
  if (!res.ok) throw new Error(`GAS batch_history failed: ${res.status}`)
  return res.json()
}
