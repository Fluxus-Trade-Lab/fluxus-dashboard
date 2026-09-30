import { describe, it, expect } from 'vitest'
import { computeThemeStrength, classifyThemeState } from './themeStrengthMath'

describe('classifyThemeState', () => {
  it('matches proxy_board.py classify(): excess sign picks the pair, momentum>=0 picks the good half', () => {
    expect(classifyThemeState(1, 1)).toBe('leading')
    expect(classifyThemeState(1, -0.01)).toBe('weakening')
    expect(classifyThemeState(-1, 0)).toBe('improving')   // 零算正
    expect(classifyThemeState(-1, -0.01)).toBe('lagging')
  })

  it('zero excess falls to the improving/lagging pair, same as level > 0 being false', () => {
    expect(classifyThemeState(0, 5)).toBe('improving')
    expect(classifyThemeState(0, -5)).toBe('lagging')
  })

  it('either input missing means no reading, not a guess', () => {
    expect(classifyThemeState(null, 1)).toBe(null)
    expect(classifyThemeState(1, null)).toBe(null)
    expect(classifyThemeState(null, null)).toBe(null)
  })
})

describe('computeThemeStrength', () => {
  const themeBoard = {
    themes: [
      { theme: 'Cybersecurity', proxy_ret: [-0.65, 7.81] },
      { theme: 'No Prior Bucket', proxy_ret: [2, null] },
      { theme: 'No Reading At All', proxy_ret: [null, null] },
    ],
    member_returns: {
      NET: [7.65, 9.31],     // excess = 8.3, momentum = (7.65-9.31)-(-0.65-7.81) = -1.66-(-8.46) = 6.8
      OKTA: [7.58, 9.42],
      RPD: [-6.06, 5.46],
      // GHOST intentionally absent — the priced-but-not-in-member_returns case
    },
  }

  it('computes excess and momentum with the one-subtraction formula, and classifies off them', () => {
    const m = computeThemeStrength(themeBoard, 'Cybersecurity', ['NET', 'OKTA', 'RPD'])
    const net = m.get('NET')
    expect(net.excess).toBeCloseTo(7.65 - -0.65, 10)
    expect(net.momentum).toBeCloseTo((7.65 - 9.31) - (-0.65 - 7.81), 10)
    expect(net.state).toBe('leading')
  })

  it('a ticker missing from member_returns does not enter the ranking at all — not as a zero', () => {
    const m = computeThemeStrength(themeBoard, 'Cybersecurity', ['NET', 'OKTA', 'RPD', 'GHOST'])
    expect(m.has('GHOST')).toBe(false)
    expect(m.size).toBe(3)
    // with GHOST excluded, top-25% of 3 members is ceil(0.75) = 1 — NET only
    expect(m.get('NET').topQuartile).toBe(true)
    expect(m.get('OKTA').topQuartile).toBe(false)
    expect(m.get('RPD').topQuartile).toBe(false)
  })

  it('a member with mr[0] present but mr[1] missing keeps its excess but gets no state', () => {
    const board = {
      themes: [{ theme: 'Cybersecurity', proxy_ret: [-0.65, 7.81] }],
      member_returns: { LONE: [3, null] },
    }
    const m = computeThemeStrength(board, 'Cybersecurity', ['LONE'])
    expect(m.get('LONE').excess).toBeCloseTo(3.65, 10)
    expect(m.get('LONE').momentum).toBe(null)
    expect(m.get('LONE').state).toBe(null)
    // still ranked purely on excess — the top-25% cut does not require momentum
    expect(m.get('LONE').topQuartile).toBe(true)
  })

  it('the theme itself missing its current-bucket proxy_ret yields an empty map, not a NaN excess', () => {
    const m = computeThemeStrength(themeBoard, 'No Reading At All', ['NET'])
    expect(m.size).toBe(0)
  })

  it('a theme name not on the board, or an empty roster, or no board at all, all come back empty', () => {
    expect(computeThemeStrength(themeBoard, 'Nonesuch', ['NET']).size).toBe(0)
    expect(computeThemeStrength(themeBoard, 'Cybersecurity', []).size).toBe(0)
    expect(computeThemeStrength(themeBoard, 'Cybersecurity', undefined).size).toBe(0)
    expect(computeThemeStrength(null, 'Cybersecurity', ['NET']).size).toBe(0)
    expect(computeThemeStrength(themeBoard, null, ['NET']).size).toBe(0)
  })

  it('top-25% cutoff is a ceiling, not a floor — 5 ranked members cut after 2, not 1', () => {
    const board = {
      themes: [{ theme: 'T', proxy_ret: [0, 0] }],
      member_returns: {
        A: [5, 0], B: [4, 0], C: [3, 0], D: [2, 0], E: [1, 0],
      },
    }
    const m = computeThemeStrength(board, 'T', ['A', 'B', 'C', 'D', 'E'])
    expect(m.get('A').topQuartile).toBe(true)
    expect(m.get('B').topQuartile).toBe(true)
    expect(m.get('C').topQuartile).toBe(false)
    expect(m.get('D').topQuartile).toBe(false)
    expect(m.get('E').topQuartile).toBe(false)
  })
})
