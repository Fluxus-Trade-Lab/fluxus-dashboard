import { describe, it, expect } from 'vitest'
import { pickRs } from './WatchlistPage'
import { translations } from '../../i18n/translations'

/**
 * The number beside a ticker, and the sentence naming it, come from one pick.
 *
 * Three hundred numbers sat on this page with nothing saying what they were,
 * and the file is about to start carrying a SECOND measure that means something
 * different — oratnek's, decoded 2026-08-17: the close/SPY ratio's own
 * percentile over its last 21 sessions, where 100 is a one-month high in
 * relative strength, not a rank against other names. Printing one under the
 * other's name would be worse than the missing label was.
 */
describe('pickRs', () => {
  it('falls back to rs_1m while the new column has not shipped', () => {
    expect(pickRs([{ ticker: 'A', rs_1m: 91 }, { ticker: 'B', rs_1m: 40 }])).toBe('rs_1m')
  })

  it('prefers the 21-day self-percentile as soon as any row carries it', () => {
    expect(pickRs([{ ticker: 'A', rs_1m: 91 }, { ticker: 'B', rs_1m: 40, rs_line_pctl_21: 57 }]))
      .toBe('rs_line_pctl_21')
  })

  it('treats a present-but-null column as absent', () => {
    // A name with fewer than 21 bars gets null, per the contract. One null row
    // must not switch the whole page onto a column nothing else has either.
    expect(pickRs([{ ticker: 'A', rs_1m: 91, rs_line_pctl_21: null }])).toBe('rs_1m')
  })

  it('says nothing at all on an empty list rather than guessing', () => {
    expect(pickRs([])).toBe('rs_1m')
    expect(pickRs()).toBe('rs_1m')
  })

  it('has a legend for every value it can return, in both languages', () => {
    for (const key of ['rs_1m', 'rs_line_pctl_21']) {
      for (const lang of ['en', 'zh']) {
        expect(translations[lang][`wl.rskey.${key}`], `${lang}/${key}`).toBeTruthy()
      }
    }
  })
})
