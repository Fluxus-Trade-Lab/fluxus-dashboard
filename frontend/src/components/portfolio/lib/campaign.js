/**
 * Group trades into pyramid campaigns.
 * Same (ticker, direction); consecutive entries within 60 business days.
 *
 * @param {Array} trades  expects fields: id, ticker, direction, entryDate (ISO),
 *                        entryPrice, originalQty, stopPrice, currentQty, trims
 * @returns {Array<Campaign>}  campaign = { id, ticker, direction, layers, blendedEntry,
 *                                          totalOriginalQty, totalCurrentQty, totalRDollars,
 *                                          openLayersCount, firstEntry, lastEntry }
 */
export function groupByCampaigns(trades) {
  const byKey = new Map()
  for (const t of trades) {
    const key = `${t.ticker}__${t.direction}`
    if (!byKey.has(key)) byKey.set(key, [])
    byKey.get(key).push(t)
  }

  const campaigns = []
  for (const [, list] of byKey) {
    const sorted = [...list].sort((a, b) => a.entryDate.localeCompare(b.entryDate))
    let cur = [sorted[0]]
    for (let i = 1; i < sorted.length; i++) {
      const prev = cur[cur.length - 1]
      if (businessDaysBetween(prev.entryDate, sorted[i].entryDate) <= 60) {
        cur.push(sorted[i])
      } else {
        campaigns.push(buildCampaign(cur))
        cur = [sorted[i]]
      }
    }
    campaigns.push(buildCampaign(cur))
  }
  return campaigns
}

function buildCampaign(layers) {
  const first = layers[0]
  const totalOriginalQty = layers.reduce((s, l) => s + l.originalQty, 0)
  const totalCurrentQty = layers.reduce((s, l) => s + l.currentQty, 0)
  const blendedEntry = totalOriginalQty > 0
    ? layers.reduce((s, l) => s + l.entryPrice * l.originalQty, 0) / totalOriginalQty
    : 0
  // Campaign-level 1R: sum of each layer's initial-stop risk. Trailing a layer's
  // live stop must never rewrite the campaign's R denominator.
  const totalRDollars = layers.reduce(
    (s, l) => s + Math.abs(l.entryPrice - (l.initialStop ?? l.stopPrice)) * l.originalQty,
    0
  )
  const openLayersCount = layers.filter(l => l.currentQty > 0).length
  return {
    id: `campaign__${first.ticker}__${first.direction}__${first.entryDate}`,
    ticker: first.ticker,
    direction: first.direction,
    layers,
    blendedEntry,
    totalOriginalQty,
    totalCurrentQty,
    totalRDollars,
    openLayersCount,
    firstEntry: first.entryDate,
    lastEntry: layers[layers.length - 1].entryDate,
  }
}

/** Naive business-days approximation: total days × 5/7. */
function businessDaysBetween(a, b) {
  const ad = new Date(a)
  const bd = new Date(b)
  const days = Math.abs(Math.round((bd - ad) / 86400000))
  return Math.round(days * 5 / 7)
}
