import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, act } from '@testing-library/react'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import process from 'node:process'
import { LanguageProvider } from '../../i18n/LanguageContext'
import VerdictCard from './VerdictCard'
import RegimeBand from './RegimeBand'
import LeadersLaggards from './LeadersLaggards'
import ThemeMovers from './ThemeMovers'
import TickerStrip from './TickerStrip'
import HowToRead from '../HowToRead'
import { ETF_GROUPS } from '../../lib/etfGroups'
import { readMarketState, readThemes, readScreener } from '../Reading'
import { translations } from '../../i18n/translations'

/* Andy 2026-10-03: 「整个网页需要有完整的中文和英文界面，而非个别地方才有中文或者英文（目前比较混乱）」.
   The Dashboard in Chinese mode, on the real nightly files: interface words in
   Chinese, tickers and numbers untouched; English mode unchanged. */

const read = (f) => JSON.parse(readFileSync(resolve(process.cwd(), '../data/output', f), 'utf8'))
const breadth = read('breadth.json')
const signals = read('signals.json')
const etfData = read('etf_data.json')
const groups = read('groups.json')

const cohort = (g) => (ETF_GROUPS[g] || []).map((t) => etfData.find((e) => e.ticker === t)).filter(Boolean)

async function mount(lang) {
  localStorage.setItem('fluxus-lang', lang)
  let c
  await act(async () => {
    c = render(
      <LanguageProvider>
        <VerdictCard verdict={breadth.verdict} onNavigate={() => {}} />
        <RegimeBand verdict={breadth.verdict} signals={signals} conditions={breadth.conditions} />
        <TickerStrip signals={signals} etfData={etfData} />
        <LeadersLaggards title={lang === 'zh' ? '行业领涨与领跌' : 'Industry Leaders and Laggards'}
                         etfs={cohort('Industries')} windows={['1D', '1W']} limit={3} />
        <LeadersLaggards title="x" etfs={cohort('Sel Sectors')} windows={['1D', '1W']} limit={3} />
        <ThemeMovers limit={3} />
        <HowToRead><p>body</p></HowToRead>
      </LanguageProvider>,
    )
  })
  return c
}

describe('Dashboard in Chinese', () => {
  beforeEach(() => vi.stubGlobal('fetch', () => Promise.resolve({ ok: true, json: () => Promise.resolve(groups) })))
  afterEach(() => { vi.unstubAllGlobals(); localStorage.clear() })

  it('prints the interface in Chinese, tickers and numbers untouched', async () => {
    const c = await mount('zh')
    const text = c.container.textContent
    for (const zh of [' / 12 票', '市场状态详情 →', '分界线', '看多', '看空', '越高越安全', '市场环境 · 自建综合分',
      '主题领涨与领跌', '领先', '走弱', '改善', '落后', '怎么读这一页', '1日', '1周', '月']) {
      expect(text, zh).toContain(zh)
    }
    // the vote labels arrive in English inside vote_detail; zh looks them up by key
    for (const zh of ['广度推力', '季度涨跌差', '站上 200 日线', 'SPY 警示']) expect(text, zh).toContain(zh)
    for (const en of ['/ 12 votes', 'Market State detail', 'the line it flips at', 'could not be counted',
      'up is always safer', 'Market conditions', 'Theme Leaders and Laggards', 'Leading', 'Weakening',
      'Improving', 'Lagging', 'How to read this', 'Quarterly spread', 'Thrust', 'New highs vs lows',
      'Natural Gas', 'Consumer Discretionary', 'Copper Miners', 'Caution', 'Neutral', 'Defence']) {
      expect(text, en).not.toContain(en)
    }
    // month ticks: 9月, never Sep
    expect(text).not.toMatch(/\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b/)
    // tickers stay Latin
    for (const tk of ['SPY', 'QQQ', 'VIX']) expect(text, tk).toContain(tk)
  })

  it('leaves English exactly as it was', async () => {
    const c = await mount('en')
    const text = c.container.textContent
    for (const en of [' / 12 votes', 'Market State detail →', 'the line it flips at', 'up is always safer',
      'Market conditions · our composite', 'Theme Leaders and Laggards', 'Leading', 'How to read this']) {
      expect(text, en).toContain(en)
    }
    expect(text).not.toMatch(/[一-鿿]/)
  })
})

describe('Reading sentences', () => {
  const zhT = (k, v) => {
    const d = translations.zh
    return v ? d[k].replace(/\{(\w+)\}/g, (m, x) => (v[x] != null ? String(v[x]) : m)) : d[k]
  }
  it('default to the English they always printed', () => {
    const s = readMarketState(breadth.verdict)
    expect(s).toMatch(/signals? says?/)
  })
  it('speak Chinese when handed the zh translator', () => {
    expect(readMarketState(breadth.verdict, zhT)).toMatch(/个信号说/)
    const rows = groups.themes.filter((t) => t.kind === 'theme').map((t) => ({ ...t, _value: t.perf_1w }))
    const th = readThemes(rows, '1W', zhT, 'zh')
    expect(th).toMatch(/本周领涨/)
    expect(th).not.toMatch(/leads|week/)
    expect(readScreener({ rows: [] }, zhT, 'zh')).toBeNull()
  })
})
