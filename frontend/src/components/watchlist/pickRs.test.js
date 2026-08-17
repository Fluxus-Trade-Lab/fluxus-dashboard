import { describe, it, expect } from 'vitest'
import { pickRs, RS_BANDS } from './WatchlistPage'
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

describe('RS_BANDS', () => {
  it('inks the 21-day measure only at its two definitional ends', () => {
    // 21/21 is "highest relative strength of the month", 1/21 is "lowest".
    // Everything between is a matter of degree, and stays grey.
    //
    // Asserted on the VALUES THE FILE CARRIES, not on the constant. The first
    // version of this test pinned lo to exactly 100/21 and passed while the
    // band was dead: the pipeline rounds, so 1/21 arrives as 5 and 5 > 4.76.
    // A test that checks the number I wrote instead of the behaviour I wanted
    // will agree with me every time I am wrong.
    const { hi, lo } = RS_BANDS.rs_line_pctl_21
    expect(21 >= hi ? false : true).toBe(true)     // guard: hi is in 0-100 units
    expect(100 >= hi).toBe(true)                   // 21/21 inks
    expect(95 >= hi).toBe(false)                   // 20/21 does not
    expect(5 <= lo).toBe(true)                     // 1/21, as rounded, inks
    expect(10 <= lo).toBe(false)                   // 2/21 does not
  })

  it('does not reuse the cross-sectional cuts on the self-percentile', () => {
    // The 80/40 cuts are calibrated for a flat distribution. On the 29 values
    // from oratnek's screen they would have inked 76% blue and nothing red.
    const sample = [100, 100, 95, 81, 90, 81, 67, 67, 71, 100, 43, 95, 71, 57, 57,
      100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 95, 100, 95, 100]
    const blueUnderOldCuts = sample.filter((v) => v >= RS_BANDS.rs_1m.hi).length
    const blueUnderNew = sample.filter((v) => v >= RS_BANDS.rs_line_pctl_21.hi).length
    expect(blueUnderOldCuts / sample.length).toBeGreaterThan(0.7)
    expect(blueUnderNew).toBeLessThan(blueUnderOldCuts)
  })
})
