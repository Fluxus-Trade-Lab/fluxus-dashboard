#!/usr/bin/env node
/**
 * The quality gate on the model book library.
 *
 * WHY. Model Books opened sorted by GAIN, and the first screen was physically
 * impossible: SAF 2016 at +465,308.8% over 198 days, SAF 2014 at +302,632%,
 * CHK 2020 at +64,429.6% for a company that filed Chapter 11 that June,
 * UAUA 2006 at +41,172.7% in three days. A library whose first screen is
 * impossible teaches the reader nothing except not to trust the library.
 *
 * THE ROOT, FOUND 2026-09-25. `gain_pct` is not ours and is not a return. It
 * arrives from the upstream `big_movers_result.csv` as high_price/low_price
 * over that CALENDAR YEAR (`pipeline/tools/import_big_movers.py:105-112`) — a
 * range, and one measured on a different window from the bars we store, which
 * run wider on both sides. The two therefore disagree in both directions:
 * MARA 2020 is filed at +4,088% while its own bars run +7,049% from the
 * breakout, and SAF 2016 is filed at +465,308% on bars that can only hold
 * 8.4x. Sorting the library by that column put the dirtiest files on the first
 * screen by construction. So this script does two jobs: it throws out what
 * cannot be believed, and it measures what a reader could actually have taken
 * (`advance_pct`, pivot close -> peak close, on our own bars) so the page has
 * something honest to rank by. `gain_pct` stays in `index.json` untouched —
 * it belongs to the importer — and the page labels it for what it is.
 *
 * WHAT IT WRITES, all into `public/data/modelbooks/`:
 *
 *   excluded.json  ids that do not belong in the library, each with the rule
 *                  that caught it and a sentence naming the measurement.
 *                  Nothing is deleted from disk — the page filters on this.
 *   analysis.json  per surviving entry: the pivot bar, the advance from it,
 *                  and a `lowres` flag for charts whose price resolution is
 *                  gone. This is what the page ranks and replays on.
 *
 * Andy approved the four rules and the rank change on 2026-09-25 ("1 y 2 y 3 A
 * 4 y"). Both files are recomputed from the bars on every build, so a
 * re-import of `index.json` (owned by `pipeline/tools/import_big_movers.py`)
 * cannot silently drop the gate.
 *
 * ── THE FOUR EXCLUSION RULES ────────────────────────────────────────────────
 *
 * 1. IMPOSSIBLE PRICE — any bar priced above $100,000.
 *    Chained reverse splits push the adjusted early history into the billions
 *    and, for NUWE 2017, to $6.3 trillion a share. 66 entries: DRYS, CANB ×6,
 *    SCON ×4, OSAT ×7, INPX ×4 and the rest.
 *
 * 2. BARS CONTRADICT THEMSELVES — the original shape gate, unchanged, except
 *    that its verdict now excludes rather than hides. Measured over all 1,504
 *    entries with bars on 2026-08-31:
 *
 *      close range max/min   p50 4.3x   p90 16.1x   p95 31.6x   p99 156.7x
 *      adjacent close jump   p50 1.31x  p90 2.11x   p95 3.01x   p99 14.8x
 *
 *    RANGE_MAX = 500x. The largest ranges anyone can verify by hand are real
 *    and sit far below it — GME 2020 at 124x, RIOT at 120x, MARA at 120x, all
 *    genuine and all under a quarter of the gate. The smallest thing it
 *    catches is CHK 2020 at 533x, which is the bankruptcy.
 *    JUMP_MAX = 10x, above the library's own 99th percentile. A stock does
 *    not close ten times its previous close; a reverse split does.
 *    The third test needs no threshold because it is a contradiction rather
 *    than a magnitude: a stated `gain_pct` larger than max(high)/min(low) over
 *    the entry's own bars claims a move its own chart cannot contain.
 *
 * 3. UNTRADABLE AT THE BUY POINT — median dollar volume over the 20 sessions
 *    before the advance below $250,000.
 *    ⚠️ SELF-MADE THRESHOLD, and it must stay labelled as one. The industry
 *    filter (IBD, Minervini) is ~$20M average daily dollar volume, which would
 *    also throw out HD 1982 ($432k adjusted) and every other pre-1990 classic.
 *    So this is the library's own ~1st percentile instead: the median entry
 *    here trades $110M a day. Price × volume is what survives split
 *    adjustment (both sides scale inversely) and is comparable across eras,
 *    which is why it, and not the price level, is the ruler.
 *    Catches GNUS ($137k), TOON ($138k), KOSS ($14k), DDAY ($2.5k), APT, BULL,
 *    SBET, INDO, BATL, MRIN, EVTV.
 *
 * 4. DUPLICATE — byte-identical bar files. Renamed tickers were imported
 *    twice: WCST = SSC, WFR = SUNE, FSTO = FST, and JDSU 1998 twice over.
 *    The first id in `index.json` order keeps the entry.
 *
 * ── THE FIFTH RULE FLAGS, IT DOES NOT EXCLUDE ───────────────────────────────
 *
 * LOW RESOLUTION — more than half the bars have open = high = low = close.
 * Found while building the replay: HD 1982, MSFT 1986 and CSCO 1990 — the
 * three best-annotated O'Neil classics in the library — adjust to $0.02–$0.07
 * and then round to the cent, so 92% / 82% / 75% of their bars collapse to a
 * single number. Those charts are step functions, not charts. Four entries
 * trip this rule once the exclusions are applied. They are the
 * entries most worth keeping and the ones whose data must be re-fetched
 * unadjusted; until then the page says so on the chart rather than pretending.
 *
 * ── THE PIVOT ───────────────────────────────────────────────────────────────
 *
 * The first bar to close above the prior 20 sessions' high on volume at least
 * 40% above its 50-session average, searched forward from the lowest close
 * before the peak. The +40% volume is O'Neil's own breakout condition; the
 * 20-session base length is SELF-MADE and registered as such in
 * `data/reference/METRIC_SOURCES.md`. Found on 1,130 of the 1,399 surviving
 * entries (81%); where it is not found, `pivot` is null and the page draws no
 * breakout mark rather than inventing one.
 */
import { readFileSync, writeFileSync, existsSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createHash } from 'node:crypto'

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const DIR = join(ROOT, 'public', 'data', 'modelbooks')
const INDEX = join(DIR, 'index.json')
const EXCLUDED = join(DIR, 'excluded.json')
const ANALYSIS = join(DIR, 'analysis.json')
const NOTES = join(DIR, 'notes.json')

export const RANGE_MAX = 500        // max(close) / min(close)
export const JUMP_MAX = 10          // largest close-to-close ratio, either direction
export const PRICE_MAX = 100_000    // no US equity bar is priced above this
export const DOLLAR_VOL_MIN = 250_000 // pre-advance median close x volume
export const FLAT_SHARE_MAX = 0.5   // share of bars with o = h = l = c
const GAIN_SLACK = 1.02             // rounding room on the stated gain
const BASE_LOOKBACK = 20            // self-made: how long a base we require
const VOL_LOOKBACK = 50
export const VOL_MULT = 1.4         // O'Neil: breakout volume >= +40% over average

/** Why this entry's bars cannot be believed — or null when they can. */
export function judge(bars, gainPct) {
  const closes = [], highs = [], lows = []
  for (const b of bars) {
    if (b?.close > 0) closes.push(b.close)
    if (b?.high > 0) highs.push(b.high)
    if (b?.low > 0) lows.push(b.low)
  }
  if (closes.length < 2) return null

  const range = Math.max(...closes) / Math.min(...closes)
  if (range > RANGE_MAX) return `close range ${range.toFixed(0)}x`

  let jump = 1
  for (let i = 1; i < closes.length; i++) {
    const [a, b] = [closes[i - 1], closes[i]]
    jump = Math.max(jump, a / b, b / a)
  }
  if (jump > JUMP_MAX) return `one-day jump ${jump.toFixed(1)}x`

  if (gainPct != null && highs.length && lows.length) {
    const hl = Math.max(...highs) / Math.min(...lows)
    if (1 + gainPct / 100 > hl * GAIN_SLACK) {
      return `stated gain ${(1 + gainPct / 100).toFixed(0)}x exceeds its bars' ${hl.toFixed(1)}x`
    }
  }
  return null
}

function median(xs) {
  if (!xs.length) return 0
  const s = [...xs].sort((a, b) => a - b)
  const m = s.length >> 1
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2
}

/**
 * The bar on or after a date, or null when the date falls outside the file.
 * Model books state a calendar date; the bars are what we hold.
 */
export function barOnOrAfter(bars, iso) {
  if (!iso) return null
  for (let i = 0; i < bars.length; i++) if (bars[i].time >= iso) return i
  return null
}

/** The index of the highest close, and of the lowest close before it. */
export function extremes(bars) {
  let peak = 0
  for (let i = 1; i < bars.length; i++) if (bars[i].close > bars[peak].close) peak = i
  let low = 0
  for (let i = 1; i < peak; i++) if (bars[i].close < bars[low].close) low = i
  return { low, peak }
}

/**
 * The breakout bar: first close above the prior BASE_LOOKBACK highs on volume
 * at least VOL_MULT of its VOL_LOOKBACK average. null when the entry never
 * shows one — which is a real answer, not a failure to be papered over.
 */
export function findPivot(bars) {
  const { low, peak } = extremes(bars)
  const start = Math.max(low, VOL_LOOKBACK, BASE_LOOKBACK)
  for (let i = start; i <= peak; i++) {
    let priorHigh = 0
    for (let k = i - BASE_LOOKBACK; k < i; k++) priorHigh = Math.max(priorHigh, bars[k].high)
    let volSum = 0
    for (let k = i - VOL_LOOKBACK; k < i; k++) volSum += bars[k].volume || 0
    const avgVol = volSum / VOL_LOOKBACK
    if (bars[i].close > priorHigh && avgVol > 0 && (bars[i].volume || 0) > VOL_MULT * avgVol) return i
  }
  return null
}

/** Median dollar volume over the 20 sessions before the advance begins. */
export function preAdvanceDollarVolume(bars) {
  const { peak } = extremes(bars)
  const end = Math.max(peak - 20, 1)
  const pre = bars.slice(0, end).slice(-20)
  const window = pre.length ? pre : bars.slice(0, 5)
  return median(window.map(b => (b.close || 0) * (b.volume || 0)))
}

/** Share of bars whose four prices are the same number. */
export function flatShare(bars) {
  if (!bars.length) return 0
  let flat = 0
  for (const b of bars) if (b.open === b.high && b.high === b.low && b.low === b.close) flat += 1
  return flat / bars.length
}

/**
 * The one verdict for one entry. `seen` maps a bar-file hash to the id that
 * claimed it first, and is mutated as entries pass.
 */
export function verdict(entry, bars, rawHash, seen) {
  if (!Array.isArray(bars) || bars.length < 10) {
    return { rule: 'too_few_bars', why: `only ${bars?.length ?? 0} bars` }
  }
  const maxPrice = Math.max(...bars.map(b => b.high || 0))
  if (maxPrice > PRICE_MAX) {
    return { rule: 'impossible_price', why: `a bar priced at $${maxPrice.toExponential(1)}` }
  }
  const shape = judge(bars, entry.gain_pct)
  if (shape) return { rule: 'broken_bars', why: shape }

  const first = seen.get(rawHash)
  if (first) return { rule: 'duplicate', why: `same bars as ${first}` }

  const dv = preAdvanceDollarVolume(bars)
  if (dv < DOLLAR_VOL_MIN) {
    return { rule: 'untradable', why: `pre-advance median $${Math.round(dv).toLocaleString('en-US')}/day` }
  }
  seen.set(rawHash, `${entry.ticker} ${entry.year}`)
  return null
}

function main() {
  if (!existsSync(INDEX)) {
    console.warn('[modelbooks] no index.json — nothing to gate')
    return
  }
  const index = JSON.parse(readFileSync(INDEX, 'utf8'))
  // notes.json is written by `pipeline/tools/import_modelbook_notes.py` and
  // committed, so the build never needs Python to honour the rule above.
  let notes = {}
  if (existsSync(NOTES)) {
    try { notes = JSON.parse(readFileSync(NOTES, 'utf8')).entries ?? {} } catch { notes = {} }
  }
  const excluded = {}
  const analysis = {}
  const seen = new Map()
  let checked = 0

  for (const e of index) {
    if (!e?.ohlcv_file) continue
    const p = join(DIR, e.ohlcv_file)
    if (!existsSync(p)) continue
    checked += 1
    let raw, bars
    try {
      raw = readFileSync(p, 'utf8')
      bars = JSON.parse(raw)
    } catch { continue }
    const hash = createHash('md5').update(raw).digest('hex')

    const bad = verdict(e, bars, hash, seen)
    if (bad) { excluded[e.id] = bad; continue }

    /* Andy, 2026-09-25: "如果有重复或者有批注，用traderlion的版本." A model book
       that names its own breakout beats our rule — Ross Haber picked the base
       that launched the year's move, while `findPivot` takes the first one that
       clears its filter, and on a file spanning two bases those are different
       days. Both are kept so the page can mark them separately. */
    const computed = findPivot(bars)
    const stated = barOnOrAfter(bars, notes[`${e.ticker}-${e.year}`]?.breakout?.date)
    const pivot = stated ?? computed
    const { low, peak } = extremes(bars)
    const flat = flatShare(bars)
    analysis[e.id] = {
      low,
      pivot,
      pivot_source: stated != null ? 'stated' : computed != null ? 'computed' : null,
      computed_pivot: computed,
      pivot_date: pivot == null ? null : bars[pivot].time,
      peak,
      peak_date: bars[peak].time,
      // What a reader could have taken: breakout close to the highest close.
      advance_pct: pivot == null ? null
        : Math.round((bars[peak].close / bars[pivot].close - 1) * 1000) / 10,
      bars: bars.length,
      lowres: flat > FLAT_SHARE_MAX,
      flat_share: Math.round(flat * 100) / 100,
    }
  }

  const stamp = new Date().toISOString()
  writeFileSync(EXCLUDED, JSON.stringify({
    generated_at: stamp,
    thresholds: {
      range_max: RANGE_MAX, jump_max: JUMP_MAX, price_max: PRICE_MAX,
      dollar_vol_min: DOLLAR_VOL_MIN,
    },
    checked,
    entries: excluded,
  }, null, 2) + '\n')

  writeFileSync(ANALYSIS, JSON.stringify({
    generated_at: stamp,
    pivot: { base_lookback: BASE_LOOKBACK, vol_lookback: VOL_LOOKBACK, vol_mult: VOL_MULT },
    flat_share_max: FLAT_SHARE_MAX,
    entries: analysis,
  }, null, 2) + '\n')

  const kept = Object.keys(analysis).length
  const withPivot = Object.values(analysis).filter(a => a.pivot != null).length
  const fromBook = Object.values(analysis).filter(a => a.pivot_source === 'stated').length
  const lowres = Object.values(analysis).filter(a => a.lowres).length
  console.log(
    `[modelbooks] ${Object.keys(excluded).length} of ${checked} excluded · ` +
    `${kept} kept · ${withPivot} with a pivot (${fromBook} taken from a model book) · ` +
    `${lowres} low-resolution`)
}

if (process.argv[1] && process.argv[1].endsWith('flag-modelbook-outliers.mjs')) main()
