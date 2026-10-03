/* global process */
import { describe, it, expect, vi, afterEach } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { render, act, fireEvent, cleanup } from '@testing-library/react'

// Andy 2026-10-03: 「整个网页需要有完整的中文和英文界面，而非个别地方才有中文或者英文」.
// Today's List (both tabs) on the real data/output files: Chinese mode leaves no
// interface English behind, English mode prints no Chinese of its own. The only
// Chinese allowed in English mode is text the shortlist FILE carries in one
// language (seat reasons, verdicts, legend) — that is data, listed, not invented.
const read = (f) => JSON.parse(readFileSync(resolve(process.cwd(), '..', 'data/output', f), 'utf8'))
const FILES = { 'watchlist.json': read('watchlist.json'), 'shortlist.json': read('shortlist.json'), 'universe.json': read('universe.json') }
const HAN = /[一-鿿]/

afterEach(() => { cleanup(); localStorage.clear(); vi.unstubAllGlobals() })

/** every text node and every title / placeholder / aria-label, after clicking
 *  through all five steps (each step prints its own three lines) */
async function mount(lang, zone) {
  vi.resetModules()
  localStorage.clear(); localStorage.setItem('fluxus-lang', lang)
  vi.stubGlobal('fetch', (url) => {
    const f = Object.keys(FILES).find((k) => String(url).endsWith(`/${k}`))
    return Promise.resolve(f ? { ok: true, status: 200, json: () => Promise.resolve(FILES[f]) }
      : { ok: false, status: 404, json: () => Promise.resolve(null) })
  })
  const { default: WatchlistPage } = await import('./WatchlistPage')
  const { LanguageProvider } = await import('../../i18n/LanguageContext')
  let c
  await act(async () => { c = render(<LanguageProvider><WatchlistPage zone={zone} /></LanguageProvider>) })
  await act(async () => { await new Promise((r) => setTimeout(r, 30)) })
  const seen = []
  const grab = () => {
    const w = document.createTreeWalker(c.container, NodeFilter.SHOW_TEXT)
    let n
    while ((n = w.nextNode())) if (n.nodeValue.trim()) seen.push(n.nodeValue.trim())
    c.container.querySelectorAll('[title],[placeholder],[aria-label]').forEach((el) => {
      for (const a of ['title', 'placeholder', 'aria-label']) if (el.getAttribute(a)) seen.push(el.getAttribute(a))
    })
  }
  grab()
  const steps = () => [...c.container.querySelectorAll('button[aria-pressed]')]
  if (!zone) {
    for (let i = 0; i < steps().length; i++) {
      await act(async () => { fireEvent.click(steps()[i]) })
      grab()
    }
  } else {
    // open every card's history
    for (const b of [...c.container.querySelectorAll('button')].filter((b) => /\(\d+/.test(b.textContent))) {
      await act(async () => { fireEvent.click(b) })
    }
    grab()
  }
  return seen
}

// text the shortlist file itself carries, in Chinese only
const s = FILES['shortlist.json']
const DATA_ZH = new Set([
  ...(s.seats || []).map((x) => x.why),
  ...(s.cards || []).map((x) => x.verdict),
  ...Object.values(s.legend || {}),
].filter(Boolean))

describe("Today's List in Chinese", () => {
  it('morning tab: Chinese steps, gates and panel names, no interface English', async () => {
    const all = (await mount('zh')).join('\n')
    for (const zh of ['晨报', '短名单', '水域', '脚印', '位置', '入场', '出场', '别这么用：',
      '只在领先 / 改善的主题里找票', '结构转折', '排除医疗保健', '市值 ≥ $1B', '日成交额 ≥ $20M',
      '破位区除外', '收复均线', '口袋支点', '只减不买', '主题是领先或改善', '收盘价/SPY']) {
      expect(all, zh).toContain(zh)
    }
    for (const en of ['Short List', 'exclude healthcare', 'except trouble', '$1B cap', 'M/day traded',
      'MA Reclaim', 'Pocket Pivot', '(today)', 'Leading or Improving', 'Leading / Improving',
      'Industry ranks in the top 20', 'the healthcare view', 'close/SPY', 'Themes 页', 'momentum',
      'precision', 'Delayed-EP', 'Liquid Leader Pullback', 'Extended ≥7']) {
      expect(all, en).not.toContain(en)
    }
    expect(all).toContain('SPY')   // tickers and the trade's proper nouns stay Latin
  })

  it('short list tab: Chinese seats, readings and buttons', async () => {
    const all = (await mount('zh', 'shortlist')).join('\n')
    for (const zh of ['今日六席', '我的名单', '在烧 · 今天谁在堆叠信号', '✗ 今天不要', '★ 关注', '备注',
      '量比', '合流日', '热度', '收起历史', '上过哪些格']) {
      expect(all, zh).toContain(zh)
    }
    for (const en of ['not measured', 'My list', 'Burning', 'not today', 'Rel vol', 'Signal', 'hide history',
      'chase', 'Short List']) {
      expect(all, en).not.toContain(en)
    }
  })
})

describe("Today's List in English", () => {
  it('morning tab prints no Chinese at all', async () => {
    const han = (await mount('en')).filter((x) => HAN.test(x))
    expect(han).toEqual([])
  })

  it('short list tab prints Chinese only where the file does', async () => {
    const han = (await mount('en', 'shortlist')).filter((x) => HAN.test(x) && !DATA_ZH.has(x))
    expect(han).toEqual([])
  })

  it('keeps the strings English mode always printed', async () => {
    const all = (await mount('en')).join('\n')
    for (const en of ['Short List', 'exclude healthcare', '$1B cap · $20M/day traded · ADR ≥ 3.5% except trouble',
      'Pocket Pivot (Morales/Kacher, 10D)', 'MA Reclaim (close crossed up the 21EMA / 50SMA)']) {
      expect(all, en).toContain(en)
    }
  })
})

describe('zone detail route', () => {
  // #/watchlist/<zone> threw "Cannot access 'view' before initialization":
  // ZoneDetail was handed `view` before the const was declared (on main since before 10-04).
  it('opens a zone page without throwing, in both languages', async () => {
    const key = FILES['watchlist.json'].zones[0].key
    for (const lang of ['en', 'zh']) {
      const seen = await mount(lang, key)
      expect(seen.length).toBeGreaterThan(0)
    }
  })
})
