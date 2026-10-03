/* global process */
import { translations } from '../../i18n/translations'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { LanguageProvider } from '../../i18n/LanguageContext'
import { dataName } from '../../i18n/names'
import { resetThemeBoardCache } from '../../hooks/useThemeBoard'
import RotationPage from './RotationPage'

// Andy 2026-10-03: 「整个网页需要有完整的中文和英文界面」. The Rotation page on
// the real data/output files, in Chinese, must not leave interface English behind.
const read = (f) => JSON.parse(readFileSync(resolve(process.cwd(), '..', 'data/output', f), 'utf8'))
const FILES = { 'groups.json': read('groups.json'), 'theme_ladder.json': read('theme_ladder.json'), 'theme_board.json': read('theme_board.json') }

describe('Rotation page in Chinese', () => {
  beforeEach(() => {
    localStorage.setItem('fluxus-lang', 'zh')
    resetThemeBoardCache()
    vi.stubGlobal('fetch', (url) => {
      const f = Object.keys(FILES).find((k) => String(url).endsWith(`/${k}`))
      return Promise.resolve(f ? { ok: true, status: 200, json: () => Promise.resolve(FILES[f]) } : { ok: false, status: 404, json: () => Promise.resolve(null) })
    })
  })
  afterEach(() => { localStorage.removeItem('fluxus-lang'); vi.unstubAllGlobals() })

  it('prints Chinese labels and theme names, no interface English', async () => {
    render(<LanguageProvider><RotationPage /></LanguageProvider>)
    await screen.findByText('代理 ETF 四态板')
    const board = FILES['theme_board.json'].themes
    await waitFor(() => expect(screen.getAllByText(dataName(board[0].theme, 'zh')).length).toBeGreaterThan(0))
    await waitFor(() => expect(document.body.textContent).toContain('RS 最近 2 周'))
    // open the explainer (its toggle label lives in shared HowToRead, not on this page)
    // HowToRead is shared; its label is whatever the zh dictionary says (English until it is translated)
    fireEvent.click(screen.getByRole('button', { name: new RegExp(translations.zh['db.howto.title'] ?? 'How to read this') }))
    const text = document.body.textContent

    for (const zh of ['地形', '轨迹', '两种动量和加速度', '爆发', '加速度', '耐力', 'RS 本周对比前 3 周', 'RS 最近 13 周',
      '领先', '走弱', '改善', '落后', '个主题', '每个主题只看一只代理 ETF', '梯队量到的每个组', '基准就是零线']) {
      expect(text, zh).toContain(zh)
    }
    for (const en of ['Proxy Board', 'RS Last 2 weeks', 'RS This week vs prior 3', 'RS Last 13 weeks', 'Leading', 'Weakening',
      'Improving', 'Lagging', 'Show fewer', ' themes', 'Each theme reads', 'Every group the ladder', 'The benchmark is the zero line',
      'Cloud Software', 'Semiconductors']) {
      expect(text, en).not.toContain(en)
    }
    // tickers and the trade's proper nouns stay Latin
    expect(text).toContain('SPY')
  })
})
