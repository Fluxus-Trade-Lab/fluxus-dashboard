/* global process */
import { describe, it, expect, vi, afterEach } from 'vitest'
import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'
import { render, act, fireEvent, cleanup } from '@testing-library/react'
import { translations } from '../../i18n/translations'
import { rowsPassingGate, stepCounts } from './funnel/stepMath'

// Andy 2026-10-04: 「先把已经有内容的做出来上线。管线没有到位的待会儿做」 — the merged
// Screener, mounted on the real files (data/output + frontend/public/data).
const ROOT = resolve(process.cwd(), '..')
const OUT = resolve(ROOT, 'data/output')
const PUB = resolve(process.cwd(), 'public/data')
const json = (dir, f) => JSON.parse(readFileSync(resolve(dir, f), 'utf8'))
const FOCUS = json(PUB, 'focus.json')
const UNIVERSE = json(OUT, 'universe.json')
const HAN = /[一-鿿]/
export const FORBIDDEN = {
  zh: ['§', '课程第', 'PRODUCT.md', '归你', '管线', '还没', '待补'],
  en: ['§', 'course', 'pipeline', 'not built yet', 'PRODUCT.md'],
}

function serve(url) {
  const u = String(url).split('?')[0]
  const name = u.split('/').pop()
  const file = u.includes('/data/output/') ? resolve(OUT, u.split('/data/output/')[1])
    : resolve(PUB, name)
  if (!existsSync(file)) return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve(null) })
  const body = JSON.parse(readFileSync(file, 'utf8'))
  return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(body) })
}

// whole-page mounts on the real files; under a full parallel run they need room
vi.setConfig({ testTimeout: 30000 })

afterEach(() => { cleanup(); localStorage.clear(); vi.unstubAllGlobals() })

export async function mountPage(lang, which, props = {}, keep = false) {
  if (!keep) vi.resetModules()
  if (!keep) localStorage.clear()
  localStorage.setItem('fluxus-lang', lang)
  vi.stubGlobal('fetch', serve)
  vi.stubGlobal('requestAnimationFrame', (f) => setTimeout(f, 0))
  const { LanguageProvider } = await import('../../i18n/LanguageContext')
  const Page = which === 'screener'
    ? (await import('./ScreenerPage')).default
    : (await import('../watchlist/WatchlistPage')).default
  let c
  await act(async () => { c = render(<LanguageProvider><Page {...props} /></LanguageProvider>) })
  await act(async () => { await new Promise((r) => setTimeout(r, 60)) })
  return c
}

export function grab(container, into = []) {
  const w = document.createTreeWalker(container, NodeFilter.SHOW_TEXT)
  let n
  while ((n = w.nextNode())) if (n.nodeValue.trim()) into.push(n.nodeValue.trim())
  container.querySelectorAll('[title],[placeholder],[aria-label]').forEach((el) => {
    for (const a of ['title', 'placeholder', 'aria-label']) if (el.getAttribute(a)) into.push(el.getAttribute(a))
  })
  return into
}

const stepValue = (c, k) => c.container.querySelector(`[data-step="${k}"] span:last-child`).textContent
const rowCount = (c) => c.container.querySelectorAll('[data-testid="results"] tbody tr[data-row]').length
const click = async (el) => { await act(async () => { fireEvent.click(el) }) }

/** every text on the Screener: each step, each live scan, both presets */
async function walkScreener(lang) {
  const c = await mountPage(lang, 'screener')
  const seen = grab(c.container)
  for (const k of ['gate', 'setup', 'qual', 'focus', 'water']) {
    const b = c.container.querySelector(`[data-step="${k}"]`)
    if (b && !b.disabled) { await click(b); grab(c.container, seen) }
  }
  for (const b of [...c.container.querySelectorAll('[data-scan]')].filter((x) => x.tagName === 'BUTTON')) {
    await click(b); grab(c.container, seen)
  }
  await click(c.container.querySelector('[data-row] button'))   // opens the chart band
  grab(c.container, seen)
  await click(c.container.querySelector('[data-preset="custom"]'))
  grab(c.container, seen)
  return seen
}

describe('step bar reads focus.json', () => {
  // comparable only while focus.json was built off this very universe.json
  it.skipIf(FOCUS.universe_timestamp !== UNIVERSE.timestamp)('the gate rule over universe.json lists exactly counts.gate names', () => {
    expect(rowsPassingGate(UNIVERSE.rows, FOCUS.rule.gate).length).toBe(FOCUS.counts.gate)
  })

  it('each cell shows the file\'s number for the selected setup', async () => {
    const c = await mountPage('zh', 'screener')
    const n = stepCounts(FOCUS, 'pullback')
    const rows = FOCUS.setups.pullback.rows
    expect(stepValue(c, 'gate')).toBe(FOCUS.counts.gate.toLocaleString('en-US'))
    expect(stepValue(c, 'setup')).toBe(String(rows.length))
    expect(stepValue(c, 'qual')).toBe(String(rows.filter((r) => r.qn === 4).length))
    expect(stepValue(c, 'focus')).toBe(String(rows.filter((r) => r.focus).length))
    expect(stepValue(c, 'water')).toBe(String(n.water))
    expect(n.water).toBe(rows.filter((r) => r.focus && ['Leading', 'Improving'].includes(r.theme?.state)).length)

    // another setup: the cells follow it
    await click(c.container.querySelector('[data-scan="ep"]'))
    expect(stepValue(c, 'setup')).toBe(String(FOCUS.setups.ep.rows.length))
    expect(stepValue(c, 'focus')).toBe(String(FOCUS.setups.ep.rows.filter((r) => r.focus).length))
  })

  it('pressing a step changes the rows; 水域 is off by default and narrows when on', async () => {
    const c = await mountPage('zh', 'screener')
    await click(c.container.querySelector('[data-step="setup"]'))
    expect(c.container.querySelector('[data-testid="row-count"]').textContent)
      .toBe(`10 / ${FOCUS.setups.pullback.rows.length}`)
    await click(c.container.querySelector('[data-step="focus"]'))
    const focusN = FOCUS.setups.pullback.rows.filter((r) => r.focus).length
    expect(c.container.querySelector('[data-testid="row-count"]').textContent).toBe(`10 / ${focusN}`)
    expect(c.container.querySelector('[data-step="water"]').getAttribute('aria-pressed')).toBe('false')
    await click(c.container.querySelector('[data-step="water"]'))
    const w = stepCounts(FOCUS, 'pullback').water
    expect(c.container.querySelector('[data-testid="row-count"]').textContent).toBe(`${Math.min(10, w)} / ${w}`)
    await click(c.container.querySelector('[data-step="gate"]'))
    await click(c.container.querySelector('[data-step="water"]'))
    expect(c.container.querySelector('[data-testid="row-count"]').textContent)
      .toBe(`10 / ${rowsPassingGate(UNIVERSE.rows, FOCUS.rule.gate).length}`)
  })

  it('panel scans from watchlist.json join the list; no-data scans are dashed and not buttons', async () => {
    const c = await mountPage('zh', 'screener')
    const tml = c.container.querySelector('[data-scan="true_market_leaders"]')
    expect(tml.tagName).toBe('BUTTON')
    await click(tml)
    const wl = json(OUT, 'watchlist.json')
    const p = wl.zones.flatMap((z) => z.panels).find((x) => x.key === 'true_market_leaders')
    expect(rowCount(c)).toBe(Math.min(10, p.tickers.length))
    const dashed = c.container.querySelector('[data-scan="growth"]')
    expect(dashed.tagName).toBe('SPAN')
    expect(dashed.getAttribute('aria-disabled')).toBe('true')
    // exits stay off this page
    expect(c.container.querySelector('[data-scan="stop_hit"]')).toBeNull()
  })
})

describe('row-count control', () => {
  it('5 / 10 / 15 / all, default 10, with a footer for the rest', async () => {
    const c = await mountPage('zh', 'screener')
    await click(c.container.querySelector('[data-step="setup"]'))
    const total = FOCUS.setups.pullback.rows.length
    expect(rowCount(c)).toBe(10)
    expect(c.container.querySelector('[data-testid="more"]').textContent).toBe(`另有 ${total - 10} 只`)
    const btn = (label) => [...c.container.querySelectorAll('[data-testid="top-n"] button')].find((b) => b.textContent === label)
    await click(btn('5')); expect(rowCount(c)).toBe(5)
    await click(btn('15')); expect(rowCount(c)).toBe(15)
    await click(btn('全部')); expect(rowCount(c)).toBe(total)
    expect(c.container.querySelector('[data-testid="more"]').textContent).toBe('')
  })
})

describe('one shortlist', () => {
  it('the Screener has no shortlist tray', async () => {
    const c = await mountPage('zh', 'screener')
    const text = c.container.textContent
    for (const lang of ['en', 'zh']) expect(text).not.toContain(translations[lang]['sh.st.title'])
  })

  it('+ 短名单 toggles and the header chip counts it', async () => {
    const c = await mountPage('zh', 'screener')
    const chip = () => c.container.querySelector('[data-testid="shortlist-chip"]')
    const n0 = Number(chip().textContent.match(/\d+/)[0])
    expect(chip().getAttribute('href')).toBe('#/watchlist/shortlist')
    const first = [...c.container.querySelectorAll('[data-add]')].find((b) => b.getAttribute('aria-pressed') === 'false')
    const tk = first.getAttribute('data-add')
    await click(first)
    expect(c.container.querySelector(`[data-add="${tk}"]`).textContent).toBe('✓ 已加')
    expect(chip().textContent).toBe(`短名单 ${n0 + 1} →`)
    await click(c.container.querySelector(`[data-add="${tk}"]`))
    expect(chip().textContent).toBe(`短名单 ${n0} →`)
  })

  it('the header chip and 我的短名单 show the same number on the real data', async () => {
    const s = await mountPage('zh', 'screener')
    const chipN = Number(s.container.querySelector('[data-testid="shortlist-chip"]').textContent.match(/\d+/)[0])
    cleanup()
    const c = await mountPage('zh', 'watchlist', { zone: 'shortlist' }, true)
    const head = [...c.container.querySelectorAll('h2')].find((h) => h.textContent.startsWith('我的短名单'))
    const mineN = Number(head.textContent.replace('我的短名单', '').trim() || 0)
    expect(chipN).toBe(mineN)
    expect(mineN).toBeGreaterThan(0)   // the file's manual names count, not only this browser's
  })
})

describe('copy', () => {
  for (const lang of ['zh', 'en']) {
    it(`no internal wording on the Screener (${lang})`, async () => {
      const all = (await walkScreener(lang)).join('\n')
      for (const w of FORBIDDEN[lang]) expect(all.toLowerCase(), w).not.toContain(w.toLowerCase())
    })
  }

  it('English mode prints no Chinese on the Screener', async () => {
    const han = (await walkScreener('en')).filter((x) => HAN.test(x))
    expect(han).toEqual([])
  })

  it('Chinese mode keeps the owner\'s words', async () => {
    const all = (await walkScreener('zh')).join('\n')
    for (const w of ['课程漏斗', '自定义', '可交易', '形态', '资格', '过闸', '水域', '市场环境', '市场状态 →',
      '收着做', '龙头TML', '+ 短名单']) expect(all, w).toContain(w)
  })
})

/** every text on Today's List, with every card's history opened */
async function walkTodaysList(lang, zone = 'shortlist') {
  const c = await mountPage(lang, 'watchlist', { zone })
  const seen = grab(c.container)
  for (const b of [...c.container.querySelectorAll('button')].filter((x) => /\(\d+/.test(x.textContent))) {
    await click(b)
  }
  return { c, seen: grab(c.container, seen) }
}

describe("Today's List", () => {
  it('has no 晨报 tab: the page is 今日六席 + 我的短名单', async () => {
    for (const zone of [undefined, 'shortlist']) {
      const { c } = await walkTodaysList('zh', zone)
      const buttons = [...c.container.querySelectorAll('button')].map((b) => b.textContent.trim())
      expect(buttons).not.toContain(translations.zh['wl2.tab.morning'])
      expect(buttons).not.toContain(translations.zh['wl2.tab.shortlist'])
      const heads = [...c.container.querySelectorAll('h2')].map((h) => h.textContent.trim())
      expect(heads[0]).toBe('今日六席')
      expect(heads[1]).toMatch(/^我的短名单/)
    }
  })

  it('an old zone route does not throw and lands on the shortlist view', async () => {
    const wl = json(OUT, 'watchlist.json')
    for (const z of [...wl.zones.map((x) => x.key), 'nonsense']) {
      const c = await mountPage('en', 'watchlist', { zone: z })
      expect(c.container.textContent).toContain('Today’s six seats')
    }
  })

  it('+ 短名单 on the Screener lands in 我的短名单', async () => {
    const mineHead = (c) => [...c.container.querySelectorAll('h2')].find((h) => h.textContent.startsWith('我的短名单'))
    const mineText = (c) => {
      let out = '', el = mineHead(c).parentElement.nextElementSibling
      while (el) { out += el.textContent; el = el.nextElementSibling }
      return out
    }
    const before = await mountPage('zh', 'watchlist', { zone: 'shortlist' })
    const n0 = Number(mineHead(before).textContent.replace('我的短名单', '').trim() || 0)
    const had = mineText(before)
    cleanup()
    const s = await mountPage('zh', 'screener', {}, true)
    const btn = [...s.container.querySelectorAll('[data-add]')].find((b) => !had.includes(b.getAttribute('data-add')))
    const tk = btn.getAttribute('data-add')
    await click(btn)
    cleanup()
    const c = await mountPage('zh', 'watchlist', { zone: 'shortlist' }, true)
    expect(mineHead(c).textContent.trim()).toBe(`我的短名单 ${n0 + 1}`)
    expect(mineText(c), `${tk} under 我的短名单`).toContain(tk)
  })

  for (const lang of ['zh', 'en']) {
    it(`no internal wording on Today's List (${lang})`, async () => {
      const all = (await walkTodaysList(lang)).seen.join('\n')
      for (const w of FORBIDDEN[lang]) expect(all.toLowerCase(), w).not.toContain(w.toLowerCase())
    })
  }

  it("English mode prints no Chinese on Today's List", async () => {
    const han = (await walkTodaysList('en')).seen.filter((x) => HAN.test(x))
    expect(han).toEqual([])
  })
})

describe('dictionary', () => {
  it('the merge\'s own keys exist in both languages and carry no internal wording', () => {
    const own = (lang) => Object.entries(translations[lang]).filter(([k]) => /^(scx|tlx)\./.test(k))
    expect(own('en').map(([k]) => k).sort()).toEqual(own('zh').map(([k]) => k).sort())
    for (const lang of ['en', 'zh']) {
      for (const [k, v] of own(lang)) {
        for (const w of FORBIDDEN[lang]) expect(v.toLowerCase(), `${lang} ${k}`).not.toContain(w.toLowerCase())
      }
    }
  })
})
