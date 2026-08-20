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

describe('the pull-down reason', () => {
  it('names the voter and its condition when the word disagrees with the number', () => {
    const c = draw({
      conditions: { today: 76, history: HISTORY, n_votes: 15 },
      verdict: { score: 6, spy_state: 'Sideways', qqq_state: 'Sideways' },
      signals: power('POWER_3'),
    })
    const t = flat(c)
    expect(t).toContain('76 scores Constructive')
    expect(t).toContain('Pulled to Neutral by structure')
    expect(t).toContain('SPY and QQQ below trend')
  })

  it('says nothing about a pull on a day when nothing pulls', () => {
    const c = draw({
      conditions: { today: 50, history: HISTORY, n_votes: 15 },
      verdict: { score: 9, ...up },
      signals: power('POWER_3'),
    })
    expect(flat(c)).toContain('50 scores Neutral')
    expect(flat(c)).not.toContain('Pulled to')
  })

  it('names both voters, and conjugates, when two fail together', () => {
    const c = draw({
      conditions: { today: 90, history: HISTORY, n_votes: 15 },
      verdict: { score: 5, spy_state: 'Uptrend', qqq_state: 'Sideways' },
      signals: power('POWER_3'),
    })
    expect(flat(c)).toContain('Pulled to Constructive by breadth and structure')
  })

  it('prints all three voters and inks only the binding one', () => {
    const c = draw({
      conditions: { today: 76, history: HISTORY, n_votes: 15 },
      verdict: { score: 6, spy_state: 'Sideways', qqq_state: 'Sideways' },
      signals: power('POWER_3'),
    })
    const items = [...c.container.querySelectorAll('ul li')]
    expect(items.map((li) => li.textContent.trim().split(' ')[0])).toEqual(['breadth', 'structure', 'power'])
    const bold = items.filter((li) => li.querySelector('.font-semibold'))
    expect(bold).toHaveLength(1)
    expect(bold[0].textContent).toContain('structure')
  })
})

describe("the band's base rate", () => {
  it('counts the score into its band over the loaded history', () => {
    const c = draw({
      conditions: { today: 70, history: HISTORY, n_votes: 15 },
      verdict: { score: 9, ...up },
      signals: power('POWER_3'),
    })
    expect(flat(c)).toContain('as did 40% of the last 10 sessions')
  })

  it('omits the rate rather than inventing one when there is no history', () => {
    const c = render(<RegimeBand conditions={{ today: 70 }} verdict={{ score: 9, ...up }}
                                 signals={power('POWER_3')} />)
    expect(flat(c)).toContain('70 scores Constructive.')
    expect(flat(c)).not.toContain('% of the last')
  })
})

describe('the two schemes', () => {
  it('prints the analysis band with its own score and its own denominator', () => {
    const c = draw({
      conditions: { today: 76, history: HISTORY, n_votes: 15 },
      verdict: { score: 6, spy_state: 'Sideways', qqq_state: 'Sideways' },
      signals: power('POWER_3'),
      regime: { score: 75.0, band_label: 'Extended', of: 9 },
    })
    const t = flat(c)
    // the seam, live: top band by one scheme, second band by the other
    expect(t).toContain('75 / 100 Extended')
    expect(t).toContain('9 conditions')
    expect(t).toContain('the band above counts 15')
  })

  it('prints nothing at all when the analysis layer did not report', () => {
    const c = draw({
      conditions: { today: 76, history: HISTORY, n_votes: 15 },
      verdict: { score: 6, ...up }, signals: power('POWER_3'),
    })
    expect(flat(c)).not.toContain('analysis scheme')
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
