import { usable } from './headCoach'

/**
 * Do the setup labels separate winners from losers?
 *
 * The selection stage's whole premise is that some setups pay and others do
 * not, so you take more of one and fewer of the other. This checks it, and on
 * the 2026-08-17 book the answer is no: six of seven labels have a bootstrap
 * interval containing the book average, and the seventh has n = 7.
 *
 * A section whose usual answer is "no signal here" is doing its job. The
 * alternative — ranking the setups by expectancy and letting the reader take
 * the top one seriously — turns 7 trades into a strategy.
 *
 * MULTIPLE COMPARISONS. Seven intervals at 90% means about 0.7 false
 * separations expected by chance, so ONE apparent hit is what you would see if
 * nothing were true. The verdict counts the hits against that expectation
 * rather than celebrating the first one.
 */

/** Deterministic PRNG — a bootstrap that moves on reload is not evidence. */
function mulberry32(seed) {
  let a = seed >>> 0
  return () => {
    a = (a + 0x6d2b79f5) >>> 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const mean = (xs) => xs.reduce((s, x) => s + x, 0) / xs.length

/** 90% bootstrap interval for the mean. */
function interval(v, rand, runs) {
  const ms = []
  for (let r = 0; r < runs; r++) {
    let s = 0
    for (let i = 0; i < v.length; i++) s += v[Math.floor(rand() * v.length)]
    ms.push(s / v.length)
  }
  ms.sort((a, b) => a - b)
  return [ms[Math.floor(runs * 0.05)], ms[Math.floor(runs * 0.95)]]
}

export function setupEdge(trades = [], { minTrades = 7, runs = 1500, seed = 20260817 } = {}) {
  const closed = trades.filter(usable)
  if (closed.length < 40) return null

  const byType = new Map()
  for (const t of closed) {
    const k = t.setup_type || '—'
    if (!byType.has(k)) byType.set(k, [])
    byType.get(k).push(t.realized_R)
  }

  const all = closed.map((t) => t.realized_R)
  const book = mean(all)
  const rand = mulberry32(seed)

  const rows = [...byType.entries()]
    .filter(([, v]) => v.length >= minTrades)
    .map(([setup, v]) => {
      const [lo, hi] = interval(v, rand, runs)
      return {
        setup,
        n: v.length,
        mean: mean(v),
        lo,
        hi,
        // "Separates" means the interval excludes the book average — the only
        // claim this data can support about a setup being different.
        separates: lo > book || hi < book,
      }
    })
    .sort((a, b) => b.n - a.n)

  const hits = rows.filter((r) => r.separates).length
  // 10% of intervals miss by construction; that is the null expectation.
  const expectedByChance = rows.length * 0.1

  return {
    rows,
    book,
    total: closed.length,
    // Share of the book sitting in its single largest label. A label holding
    // two thirds of everything is not sorting anything.
    concentration: rows.length ? Math.max(...rows.map((r) => r.n)) / closed.length : 0,
    hits,
    expectedByChance,
    // Only a real signal if the hits meaningfully exceed what chance gives.
    signal: hits > expectedByChance + 1,
  }
}
