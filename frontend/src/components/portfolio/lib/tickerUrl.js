/**
 * Build the hash URL for a ticker tear-sheet.
 * @param {string} symbol  Ticker; normalized to uppercase.
 * @returns {string}  e.g. "#/ticker/AAPL"
 */
export function tickerHref(symbol) {
  if (!symbol) return '#/'
  return `#/ticker/${String(symbol).toUpperCase()}`
}

/**
 * Parse a hash like `#/ticker/AAPL` into the ticker symbol.
 * Returns null if the hash doesn't match.
 * @param {string} hash
 * @returns {string|null}
 */
export function parseTickerHash(hash) {
  const m = (hash || '').match(/^#\/ticker\/([A-Z0-9.\-]+)$/i)
  return m ? m[1].toUpperCase() : null
}
