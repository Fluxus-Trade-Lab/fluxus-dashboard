/* global process */
import { describe, it, expect, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { render, screen, fireEvent } from '@testing-library/react'
import { LanguageProvider } from '../../i18n/LanguageContext'
import BreadthPage from './BreadthPage'
import { resetMarketLightCache } from '../../hooks/useMarketLight'

/* The Advanced fold mounts the lightweight-charts panels. jsdom has no canvas,
   so a real createChart throws ~224 unhandled errors and vitest exits 1 even
   with every test green (introduced by 4dae8e92b, caught 10-03). This is a
   structure test — the charts' own drawing is not what it checks. */
vi.mock('./useBreadthChart', async (orig) => ({ ...(await orig()), useBreadthChart: () => {} }))

/**
 * A mount test, not a unit test — the 2026-09-11 rewrite touched nine files
 * at once (BoardCard/ChainCard/VoteCard replacing StateBoard/VerdictBanner/
 * MarketStateSummary, plus Reference's redesign), and a bad prop threaded
 * through any one of them throws at render, not at import. `provenanceCount`
 * set the pattern this follows: mount on the real file, read the sentence.
 */
const read = (p) => JSON.parse(readFileSync(resolve(process.cwd(), '..', p), 'utf8'))
const breadth = read('data/output/breadth.json')
const market_health = read('data/output/market_health.json')
const signals = read('data/output/signals.json')

function renderPage() {
  return render(
    <LanguageProvider>
      <BreadthPage data={{ breadth, market_health, signals }} />
    </LanguageProvider>,
  )
}

/* market_light.json as DATA_CONTRACTS §七 e5546418 asks for it — the 09-10
   session: 10 EMA a hair above the 20, both falling, so 1 of 3 and red. */
const ML = {
  date: '2026-09-10', ma_type: 'EMA',
  spy: {
    checks: [
      { key: 'fast_above_slow', pass: true, a: 765.087, b: 765.086 },
      { key: 'fast_rising', pass: false, a: 765.087, b: 766.700 },
      { key: 'slow_rising', pass: false, a: 765.086, b: 765.850 },
    ],
    checks_passed: 1, light: 'red',
    gear: { n: 7, label: 'High below the line — maximum defense' },
    history: [
      { date: '2026-09-04', close: 771.2, fast: 767.0, slow: 764.1, checks_passed: 3 },
      { date: '2026-09-08', close: 768.1, fast: 767.3, slow: 764.5, checks_passed: 2 },
      { date: '2026-09-09', close: 762.4, fast: 766.7, slow: 765.9, checks_passed: 1 },
      { date: '2026-09-10', close: 757.8, fast: 765.1, slow: 765.1, checks_passed: 1 },
    ],
  },
  brightness: { setups: { count: 43 }, leaders: [{ ticker: 'MRNA', status: 'holding' }, { ticker: 'BVS', status: 'broken' }] },
}
const withFetch = (payloads) => { resetMarketLightCache(); return vi.stubGlobal('fetch', (url) => {
  const hit = Object.entries(payloads).find(([k]) => String(url).includes(k))
  return Promise.resolve({ ok: !!hit, json: () => Promise.resolve(hit ? hit[1] : null) })
}) }

describe('BreadthPage — minimal (2026-10-03)', () => {
  // Andy 2026-10-03: 「重点是数据呈现，少注解和状态判断」「做到极简」; preview
  // artifact Mf9ZEf6kYwVNSp3sR9GMNb 「对。market time machine 这个功能先下线。」
  it('mounts on the real file without throwing', () => {
    expect(() => renderPage()).not.toThrow()
  })

  it('lays out data sections in the book\'s order, with no step numbers or questions', () => {
    renderPage()
    const secs = [...document.querySelectorAll('h2')].map((h) => h.textContent)
    const order = ['Index', 'Breadth', 'Leaders', 'Themes', 'Cross-asset'].map((t) => secs.indexOf(t))
    expect(order.every((i) => i >= 0)).toBe(true)
    expect([...order].sort((x, y) => x - y)).toEqual(order)
  })

  it('carries no book citations, internal notes or the time machine', () => {
    renderPage()
    const text = document.body.textContent
    for (const gone of ['FOUNDATIONS', 'Foundations ch', '§', 'What changed', 'synthetic', 'a scan count',
      'awaiting Andy', 'Your book', 'How to read this', 'Votes', 'Conditions catalog', 'Board & chain']) {
      expect(text, gone).not.toContain(gone)
    }
    // TimeMachineBar renders 'Market Time Machine' (CSS uppercases it) -- case-blind on purpose
    expect(text).not.toMatch(/time machine/i)
  })

  it('shows the verdict with the readings it is made of', async () => {
    withFetch({ market_light: { ...ML, verdict: 'avoid', qqq: { light: 'green', checks_passed: 3 }, brightness: { ...ML.brightness, breadth: { env: 'MIXED' } } } })
    renderPage()
    expect(await screen.findByText('avoid')).toBeInTheDocument()
    const strip = screen.getByText('avoid').parentElement
    expect(strip.textContent).toContain('SPY')
    expect(strip.textContent).toContain('1/3')
    expect(strip.textContent).toContain('QQQ')
    expect(strip.textContent).toContain('Leaders')
    expect(strip.textContent).toContain('1/2')
    expect(strip.textContent).toContain('MIXED')
    vi.unstubAllGlobals()
  })

  it('leads new highs with the High-Low Index from the real file', () => {
    renderPage()
    const last = breadth.history.rows.at(-1)
    const tile = screen.getByText('High-Low Index').parentElement
    expect(tile.textContent).toContain(String(Math.round(last.high_low_index)))
    expect(tile.textContent).toContain(`${last.new_highs_common} highs · ${last.new_lows_common} lows`)
  })

  it('folds the advanced breadth closed by default and opens it on click', () => {
    renderPage()
    const btn = screen.getByText('Advanced breadth').closest('button')
    expect(btn).toHaveAttribute('aria-expanded', 'false')
    fireEvent.click(btn)
    expect(btn).toHaveAttribute('aria-expanded', 'true')
  })

  it('Correction risk prints prob, n and base rate together, from the real file', async () => {
    const cr = read('data/output/correction_risk.json')
    const tc = read('data/output/tick_cycle.json')
    vi.stubGlobal('fetch', (url) => Promise.resolve({
      ok: true,
      json: () => Promise.resolve(String(url).includes('correction_risk') ? cr : String(url).includes('tick_cycle') ? tc : null),
    }))
    renderPage()
    fireEvent.click(screen.getByText('Advanced breadth').closest('button'))
    const ts = cr.ts_dimension.today
    const probEl = await screen.findByText(`${(ts.prob_3d * 100).toFixed(1)}%`)
    const line = probEl.parentElement.textContent
    expect(line).toContain(ts.n_cell_3d.toLocaleString())
    expect(line).toContain(`${(cr.base_rate * 100).toFixed(1)}%`)
    expect(screen.getByText(/no fitted parameters/)).toBeInTheDocument()
    expect(screen.getByText(cr.caveats[0])).toBeInTheDocument()
    expect(screen.getByText('Side readings')).toBeInTheDocument()
    // only the Raschke chart's heading — the text-only block inside Correction
    // risk came off 10-03 (Andy: 「上面那个没数据，删除。」)
    expect(screen.getAllByText('TICK cycle')).toHaveLength(1)
    // the chart itself sits inside the fold (red if <TickCycleChart /> is removed)
    expect(await screen.findByRole('img', { name: /TICK 10-day averages of high, close and low, \d+ sessions/ })).toBeInTheDocument()
    vi.unstubAllGlobals()
  })

  it('pins today as the archive\'s first row, bold, with the A/D line', () => {
    renderPage()
    fireEvent.click(screen.getByText('Advanced breadth').closest('button'))
    const today = document.querySelector('tr.today')
    expect(today.className).toMatch(/sticky/)
    expect(today.className).toMatch(/font-semibold/)
    const last = breadth.history.rows.at(-1)
    const [, m, d] = last.date.split('-')
    expect(today.textContent).toContain(`${parseInt(m)}/${parseInt(d)}`)
    expect(screen.getByText('A/D line')).toBeInTheDocument()
    expect(today.textContent).toContain(last.ad_line.toLocaleString())
  })

  it('Advanced breadth drops the panels that repeated the main screen (Andy 选 A, 2026-10-03)', () => {
    renderPage()
    fireEvent.click(screen.getByText('Advanced breadth').closest('button'))
    for (const gone of [/^% above 20 \/ 50 \/ 200 SMA$/i, /^Up\/down ratio · 5D \/ 10D/i, /^Quarterly ±25% spread · Stockbee/i, /^Quarterly breadth \(25%\+\)/, /^5-day \/ 10-day ratio/, /^McClellan Oscillator \(Nasdaq-100\)/i]) {
      expect(screen.queryAllByText(gone)).toHaveLength(0)
    }
    expect(screen.getByText('Advanced breadth').closest('button').textContent).toMatch(/4/)
    // Benchmarks off the page 10-03 (Andy: 「图1的内容全部下线」)
    for (const gone of ['Distance from each average', 'Below 20 SMA', 'warnings as of']) {
      expect(screen.queryAllByText(new RegExp(gone, 'i'))).toHaveLength(0)
    }
  })

  it('moves the three series only Advanced had into the main chart\'s indicator menu', () => {
    renderPage()
    for (const l of ['McClellan summation (NDX)', 'Up/down ratio · 5 / 10-day (Stockbee)', 'Quarterly ±25% spread (Stockbee)']) {
      expect(screen.getByRole('button', { name: l })).toBeInTheDocument()
    }
  })
})

import { CondGrid, StateBars, TickEvidence } from './CorrectionRiskPanel'

describe('Correction risk charts', () => {
  const cr = read('data/output/correction_risk.json')
  const tc = read('data/output/tick_cycle.json')

  it('rings exactly one cell of the grid, and it is today\'s', () => {
    const t = { ...cr.today, ts_state: cr.ts_dimension.today.ts_state }
    const { container } = render(<CondGrid ts={cr.ts_dimension} today={t} />)
    const rings = container.querySelectorAll('rect[stroke-width="2.2"]')
    expect(rings.length).toBe(1)
    const title = rings[0].parentElement.querySelector('title').textContent
    expect(title).toContain(`${(cr.ts_dimension.today.prob_3d * 100).toFixed(1)}%`)
    expect(title).toContain(cr.ts_dimension.today.n_cell_3d.toLocaleString())
  })

  it('draws a reading\'s state bars from its own table, and nothing without one', () => {
    const { table: _drop, ...bare } = cr.side_readings.nhnl
    expect(render(<StateBars reading={bare} />).container.firstChild).toBeNull()
    for (const k of ['nhnl', 'gex']) {
      const rd = cr.side_readings[k]
      const { container } = render(<StateBars reading={rd} />)
      expect(container.querySelectorAll('rect').length).toBe(Object.keys(rd.table).length)
      const on = container.querySelector('rect[opacity="1"]').parentElement.textContent
      expect(on).toContain(`${(rd.table[rd.today_state].rate * 100).toFixed(0)}%`)
    }
  })

  it('draws the TICK comparison from the evidence block', () => {
    const { container } = render(<TickEvidence e={tc.evidence} />)
    expect(container.querySelectorAll('rect').length).toBe(4)
    expect(container.textContent).toContain(`${(tc.evidence.sell_p_dd5 * 100).toFixed(1)}%`)
  })
})

/* Andy 09-11: 「原有的数据它可能只是以不同的前端形式而呈现了。是不是这样子」 — every
   field the old VerdictBanner printed has to reach the page. The 09-11 rebuild
   dropped five; this pins all seven columns so it cannot happen quietly again. */
