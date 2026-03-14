/**
 * Apply filters to universe rows. Returns filtered array.
 * Each range filter is { enabled, min, max }.
 * Values in universe are decimals (0.05 = 5%) for pct fields,
 * except RS scores which are 0-99 integers, and adr_pct which is already in %.
 */
export function applyFilters(rows, filters, tickerSearch) {
  if (!rows) return []

  let result = rows

  // Ticker search
  if (tickerSearch) {
    const q = tickerSearch.toUpperCase()
    result = result.filter(r => r.ticker?.toUpperCase().includes(q))
  }

  // Market cap (filter value in billions, data in raw number)
  if (filters.marketCapEnabled !== false && filters.marketCapMin) {
    const minCap = filters.marketCapMin * 1e9
    result = result.filter(r => r.market_cap != null && r.market_cap >= minCap)
  }

  // Volume (filter value in millions, data in raw number)
  if (filters.vol50dEnabled !== false && filters.vol50dMin) {
    const minVol = filters.vol50dMin * 1e6
    result = result.filter(r => r.avg_volume != null && r.avg_volume >= minVol)
  }

  // Exclude healthcare
  if (filters.excludeHealthcare) {
    result = result.filter(r => r.sector !== 'Healthcare')
  }

  // Range filters — pct values (stored as decimals in data, user enters whole %)
  const pctRanges = [
    ['dailyPct', 'change_pct'],
    ['weeklyPct', 'perf_1w'],
    ['monthlyPct', 'perf_1m'],
  ]
  for (const [filterKey, dataKey] of pctRanges) {
    const f = filters[filterKey]
    if (f?.enabled) {
      result = result.filter(r => {
        const val = r[dataKey] != null ? r[dataKey] * 100 : null
        if (val == null) return false
        if (f.min !== '' && f.min != null && val < f.min) return false
        if (f.max !== '' && f.max != null && val > f.max) return false
        return true
      })
    }
  }

  // MA distance ranges (data is decimal, user enters %)
  const maRanges = [
    ['sma20Dist', 'sma20_dist'],
    ['sma50Dist', 'sma50_dist'],
    ['sma200Dist', 'sma200_dist'],
  ]
  for (const [filterKey, dataKey] of maRanges) {
    const f = filters[filterKey]
    if (f?.enabled) {
      result = result.filter(r => {
        const val = r[dataKey] != null ? r[dataKey] * 100 : null
        if (val == null) return false
        if (f.min !== '' && f.min != null && val < f.min) return false
        if (f.max !== '' && f.max != null && val > f.max) return false
        return true
      })
    }
  }

  // ADR% (data already in %, no conversion needed)
  if (filters.adrPct?.enabled) {
    const f = filters.adrPct
    result = result.filter(r => {
      if (r.adr_pct == null) return false
      if (f.min !== '' && f.min != null && r.adr_pct < f.min) return false
      if (f.max !== '' && f.max != null && r.adr_pct > f.max) return false
      return true
    })
  }

  // RS score ranges (data is 0-99 integer)
  const rsRanges = [
    ['rsIbd', 'rs_ibd'],
    ['rs63d', 'rs_63d'],
  ]
  for (const [filterKey, dataKey] of rsRanges) {
    const f = filters[filterKey]
    if (f?.enabled) {
      result = result.filter(r => {
        if (r[dataKey] == null) return false
        if (f.min !== '' && f.min != null && r[dataKey] < f.min) return false
        if (f.max !== '' && f.max != null && r[dataKey] > f.max) return false
        return true
      })
    }
  }

  // 52W high distance (data is decimal, user enters %)
  if (filters.high52wDist?.enabled) {
    const f = filters.high52wDist
    result = result.filter(r => {
      const val = r.high_52w_dist != null ? r.high_52w_dist * 100 : null
      if (val == null) return false
      if (f.min !== '' && f.min != null && val < f.min) return false
      if (f.max !== '' && f.max != null && val > f.max) return false
      return true
    })
  }

  // Relative volume filter
  if (filters.relVolume?.enabled) {
    const f = filters.relVolume
    result = result.filter(r => {
      if (r.rel_volume == null) return false
      if (f.min !== '' && f.min != null && r.rel_volume < f.min) return false
      if (f.max !== '' && f.max != null && r.rel_volume > f.max) return false
      return true
    })
  }

  return result
}
