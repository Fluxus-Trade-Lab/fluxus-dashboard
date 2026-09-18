/**
 * Where the engine reads each Market Monitor count (DATA ALEX 2026-09-18,
 * Andy 「全部按原文」): Stockbee's own scans, and common-stock new highs/lows.
 * Mirrors `breadth_signals.py` THRUST_UP/DOWN, RATIO_COLS and SPREAD_COLS;
 * origCols.test.js reads the Python file so this copy cannot drift.
 *
 * The unsuffixed archive columns are the older price-only / point-to-point /
 * SPAC-inclusive counts. They keep their history and the page keeps showing
 * them — but as the OLD count, muted and never tinted, the same way the engine
 * treats them: "never voted on the old column instead".
 */
export const ORIG_COLS = {
  up_4pct: 'up_4pct_stockbee',
  down_4pct: 'down_4pct_stockbee',
  ratio_5d: 'ratio_5d_stockbee',
  ratio_10d: 'ratio_10d_stockbee',
  up_25pct_qtr: 'up_25pct_qtr_stockbee',
  down_25pct_qtr: 'down_25pct_qtr_stockbee',
  up_13pct_34d: 'up_13pct_34d_stockbee',
  down_13pct_34d: 'down_13pct_34d_stockbee',
  up_25pct_month: 'up_25pct_month_stockbee',
  down_25pct_month: 'down_25pct_month_stockbee',
  up_50pct_month: 'up_50pct_month_stockbee',
  down_50pct_month: 'down_50pct_month_stockbee',
  new_highs: 'new_highs_common',
  new_lows: 'new_lows_common',
}

/** The author-definition value if the row has it, else the old one flagged as old. */
export function orig(row, key) {
  const v = row?.[ORIG_COLS[key]]
  if (v != null) return { v, old: false }
  const o = row?.[key]
  return { v: o ?? null, old: o != null }
}

/** The author-definition series only — null where the column did not exist yet. */
export const origSeries = (rows, key) => rows.map((r) => r?.[ORIG_COLS[key]] ?? null)
