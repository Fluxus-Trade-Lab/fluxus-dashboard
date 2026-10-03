import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, act, fireEvent } from '@testing-library/react'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import process from 'node:process'
import { LanguageProvider } from '../../i18n/LanguageContext'
import ModelBooksPage from './ModelBooksPage'
import NotesRail from './NotesRail'
import TradingGym from './TradingGym'

/* Andy 2026-10-03: 「整个网页需要有完整的中文和英文界面，而非个别地方才有中文或者英文（目前比较混乱）」.
   Model Books on the real library files: Chinese mode prints the interface in
   Chinese (book, author and ticker names stay Latin); English mode prints no
   Han character anywhere — text, placeholders or tooltips. */

const DIR = resolve(process.cwd(), 'public/data/modelbooks')
const serve = (url) => {
  const name = String(url).replace(/^\/data\/modelbooks\//, '')
  const body = JSON.parse(readFileSync(resolve(DIR, name), 'utf8'))
  return Promise.resolve({ ok: true, json: () => Promise.resolve(body) })
}

const HAN = /\p{Script=Han}/u

function attrs(container) {
  return [...container.querySelectorAll('[title],[placeholder]')]
    .flatMap(el => [el.getAttribute('title'), el.getAttribute('placeholder')])
    .filter(Boolean).join(' | ')
}

async function mountPage(lang) {
  localStorage.setItem('fluxus-lang', lang)
  let c
  await act(async () => { c = render(<LanguageProvider><ModelBooksPage /></LanguageProvider>) })
  await act(async () => { await new Promise(r => setTimeout(r, 30)) })
  return c
}

const NOTE_ENTRY = {
  id: 'x', ticker: 'NVDA', year: 2023, source: 'Market Leaders',
  patterns: ['cup_with_handle', 'vcp'], key_lessons: ['Holds the 21 EMA'],
  libraryNoteCount: 200,
  note: {
    breakout: { date: '2023-01-31', price: 200 }, peak: { date: '2023-08-31', price: 490 },
    gain_pct: 145, weeks: 30,
    sources: [{ book: '10 Years of Market Leaders（Richard Moglen）', author: 'Richard Moglen',
      page: 12, labels: ['Base Pivot'], prose: 'head\nBody text' }],
  },
}

describe('Model Books i18n', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', serve)
    vi.stubGlobal('ResizeObserver', class { observe() {} disconnect() {} })
    window.matchMedia = window.matchMedia || (() => ({ addEventListener() {}, removeEventListener() {} }))
  })
  afterEach(() => { vi.unstubAllGlobals(); localStorage.clear() })

  it('Chinese mode: library, transport and stats in Chinese', async () => {
    const c = await mountPage('zh')
    let text = c.container.textContent
    for (const zh of ['标杆案例', '条有 K 线', '翻库 + 回放', '统计', '练习', '全部形态', '全部来源', '有注释',
      '按突破后涨幅', '距 50 日线', '▶ 播放', '全部显示', '个月', '杯柄形态', '大牛股', '版权归原作者']) {
      expect(text, zh).toContain(zh)
    }
    for (const en of ['Browse + replay', 'Practice', 'All Patterns', 'All Sources', 'Sort:',
      'Show all', 'Cup With Handle', 'Big Movers', 'Flat Base', 'High Tight Flag', 'Vcp', 'Ipo Base']) {
      expect(text, en).not.toContain(en)
    }
    // book titles stay Latin
    expect(text).toContain('10 Years of Market Leaders（Richard Moglen）')

    await act(async () => { fireEvent.click(c.getByText('统计')) })
    text = c.container.textContent
    for (const zh of ['全部年代', '2020 年代', '条案例', '条数', '平均涨幅', '平均天数']) expect(text, zh).toContain(zh)
    for (const en of ['All Time', '2020s', 'setups', 'Count', 'Avg Gain', 'Avg Duration']) expect(text, en).not.toContain(en)
  })

  it('English mode: no Han character in text, placeholders or tooltips', async () => {
    const c = await mountPage('en')
    let text = c.container.textContent
    for (const en of ['Model Books', 'Browse + replay', 'Practice', 'Sort: Advance after breakout',
      'Cup With Handle', 'Big Movers', 'vs 50-day', '▶ Play', 'Show all']) {
      expect(text, en).toContain(en)
    }
    expect(text.match(HAN), text.slice(0, 400)).toBeNull()
    expect(attrs(c.container).match(HAN)).toBeNull()

    await act(async () => { fireEvent.click(c.getByText('Stats')) })
    text = c.container.textContent
    for (const en of ['All Time', '2020s', 'setups', 'Count', 'Avg Gain']) expect(text, en).toContain(en)
    expect(text.match(HAN)).toBeNull()
  })

  it('notes rail and practice follow the language; quoted annotations stay as written', async () => {
    localStorage.setItem('fluxus-lang', 'zh')
    vi.stubGlobal('fetch', () => Promise.reject(new Error('offline')))
    let c
    await act(async () => {
      c = render(<LanguageProvider><NotesRail entry={NOTE_ENTRY} /><TradingGym cards={[NOTE_ENTRY].map(e => ({ ...e, ohlcv_file: 'x.json' }))} /></LanguageProvider>)
    })
    let text = c.container.textContent
    for (const zh of ['模型册写明的突破', '高点', '作者记的是 145% / 30 周', '关键经验', '原文（Richard Moglen）',
      '杯柄形态', 'VCP 波动收缩', '第 0 轮', '连对：', '最佳：', '简单', '混合', '图表数据载入失败']) {
      expect(text, zh).toContain(zh)
    }
    for (const en of ['Key lessons', 'Round', 'Streak', 'Easy', 'Mixed', 'Failed to load']) expect(text, en).not.toContain(en)
    // data quoted from the books is not translated
    expect(text).toContain('Holds the 21 EMA')
    expect(text).toContain('Base Pivot')
    c.unmount()

    localStorage.setItem('fluxus-lang', 'en')
    await act(async () => {
      c = render(<LanguageProvider><NotesRail entry={NOTE_ENTRY} /><TradingGym cards={[NOTE_ENTRY].map(e => ({ ...e, ohlcv_file: 'x.json' }))} /></LanguageProvider>)
    })
    text = c.container.textContent
    for (const en of ['Breakout stated in the model book', 'the author records 145% / 30 weeks', 'Key lessons',
      'Round 0', 'Streak:', 'Failed to load chart data']) {
      expect(text, en).toContain(en)
    }
    expect(text.match(HAN)).toBeNull()
  })
})
