import { usable } from './headCoach'

/**
 * Does a losing streak change the next trade?
 *
 * The stopping stage's question is when to step away, and every answer to it is
 * a belief about this. On the real book the win rate decays monotonically with
 * streak depth — 39% overall, then 32 / 27 / 26 / 25 — and expectancy with it.
 *
 * WHY THE PERMUTATION TEST IS NOT OPTIONAL. A decay like that appears in random
 * sequences too: losses cluster by arithmetic, and conditioning on "the last
 * two lost" selects a window that is unusual for reasons having nothing to do
 * with the trader. Reading the raw decay as tilt is the same error as reading a
 * hot hand into a coin. So the sequence is shuffled thousands of times with
 * every trade's result kept intact — only the ORDER changes — and the observed
 * gap is placed in that distribution. If order carries no information, the
 * observed value sits in the middle of it.
 *
 * On the 2026-08-17 book: p = 0.0012 over 20,000 shuffles. Order carries
 * information.
 *
 * The seed is fixed so the same book always gives the same p. A number that
 * moves when you reload is not evidence.
 */

/** A small deterministic PRNG — Math.random would make p jitter per render. */
function mulberry32(seed) {
  let a = seed >>> 0
  return () => {
    a = (a + 0x6d2b79f5) >>> 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/** Chronological realised R. Ties broken by ticker so the order is stable. */
export function sequence(trades = []) {
  return trades
    .filter((t) => usable(t) && t.exit_date)
    .sort((a, b) => (a.exit_date < b.exit_date ? -1
      : a.exit_date > b.exit_date ? 1
        : a.ticker < b.ticker ? -1 : 1))
    .map((t) => t.realized_R)
}

const mean = (xs) => (xs.length ? xs.reduce((s, x) => s + x, 0) / xs.length : 0)

/** Trades that followed `depth` consecutive losses. */
function following(R, depth) {
  const out = []
  for (let i = depth; i < R.length; i++) {
    let all = true
    for (let k = 0; k < depth; k++) if (R[i - k - 1] >= 0) { all = false; break }
    if (all) out.push(R[i])
  }
  return out
}

/** One row per streak depth, plus the after-a-win row for contrast. */
export function streakRows(trades = [], minSample = 12) {
  const R = sequence(trades)
  if (R.length < 40) return []
  const base = { key: 'all', depth: 0, n: R.length, mean: mean(R),
                 win: R.filter((x) => x > 0).length / R.length }
  const rows = [base]
  for (let d = 1; d <= 4; d++) {
    const a = following(R, d)
    if (a.length < minSample) break
    rows.push({ key: `L${d}`, depth: d, n: a.length, mean: mean(a),
                win: a.filter((x) => x > 0).length / a.length })
  }
  const afterWin = []
  for (let i = 1; i < R.length; i++) if (R[i - 1] > 0) afterWin.push(R[i])
  if (afterWin.length >= minSample) {
    rows.push({ key: 'W1', depth: -1, n: afterWin.length, mean: mean(afterWin),
                win: afterWin.filter((x) => x > 0).length / afterWin.length })
  }
  return rows
}

/**
 * How often does shuffling the order produce a gap this extreme?
 * `null` when there is not enough history to shuffle meaningfully.
 */
export function orderMatters(trades = [], { depth = 2, runs = 4000, seed = 20260817 } = {}) {
  const R = sequence(trades)
  if (R.length < 60) return null
  const gap = (seq) => {
    const a = following(seq, depth)
    return a.length < 20 ? null : mean(a) - mean(seq)
  }
  const observed = gap(R)
  if (observed == null) return null

  const rand = mulberry32(seed)
  const shuffled = R.slice()
  let atLeastAsExtreme = 0
  let counted = 0
  for (let r = 0; r < runs; r++) {
    for (let i = shuffled.length - 1; i > 0; i--) {      // Fisher–Yates
      const j = Math.floor(rand() * (i + 1))
      const tmp = shuffled[i]; shuffled[i] = shuffled[j]; shuffled[j] = tmp
    }
    const v = gap(shuffled)
    if (v == null) continue
    counted++
    if (v <= observed) atLeastAsExtreme++
  }
  if (!counted) return null
  return { observed, p: atLeastAsExtreme / counted, runs: counted, depth }
}
