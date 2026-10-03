import { describe, it, expect, afterEach, vi } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import fs from 'node:fs'
import path from 'node:path'
import { LanguageProvider } from '../../i18n/LanguageContext'

// Andy 2026-10-03: 「整个网页需要有完整的中文和英文界面」— one language at a
// time. Review is member-only, so the live audit never sees it; this renders the
// journal, one trade's page and the Review sections with the real post-mortem
// files, in both languages. None of these fixtures carry text the owner typed.
const HAN = /\p{Script=Han}/u
const OUT = path.resolve(__dirname, '../../../../data/output/trades')
const INDEX = JSON.parse(fs.readFileSync(path.join(OUT, '_index.json'), 'utf8'))
const TRADE = JSON.parse(fs.readFileSync(path.join(OUT, 'AAOI_2026-02-19_000.json'), 'utf8'))

vi.mock('../../hooks/useTradeJournal', () => ({
  useTradeJournal: () => ({ trades: INDEX.trades, loading: false }),
  useTradePostmortem: () => ({ data: TRADE, loading: false, error: null }),
}))

const { default: TradeJournalPage } = await import('./TradeJournalPage')
const { default: TradeDetailPage } = await import('./TradeDetailPage')
const { default: SetupEdgeSection } = await import('./analytics/SetupEdgeSection')
const { default: AfterLossSection } = await import('./analytics/AfterLossSection')
const { default: HoldCaptureSection } = await import('./analytics/HoldCaptureSection')
const { default: TrimStopsSection } = await import('./analytics/TrimStopsSection')
const { default: RiskSection } = await import('./analytics/RiskSection')
const { default: RiskAdjustedSection } = await import('./analytics/RiskAdjustedSection')
const { default: CoachTab } = await import('./CoachTab')
const { default: TharpLessons } = await import('./sizing/TharpLessons')
const { default: SqnReadout } = await import('./sizing/SqnReadout')
const { default: ObjectiveSimulator } = await import('./sizing/ObjectiveSimulator')

const trims = [1, 2, 3].map((i) => ({
  ticker: `AA${i}`, direction: 'long', tooEarly: true, leftOnTable: 6, captured: 50,
  trimIndex: 1, trimDate: '2026-01-02', trimPrice: 10, peakAfterTrim: 12, peakDate: '2026-01-05',
}))
const stops = [1, 2, 3].map((i) => ({
  ticker: `BB${i}`, direction: 'short', stopTooTight: true, stopDistPct: 3, recoveryPct: 12,
  entryPrice: 10, stopPrice: 11, exitDate: '2026-02-01', recoveryPeak: 9,
}))
const open = [{ id: 'x', ticker: 'CCC', direction: 'long', marketVal: 30000, weight: 30, currentQty: 100 }]
const heat = { positions: [{ ticker: 'CCC', hasStop: true, heat: 1.2 }], totalHeat: 9, noStopCount: 2 }
const risk = { annualizedReturn: 40, maxDrawdown: 12, correlation: 0.5, beta: 1.1, alpha: 5, sharpe: 1.8, sortino: 2.4 }
const rs = [2, -1, -1, 3.5, -0.5, 1, -1, 4, -1, 0.5, -1, 2.2]

// jsdom has no layout, so CoachTab's scroll-to-bottom needs a stand-in.
Element.prototype.scrollIntoView ||= () => {}

function renderAll(lang) {
  localStorage.setItem('fluxus-lang', lang)
  render(
    <LanguageProvider>
      <TradeJournalPage />
      <TradeDetailPage tradeId={TRADE.trade_id} />
      <SetupEdgeSection />
      <AfterLossSection />
      <HoldCaptureSection />
      <TrimStopsSection trimAnalysis={trims} stopAnalysis={stops} />
      <RiskSection openTrades={open} enriched={[]} heatData={heat} sectorData={[]}
                   dailyPrices={{}} spyHistory={[]} portfolioValue={100000} />
      <RiskAdjustedSection riskMetrics={risk} benchmarkTicker="SPY" />
      <CoachTab strategy="vcp" />
      <TharpLessons />
      <SqnReadout rs={rs} />
      <ObjectiveSimulator rs={rs} />
    </LanguageProvider>,
  )
}

// Labels the 2026-10-03 audit found English in Chinese mode, plus the Review
// sections' own chrome.
const EN_LABELS = [
  'Trading recap', 'Entry', 'Ticker', 'Realized R', 'Optimal R', 'Capture', 'Setup', 'Lesson',
  'Insufficient data', 'Failed setup', 'Good execution', 'Long in mixed structure',
  'Extended long — RSI overbought', 'Entry snapshot', 'Path analytics', 'Execution',
  'Trim Analysis', 'Stop Analysis', 'Portfolio Heat', 'Beta-Weighted Exposure', 'Exposure',
  'Sharpe Ratio', 'Copy-paste mode', 'Send', 'Van Tharp — The Study of Position Sizing',
  'System Quality — SQN & Expectancy', 'Size to Objectives — Monte-Carlo', 'Median Return',
]

describe('journal + review — one language at a time', () => {
  afterEach(() => { cleanup(); localStorage.removeItem('fluxus-lang') })

  it('zh shows Chinese and none of the English labels', () => {
    renderAll('zh')
    for (const zh of ['交易回顾', '已实现 R', '最优 R', '捕获率', '教训', '入场快照', '路径分析',
                      '减仓分析', '止损分析', '组合风险', 'Beta 加权敞口', '夏普比率',
                      '系统质量——SQN 与期望值', '按目标定仓——蒙特卡洛', '波动收缩形态（VCP）']) {
      expect(screen.getAllByText(zh).length, zh).toBeGreaterThan(0)
    }
    for (const en of EN_LABELS) {
      expect(screen.queryAllByText(en), en).toHaveLength(0)
    }
    const body = document.body.textContent
    expect(body).toContain('均线结构混乱时做多')
    expect(body).toContain('笔交易')
    // The narrative is rebuilt in Chinese, not the pipeline's English sentence.
    expect(body).not.toContain('Entered AAOI long')
    expect(body).toContain('做多入场 AAOI')
  })

  it('en shows no Han characters', () => {
    renderAll('en')
    expect(document.body.textContent).not.toMatch(HAN)
    expect(screen.getAllByText('Trading recap').length).toBeGreaterThan(0)
    // The narrative is the pipeline's own sentence, untouched.
    expect(document.body.textContent).toContain('Entered AAOI long on 2026-02-19 at $44.41')
  })
})
