import { describe, it, expect, vi, beforeEach } from 'vitest'
import { act, render } from '@testing-library/react'

/**
 * A width drawn as a width, and never as an alarm.
 *
 * The data side proposed grind = red, washout = green. The payload's own
 * numbers refuse it: entering the contracted band halves the next 21 days'
 * median return AND cuts the probability of a 5% drawdown — 9.9% against a
 * 15.4% baseline over 17 years. A red light above a sentence that ends
 * 「磨，不是崩」would contradict the sentence.
 *
 * Red is also already spoken for on this page: the regime badge turns red only
 * when the band binds what you may carry. Two meanings for one token is the
 * failure this design system has a rule about.
 */
beforeEach(() => { vi.resetModules(); vi.restoreAllMocks() })

const DOC = {
  as_of: '2026-08-21', band: 'grind', band_since: '2026-08-06',
  spread_rank252: 0.024, stale_days: 0,
  reading: '红带磨市：…5% 回撤概率反而低于基准（9.9% vs 15.4%）——磨，不是崩。',
  evidence: { sell_p_dd5: 0.099, base_p_dd5: 0.154 },
}
/* The hook caches the file at module scope — deliberately, so the card and any
   later reader fetch it once per session. Which means a test drawing twice must
   reset the module between, or the second draw silently gets the first's data
   and an assertion about the difference passes on identical output. */
const draw = async (doc) => {
  vi.resetModules()
  globalThis.fetch = () => Promise.resolve({ ok: !!doc, json: async () => doc })
  const { default: TickBand } = await import('./TickBand')
  let c
  await act(async () => { c = render(<TickBand />) })
  await act(async () => { await new Promise((r) => setTimeout(r, 0)) })
  return c
}
const strokes = (c) => [...c.container.querySelectorAll('line')]
  .map((l) => l.getAttribute('stroke'))

describe('the TICK band', () => {
  it('prints the engine’s sentence rather than a word of its own', async () => {
    const c = await draw(DOC)
    expect(c.container.textContent).toContain('磨，不是崩')
    expect(c.container.textContent).toContain('2026-08-06 入带')
  })

  it('uses no colour that could read as a side', async () => {
    const c = await draw(DOC)
    for (const s of strokes(c)) {
      expect(s).not.toMatch(/refused|took|signal-riskoff|red|green/i)
      expect(s).toMatch(/var\(--color-(text|border)\)/)
    }
  })

  it('draws the gap narrow when the year says narrow, wide when wide', async () => {
    const gap = (c) => {
      const ys = [...c.container.querySelectorAll('line')]
        .filter((l) => !l.getAttribute('stroke-dasharray'))
        .map((l) => +l.getAttribute('y1'))
      return Math.abs(ys[1] - ys[0])
    }
    const tight = gap(await draw({ ...DOC, spread_rank252: 0.02 }))
    const wide = gap(await draw({ ...DOC, spread_rank252: 0.95 }))
    expect(wide).toBeGreaterThan(tight * 3)
  })

  it('says not-measured on a stale file instead of drawing a reading', async () => {
    const c = await draw({ ...DOC, stale_days: 9 })
    expect(c.container.textContent).toContain('未测量')
    expect(c.container.textContent).toContain('9 天没更新')
    expect(c.container.textContent).not.toContain('磨，不是崩')
    expect(c.container.textContent).not.toContain('入带')
  })

  it('renders nothing at all rather than an empty frame before the file exists', async () => {
    const c = await draw(null)
    expect(c.container.textContent).toBe('')
  })
})
