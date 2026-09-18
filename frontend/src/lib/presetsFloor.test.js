/* global process */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

/* Nighty Zac 09-18: nine presets carried marketCapMin 1.0 and Weekly Momentum 97
   carried none, so when the universe doubled (06-26) only that preset's hit
   history filled with sub-$1B names (63.5%) while the watchlist's global
   $1B gate hid the difference on the page. Every built-in preset carries a floor. */
describe('built-in screener presets', () => {
  const presets = JSON.parse(readFileSync(resolve(process.cwd(), 'public/data/screener-presets.json'), 'utf8'))

  it('every built-in preset states a market-cap floor', () => {
    const missing = presets.filter((p) => p.readonly && !(p.filters?.marketCapMin > 0)).map((p) => p.name)
    expect(missing).toEqual([])
  })
})
