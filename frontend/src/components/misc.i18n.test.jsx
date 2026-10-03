import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import { LanguageProvider } from '../i18n/LanguageContext'
import { translations } from '../i18n/translations'
import PreMarketChecklist from './dashboard/PreMarketChecklist'
import WritingSlot from './WritingSlot'
import DataUnavailable from './DataUnavailable'
import SummarySection from './journal/analytics/SummarySection'
import { computeInsights } from './portfolio/lib/diagnostics'

// Andy 2026-10-03: 「整个网页需要有完整的中文和英文界面」. The last English
// left in Chinese mode: the pre-market checklist, the writing slots' stepper,
// the "data did not load" page and the Summary insight sentences.
const HAN = /\p{Script=Han}/u

const trade = (pl, hold, day) => ({
  isClosed: true, totalPL: pl, holdingDays: hold, rr: pl > 0 ? 2 : -1,
  entryDate: `2026-01-${String(day).padStart(2, '0')}`,
  trims: [{ date: `2026-02-${String(day).padStart(2, '0')}`, price: 10 }],
})
// A: low win rate + big winners, winners held longer, 7-loss streak, early
// trims, tight stops, every month green.
const A = [
  ...[1, 2, 3].map((d) => trade(1000, 30, d)),
  ...[4, 5, 6, 7, 8, 9, 10].map((d) => trade(-100, 5, d)),
]
// B: high win rate + big losers, losers held longer, every month red.
const B = [
  ...[1, 2, 3, 4, 5, 6, 7].map((d) => trade(10, 2, d)),
  ...[8, 9, 10].map((d) => trade(-100, 10, d)),
]
const trims = [{ tooEarly: true, leftOnTable: 8 }, { tooEarly: true, leftOnTable: 6 }]
const stops = [{ stopTooTight: true, stopDistPct: 3 }, { stopTooTight: true, stopDistPct: 4 }]
const green = [1, 2, 3].map((i) => ({ month: `2026-0${i}`, monthlyRetPct: 2 }))
const red = [1, 2, 3].map((i) => ({ month: `2026-0${i}`, monthlyRetPct: -2 }))
const INSIGHTS = [
  ...computeInsights(A, green, trims, stops),
  ...computeInsights(B, red, [], []),
]
const fill = (s, vars) => s.replace(/\{(\w+)\}/g, (m, k) => (vars[k] != null ? String(vars[k]) : m))

function renderAll(lang) {
  localStorage.setItem('fluxus-lang', lang)
  render(
    <LanguageProvider>
      <PreMarketChecklist />
      <WritingSlot label="slot" kind="misc-test" placeholder="" />
      <DataUnavailable group="book" title="T" what="w" why="y" command="python -m x" />
      <SummarySection enriched={[]} closedTrades={A} monthlyStats={[]} performanceData={[]}
                      insights={INSIGHTS} startingCapital={100000} />
    </LanguageProvider>,
  )
}

const EN_LABELS = [
  'Pre-Market Checklist', 'Am I following my rules?', 'Market environment favorable?',
  'Am I sized correctly?', 'Do I have a clear setup today?', 'Emotional state?',
  'Breakouts working this week?', 'Yes', 'Somewhat', 'Clear setup', 'Forcing', 'No setup',
  'Focused', 'Tilted', 'Fearful', 'Mixed', 'Not loaded', 'no data',
]

describe('misc — one language at a time', () => {
  afterEach(() => { cleanup(); localStorage.clear() })

  it('every insight branch fires, and its English template reproduces the sentence', () => {
    expect(new Set(INSIGHTS.map((i) => i.key)).size).toBe(9)
    for (const ins of INSIGHTS) {
      expect(fill(translations.en[ins.key], ins.vars)).toBe(ins.text)
    }
  })

  it('zh shows Chinese in all four areas and none of the English', () => {
    // Two written days so the "{n} written" line shows.
    localStorage.setItem('fluxus-writing:misc-test', JSON.stringify({ '2020-01-01': 'old', '2020-01-02': 'older' }))
    renderAll('zh')
    for (const zh of ['盘前清单', '我在守自己的规矩吗？', '形态清楚', '硬凑', '没有载入', '没有数据', '重建命令']) {
      expect(screen.getAllByText(zh).length, zh).toBeGreaterThan(0)
    }
    for (const en of EN_LABELS) expect(screen.queryAllByText(en), en).toHaveLength(0)
    const body = document.body.textContent
    expect(body).not.toContain('Rebuild it with')
    for (const ins of INSIGHTS) {
      expect(body).not.toContain(ins.text)
      expect(body).toContain(fill(translations.zh[ins.key], ins.vars))
    }
    expect(body).toContain('胜率低（30%）')
    expect(body).toContain('已写 2 篇')
  })

  it('en shows no Han characters and the original sentences', () => {
    renderAll('en')
    const body = document.body.textContent
    expect(body).not.toMatch(HAN)
    expect(screen.getByText('Pre-Market Checklist')).toBeTruthy()
    expect(body).toContain('Rebuild it with python -m x')
    for (const ins of INSIGHTS) expect(body).toContain(ins.text)
  })
})
