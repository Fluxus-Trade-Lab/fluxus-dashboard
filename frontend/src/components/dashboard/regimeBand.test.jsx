import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import RegimeBand from './RegimeBand'

/**
 * The card prints one word. These are the three things that word hides.
 *
 * Measured over the 260 sessions in breadth.json on 2026-08-20:
 *
 *   1. On 76 of them — 29% — the badge word disagrees with the number beside
 *      it, because a voter pulled the reading below what the score alone gives.
 *      Structure did 63 of the 76; 25 were pulls of two or three whole bands.
 *   2. The top band held 26% of sessions in 21 runs, median run ONE DAY. A word
 *      that common needs its denominator or it reads as an alarm.
 *   3. `regime.py` calls >= 75 Extended over NINE conditions; this file calls
 *      >= 84 Euphoria over FIFTEEN. On 39 sessions — 15% — the analysis layer
 *      is in its top band and the display is not. 2026-08-20 is one of them:
 *      76 / NEUTRAL beside 75.0 / Extended.
 */

const HISTORY = [
  // 10 sessions: 4 in Constructive (62-83), 6 elsewhere — a 40% base rate
  ...[70, 65, 75, 80].map((score, i) => ({ date: `2026-01-0${i + 1}`, score })),
  ...[30, 35, 45, 50, 90, 95].map((score, i) => ({ date: `2026-02-0${i + 1}`, score })),
]
const up = { spy_state: 'Uptrend', qqq_state: 'Uptrend' }
const power = (sig) => ({ SPY: { signal: sig, power_trend: {} }, QQQ: { signal: sig, power_trend: {} } })
const draw = (p) => render(<RegimeBand conditions={{ history: HISTORY, n_votes: 15 }} {...p} />)
const flat = (c) => c.container.textContent.replace(/\s+/g, ' ')

/* 2026-08-24: the prose went. Andy read this page and struck out every
   sentence on it — "62 scores Constructive, as did 32% of the last 260
   sessions. Pulled to Neutral by breadth and structure" among them. These
   tests now pin the ABSENCE, because a sentence that returns by accident is
   how a page grows its prose back. The reading itself did not go anywhere: the
   three voters still print and the binding one still carries the ink, which is
   the same fact in three words. */
describe('the sentence that used to explain the word', () => {
  it('does not print, on the day it had the most to say', () => {
    const c = draw({
      conditions: { today: 76, history: HISTORY, n_votes: 15 },
      verdict: { score: 6, spy_state: 'Sideways', qqq_state: 'Sideways' },
      signals: power('POWER_3'),
    })
    const t = flat(c)
    expect(t).not.toContain('scores Constructive')
    expect(t).not.toContain('Pulled to')
    expect(t).not.toContain('% of the last')
    // and the band it argues about is still stated, in one word (the badge
    // uppercases in CSS, so the text node is title case)
    expect(t).toContain('Neutral')
  })

  it('does not print the voter row either — only the word it produces', () => {
    const c = draw({
      conditions: { today: 76, history: HISTORY, n_votes: 15 },
      verdict: { score: 6, spy_state: 'Sideways', qqq_state: 'Sideways' },
      signals: power('POWER_3'),
    })
    const t = flat(c)
    // the row went on 2026-08-24; the votes still decide the word
    expect(c.container.querySelectorAll('ul li')).toHaveLength(0)
    expect(t).not.toContain('SPY+QQQ not in uptrend')
    expect(t).not.toContain('SPY POWER 3')
    expect(t).toContain('Neutral')
  })
  it('still lets the weakest voter pull the band down — only the sentence went', () => {
    const c = draw({
      conditions: { today: 90, history: HISTORY, n_votes: 15 },
      verdict: { score: 5, spy_state: 'Uptrend', qqq_state: 'Sideways' },
      signals: power('POWER_3'),
    })
    // 90 alone reads Euphoria; two voters short of it pull the word down
    expect(flat(c)).toContain('Constructive')
  })
})

describe('the two schemes', () => {
  /* This card cuts five bands over `conditions.today` (fifteen conditions, for
     position size); `regime.py` cuts four over `regime.score` (nine conditions,
     empirical quartiles, for analysis). Both still run. Only one was ever
     actionable from this page, and on 2026-08-24 the other stopped printing
     here. */
  it('says nothing about the analysis layer, even when it reported', () => {
    const c = draw({
      conditions: { today: 76, history: HISTORY, n_votes: 15 },
      verdict: { score: 6, spy_state: 'Sideways', qqq_state: 'Sideways' },
      signals: power('POWER_3'),
      regime: { score: 75.0, band_label: 'Extended', of: 9 },
    })
    const t = flat(c)
    expect(t).not.toContain('analysis scheme')
    expect(t).not.toContain('75 / 100')
    expect(t).not.toContain('Extended')
    expect(t).toContain('76 / 100')   // this card's own score is untouched
  })
})

describe('the guard in front of all of it', () => {
  it('says which voters are missing instead of printing a reading off two', () => {
    const c = draw({ conditions: { today: 76, history: HISTORY }, verdict: { score: 6, ...up } })
    const t = flat(c)
    expect(t).toContain('Not measured')
    expect(t).toContain('power')
    expect(t).not.toContain('scores Constructive')
  })
})
