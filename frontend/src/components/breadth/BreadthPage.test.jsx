/* global process */
import { describe, it, expect, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { render, screen, fireEvent } from '@testing-library/react'
import { LanguageProvider } from '../../i18n/LanguageContext'
import BreadthPage from './BreadthPage'
import { resetMarketLightCache } from '../../hooks/useMarketLight'

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
    checks_passed: 1, light: 'red', plus_n: -3,
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

describe('BreadthPage — in the course\'s order (09-11)', () => {
  it('mounts on the real file without throwing', () => {
    expect(() => renderPage()).not.toThrow()
  })

  it('leads with the course\'s Core: verdict, the light, brightness', () => {
    renderPage()
    expect(screen.getByText('Today')).toBeInTheDocument()
    expect(screen.getByText('Step 1 · The light')).toBeInTheDocument()
    expect(screen.getByText('Step 2 · Brightness')).toBeInTheDocument()
    // the old second verdict is gone from the page
    expect(screen.queryByText(/signals say no/)).not.toBeInTheDocument()
  })

  it('says "not measured" — never a zero — until market_light.json exists', () => {
    renderPage()
    expect(screen.getByText(/Today's aggression — not measured/)).toBeInTheDocument()
    expect(screen.getByText(/The light — not measured/)).toBeInTheDocument()
  })

  it('reads a red light as AVOID and fades step 2, from a contract-shaped file', async () => {
    withFetch({ market_light: ML })
    renderPage()
    expect((await screen.findAllByText('AVOID')).length).toBeGreaterThan(0)
    expect(screen.getByText(/The light is red — 1 of 3 checks/)).toBeInTheDocument()
    expect(screen.getByText('in-between: counts as red')).toBeInTheDocument()
    expect(screen.getByText(/the course says skip this step today/)).toBeInTheDocument()
    expect(screen.getByText('-3')).toBeInTheDocument()
    expect(screen.getByText('7 / 7')).toBeInTheDocument()
    vi.unstubAllGlobals()
  })

  it('keeps the board rows, now inside the Board & chain fold', () => {
    renderPage()
    fireEvent.click(screen.getByText('Board & chain').closest('button'))
    for (const row of breadth.state_board.rows) {
      expect(screen.getAllByText(new RegExp(`^${row.key}$`, 'i')).length).toBeGreaterThan(0)
    }
  })

  it('shows the votes as evidence first, with the engine\'s own call kept and labelled', () => {
    renderPage()
    fireEvent.click(screen.getByText('Votes').closest('button'))
    expect(screen.getByText(/evidence for Q3, not a call/)).toBeInTheDocument()
    expect(screen.getByText(/confirming ·/)).toBeInTheDocument()
    expect(screen.getByText(/engine’s own reading — for reference, not today’s call/)).toBeInTheDocument()
    expect(screen.getByText(breadth.verdict.guidance)).toBeInTheDocument()
  })

  it('folds the reference rows closed by default and opens one on click', () => {
    renderPage()
    const btn = screen.getByText('Archive').closest('button')
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
    fireEvent.click(screen.getByText('Correction risk').closest('button'))
    const ts = cr.ts_dimension.today
    const prob = `${(ts.prob_3d * 100).toFixed(1)}%`
    const probEl = await screen.findByText(prob)
    const line = probEl.parentElement.textContent
    expect(line).toContain(ts.n_cell_3d.toLocaleString())
    expect(line).toContain(`${(cr.base_rate * 100).toFixed(1)}%`)
    expect(screen.getByText(/no fitted parameters/)).toBeInTheDocument()
    expect(screen.getByText(cr.caveats[0])).toBeInTheDocument()
    expect(screen.getByText('Side readings')).toBeInTheDocument()
    expect(screen.getByText('TICK cycle')).toBeInTheDocument()
    vi.unstubAllGlobals()
  })

  it('keeps the Mastery folds and drops the merged ones', () => {
    renderPage()
    for (const l of ['Breadth, advanced', 'Votes', 'Board & chain', 'Correction risk', 'Style rotation', 'Benchmarks', 'Archive']) {
      expect(screen.getByText(l)).toBeInTheDocument()
    }
    for (const gone of ['Series', 'Ratio and spread', 'Market monitor', 'Classic breadth', 'Danger signals']) {
      expect(screen.queryByText(gone)).not.toBeInTheDocument()
    }
  })

  it('pins today as the archive\'s first row, bold, with the A/D line the tiles used to carry', () => {
    renderPage()
    fireEvent.click(screen.getByText('Archive').closest('button'))
    const today = document.querySelector('tbody tr')
    expect(today.className).toMatch(/\btoday\b/)
    expect(today.className).toMatch(/sticky/)
    expect(today.className).toMatch(/font-semibold/)
    const last = breadth.history.rows.at(-1)
    const [, m, d] = last.date.split('-')
    expect(today.textContent).toContain(`${parseInt(m)}/${parseInt(d)}`)
    expect(screen.getByText('A/D line')).toBeInTheDocument()
    expect(today.textContent).toContain(last.ad_line.toLocaleString())
  })
})

/* The three Correction risk charts, on the real payloads. */
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
describe('nothing the old verdict banner printed is lost', () => {
  it('prints all seven engine fields and the warning total', () => {
    renderPage()
    fireEvent.click(screen.getByText('Votes').closest('button'))
    const v = breadth.verdict
    for (const label of ['Risk level', 'Exposure', 'SPY', 'QQQ', 'Alignment', 'Breadth confirmation', 'Playbook']) {
      expect(screen.getAllByText(label).length).toBeGreaterThan(0)
    }
    for (const val of [v.risk, v.exposure, v.alignment, v.confirmation, v.playbook]) {
      expect(screen.getAllByText(val).length).toBeGreaterThan(0)
    }
    expect(screen.getByText(`${v.warn_total} total warnings`)).toBeInTheDocument()
  })
})

/* Andy 09-11: 「如果是有内容被删除了, 那我希望被删除的内容先放在折叠页里面」 — every
   item the rebuild had deleted is back, in a fold. One assertion per item. */
describe('deleted content is back, in the folds', () => {
  it('summary tiles: the four readings in words, with percentiles', () => {
    renderPage()
    fireEvent.click(screen.getByText('Summary tiles').closest('button'))
    for (const l of ['Up 4% / Down 4%', '5-day / 10-day ratio', 'Quarterly breadth (25%+)', 'T2108']) {
      expect(screen.getAllByText(l).length).toBeGreaterThan(0)
    }
  })

  it('chain: each link\'s evidence sentence is printed again', () => {
    renderPage()
    fireEvent.click(screen.getByText('Board & chain').closest('button'))
    for (const l of breadth.state_board.chain) {
      if (l.evidence) expect(screen.getAllByText(l.evidence).length).toBeGreaterThan(0)
    }
  })

  it('votes: the sentence that used to head the page sits in the engine block', async () => {
    const { readMarketState } = await import('../Reading')
    renderPage()
    fireEvent.click(screen.getByText('Votes').closest('button'))
    expect(screen.getByText(readMarketState(breadth.verdict))).toBeInTheDocument()
  })
})

/* DATA ALEX's real output (pipeline/screeners/market_light.py @ 640643c4, run
   on the 2026-09-10 session), not a hand-written shape — so a renamed key on
   either side turns this red. */
describe('the course read on DATA ALEX\'s real market_light.json', () => {
  const real = JSON.parse(readFileSync(resolve(process.cwd(), 'src/components/breadth/__fixtures__/market_light.2026-09-10.json'), 'utf8'))

  it('draws the light, the count, the gear and the call from the real file', async () => {
    withFetch({ market_light: real })
    renderPage()
    expect((await screen.findAllByText('AVOID')).length).toBeGreaterThan(0)
    expect(screen.getByText(`${real.spy.plus_n}`)).toBeInTheDocument()
    expect(screen.getByText(`${real.spy.gear.n} / 7`)).toBeInTheDocument()
    const held = real.brightness.leaders.filter((l) => l.status !== 'broken').length
    expect(screen.getByText(new RegExp(`${held} of ${real.brightness.leaders.length} above the 50-day`))).toBeInTheDocument()
    expect(screen.getAllByText('provisional').length).toBe(2)
    expect(screen.getByText(/no scan yet for BO \/ HTF/)).toBeInTheDocument()
    vi.unstubAllGlobals()
  })
})

/* Studio Q 09-11 (a7bd310b): the page names its method, a green-day call is
   tagged synthetic, and Q1 stays faded while provisional. */
describe('Studio Q rulings on the page', () => {
  const real = JSON.parse(readFileSync(resolve(process.cwd(), 'src/components/breadth/__fixtures__/market_light.2026-09-10.json'), 'utf8'))

  it('names the light\'s method and the lesson chart\'s other method', async () => {
    withFetch({ market_light: real })
    renderPage()
    expect(await screen.findByText(/The lesson’s own chart uses SMA 10 \/ 20/)).toBeInTheDocument()
    vi.unstubAllGlobals()
  })

  it('tags a green-day verdict as synthetic, and shows breadth\'s three-valued answer', async () => {
    const green = { ...real, verdict: 'dim', verdict_pending: null,
      spy: { ...real.spy, light: 'green', checks_passed: 3 },
      brightness: { ...real.brightness, breadth: { state: 'mixed' } } }
    withFetch({ market_light: green })
    renderPage()
    expect((await screen.findAllByText('DIM')).length).toBeGreaterThan(0)
    expect(screen.getByText(/synthetic — the rule that combines/)).toBeInTheDocument()
    expect(screen.getByText('Mixed')).toBeInTheDocument()
    vi.unstubAllGlobals()
  })
})
