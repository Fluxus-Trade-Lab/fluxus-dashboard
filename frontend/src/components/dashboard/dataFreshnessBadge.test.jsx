import { describe, it, expect, vi, afterEach } from 'vitest'
import { render } from '@testing-library/react'
import DataFreshnessBadge from './DataFreshnessBadge'

/* The badge reads the wall clock, so the clock is the fixture. ET "today" for
   all of these is 2026-08-27 (the UTC instant is 02:57 on the 28th — the same
   trap the JST host falls into, held still on purpose). */
const NOW = new Date('2026-08-28T02:57:00Z')
const at = (d) => { vi.useFakeTimers(); vi.setSystemTime(NOW); return render(<DataFreshnessBadge sessionDate={d} />) }
afterEach(() => vi.useRealTimers())

describe('DataFreshnessBadge', () => {
  it('renders nothing when the data is current — silence is the reading', () => {
    expect(at('2026-08-26').container.textContent).toBe('')
    expect(at('2026-08-27').container.textContent).toBe('')
  })

  it('says how far behind, and names the session it is showing', () => {
    const t = at('2026-08-25').container.textContent.replace(/\s+/g, ' ')
    expect(t).toContain('2')
    expect(t).toContain('weekdays behind')
    expect(t).toContain('newest Aug 25')
  })

  it('stays ink while merely behind — no colour for a two-day gap', () => {
    const el = at('2026-08-25').container.querySelector('span')
    expect(el.getAttribute('style')).toContain('--color-text-secondary')
    expect(el.getAttribute('style')).not.toContain('--color-refused')
  })

  it('turns red at four weekdays — a page this stale is the binding constraint', () => {
    const el = at('2026-08-21').container.querySelector('span')
    expect(el.getAttribute('style')).toContain('--color-refused')
    // textContent has no space between the count and the word — they are
    // separate elements with a flex gap, which the DOM does not render as text
    expect(el.textContent.replace(/\s+/g, ' ')).toContain('4weekdays behind')
  })

  it('renders nothing rather than guessing when no session date arrived', () => {
    expect(at(null).container.textContent).toBe('')
  })
})
