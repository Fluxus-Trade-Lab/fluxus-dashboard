/**
 * The Scan vocabulary: every list the pipeline already publishes, as a set.
 *
 * A scan here is not a query — it is the output file a screener wrote this
 * session, reduced to "which tickers are on it". The screener JSONs use three
 * container shapes (a flat list, buckets keyed by score, results), which is a
 * fact about their authors, not about the data; this module absorbs the
 * difference so the page sees one shape.
 *
 * Day-sensitive scans (EP, 4% gainers, vol-up) are legitimately empty on quiet
 * sessions. An empty scan stays in the vocabulary and shows its zero — a scan
 * that found nothing today is a reading, not a malfunction.
 */

export const SCAN_DEFS = [
  { key: 'all',            label: 'All' },
  { key: 'confluence',     label: 'Confluence' },
  { key: 'momentum_97',    label: 'Momentum 97',   container: 'buckets' },
  { key: 'healthy_charts', label: 'Healthy charts', container: 'rs_groups' },
  { key: 'ema21_watch',    label: 'EMA21',          container: 'rs_groups' },
  { key: 'vcp',            label: 'VCP',            container: 'results' },
  { key: 'episodic_pivot', label: 'EP',             container: 'tickers' },
  { key: 'gainers_4pct',   label: '4% gainers',     container: 'tickers' },
  { key: 'vol_up_gainers', label: 'Vol-up',         container: 'tickers' },
]

/** Tickers named by one scan file, whatever container shape it uses. */
export function scanTickers(json, container) {
  const v = json?.[container]
  if (!v) return new Set()
  const rows = Array.isArray(v) ? v : Object.values(v).flat()
  return new Set(rows.map((r) => r?.ticker).filter(Boolean))
}
