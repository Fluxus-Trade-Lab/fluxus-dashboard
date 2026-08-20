/**
 * The denominator, built on the page instead of waited for.
 *
 * "Which seat gets vetoed most" is not answerable from a list of vetoes. The
 * six seats have wildly different exposure — 在烧 has a name every single day,
 * 入场 is empty on any day without an EP — so a seat that shows up daily
 * accumulates more ✗ for reasons that have nothing to do with whether it chose
 * well. Counting only the marks measures attendance, not judgement.
 *
 * So a day produces one row PER SEAT, always, and four outcomes that are all
 * equally records:
 *
 *   vetoed    Andy said not this, today
 *   starred   Andy took it
 *   ignored   the seat showed a name and he did not act — this is DATA, and it
 *             is the row that a veto-only log throws away
 *   empty     the seat had no name to show — not a judgement at all, and it
 *             must not sit in the same denominator as the three above
 *
 * `ignored` and `empty` are two different denominators and the analysis will
 * need them apart: veto-rate among names SHOWN is a different question from
 * how often a seat can field anyone.
 *
 * The learning half of this loop is under research on the data side (Andy,
 * 2026-08-20: 机制在研究，前端框架先搭). This file is the frontend's half —
 * the shape a row has to have, computed from what is on screen, ready for the
 * `shortlist_upsert` action the moment it exists. It stores nothing and pushes
 * nothing; it only says what a day looked like.
 */

export const OUTCOMES = ['vetoed', 'starred', 'ignored', 'empty']

/** Readings the analysis will want beside the outcome. Snapshotted at the
 *  moment of the mark, because the question worth asking about an old veto is
 *  what the name looked like ON THE DAY, not what it looks like now. */
const SNAPSHOT = [
  'close', 'change_pct', 'rel_volume', 'rs_1m', 'rs_3m', 'h_score',
  'rs_line_pctl_21', 'rs_line_pctl_63', 'atr_from_sma50', 'high_52w_dist',
  'vcs', 'trend_base', 'sector', 'sp_signal',
]

function snap(readings = {}) {
  const out = {}
  // A field the payload does not carry stays ABSENT from the row rather than
  // arriving as null — a row that says `vcs: null` claims vcs was measured and
  // came out empty, which is a different sentence from not carrying it at all.
  for (const k of SNAPSHOT) if (k in readings) out[k] = readings[k]
  return out
}

/**
 * One row per seat for the day, plus one per manual name.
 *
 * @param doc   shortlist.json
 * @param marks { [ticker]: 'vetoed' | 'starred' } for THIS date only
 */
export function buildLedger(doc, marks = {}) {
  if (!doc) return []
  const byTicker = Object.fromEntries((doc.cards || []).map((c) => [c.ticker, c]))
  const rows = (doc.seats || []).map((s) => {
    const card = s.ticker ? byTicker[s.ticker] : null
    if (!card) {
      return { date: doc.date, seat: s.seat, ticker: null, shown: false,
               outcome: 'empty', why: s.why ?? null }
    }
    return {
      date: doc.date, seat: s.seat, ticker: card.ticker, shown: true,
      outcome: marks[card.ticker] ?? 'ignored',
      why: s.why ?? null, source: card.source ?? 'auto',
      readings: snap(card.readings),
    }
  })

  // Manual names are shown too, so they are judged too — but they are not a
  // seat's pick, and folding them into a seat's rate would credit or blame a
  // rule for a name Andy chose himself.
  for (const c of doc.cards || []) {
    if (c.source !== 'manual') continue
    rows.push({
      date: doc.date, seat: 'manual', ticker: c.ticker, shown: true,
      outcome: marks[c.ticker] ?? 'ignored', why: null, source: 'manual',
      readings: snap(c.readings),
    })
  }
  return rows
}

/** The day in four numbers. `shown` is the denominator for the first three;
 *  `empty` is deliberately outside it. */
export function tally(rows) {
  const t = { vetoed: 0, starred: 0, ignored: 0, empty: 0, shown: 0, seats: 0 }
  for (const r of rows) {
    if (r.seat !== 'manual') t.seats += 1
    t[r.outcome] = (t[r.outcome] ?? 0) + 1
    if (r.shown) t.shown += 1
  }
  return t
}
