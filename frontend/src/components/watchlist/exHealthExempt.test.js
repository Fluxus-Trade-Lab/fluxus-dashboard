import { describe, it, expect } from 'vitest'
import { shown } from './WatchlistPage'

/**
 * One view, and the one scan it is not allowed to touch.
 *
 * `exclude healthcare` is a momentum-grid habit: biotech binaries add noise to
 * a list you are ranking by strength. Episodic Pivot is not that list. An EP is
 * a REPRICING — a gap on news — and biotech is the main factory for those, so
 * the data side built the panel without the exclusion on purpose. A global
 * switch that quietly emptied it would be the page overriding a screen's own
 * definition, which is the one thing a view may not do.
 *
 * The panel ships with tonight's cron, so this is the only place the behaviour
 * can be seen until then. It is also the only place the wiring can be wrong in
 * a way that looks fine: `shown` reads `panel.key`, and a panel that arrived
 * without one would fall straight through the exemption and be filtered.
 */
const bio = { ticker: 'MRNA', sector: 'Healthcare', rs_1m: 90, top_3m: true, rs_high: true }
const chip = { ticker: 'NVDA', sector: 'Technology', rs_1m: 90, top_3m: true, rs_high: true }

describe('the healthcare view', () => {
  it('empties Healthcare out of an ordinary momentum panel', () => {
    const panel = { key: 'heating_up', measured: true, tickers: [bio, chip] }
    expect(shown(panel, { exHealth: true }).map((r) => r.ticker)).toEqual(['NVDA'])
  })

  it('does not apply to Episodic Pivot, where biotech is the main product', () => {
    const panel = { key: 'episodic_pivot', measured: true, tickers: [bio, chip] }
    expect(shown(panel, { exHealth: true }).map((r) => r.ticker)).toEqual(['MRNA', 'NVDA'])
  })

  it('leaves the exempt panel open to every other switch', () => {
    const panel = { key: 'episodic_pivot', measured: true, tickers: [bio, { ...chip, top_3m: false }] }
    expect(shown(panel, { exHealth: true, pool3m: true }).map((r) => r.ticker)).toEqual(['MRNA'])
  })

  it('does not exempt a panel that arrived without a key', () => {
    const panel = { measured: true, tickers: [bio, chip] }
    expect(shown(panel, { exHealth: true }).map((r) => r.ticker)).toEqual(['NVDA'])
  })
})
