/**
 * The morning read's arithmetic — every number the six steps print, as pure
 * functions over the files the page already fetches. No fetching here, so a
 * test can hand each function a fixture and read the sentence.
 *
 * Order and vocabulary are the course's: Foundations ch.7 §7.2 fixes the
 * morning walk — index, breadth, RS leadership, RS themes, news, your own
 * book — and ch.1 §1.7 gives the index step its four questions. Andy 09-23:
 * 「A 的骨架，把B它的「四问对照表」搬进 A 的第①段当指数那格的正文」.
 *
 * Where the course gives a rule with no numeric test (a line "going up", a
 * defensive sector "leading"), the operationalization is ours and says so in
 * the returned `rule` string — the same convention market_light.json uses for
 * its `rising_rule`. Nothing here invents a threshold the course does not give.
 */

const num = (v) => (Number.isFinite(v) ? v : null)
const last = (arr, k) => num(arr?.at?.(-1)?.[k])

/** ch.1 §1.7 — four questions, answered `on` / `off` / null (not measured). */
export function fourQuestions({ ml, signals, rows }) {
  const spy = ml?.spy
  const sig = signals?.SPY
  const h = spy?.history?.at?.(-1)
  const daily = spy?.checks
    ? (spy.light === 'green' && h && h.close > h.fast && h.close > h.slow ? 'on'
      : spy.light === 'green' ? 'on' : 'off')
    : null
  const weekly = sig?.ma_structure
    ? (sig.ma_structure['50sma_gt_200sma'] && sig.close > sig.sma200 ? 'on' : 'off')
    : null
  // 52-week net new highs "going up": today's net above the net five sessions
  // ago — our operationalization (the lesson only says "往正的方向走").
  const nets = (rows ?? []).map((r) => (num(r.new_highs_common) != null && num(r.new_lows_common) != null
    ? r.new_highs_common - r.new_lows_common : null))
  const today = nets.at(-1), ago = nets.at(-6)
  const nhnl = today == null || ago == null ? null : (today > ago ? 'on' : 'off')
  return {
    rule: 'daily = the light (10/20 EMA, three checks); weekly = 50 SMA above 200 SMA and close above the 200 (the lesson\'s 10/40-week proxy); 5 EMA not in the pipeline; NH−NL "going up" = today\'s net above five sessions ago — our operationalization',
    items: [
      { key: 'daily', label: 'Daily', on: 'above the 10/20 EMA, 10 above 20', off: 'below both lines, or 10 back under 20',
        state: daily, read: spy?.checks ? `${spy.checks_passed}/3 checks` : null },
      { key: 'weekly', label: 'Weekly', on: 'above the 10/40-week lines, 50 SMA above 200', off: 'below the 40-week, or 50 under 200',
        state: weekly, read: sig?.sma50 != null ? `50 SMA ${sig.sma50.toFixed(0)} · 200 SMA ${sig.sma200.toFixed(0)}` : null },
      { key: 'week', label: 'Last week', on: '5 EMA rising', off: '5 EMA falling', state: null, read: null, missing: '5 EMA is not in the pipeline' },
      { key: 'nhnl', label: 'New highs − lows', on: '52-week net new highs going up', off: 'going down',
        state: nhnl, read: today == null ? null : `${rows.at(-1).new_highs_common} − ${rows.at(-1).new_lows_common} = ${today > 0 ? '+' : ''}${today}` },
    ],
  }
}

/** Sessions in a row that the light has read 3/3 — "new green light, day N". */
export function greenStreak(history) {
  let n = 0
  for (let i = (history?.length ?? 0) - 1; i >= 0; i -= 1) {
    if (history[i].checks_passed === 3) n += 1
    else break
  }
  return n
}

/** Sessions in a row with common-stock net new highs below zero. */
export function negativeStreak(rows) {
  let n = 0
  for (let i = (rows?.length ?? 0) - 1; i >= 0; i -= 1) {
    const r = rows[i]
    if (num(r.new_highs_common) == null || num(r.new_lows_common) == null) break
    if (r.new_highs_common - r.new_lows_common < 0) n += 1
    else break
  }
  return n
}

/** ch.7 §7.6 — the four lines plus the two counts the lesson adds under them. */
export function breadthReads({ rows, themes, watchlist }) {
  const r = rows ?? []
  const nhnl = r.map((x) => (num(x.new_highs_common) != null && num(x.new_lows_common) != null
    ? x.new_highs_common - x.new_lows_common : null))
  const counts = { Leading: 0, Improving: 0, Weakening: 0, Lagging: 0 }
  for (const t of themes ?? []) if (t.state in counts) counts[t.state] += 1
  const panel = (k) => watchlist?.zones?.flatMap((z) => z.panels ?? []).find((p) => p.key === k)?.count ?? null
  return {
    net_advances: last(r, 'net_advances'), net_advances_prev: num(r.at(-2)?.net_advances),
    ad_line: r.map((x) => num(x.ad_line)),
    mco: last(r, 'mcclellan_osc'), mco_series: r.map((x) => num(x.mcclellan_osc)),
    nhnl: nhnl.at(-1) ?? null, nhnl_series: nhnl,
    pct20: last(r, 'pct_above_20sma'),
    width: counts, width_n: (themes ?? []).length,
    gainers20: panel('weekly_20_gainers'),
    stop_hit: panel('stop_hit'),
  }
}

/** ch.7 §7.2 (4) — who just took the lead, who just lost it, over `lag` sessions. */
export function themeTransitions(groupsHistory, lag = 5) {
  const rank = { Lagging: 0, Weakening: 1, Improving: 2, Leading: 3 }
  const out = []
  for (const [name, g] of Object.entries(groupsHistory?.groups ?? {})) {
    if (g.kind !== 'theme') continue
    const s = g.state
    if (!s || s.length <= lag) continue
    const from = s.at(-1 - lag), to = s.at(-1)
    if (from && to && from !== to) out.push({ name, from, to, dir: rank[to] > rank[from] ? 'up' : 'down' })
  }
  const up = out.filter((t) => t.dir === 'up').sort((a, b) => rank[b.to] - rank[a.to] || a.name.localeCompare(b.name))
  const down = out.filter((t) => t.dir === 'down').sort((a, b) => rank[a.to] - rank[b.to] || a.name.localeCompare(b.name))
  return { up, down, lag, sessions: groupsHistory?.dates?.length ?? 0 }
}

/** ch.7 §7.4 / §7.7 — the sentinels, from etf_data + signals + correction_risk. */
export function sentinels({ etfs, signals, correctionRisk }) {
  const by = Object.fromEntries((etfs ?? []).map((e) => [e.ticker, e]))
  const w = (t) => num(by[t]?.perf_1w)
  const vix = num(signals?.['^VIX']?.close)
  const ts = correctionRisk?.ts_dimension?.today
  const defense = w('XLP') != null && w('XLU') != null && w('SPY') != null
    ? (w('XLP') > w('SPY') && w('XLU') > w('SPY')) : null
  return {
    oil: w('USO'), korea: w('EWY'), dollar: null,
    offense: { SMH: w('SMH'), IGV: w('IGV') }, defense_leading: defense,
    defense_reads: { XLP: w('XLP'), XLU: w('XLU'), SPY: w('SPY') },
    vix, vix_band: vix == null ? null : vix < 15 ? 'complacent' : vix < 20 ? 'neutral' : vix < 25 ? 'wary' : 'fear',
    ts: ts ? { value: num(ts.ts_ema), label: String(ts.ts_label ?? '').split('(')[0] } : null,
    rule: 'defensive leading = both XLP and XLU beat SPY on the week — our operationalization; VIX bands are the lesson\'s (§7.7): <15 complacent, 15–20 neutral, >25 fear',
  }
}

/* ── the two rules that keep the readings honest (Andy 2026-09-23) ────────
 * 「「问什么」和「读数」两栏 看不清楚」. Two fixes, both mechanical:
 *   1. every reading that has a prior session prints its change; one that has
 *      no history prints nothing — never an invented "flat".
 *   2. the only state word a reading may wear is the ENGINE's vote. A reading
 *      the engine does not vote on gets no word (the mock-up gave 站上20日线
 *      and 净涨跌 words I had written myself — that is the bug, not the fix).
 */

/** Reading key → the vote key in `verdict.votes` that judges it. */
export const VOTE_OF = {
  nhnl: 'nh_nl',
  t2108: 't2108_zone',
  mco: 'mcclellan',
  pct200: 'pct200',
  ratio5: 'ratio_5d',
  ratio10: 'ratio_10d',
  qtr: 'qtr_spread',
  s1334: 'spread_13_34',
  thrust: 'thrust',
}

/** The engine's word for a reading, or null when the engine has no vote on it. */
export function voteFor(votes, readingKey) {
  const k = VOTE_OF[readingKey]
  if (!k) return null
  const v = votes?.[k]
  return v === 'bull' || v === 'bear' || v === 'neutral' ? v : null
}

/** Today minus the prior session for one archive column, or null without one. */
export function vsPrior(rows, key) {
  const r = rows ?? []
  if (r.length < 2) return null
  const now = num(r.at(-1)?.[key]), was = num(r.at(-2)?.[key])
  if (now == null || was == null) return null
  return { now, was, delta: now - was }
}

/** Same, for a reading built from two columns (highs − lows). */
export function vsPriorSpread(rows, upKey, downKey) {
  const r = rows ?? []
  if (r.length < 2) return null
  const net = (x) => (num(x?.[upKey]) != null && num(x?.[downKey]) != null ? x[upKey] - x[downKey] : null)
  const now = net(r.at(-1)), was = net(r.at(-2))
  if (now == null || was == null) return null
  return { now, was, delta: now - was }
}

const pct = (v, d = 1) => (v == null ? '—' : `${v >= 0 ? '+' : ''}${(v * 100).toFixed(d)}%`)
export { pct }
