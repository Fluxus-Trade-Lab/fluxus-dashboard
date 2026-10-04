import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, act } from '@testing-library/react'
import { LanguageProvider } from '../../i18n/LanguageContext'
import ScanBar from './ScanBar'
import ResultsTable from './ResultsTable'

/* Andy 2026-10-03: 「整个网页需要有完整的中文和英文界面，而非个别地方才有中文或者英文」.
   In Chinese mode the Screener speaks Chinese: the custom bar, the results
   table the page renders (ResultsTable), theme names, and the zh note.
   Tickers and numbers stay as they are. */

const focusDoc = {
  asof: '2026-10-02',
  counts: { universe: 5618, gate: 781, healthy: 119, healthy_gate: 72 },
  rule: { gate: { cap: 1e9, dollar_vol: 2e7, adr: 3.5 } },
  market: {
    spy_light: 'green', spy_checks: 3, qqq_light: 'green', qqq_checks: 3, light_verdict: 'dim',
    env: 'MIXED', score: 0, exposure: 'Reduced / selective', regime: 'Damaged', regime_score: 37.5,
    nh: 7, nl: 27, leaders_hold: 10, leaders_n: 10,
    themes_leading: ['Cybersecurity'], themes_improving: [], themes_weakening: ['Cloud Software'], themes_lagging: [],
  },
  setups: {
    pullback: { rows: [{ t: 'TEAM', rs: 97, focus: true, tight: true, qn: 4,
      theme: { name: 'Cloud Software', state: 'Weakening', accel: -3 } }] },
    ep: { rows: [] }, vcp: { rows: [] },
  },
  notes: {
    _market: { zh: '大盘这句是中文。', en: 'The market line in English.' },
    TEAM: { zh: '榜上同组五只里回踩最深。', en: 'The deepest pullback of the five in its group.' },
  },
}

const scans = [
  { key: 'all', label: 'All', count: 2548, loaded: true },
  { key: 'confluence', label: 'Confluence', count: 50, loaded: true },
]
// a row as the page builds it for the table it actually renders (ResultsTable)
const row = (lang) => ({
  t: 'TEAM', rs: 97, group: 'Cloud Software', gstate: 'Improving', heat: 7.5,
  e21: 0.48, s50: 2.66, m1: -3.5, hi: -6.1, note: focusDoc.notes.TEAM[lang], flagged: false,
  entry: { group: 'Cloud Software', group_state: 'Improving', rs_1m: 80 },
})

async function mount(lang) {
  localStorage.setItem('fluxus-lang', lang)
  vi.stubGlobal('fetch', () => Promise.resolve({ ok: true, json: () => Promise.resolve(focusDoc) }))
  let c
  await act(async () => {
    c = render(
      <LanguageProvider>
        <ScanBar scans={scans} scan="confluence" onScan={() => {}}
                 stateCounts={{ Leading: 3 }} states={new Set()} onToggleState={() => {}}
                 gates={new Set()} gateCounts={{ liquid: 1, exHealth: 1 }} onToggleGate={() => {}}
                 themes={[{ group: 'Cloud Software', members: 30 }]} chosen={new Set(['Cloud Software'])}
                 onTheme={() => {}} handoff={['Cloud Software']} search="" onSearch={() => {}}
                 receipt="1" wideNote={{ n: 12, onWiden: () => {} }} />
        <ResultsTable title="t" rows={[row(lang)]} n={10} setN={() => {}} showHeat defaultSort="heat" />
      </LanguageProvider>,
    )
  })
  await act(async () => { await new Promise((r) => setTimeout(r, 0)) })
  return c.container
}

describe('Screener in Chinese', () => {
  afterEach(() => { vi.unstubAllGlobals(); localStorage.clear() })

  it('prints the interface in Chinese, tickers and numbers untouched', async () => {
    const box = await mount('zh')
    const text = box.textContent
    // the funnel panel's strings left with the panel (2026-10-04 merge); the
    // merged page is covered by merged.test.jsx
    for (const zh of ['云软件',
      '不限', '不设', '已收窄到你在主题页上比较的那个主题', '去掉扫描', '改善',
      '代码', '热度', '主题', '离 21EMA', '离 50 日线', '1 月', '离 52 周高', '一句话', '+ 短名单', '全部',
      '榜上同组五只里回踩最深。', '0.48 ATR', '−3.5%']) {
      expect(text, zh).toContain(zh)
    }
    for (const en of ['Cloud Software',
      'any', 'none', 'Narrowed', 'drop the scan', 'Improving', 'Ticker', 'Heat', 'From 21EMA', 'Shortlist',
      'The deepest pullback']) {
      expect(text, en).not.toContain(en)
    }
    expect(text).toContain('TEAM')
    expect(box.querySelector('input[placeholder="查代码…"]')).not.toBeNull()
  })

  it('English stays as it was', async () => {
    const text = (await mount('en')).textContent
    for (const en of ['Cloud Software',
      'any', 'Narrowed to the theme you were comparing on Themes — Cloud Software.', 'drop the scan',
      'Improving', 'Ticker', 'Heat', 'Theme', 'From 21EMA', 'From 50-day', 'From 52w high', 'Note', '+ Shortlist',
      'The deepest pullback of the five in its group.']) {
      expect(text, en).toContain(en)
    }
  })
})
