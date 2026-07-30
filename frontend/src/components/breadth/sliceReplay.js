// Pure adapter: turn the replay book into exactly the props the live
// breadth components already consume, truncated to `date`. No recomputation
// happens here — verdicts come precomputed from the Python engine.

const HISTORY_WINDOW = 100

function cutSeries(block, keep) {
  return {
    candles: block.candles.slice(0, keep),
    sma20: block.sma20.slice(0, keep),
    sma50: block.sma50.slice(0, keep),
    sma200: block.sma200.slice(0, keep),
  }
}

function healthAt(block, date) {
  const keep = block.candles.filter((c) => c.date <= date).length
  if (!keep) return null
  const sigs = block.signals_history.filter((s) => s.date <= date)
  const last = sigs[sigs.length - 1]
  return {
    ...cutSeries(block, keep),
    danger: last
      ? { signals: last.signals, count: last.count, date: last.date }
      : { signals: {}, count: 0 },
    warn_history: sigs.map((s) => ({ date: s.date, count: s.count })),
  }
}

export function sliceToDate(replay, date) {
  if (!replay?.verdicts?.[date]) return null

  const upto = replay.dates.filter((d) => d <= date)
  const windowDates = upto.slice(-HISTORY_WINDOW)
  const rows = windowDates.map((d) => replay.rows[d])
  const last = rows[rows.length - 1] ?? {}

  const breadth = {
    universe_size: last.universe_size ?? null,
    spx_close: last.spx_close ?? null,
    verdict: replay.verdicts[date],
    mm: {
      up_4pct: last.up_4pct, down_4pct: last.down_4pct,
      ratio_5d: last.ratio_5d, ratio_10d: last.ratio_10d,
      up_25pct_qtr: last.up_25pct_qtr, down_25pct_qtr: last.down_25pct_qtr,
      up_25pct_month: last.up_25pct_month, down_25pct_month: last.down_25pct_month,
      up_50pct_month: last.up_50pct_month, down_50pct_month: last.down_50pct_month,
      up_13pct_34d: last.up_13pct_34d, down_13pct_34d: last.down_13pct_34d,
    },
    breadth: {
      t2108: last.t2108,
      pct_above_200sma: last.pct_above_200sma,
      pct_above_50sma: last.pct_above_50sma,
      pct_above_20sma: last.pct_above_20sma,
      advances: last.advances, declines: last.declines,
      new_highs: last.new_highs, new_lows: last.new_lows,
      ad_line: last.ad_line, mcclellan_osc: last.mcclellan_osc,
    },
    history: {
      dates: windowDates,
      pct_above_200sma: rows.map((r) => r.pct_above_200sma),
      pct_above_50sma: rows.map((r) => r.pct_above_50sma),
      pct_above_20sma: rows.map((r) => r.pct_above_20sma),
      mcclellan_osc: rows.map((r) => r.mcclellan_osc),
      rows,
    },
    data_quality: { stale: false },
  }

  let marketHealth = null
  if (replay.health) {
    const spy = healthAt(replay.health.spy, date)
    const qqq = healthAt(replay.health.qqq, date)
    if (spy && qqq) marketHealth = { stale: false, spy, qqq }
  }

  return { breadth, marketHealth }
}
