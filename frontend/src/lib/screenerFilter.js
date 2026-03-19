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

  // Boolean flag filters
  if (filters.trendBaseOnly) {
    result = result.filter(r => r.trend_base === true)
  }
  if (filters.pocketPivotOnly) {
    result = result.filter(r => r.pocket_pivot === true)
  }
  if (filters.momentum97Only) {
    result = result.filter(r => r.momentum_97 === true)
  }

  // Range filters — pct values (stored as decimals in data, user enters whole %)
  const pctRanges = [
    ['dailyPct', 'change_pct'],
    ['weeklyPct', 'perf_1w'],
    ['monthlyPct', 'perf_1m'],
    ['fromOpenPct', 'from_open_pct'],
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

  // ATR-distance ranges (data is R-multiple, user enters R value directly)
  const atrRanges = [
    ['ema21Atr', 'ema21_r'],
    ['sma50Atr', 'sma50_r'],
  ]
  for (const [filterKey, dataKey] of atrRanges) {
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

  // 21EMA Low Dist% (data is decimal, user enters %)
  if (filters.ema21LowDist?.enabled) {
    const f = filters.ema21LowDist
    result = result.filter(r => {
      const val = r.ema21_low_dist != null ? r.ema21_low_dist * 100 : null
      if (val == null) return false
      if (f.min !== '' && f.min != null && val < f.min) return false
      if (f.max !== '' && f.max != null && val > f.max) return false
      return true
    })
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

  // VCS (data is 0-100, no conversion)
  if (filters.vcs?.enabled) {
    const f = filters.vcs
    result = result.filter(r => {
      if (r.vcs == null) return false
      if (f.min !== '' && f.min != null && r.vcs < f.min) return false
      if (f.max !== '' && f.max != null && r.vcs > f.max) return false
      return true
    })
  }

  // DCR% (data is decimal 0-1, user enters 0-100)
  if (filters.dcrPct?.enabled) {
    const f = filters.dcrPct
    result = result.filter(r => {
      const val = r.dcr_pct != null ? r.dcr_pct * 100 : null
      if (val == null) return false
      if (f.min !== '' && f.min != null && val < f.min) return false
      if (f.max !== '' && f.max != null && val > f.max) return false
      return true
    })
  }

  // PP Count (raw integer, no conversion)
  if (filters.ppCount?.enabled) {
    const f = filters.ppCount
    result = result.filter(r => {
      const val = r.pp_count_30d
      if (val == null) return false
      if (f.min !== '' && f.min != null && val < f.min) return false
      if (f.max !== '' && f.max != null && val > f.max) return false
      return true
    })
  }

  // RS score ranges (data is 0-99 integer)
  const rsRanges = [
    ['hScore', 'h_score'],
    ['fScore', 'f_score'],
    ['iScore', 'i_score'],
    ['rs21d', 'rs_21d'],
    ['rs63d', 'rs_63d'],
    ['rs126d', 'rs_126d'],
    ['rsIbd', 'rs_ibd'],
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

  // Percentile ranges (data is 0-1, user enters 0-1 directly)
  const pctileRanges = [
    ['perf1wPctile', 'perf_1w_pctile'],
    ['perf3mPctile', 'perf_3m_pctile'],
  ]
  for (const [filterKey, dataKey] of pctileRanges) {
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
