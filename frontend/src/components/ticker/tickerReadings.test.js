import { describe, it, expect } from 'vitest'
import { readFileSync, readdirSync } from 'node:fs'
import { resolve } from 'node:path'
import { keyLevels, indicators, provenance } from './tickerReadings'

/**
 * The algebra, checked against bars — and the staleness it exposed.
 *
 * A moving-average price is recovered from the published distance as
 * `close / (1 + dist)`. Checking that ACROSS the two files would measure their
 * date gap, not the formula, so each ticker file is checked against ITSELF:
 * its own technicals are internally consistent, whatever day they are from.
 *
 * The cross-file comparison is worth stating because it is what sent this
 * rewrite: 200-day averages agreed to 0.01% while 20-day averages were off by
 * 4–13%. The error scaling with how fast the average moves is the signature of
 * an old file, not a wrong equation.
 */
const ROOT = resolve(process.cwd(), '..')
const load = (p) => { try { return JSON.parse(readFileSync(resolve(ROOT, p), 'utf8')) } catch { return null } }
const uni = load('data/output/universe.json')
const byTicker = uni ? Object.fromEntries(uni.rows.map((r) => [r.ticker, r])) : {}

/** ticker files that still hold their own technicals — self-consistent by
 *  construction, whichever day they were written */
const selfConsistent = (() => {
  if (!uni) return []
  const dir = resolve(ROOT, 'data/output/tickers')
  const out = []
  for (const f of readdirSync(dir)) {
    const d = load(`data/output/tickers/${f}`)
    const t = d?.technicals
    if (!t?.ma200 || !t.high_52w || !t.low_52w || d.current_price == null) continue
    out.push({ ticker: d.ticker, price: d.current_price, t })
    if (out.length >= 40) break
  }
  return out
})()

describe.skipIf(!selfConsistent.length)('the implied-price algebra', () => {
  it('recovers a moving-average price from its own distance', () => {
    for (const { price, t } of selfConsistent) {
      for (const ma of ['ma20', 'ma50', 'ma200']) {
        const dist = price / t[ma] - 1
        expect(price / (1 + dist)).toBeCloseTo(t[ma], 4)
      }
    }
  })

  it('puts a name in its 52-week range where the bars put it', () => {
    for (const { ticker, price, t } of selfConsistent) {
      if (t.position_in_52w_range_pct == null) continue
      const row = { close: price, high_52w_dist: price / t.high_52w - 1,
                    low_52w: price / t.low_52w - 1 }
      const got = indicators(row).find((r) => r.label === '52 周位置')
      expect(parseFloat(got.value), ticker).toBeCloseTo(t.position_in_52w_range_pct, 1)
    }
  })
})

describe.skipIf(!uni)('reading MRNA off the live file', () => {
  const u = byTicker.MRNA

  it('has levels the page was printing as dashes', () => {
    const lv = Object.fromEntries(keyLevels(u).map((l) => [l.label, l]))
    for (const k of ['52 周高', 'MA20', 'MA50', 'MA200', 'EMA21', 'Structure Pivot 止损']) {
      expect(lv[k].price, k).not.toBeNull()
    }
    /* An earlier version asserted the implied MA50 lands on `sp_stop`. On
       2026-08-19 they read 63.91 and 63.99 and that looked like two independent
       numbers agreeing; on 08-20 they read 65.62 and 69.86. `sp_ma` is the
       Structure Pivot's own level and was never the 50-day — it sat on it for a
       day. A coincidence written down as a law is worse than no test, because
       it fails on a true value and invites widening the tolerance until it
       passes. The algebra is checked where it can be: against each ticker
       file's own technicals, above. */
    expect(lv.MA50.dist).toBeCloseTo(u.sma50_dist * 100, 4)
  })

  it('keeps what universe genuinely does not carry absent, and says where from', () => {
    const lv = keyLevels(u)
    const missing = lv.filter((l) => l.price == null)
    expect(missing.map((l) => l.label)).toEqual(['20 日高', '10 日低', '5 日低'])
    for (const m of missing) expect(m.from).toBe('ticker_file')
    expect(indicators(u).find((r) => r.label === 'RSI(14)').from).toBe('ticker_file')
  })

  it('marks a recovered price as derived and a published one as not', () => {
    const lv = Object.fromEntries(keyLevels(u).map((l) => [l.label, l]))
    expect(lv.MA50.derived).toBe(true)
    expect(lv.EMA21.derived).toBeUndefined()
    expect(lv['Structure Pivot 止损'].derived).toBeUndefined()
  })
})

describe('provenance', () => {
  it('calls a file with news and no bars a dead price feed, not a half-live one', () => {
    const p = provenance({ bar_date: '2026-08-19', bars_stale: false },
      { fetched_at: '2026-08-20T03:30:50Z', ohlc_2y: [], info: {}, news: [1, 2, 3] })
    expect(p.tickerFile.present).toBe(true)
    expect(p.tickerFile.alive).toBe(false)
    expect(p.tickerFile.hasNews).toBe(true)
    expect(p.tickerFile.hasInfo).toBe(false)
  })

  it('measures the gap between the bars on screen and the file behind them', () => {
    const p = provenance({ bar_date: '2026-08-19' },
      { fetched_at: '2026-08-09T17:22:52Z', ohlc_2y: new Array(501) })
    expect(p.tickerFile.alive).toBe(true)
    expect(p.tickerFile.ageDays).toBe(10)
  })

  it('says nothing rather than zero when there is no file at all', () => {
    const p = provenance({ bar_date: '2026-08-19' }, null)
    expect(p.tickerFile.present).toBe(false)
    expect(p.tickerFile.ageDays).toBeNull()
  })
})
