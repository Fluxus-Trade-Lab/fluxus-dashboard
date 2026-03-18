import { todayStr } from './portfolioFormat'

const esc = (v) => {
  const s = String(v ?? '')
  return s.includes(',') || s.includes('"') ? '"' + s.replace(/"/g, '""') + '"' : s
}

const TRADE_HEADERS = [
  'Ticker', 'Direction', 'Sector', 'Entry Date', 'Entry Price',
  'Original Qty', 'Current Qty', 'Stop Price', 'Closed',
  'Trim1 Date', 'Trim1 Price', 'Trim1 Qty', 'Trim1 Type',
  'Trim2 Date', 'Trim2 Price', 'Trim2 Qty', 'Trim2 Type',
  'Trim3 Date', 'Trim3 Price', 'Trim3 Qty', 'Trim3 Type',
]

export function generateCSV(trades, startingCapital) {
  const rows = trades.map(t => {
    const tr = t.trims || []
    return [
      t.ticker, t.direction, t.sector || '', t.entryDate, t.entryPrice,
      t.originalQty, t.currentQty, t.stopPrice, t.isClosed ? 'YES' : 'NO',
      tr[0]?.date || '', tr[0]?.price || '', tr[0]?.qty || '', tr[0]?.type || '',
      tr[1]?.date || '', tr[1]?.price || '', tr[1]?.qty || '', tr[1]?.type || '',
      tr[2]?.date || '', tr[2]?.price || '', tr[2]?.qty || '', tr[2]?.type || '',
    ]
  })

  return [
    '_meta,startingCapital,' + startingCapital,
    '_meta,exportDate,' + todayStr(),
    TRADE_HEADERS.map(esc).join(','),
    ...rows.map(r => r.map(esc).join(',')),
  ].join('\n')
}

function parseTradeRows(rows) {
  return rows.filter(r => r.Ticker || r.ticker || r[0]).map((r, i) => {
    const get = (key, idx) => r[key] ?? r[idx] ?? ''
    const trims = []
    for (let n = 1; n <= 3; n++) {
      const d = get(`Trim${n} Date`, 8 + (n - 1) * 4 + 1)
      const p = get(`Trim${n} Price`, 8 + (n - 1) * 4 + 2)
      const q = get(`Trim${n} Qty`, 8 + (n - 1) * 4 + 3)
      const tp = get(`Trim${n} Type`, 8 + (n - 1) * 4 + 4)
      if (d && p && q) {
        trims.push({ date: String(d), price: parseFloat(p), qty: parseInt(q), type: String(tp) || 'trim_1_3' })
      }
    }
    const oq = parseInt(get('Original Qty', 5)) || 0
    return {
      id: Date.now().toString() + '_' + i,
      ticker: String(get('Ticker', 0) || '').toUpperCase(),
      direction: String(get('Direction', 1) || 'long').toLowerCase(),
      sector: String(get('Sector', 2) || 'Unknown'),
      entryDate: String(get('Entry Date', 3) || todayStr()),
      entryPrice: parseFloat(get('Entry Price', 4)) || 0,
      originalQty: oq,
      currentQty: parseInt(get('Current Qty', 6)) ?? oq,
      stopPrice: parseFloat(get('Stop Price', 7)) || 0,
      trims,
      isClosed: String(get('Closed', 8)).toUpperCase() === 'YES',
    }
  })
}

/**
 * Parse CSV text — supports both old ## format and new _meta format.
 * Returns { trades, startingCapital, dailyPrices }
 */
export function parseCSV(text) {
  const lines = text.split('\n').map(l => l.trim()).filter(Boolean)
  let capital = null
  const dailyPrices = {}

  // Detect format
  const isOldFormat = lines.some(l => l.startsWith('##'))

  if (isOldFormat) {
    // Old format: ## Settings / ## Trades / ## PriceCache sections
    const metaLines = lines.filter(
      l => !l.startsWith('##') && lines.indexOf(l) < lines.findIndex(l2 => l2.startsWith('Ticker') || l2.startsWith('## Trades'))
    )
    metaLines.forEach(l => {
      const parts = l.split(',')
      if (parts[0] === 'Starting Capital') capital = parseFloat(parts[1])
    })

    // Parse trades section
    const tradeHeaderIdx = lines.findIndex(l => l.startsWith('Ticker'))
    if (tradeHeaderIdx === -1) return { trades: [], startingCapital: capital }

    const headers = lines[tradeHeaderIdx].split(',').map(h => h.trim().replace(/^"|"$/g, ''))
    let tradeEndIdx = lines.length
    for (let i = tradeHeaderIdx + 1; i < lines.length; i++) {
      if (lines[i].startsWith('##')) { tradeEndIdx = i; break }
    }
    const dataRows = lines.slice(tradeHeaderIdx + 1, tradeEndIdx)
      .filter(l => l && !l.startsWith('##'))
      .map(l => {
        const vals = l.split(',').map(v => v.trim().replace(/^"|"$/g, ''))
        const obj = {}
        headers.forEach((h, i) => { obj[h] = vals[i] || '' })
        return obj
      })

    // Parse PriceCache section (old format stores cached prices)
    const pcIdx = lines.findIndex(l => l === '## PriceCache')
    if (pcIdx !== -1) {
      for (let i = pcIdx + 2; i < lines.length; i++) {
        if (lines[i].startsWith('##')) break
        const parts = lines[i].split(',').map(v => v.trim().replace(/^"|"$/g, ''))
        if (parts[0] && parts[1] && parts[2]) {
          dailyPrices[parts[0] + ':' + parts[1]] = parseFloat(parts[2])
        }
      }
    }

    return { trades: parseTradeRows(dataRows), startingCapital: capital, dailyPrices }
  }

  // New format: _meta rows + flat CSV
  const metaRows = lines.filter(l => l.startsWith('_meta,'))
  metaRows.forEach(l => {
    const parts = l.split(',')
    if (parts[1] === 'startingCapital') capital = parseFloat(parts[2])
  })

  const headerIdx = lines.findIndex(l => l.startsWith('Ticker'))
  if (headerIdx === -1) return { trades: [], startingCapital: capital, dailyPrices }

  const headers = lines[headerIdx].split(',').map(h => h.trim().replace(/^"|"$/g, ''))
  const dataRows = lines.slice(headerIdx + 1)
    .filter(l => l && !l.startsWith('_meta'))
    .map(l => {
      const vals = l.split(',').map(v => v.trim().replace(/^"|"$/g, ''))
      const obj = {}
      headers.forEach((h, i) => { obj[h] = vals[i] || '' })
      return obj
    })

  return { trades: parseTradeRows(dataRows), startingCapital: capital, dailyPrices }
}

export function downloadFile(content, filename, type) {
  try {
    const blob = new Blob([content], { type })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.style.display = 'none'
    document.body.appendChild(a)
    a.click()
    setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url) }, 2000)
    return true
  } catch (e) {
    console.error('Download failed:', e)
    return false
  }
}
