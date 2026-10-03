/* global process */
import { describe, it, expect, vi, afterEach } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { render, screen } from '@testing-library/react'
import { LanguageProvider } from '../../i18n/LanguageContext'
import CorrectionRiskPanel from './CorrectionRiskPanel'

/* Andy 2026-10-03: 「整个网页需要有完整的中文和英文界面」 — in Chinese mode the
   Correction risk panel speaks Chinese, on the real files. */
const read = (p) => JSON.parse(readFileSync(resolve(process.cwd(), '..', p), 'utf8'))

describe('Correction risk panel — Chinese interface', () => {
  afterEach(() => { vi.unstubAllGlobals(); localStorage.removeItem('fluxus-lang') })

  it('renders its own words in Chinese, data numbers unchanged', async () => {
    const cr = read('data/output/correction_risk.json')
    const tc = read('data/output/tick_cycle.json')
    vi.stubGlobal('fetch', (url) => Promise.resolve({
      ok: true,
      json: () => Promise.resolve(String(url).includes('correction_risk') ? cr : String(url).includes('tick_cycle') ? tc : null),
    }))
    localStorage.setItem('fluxus-lang', 'zh')
    render(<LanguageProvider><CorrectionRiskPanel session={cr.date} /></LanguageProvider>)

    expect(await screen.findByText('标普 500 在 21 个交易日内回撤 ≥5% 的概率')).toBeInTheDocument()
    expect(screen.getByText('旁证读数')).toBeInTheDocument()
    // the TICK block left this panel 10-03 (Andy 「上面那个没数据，删除。」)
    expect(screen.queryByText('TICK 周期')).toBeNull()
    expect(screen.queryByText('Side readings')).toBeNull()
    expect(screen.queryByText('TICK cycle')).toBeNull()
    expect(screen.queryByText(/no fitted parameters/)).toBeNull()
    // numbers survive translation
    const ts = cr.ts_dimension.today
    expect(screen.getByText(`${(ts.prob_3d * 100).toFixed(1)}%`)).toBeInTheDocument()
    expect(document.body.textContent).toContain(ts.n_cell_3d.toLocaleString())
  })
})
