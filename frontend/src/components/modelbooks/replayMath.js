/* The arithmetic behind the bar-by-bar replay, kept out of the canvas so it can
   be tested without a DOM. Nothing here draws; nothing here reaches for state.

   Two ideas run through the whole file and are worth stating once:

   1. THE REPLAY MUST NOT LEAK ITS OWN ENDING. Every scale — price, volume,
      the x-domain — is computed from the bars revealed so far, never from the
      whole series. A y-axis fitted to the full file prints the eventual high
      on the ruler before you have walked to it.

   2. THE WINDOW FOLLOWS THE CURSOR. Andy, 2026-09-25: "随着时间推进也应该尽量
      保持能够看清楚最近2-3个月左右的走势." So the visible span is a fixed number
      of sessions ending at the cursor, not the whole revealed series — which
      would squeeze the candles thinner with every step. */

/** Sessions on screen. A daily bar month is about 21 sessions; 0 = everything. */
export const WINDOWS = [21, 42, 63, 126, 252, 0]
export const DEFAULT_WINDOW = 2   // 63 sessions, about three months

export function windowLabel(n, t = (k, d) => d) {
  if (n === 0) return t('modelbooks.replay.window.all', 'All')
  return t('modelbooks.replay.window.months', `${n / 21}M`).replace('{n}', String(n / 21))
}

export function ema(values, period) {
  const k = 2 / (period + 1)
  const out = []
  let prev = null
  for (let i = 0; i < values.length; i++) {
    if (i < period - 1) { out.push(null); continue }
    if (i === period - 1) {
      let sum = 0
      for (let j = 0; j <= i; j++) sum += values[j]
      prev = sum / period
    } else {
      prev = values[i] * k + prev * (1 - k)
    }
    out.push(prev)
  }
  return out
}

export function sma(values, period) {
  const out = []
  let sum = 0
  for (let i = 0; i < values.length; i++) {
    sum += values[i]
    if (i >= period) sum -= values[i - period]
    out.push(i >= period - 1 ? sum / period : null)
  }
  return out
}

/**
 * The slice on screen: `[from, to]` inclusive, plus the domain width the x-axis
 * spans (the slice plus a little room to the right of the cursor, so the newest
 * bar is never jammed against the price scale).
 */
export function viewport(barCount, cursor, windowSize) {
  const revealed = Math.max(1, Math.min(cursor + 1, barCount))
  const span = windowSize === 0 ? revealed : Math.min(windowSize, revealed)
  const from = Math.max(0, revealed - span)
  const head = Math.max(2, Math.round(span * 0.1))
  return { from, to: revealed - 1, span, domain: span + head }
}

/** Price range over a slice, padded. Returns null when the slice is empty. */
export function priceRange(bars, from, to) {
  let lo = Infinity, hi = -Infinity
  for (let i = from; i <= to && i < bars.length; i++) {
    const b = bars[i]
    if (b.low < lo) lo = b.low
    if (b.high > hi) hi = b.high
  }
  if (!Number.isFinite(lo) || !Number.isFinite(hi)) return null
  const pad = (hi - lo) * 0.06 || hi * 0.03
  return { lo: Math.max(lo - pad, lo * 0.5), hi: hi + pad }
}

/**
 * Where the replay should open: a month or two before the breakout, so the
 * reader meets the base rather than a chart already in flight. Entries with no
 * breakout open a third of the way in.
 */
export function openingCursor({ bars, pivot }) {
  const n = bars?.length ?? 0
  if (!n) return 0
  const wanted = pivot != null ? pivot - 45 : Math.floor(n * 0.3)
  return Math.min(Math.max(wanted, 55, 0), n - 1)
}

/**
 * The acts marked on the transport. `stated` is what a model book's author
 * wrote; `computed` is what our own rule found. When the two disagree the page
 * shows BOTH — the disagreement is the lesson, and hiding it would be us
 * deciding we know better than Ross Haber.
 */
export function acts({ bars, low, peak, computed, stated }) {
  if (!bars?.length) return []
  const out = []
  const at = iso => {
    const i = bars.findIndex(b => b.time >= iso)
    return i < 0 ? null : i
  }
  if (low != null) out.push({ key: 'low', index: low, kind: 'computed' })
  const statedIndex = stated?.date ? at(stated.date) : null
  if (statedIndex != null) {
    out.push({ key: 'pivot', index: statedIndex, kind: 'stated', book: stated.book,
               price: stated.price })
  }
  if (computed != null && (statedIndex == null || Math.abs(computed - statedIndex) > 3)) {
    out.push({ key: 'pivot', index: computed, kind: 'computed' })
  }
  if (peak != null) out.push({ key: 'peak', index: peak, kind: 'computed' })
  return out.filter(a => a.index >= 0 && a.index < bars.length)
             .sort((a, b) => a.index - b.index)
}

/**
 * The four numbers under the chart, all as of the cursor. Each is null rather
 * than zero when its inputs are not there yet — a 50-day line does not exist
 * on bar 12, and printing 0.0% would be a lie with a decimal point on it.
 */
export function readout({ bars, cursor, pivotIndex }) {
  if (!bars?.length) return null
  const i = Math.min(Math.max(cursor, 0), bars.length - 1)
  const bar = bars[i]
  const closes = []
  for (let k = 0; k <= i; k++) closes.push(bars[k].close)

  const s50 = i >= 49 ? sma(closes, 50)[i] : null
  const vol50 = i >= 49
    ? bars.slice(i - 49, i + 1).reduce((a, b) => a + (b.volume || 0), 0) / 50
    : null
  const highSoFar = Math.max(...closes)

  return {
    date: bar.time,
    close: bar.close,
    changePct: i > 0 ? (bar.close / bars[i - 1].close - 1) * 100 : null,
    vs50dPct: s50 ? (bar.close / s50 - 1) * 100 : null,
    relVolume: vol50 ? (bar.volume || 0) / vol50 : null,
    sincePivotPct: pivotIndex != null && i >= pivotIndex
      ? (bar.close / bars[pivotIndex].close - 1) * 100 : null,
    fromHighPct: (bar.close / highSoFar - 1) * 100,
    barsLeft: bars.length - 1 - i,
  }
}

/**
 * Rank key for the library list. `advance_pct` is what a reader could have
 * taken from the breakout; `gain_pct` is the upstream screen's calendar-year
 * low-to-high and is not a return at all. Andy switched the default to the
 * former on 2026-09-25 ("2 y"). Entries without a breakout fall to the bottom
 * of that sort rather than borrowing the other column's number.
 */
export function rankValue(entry, key) {
  if (key === 'advance_pct') return entry.advance_pct ?? null
  return entry[key] ?? null
}

export function compareEntries(a, b, key, dir) {
  const av = rankValue(a, key)
  const bv = rankValue(b, key)
  if (av == null && bv == null) return 0
  if (av == null) return 1
  if (bv == null) return -1
  if (typeof av === 'string') return dir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av)
  return dir === 'asc' ? av - bv : bv - av
}
