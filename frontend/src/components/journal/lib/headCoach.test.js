/**
 * The head coach ranks by leak PER TRADE, and says nothing when it cannot.
 *
 * The per-trade rule is the whole design: on the real book the two stages'
 * totals were 397.8R and 361.8R — a tie by total — while per trade they were
 * 5.7R and 1.9R. A ranking by total would have picked whichever stage happened
 * to see more trades.
 */
import { describe, expect, it } from 'vitest'
import { headline, stageLeaks } from './headCoach'

const t = (lesson, realized, optimal) => ({
  closed: true, lesson, realized_R: realized, optimal_R: optimal,
})

/**
 * Many small selection leaks against few large holding ones, arranged so the
 * two rankings DISAGREE — 50x2R = 100R for selection against 10x8R = 80R for
 * holding. By total, selection is worse; per trade, holding is four times
 * worse. If the fixture did not disagree the test below would prove nothing.
 */
const BOOK = [
  ...Array.from({ length: 50 }, () => t('Failed setup', -1, 1)),      // 2R each
  ...Array.from({ length: 10 }, () => t('Premature trim', 1, 9)),     // 8R each
  ...Array.from({ length: 10 }, () => t('Good execution', 5, 5)),     // no stage
]

describe('stage leaks', () => {
  it('measures the gap between what was made and what was there', () => {
    const [worst] = stageLeaks(BOOK)
    expect(worst.stage).toBe('hold')
    expect(worst.perTrade).toBeCloseTo(8, 6)
    expect(worst.n).toBe(10)
  })

  it('ranks per trade, not by total — the totals here favour the other stage', () => {
    const rows = stageLeaks(BOOK)
    const byTotal = [...rows].sort((a, b) => b.leak - a.leak)
    expect(rows[0].stage).toBe('hold')        // 80R over 10 trades  = 8R each
    expect(byTotal[0].stage).toBe('select')   // 100R over 50 trades = 2R each
  })

  it('good execution belongs to no stage', () => {
    expect(stageLeaks(BOOK).some((r) => r.lessons['Good execution'])).toBe(false)
  })

  it('a trade that beat its best possible leaks nothing, never negative', () => {
    const [row] = stageLeaks([t('Premature trim', 3, 2)])
    expect(row.leak).toBe(0)
  })

  it('drops a split artefact rather than letting it own the ranking', () => {
    // One SOXS trade reported +4,827R against a 1R risk unit. Unfiltered it
    // would make its stage the answer forever.
    const rows = stageLeaks([...BOOK, t('Failed setup', -1, 4827)])
    expect(rows[0].stage).toBe('hold')
  })
})

describe('the sentence', () => {
  it('names the stage and the number that argues for it', () => {
    const h = headline(BOOK)
    expect(h.stage).toBe('hold')
    expect(h.parts.worstPerTrade).toBeCloseTo(8, 6)
    expect(h.parts.bestPerTrade).toBeCloseTo(2, 6)
    expect(h.lesson.lesson).toBe('Premature trim')
  })

  it('says nothing on too little history', () => {
    expect(headline(BOOK.slice(0, 5))).toBeNull()
  })

  it('says nothing when only one stage has any trades', () => {
    expect(headline(Array.from({ length: 40 }, () => t('Failed setup', -1, 1)))).toBeNull()
  })

  it('ignores open trades', () => {
    const open = BOOK.map((x) => ({ ...x, closed: false }))
    expect(headline(open)).toBeNull()
  })
})
