import { describe, it, expect } from 'vitest'
import { fourQuestions, greenStreak, negativeStreak, breadthReads, themeTransitions, sentinels, voteFor, vsPrior, vsPriorSpread, VOTE_OF } from './morningReadMath'

// The morning walk's arithmetic, on hand-made fixtures shaped like the real
// files (breadth.json rows, market_light.json, groups_history.json,
// watchlist.json zones, etf_data.json rows, signals.json, correction_risk.json).

const rows = (nets) => nets.map((n, i) => ({
  date: `2026-09-${String(i + 1).padStart(2, '0')}`,
  new_highs_common: n >= 0 ? n : 0, new_lows_common: n >= 0 ? 0 : -n,
  net_advances: 100 * i, ad_line: 1000 + i, mcclellan_osc: -20 + i, pct_above_20sma: 30 + i,
}))

describe('fourQuestions — ch.1 §1.7', () => {
  const ml = { spy: { light: 'green', checks_passed: 3, checks: [{}, {}, {}], history: [{ close: 10, fast: 9, slow: 8 }] } }
  const signals = { SPY: { close: 10, sma50: 9, sma200: 8, ma_structure: { '50sma_gt_200sma': true } } }
  it('daily on, weekly on, 5 EMA missing, NH−NL off when the net fell over five sessions', () => {
    const fq = fourQuestions({ ml, signals, rows: rows([5, 4, 3, 2, 1, 0, -1]) })
    expect(fq.items.map((q) => q.state)).toEqual(['on', 'on', null, 'off'])
    expect(fq.items[2].missing).toMatch(/not in the pipeline/)
    expect(fq.rule).toMatch(/our operationalization/)
  })
  it('NH−NL on when today\'s net is above five sessions ago', () => {
    const fq = fourQuestions({ ml, signals, rows: rows([-9, -8, -7, -6, -5, -4, -3]) })
    expect(fq.items[3].state).toBe('on')
    expect(fq.items[3].read).toBe('0 − 3 = -3')
  })
  it('everything null when the files are absent', () => {
    const fq = fourQuestions({ ml: null, signals: null, rows: [] })
    expect(fq.items.map((q) => q.state)).toEqual([null, null, null, null])
  })
})

describe('streaks', () => {
  it('green streak counts trailing 3/3 sessions only', () => {
    expect(greenStreak([{ checks_passed: 3 }, { checks_passed: 1 }, { checks_passed: 3 }, { checks_passed: 3 }])).toBe(2)
    expect(greenStreak([{ checks_passed: 2 }])).toBe(0)
    expect(greenStreak(undefined)).toBe(0)
  })
  it('negative streak stops at the first non-negative or unmeasured row', () => {
    expect(negativeStreak(rows([1, -1, -1, -1]))).toBe(3)
    expect(negativeStreak(rows([-1, 2]))).toBe(0)
    expect(negativeStreak([{ new_highs_common: null, new_lows_common: 3 }, { new_highs_common: 0, new_lows_common: 3 }])).toBe(1)
  })
})

describe('breadthReads — ch.7 §7.6', () => {
  it('counts themes by state and reads the two watchlist panels', () => {
    const themes = [{ state: 'Leading' }, { state: 'Leading' }, { state: 'Lagging' }, { state: 'Bogus' }]
    const watchlist = { zones: [{ panels: [{ key: 'weekly_20_gainers', count: 36 }] }, { panels: [{ key: 'stop_hit', count: 25 }] }] }
    const r = breadthReads({ rows: rows([1, 2, 3]), themes, watchlist })
    expect(r.width).toEqual({ Leading: 2, Improving: 0, Weakening: 0, Lagging: 1 })
    expect(r.width_n).toBe(4)
    expect(r.gainers20).toBe(36)
    expect(r.stop_hit).toBe(25)
    expect(r.nhnl).toBe(3)
    expect(r.net_advances).toBe(200)
    expect(r.net_advances_prev).toBe(100)
  })
  it('reads null, never zero, when a panel is missing', () => {
    const r = breadthReads({ rows: [], themes: [], watchlist: null })
    expect(r.gainers20).toBeNull()
    expect(r.nhnl).toBeNull()
  })
})

describe('themeTransitions — ch.7 §7.2 (4)', () => {
  const gh = { dates: Array(8).fill('d'), groups: {
    A: { kind: 'theme', state: ['Lagging', 'Lagging', 'Lagging', 'Improving', 'Improving', 'Improving', 'Leading', 'Leading'] },
    B: { kind: 'theme', state: ['Leading', 'Leading', 'Leading', 'Leading', 'Weakening', 'Weakening', 'Weakening', 'Weakening'] },
    C: { kind: 'theme', state: ['Improving', 'Improving', 'Improving', 'Improving', 'Improving', 'Improving', 'Improving', 'Improving'] },
    D: { kind: 'industry', state: ['Lagging', 'Lagging', 'Lagging', 'Lagging', 'Lagging', 'Lagging', 'Lagging', 'Leading'] },
    E: { kind: 'theme', state: ['Lagging', 'Leading'] },
  } }
  it('compares today with five sessions ago, themes only, long enough series only', () => {
    const t = themeTransitions(gh)
    expect(t.up).toEqual([{ name: 'A', from: 'Lagging', to: 'Leading', dir: 'up' }])
    expect(t.down).toEqual([{ name: 'B', from: 'Leading', to: 'Weakening', dir: 'down' }])
    expect(t.lag).toBe(5)
  })
  it('is empty, not broken, without history', () => {
    expect(themeTransitions(null)).toEqual({ up: [], down: [], lag: 5, sessions: 0 })
  })
})

describe('sentinels — ch.7 §7.4 / §7.7', () => {
  const etfs = [{ ticker: 'USO', perf_1w: -0.077 }, { ticker: 'EWY', perf_1w: 0.097 }, { ticker: 'XLP', perf_1w: -0.001 },
    { ticker: 'XLU', perf_1w: -0.012 }, { ticker: 'SPY', perf_1w: 0.028 }, { ticker: 'SMH', perf_1w: 0.113 }, { ticker: 'IGV', perf_1w: 0.017 }]
  it('reads oil, Korea, the defensive test and the VIX band; the dollar stays null', () => {
    const s = sentinels({ etfs, signals: { '^VIX': { close: 14.2 } }, correctionRisk: { ts_dimension: { today: { ts_ema: 0.82, ts_label: 'neutral(0.8-1.0)' } } } })
    expect(s.oil).toBeCloseTo(-0.077)
    expect(s.korea).toBeCloseTo(0.097)
    expect(s.dollar).toBeNull()
    expect(s.defense_leading).toBe(false)
    expect(s.vix_band).toBe('complacent')
    expect(s.ts).toEqual({ value: 0.82, label: 'neutral' })
  })
  it('defensives leading when both XLP and XLU beat SPY', () => {
    const s = sentinels({ etfs: etfs.map((e) => (e.ticker === 'SPY' ? { ...e, perf_1w: -0.05 } : e)), signals: {}, correctionRisk: null })
    expect(s.defense_leading).toBe(true)
    expect(s.vix).toBeNull()
    expect(s.ts).toBeNull()
  })
})

/* Andy 2026-09-23: 「「问什么」和「读数」两栏 看不清楚」. Two mechanical rules
   came out of the clean-up, and both are the kind that rot silently. */
describe('only the engine may name a state', () => {
  const votes = { nh_nl: 'bear', t2108_zone: 'bear', mcclellan: 'bear', pct200: 'neutral', ratio_5d: 'bull' }
  it('gives the engine word for a reading the engine votes on', () => {
    expect(voteFor(votes, 'nhnl')).toBe('bear')
    expect(voteFor(votes, 'mco')).toBe('bear')
    expect(voteFor(votes, 'pct200')).toBe('neutral')
  })
  it('gives nothing for a reading the engine does not vote on', () => {
    for (const k of ['p20', 'net_advances', 'width', 'gainers20', 'leaders', 'vix', 'oil']) {
      expect(voteFor(votes, k)).toBeNull()
    }
  })
  it('gives nothing when the vote is absent or not one of the three words', () => {
    expect(voteFor({}, 'nhnl')).toBeNull()
    expect(voteFor({ nh_nl: 'mixed' }, 'nhnl')).toBeNull()
    expect(voteFor(undefined, 'nhnl')).toBeNull()
  })
  it('every mapped vote key is one the engine actually publishes', () => {
    const engineKeys = ['ratio_5d', 'ratio_10d', 'thrust', 'qtr_spread', 'spread_13_34', 'nh_nl',
      'mcclellan', 'pct200', 't2108_zone', 'spy_danger', 'qqq_danger', 'bench_trend']
    for (const k of Object.values(VOTE_OF)) expect(engineKeys).toContain(k)
  })
})

describe('a change is printed only when there is a prior session', () => {
  it('reads today against the session before it', () => {
    const d = vsPrior([{ t2108: 30 }, { t2108: 33.4 }], 't2108')
    expect([d.now, d.was]).toEqual([33.4, 30])
    expect(d.delta).toBeCloseTo(3.4, 6)
    expect(vsPriorSpread([{ new_highs_common: 4, new_lows_common: 20 }, { new_highs_common: 7, new_lows_common: 15 }],
      'new_highs_common', 'new_lows_common')).toEqual({ now: -8, was: -16, delta: 8 })
  })
  it('is null — never a zero — with one row, no rows, or a hole', () => {
    expect(vsPrior([{ t2108: 33 }], 't2108')).toBeNull()
    expect(vsPrior([], 't2108')).toBeNull()
    expect(vsPrior([{ t2108: null }, { t2108: 33 }], 't2108')).toBeNull()
    expect(vsPriorSpread([{ new_highs_common: null, new_lows_common: 2 }, { new_highs_common: 7, new_lows_common: 15 }],
      'new_highs_common', 'new_lows_common')).toBeNull()
  })
})
