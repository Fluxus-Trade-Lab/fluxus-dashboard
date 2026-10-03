const fin = (v) => typeof v === 'number' && Number.isFinite(v)

/**
 * tick_cycle.json `history` → chart series: rows with all three averages,
 * a fixed y-range over the whole window (so hovering never rescales), and
 * the contiguous runs of each non-neutral band for shading.
 */
export function tickSeries(doc) {
  const rows = (doc?.history ?? []).filter((r) => r?.date && fin(r.ma_high) && fin(r.ma_close) && fin(r.ma_low))
  if (rows.length < 2) return null
  const vals = rows.flatMap((r) => [r.ma_high, r.ma_close, r.ma_low])
  const lo = Math.min(0, ...vals), hi = Math.max(0, ...vals)
  const runs = []
  rows.forEach((r, i) => {
    if (r.band !== 'grind' && r.band !== 'washout') return
    const prev = runs[runs.length - 1]
    if (prev && prev[2] === r.band && prev[1] === i - 1) prev[1] = i
    else runs.push([i, i, r.band])
  })
  return { rows, lo, hi: hi === lo ? lo + 1 : hi, runs }
}
