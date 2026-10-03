import { describe, it, expect, afterEach, beforeEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import { PortfolioProvider } from './context/PortfolioContext'
import { LanguageProvider } from '../../i18n/LanguageContext'
import { enrichTrades } from './lib/calculations'
import { computePortfolioHeat } from './lib/diagnostics'
import OverviewTab from './tabs/OverviewTab'
import ExposureTab from './tabs/ExposureTab'
import PortfolioHeader from './PortfolioHeader'
import TradeForm from './TradeForm'
import TrimModal from './TrimModal'
import SettingsPanel from './SettingsPanel'
import CapitalAtRiskWidget from './ui/CapitalAtRiskWidget'

// Andy 2026-10-03: 「整个网页需要有完整的中文和英文界面」. One language at a
// time on the Portfolio page. The page reads Sheets + localStorage, which are
// empty in a clean browser, so the live audit cannot see it — this renders it
// from a fake book instead.
//
// ⚠️ PUBLIC REPO: every ticker, price and share count below is invented
// (ZZA…ZZL, round numbers). Nothing here is a real position.

const HAN = /\p{Script=Han}/u

function fakeTrade(i) {
  return {
    id: `fake-${i}`, ticker: `ZZ${String.fromCharCode(65 + i)}`, direction: i === 3 ? 'short' : 'long',
    sector: 'Fake', entryDate: '2026-01-05', entryPrice: 10, originalQty: 30, currentQty: 30,
    // the 12th sits above entry: locked-in gain, no risk
    stopPrice: i === 3 ? 11 : i === 11 ? 12 : 9, initialStop: i === 3 ? 11 : 9,
    isClosed: false, trims: [],
  }
}
const raw = Array.from({ length: 12 }, (_, i) => fakeTrade(i))
// a pyramid: two layers of the same fake ticker → "campaign · 2 layers"
raw.push({ ...fakeTrade(0), id: 'fake-0b', entryDate: '2026-01-12' })
const enriched = enrichTrades(raw, 100000, {})
const open = enriched.filter(t => !t.isClosed)
const heat = computePortfolioHeat(open, {}, 100000)
const perf = Array.from({ length: 5 }, (_, i) => ({
  date: `2026-01-0${i + 5}`, value: 100000 + i * 100, returnPct: i * 0.1, cashPct: 50, leveragePct: 50,
}))

function renderPage(lang) {
  localStorage.setItem('fluxus-lang', lang)
  return render(
    <LanguageProvider>
      <PortfolioProvider>
        <PortfolioHeader portfolioValue={100000} totalPL={0} totalReturnPct={0}
          cashAvailable={50000} cashPct={50} openCount={14}
          onShowForm={() => {}} showForm={false} onExport={() => {}} onImport={() => {}}
          onShowSettings={() => {}} onReset={() => {}} />
        <SettingsPanel onClose={() => {}} />
        <TradeForm onClose={() => {}} />
        <TrimModal trade={open[0]} onClose={() => {}} />
        <OverviewTab performanceData={perf} totalReturnPct={0} monthlyStats={[]}
          ytdStats={{ basis: 'ytd', year: '2026', portfolioRetPct: 1, totalTrades: 0,
                      returnPct: 0, winPct: 0, avgGain: 0, avgLoss: 0, largestGain: 0,
                      largestLoss: 0, avgHoldWin: 0, avgHoldLoss: 0 }}
          enrichedTrades={enriched} qtyMismatches={[]} onTrim={() => {}} />
        <ExposureTab openTrades={open} enriched={enriched} sectorData={[]} holdingsData={[]}
          mergedHoldingsData={[]} performanceData={perf}
          capitalEfficiency={{ returnOnDeployed: 1, totalReturnPct: 1 }}
          dailyPrices={{}} spyHistory={[]} portfolioValue={100000} heatData={heat} />
        <CapitalAtRiskWidget openTrades={open} equity={100000} markDate="2026-01-09" />
      </PortfolioProvider>
    </LanguageProvider>,
  )
}

// What the page printed in English before it was keyed — none may survive in zh.
const ENGLISH = [
  'Names', 'Log New Trade', 'Add Trade', 'Entry Price', 'Stop Price', 'Size By',
  'Sync Token', 'Test Connection', 'Force Pull', 'Update', 'Action', 'Sell Price', 'Confirm',
  'Trim', '20d MA', 'Capital Deployment', 'Holdings', 'Detail', 'Return on deployed',
  'Avg leverage', 'Open risk · what can be lost', 'Method', 'Against the rule', 'at risk',
  'Since start',
]

describe('Portfolio page — one language at a time', () => {
  beforeEach(() => localStorage.removeItem('portfolio-state'))
  afterEach(() => { cleanup(); localStorage.removeItem('fluxus-lang') })

  it('zh prints Chinese labels and none of the old English ones', () => {
    renderPage('zh')
    for (const zh of ['持仓只数', '记一笔新交易', '添加交易', '止损价', '同步令牌', '确认',
                      '资金使用', '持仓分布', '明细', '持仓风险 · 最多会亏多少', '对照规则', '算法']) {
      expect(screen.getAllByText(zh).length).toBeGreaterThan(0)
    }
    for (const en of ENGLISH) expect(screen.queryAllByText(en, { exact: true })).toHaveLength(0)
    // whole sentences, not glued fragments
    expect(document.body.textContent).toContain('第十名之后还有 3 笔没画')
    expect(document.body.textContent).toContain('分批建仓 · 2 层')
    expect(document.body.textContent).toContain('⚠ 贪婪区——别再加了')
  })

  it('en prints no Han characters and keeps the English it always had', () => {
    renderPage('en')
    expect(document.body.textContent).not.toMatch(HAN)
    for (const en of ['Names', 'Log New Trade', 'Capital Deployment', 'Open risk · what can be lost']) {
      expect(screen.getAllByText(en).length).toBeGreaterThan(0)
    }
    expect(document.body.textContent).toContain('3 more positions below the tenth, not drawn — 2 of them carry')
    expect(document.body.textContent).toContain('campaign · 2 layers')
    expect(document.body.textContent).toContain("Size is the decision; the rest is the market's.")
  })
})
