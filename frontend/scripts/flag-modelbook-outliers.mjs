#!/usr/bin/env node
/**
 * The shape gate on the model book library.
 *
 * WHY. Model Books opens sorted by GAIN, and the first screen was physically
 * impossible: SAF 2016 at +465,308.8% over 198 days, SAF 2014 at +302,632%,
 * CHK 2020 at +64,429.6% for a company that filed Chapter 11 that June,
 * UAUA 2006 at +41,172.7% in three days. A library whose first screen is
 * impossible teaches the reader nothing except not to trust the library.
 *
 * WHAT IS ACTUALLY WRONG. Not the app — the bars. These entries carry
 * split-unadjusted history: a 1-for-N reverse split arrives as a single
 * close-to-close jump of N×, and the pre-split penny prices become the
 * denominator of every ratio computed off the file.
 *
 * WHAT THIS DOES. Nothing is deleted. This measures every entry's own bars and
 * writes a list of ids whose SHAPE is impossible to `suspect.json`; the browser
 * hides those rows by default and shows them behind a switch. The judgement is
 * recomputed from the data on every build, so a re-import cannot silently drop
 * the gate — which is exactly what stamping a flag into `index.json` (a file
 * `pipeline/tools/import_big_movers.py` owns and rewrites) would have risked.
 *
 * THE THRESHOLDS, AND WHAT THE LIBRARY SAYS ABOUT THEM. Measured over all
 * 1,504 entries that have bars, on 2026-08-31:
 *
 *   close range max/min   p50 4.3x   p90 16.1x   p95 31.6x   p99 156.7x
 *   adjacent close jump   p50 1.31x  p90 2.11x   p95 3.01x   p99 14.8x
 *
 * RANGE_MAX = 500x. The largest ranges anyone can verify by hand are real and
 * sit far below it — GME 2020 at 124x, RIOT at 120x, MARA at 120x, all of them
 * genuine and all of them under a quarter of the gate. The smallest thing the
 * gate catches is CHK 2020 at 533x, which is the bankruptcy.
 *
 * JUMP_MAX = 10x. Above the library's own 99th percentile. A stock does not
 * close ten times its previous close; a reverse split does, and every entry
 * this catches has one (TLRY's 1-for-15 in 2025, DRYS's chain in 2016, HOLO).
 *
 * The third rule needs no threshold at all, because it is a contradiction
 * rather than a magnitude: an entry whose stated `gain_pct` is larger than
 * max(high)/min(low) over its own bars is claiming a move its own chart cannot
 * contain. Five entries do (ORBS 2025 states +8,416% on bars spanning 8.4x).
 *
 * Together: 30 of 1,504 entries, 2.0%.
 */
import { readFileSync, writeFileSync, existsSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const DIR = join(ROOT, 'public', 'data', 'modelbooks')
const INDEX = join(DIR, 'index.json')
const OUT = join(DIR, 'suspect.json')

export const RANGE_MAX = 500   // max(close) / min(close)
export const JUMP_MAX = 10     // largest close-to-close ratio, either direction
const GAIN_SLACK = 1.02        // rounding room on the stated gain

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

function main() {
  if (!existsSync(INDEX)) {
    console.warn('[modelbooks] no index.json — nothing to gate')
    return
  }
  const index = JSON.parse(readFileSync(INDEX, 'utf8'))
  const entries = {}
  let checked = 0

  for (const e of index) {
    if (!e?.ohlcv_file) continue
    const p = join(DIR, e.ohlcv_file)
    if (!existsSync(p)) continue
    checked += 1
    let bars
    try { bars = JSON.parse(readFileSync(p, 'utf8')) } catch { continue }
    if (!Array.isArray(bars)) continue
    const why = judge(bars, e.gain_pct)
    if (why) entries[e.id] = why
  }

  writeFileSync(OUT, JSON.stringify({
    generated_at: new Date().toISOString(),
    thresholds: { range_max: RANGE_MAX, jump_max: JUMP_MAX },
    checked,
    entries,
  }, null, 2) + '\n')
  console.log(`[modelbooks] ${Object.keys(entries).length} of ${checked} entries flagged suspect`)
}

if (process.argv[1] && process.argv[1].endsWith('flag-modelbook-outliers.mjs')) main()
