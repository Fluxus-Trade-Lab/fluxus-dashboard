import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, act } from '@testing-library/react'
import { LanguageProvider } from '../../i18n/LanguageContext'
import MarketStateMin from './MarketStateMin'

/* Andy 2026-10-03: 「整个网页需要有完整的中文和英文界面，而非个别地方才有中文或者英文」.
   In Chinese mode the Market State screen speaks Chinese only — the interface
   words, not the tickers or numbers. */

const ml = { date: '2026-10-02', verdict: 'dim', spy: { light: 'green', checks_passed: 3 }, qqq: { light: 'green', checks_passed: 3 },
  brightness: { leaders: [{ ticker: 'NVDA', theme: null, status: 'holding' }], breadth: { env: 'MIXED' } } }
const etfs = [
  { ticker: 'SPY', close: 769.64, change_pct: 0.0074, perf_1w: 0.0053, high_52w_dist: -0.008, dist_sma50_atr: 1.11 },
  { ticker: 'IWM', close: 281.5, change_pct: 0.009, perf_1w: 0.005, high_52w_dist: -0.075, dist_sma50_atr: -2.81 },
  { ticker: 'TLT', close: 86, change_pct: -0.003, perf_1w: -0.011 },
]
const rows = [
  { date: '2026-10-01', advances: 2000, declines: 3000, pct_above_20sma: 25.3, pct_above_200sma: 36.4, mcclellan_osc_ndx: 36.7 },
  { date: '2026-10-02', advances: 3080, declines: 2273, high_low_index: 17.0, record_high_pct: 20.59, new_highs_common: 7, new_lows_common: 27,
    pct_above_20sma: 28.91, pct_above_200sma: 37.5, mcclellan_osc_ndx: 50.21, up_4pct_stockbee: 215, down_4pct_stockbee: 129, t2108: 26.01 },
]
const gh = { dates: ['a', 'b', 'c', 'd', 'e', 'f'], groups: { Genomics: { kind: 'theme', state: ['Lagging', 'Lagging', 'Lagging', 'Lagging', 'Lagging', 'Leading'] } } }

async function mount(lang) {
  localStorage.setItem('fluxus-lang', lang)
  let c
  await act(async () => {
    c = render(
      <LanguageProvider>
        <MarketStateMin ml={ml} etfs={etfs} signals={{ '^VIX': { close: 15.31 } }} rows={rows} paneRows={rows}
                        themes={[{ group: 'Genomics', members: 12 }]} groupsHistory={gh} universe={{}} />
      </LanguageProvider>,
    )
  })
  return c.container.textContent
}

describe('MarketStateMin in Chinese', () => {
  beforeEach(() => vi.stubGlobal('fetch', () => Promise.resolve({ ok: false })))
  afterEach(() => { vi.unstubAllGlobals(); localStorage.clear() })

  it('prints the interface in Chinese, tickers and numbers untouched', async () => {
    const text = await mount('zh')
    for (const zh of ['收着做', '绿灯', '多空分歧', '指数', '广度', '领涨股', '跨资产', '净上涨家数', '新高新低指数',
      '较前日 +3.6', '距高点 −0.8%', '上升趋势', '50 日线下方', '波动率指数', '落后', '领先', '指数与广度', '股票池', '全市场']) {
      expect(text, zh).toContain(zh)
    }
    for (const en of ['Net advances', 'Cross-asset', 'High-Low Index', 'vs prior', 'from high', 'Uptrend', 'volatility index',
      'Index over breadth', 'All market', 'Leaders', 'Lagging', 'MIXED']) {
      expect(text, en).not.toContain(en)
    }
    expect(text).toContain('SPY')
    expect(text).toContain('T2108 26%')
  })

  it('English stays as it was', async () => {
    const text = await mount('en')
    for (const en of ['dim', 'Net advances', 'Cross-asset', '+3.6 vs prior', '−0.8% from high', 'Index over breadth', 'Lagging → Leading']) {
      expect(text, en).toContain(en)
    }
  })
})
