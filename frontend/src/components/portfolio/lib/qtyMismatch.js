/**
 * Rows whose `currentQty` disagrees with `originalQty − Σtrims.qty` — the
 * seam that let this dashboard and the daily recap print two different
 * return% off one Sheet (T-0924-100/103, incident
 * 2026-09-24_one_sheet_two_return_pcts.md). The Sheet keeps `currentQty` by
 * hand and derives nothing; nothing in GAS checks that the two agree, so one
 * hand edit to either splits them silently and both products still look
 * healthy on their own.
 *
 * Mirrors `pipeline/content/recap/build_pack.py::_qty_mismatch` field for
 * field so the two sides can't drift into checking different things.
 *
 * All trims count, not only ones before some as-of date: `currentQty` is a
 * live number with every logged trim already taken out of it, so the
 * identity is date-independent — windowing it would invent violations on a
 * back-dated view.
 *
 * Never a share count (Andy 2026-09-13「管线只做 R 和 %，不写股数和美元」): the
 * gap is reported as a percent of the original position.
 *
 * @param {Array<{id: string, ticker: string, direction: string, entryDate: string, originalQty: number, currentQty: number, trims?: Array<{qty: number}>}>} trades
 * @returns {Array<{id: string, ticker: string, direction: string, entryDate: string, gapPctOfPosition: number|null, sheetSays: 'more held than the trim log implies'|'less held than the trim log implies'}>}
 */
export function computeQtyMismatches(trades) {
  const out = []
  for (const t of trades || []) {
    const trims = t.trims || []
    const derived = t.originalQty - trims.reduce((s, tr) => s + tr.qty, 0)
    if (t.currentQty === derived) continue
    out.push({
      id: t.id,
      ticker: t.ticker,
      direction: t.direction,
      entryDate: t.entryDate,
      gapPctOfPosition: t.originalQty
        ? Math.round(((t.currentQty - derived) / t.originalQty) * 1000) / 10
        : null,
      sheetSays: t.currentQty > derived
        ? 'more held than the trim log implies'
        : 'less held than the trim log implies',
    })
  }
  return out.sort((a, b) => (
    a.entryDate === b.entryDate
      ? a.ticker.localeCompare(b.ticker)
      : a.entryDate < b.entryDate ? -1 : 1
  ))
}
